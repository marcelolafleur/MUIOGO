"""Drive the OG-Core Universal Installer and the local-register helper.

These are synchronous primitives. The background-job layer (InstallJob) calls them
inside a thread and passes `log` / `progress` callbacks to surface progress; nothing
here knows about job persistence or Flask.

Three install paths, matching the API schema:
  - catalog : wrap the installer with --repo / -Repo
  - repo_url: wrap the installer with --repo-url / -RepoUrl (+ optional branch)
  - local   : validate an existing folder, optionally `uv sync`, verify the import

The installer refuses to run inside an active venv/conda env, so every subprocess
uses Config.ogc_clean_env(). Install state is decided from the process result and a
filesystem/import check, never from scraping the installer's stdout (stdout is only
streamed into log_tail for display).
"""
import codecs
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from Classes.Base import Config

_FETCH_TIMEOUT_SECONDS = 30
_SUBPROCESS_TIMEOUT_SECONDS = 60 * 60  # an install can clone + uv sync large deps


class InstallerError(Exception):
    """Raised for a setup problem we can describe (bad path, missing pyproject)."""


def _noop(*_args, **_kwargs):
    pass


def repo_name_from_url(repo_url):
    """Folder leaf the installer clones into: basename of the URL without .git."""
    leaf = repo_url.rstrip("/").rsplit("/", 1)[-1]
    if leaf.endswith(".git"):
        leaf = leaf[:-4]
    return leaf


def read_pyproject_package_name(local_path):
    """Best-effort `[project].name` from a repo's pyproject.toml, or None."""
    pyproject = Path(local_path) / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return None
    # Prefer a real TOML parse (3.11+); fall back to a scoped regex on [project].
    try:
        import tomllib

        data = tomllib.loads(text)
        name = data.get("project", {}).get("name")
        if name:
            return name
    except (ModuleNotFoundError, ValueError):
        pass
    match = re.search(
        r"^\s*\[project\]\s*$.*?^\s*name\s*=\s*[\"']([^\"']+)[\"']",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else None


def import_name(package_name):
    """Module name to import: a project name normalised (og-eth -> og_eth)."""
    return (package_name or "").strip().replace("-", "_")


class Installer:
    # ── git helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _git(args, cwd, env=None, timeout=120):
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            env=env or Config.ogc_clean_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def git_head_sha(cls, local_path):
        try:
            out = cls._git(["rev-parse", "HEAD"], local_path)
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    @classmethod
    def git_remote_url(cls, local_path):
        try:
            out = cls._git(["config", "--get", "remote.origin.url"], local_path)
            return out.stdout.strip() if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    @classmethod
    def check_update(cls, local_path):
        """Compare local HEAD to its upstream after a fetch.

        Returns {local_commit_sha, remote_commit_sha, update_available}.
        Network failures leave remote as None and update_available False.
        """
        local_sha = cls.git_head_sha(local_path)
        remote_sha = None
        try:
            cls._git(["fetch", "--quiet"], local_path, timeout=120)
            out = cls._git(["rev-parse", "@{u}"], local_path)
            if out.returncode != 0:
                out = cls._git(["rev-parse", "origin/HEAD"], local_path)
            if out.returncode == 0:
                remote_sha = out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            remote_sha = None
        return {
            "local_commit_sha": local_sha,
            "remote_commit_sha": remote_sha,
            "update_available": bool(
                local_sha and remote_sha and local_sha != remote_sha
            ),
        }

    # ── import verification ──────────────────────────────────────────────────
    @staticmethod
    def verify_import(python_path, package_name):
        """Run `<python> -c "import <pkg>"`. Returns (ok, version_or_error)."""
        pkg = import_name(package_name)
        if not pkg:
            return False, "no package name to import"
        python_path = Path(python_path)
        if not python_path.exists():
            return False, f"interpreter not found: {python_path}"
        code = (
            f"import {pkg}; print(getattr({pkg}, '__version__', '?'))"
        )
        try:
            out = subprocess.run(
                [str(python_path), "-W", "ignore", "-c", code],
                env=Config.ogc_clean_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return False, str(exc)
        if out.returncode == 0:
            return True, out.stdout.strip() or "?"
        return False, (out.stderr.strip() or "import failed")

    # ── installer script fetch ───────────────────────────────────────────────
    @staticmethod
    def _script_url_and_name():
        if Config.SYSTEM == "Windows":
            return Config.OGC_INSTALLER_PS1_URL, "install.ps1"
        return Config.OGC_INSTALLER_SH_URL, "install.sh"

    @classmethod
    def ensure_installer_script(cls):
        """Download the platform installer script into the cache, return its path.

        Always refreshes from source so MUIOGO tracks the installer's latest, but
        falls back to a previously cached copy if the fetch fails.
        """
        url, name = cls._script_url_and_name()
        Config.OGC_INSTALLER_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        target = Config.OGC_INSTALLER_CACHE_DIR / name
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "MUIOGO-installer-fetch"}
            )
            with urllib.request.urlopen(req, timeout=_FETCH_TIMEOUT_SECONDS) as resp:
                content = resp.read()
            target.write_bytes(content)
            return target
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            if target.exists():
                return target
            raise InstallerError(f"Could not fetch the installer script: {exc}")

    # ── command building ─────────────────────────────────────────────────────
    @classmethod
    def _build_command(cls, script, *, source_type, dest_parent, catalog_key,
                       repo_url, branch):
        script = str(script)
        dest = str(dest_parent)
        if Config.SYSTEM == "Windows":
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script,
                   "-Dest", dest, "-Yes", "-NoLog"]
            if source_type == "catalog":
                cmd += ["-Repo", catalog_key]
            else:
                cmd += ["-RepoUrl", repo_url]
                if branch:
                    cmd += ["-Branch", branch]
        else:
            cmd = ["bash", script, "--dest", dest, "--yes", "--no-log"]
            if source_type == "catalog":
                cmd += ["--repo", catalog_key]
            else:
                cmd += ["--repo-url", repo_url]
                if branch:
                    cmd += ["--branch", branch]
        return cmd

    @staticmethod
    def _stream(cmd, log, cwd=None):
        """Run cmd, stream output into `log`, return the exit code.

        Reads raw chunks and splits on both newline and carriage-return, so git and
        uv progress bars (which update in place with \\r, not \\n) surface as they
        arrive instead of buffering into one blob until the process exits.
        """
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=Config.ogc_clean_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,  # unbuffered: deliver bytes as the child flushes them
        )
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        pending = ""
        try:
            while True:
                chunk = proc.stdout.read(256)
                if not chunk:
                    break
                pending += decoder.decode(chunk)
                # Emit every complete segment ended by \r or \n.
                while True:
                    match = re.search(r"[\r\n]", pending)
                    if match is None:
                        break
                    segment = pending[: match.start()].strip()
                    pending = pending[match.end():]
                    if segment:
                        log(segment)
            pending += decoder.decode(b"", final=True)
            if pending.strip():
                log(pending.strip())
            return proc.wait(timeout=_SUBPROCESS_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            proc.kill()
            log("Install timed out and was stopped.")
            return 124
        finally:
            if proc.stdout:
                proc.stdout.close()

    # ── orchestration: catalog / repo_url install ────────────────────────────
    @classmethod
    def run_installer(cls, *, source_type, repo_name, dest_parent,
                      catalog_key=None, repo_url=None, branch=None,
                      package_name=None, log=None, progress=None):
        """Clone + uv sync + verify one repo via the universal installer.

        Returns a result dict: ok, local_path, venv_path, python_path,
        package_name, commit_sha, version, error.
        """
        log = log or _noop
        progress = progress or _noop

        progress("preflight", "Preparing install")
        dest_parent = Path(dest_parent)
        dest_parent.mkdir(parents=True, exist_ok=True)
        script = cls.ensure_installer_script()

        local_path = dest_parent / repo_name
        cmd = cls._build_command(
            script, source_type=source_type, dest_parent=dest_parent,
            catalog_key=catalog_key, repo_url=repo_url, branch=branch,
        )

        progress("uv_sync", "Cloning and installing dependencies with uv")
        log(f"Running installer for {repo_name}...")
        rc = cls._stream(cmd, log)

        venv_path = local_path / ".venv"
        python_path = Config.venv_python_path(venv_path)

        if rc != 0:
            return cls._fail(local_path, venv_path, python_path,
                             f"Installer exited with code {rc}.")
        if not python_path.exists():
            return cls._fail(local_path, venv_path, python_path,
                             "Install finished but no environment was created.")

        # Package: from the register for catalog installs, else inferred post-clone.
        pkg = package_name or read_pyproject_package_name(local_path)
        if not pkg:
            return cls._fail(local_path, venv_path, python_path,
                             "Could not determine the package name to verify.")

        progress("verify_import", "Verifying the model imports")
        ok, detail = cls.verify_import(python_path, pkg)
        if not ok:
            return cls._fail(local_path, venv_path, python_path,
                             f"Import check failed: {detail}")
        log(f"Imported {import_name(pkg)} ({detail}).")

        progress("register", "Recording the installed calibration")
        return {
            "ok": True,
            "local_path": str(local_path),
            "venv_path": str(venv_path),
            "python_path": str(python_path),
            "package_name": pkg,
            "commit_sha": cls.git_head_sha(local_path),
            "repo_url": repo_url or cls.git_remote_url(local_path),
            "version": detail,
            "error": None,
        }

    # ── orchestration: register an existing local copy ───────────────────────
    @classmethod
    def register_local(cls, *, local_path, package_name=None, run_uv_sync=True,
                       log=None, progress=None):
        """Validate a local repo, optionally uv sync, verify import, return result."""
        log = log or _noop
        progress = progress or _noop

        progress("preflight", "Checking the folder")
        local_path = Path(local_path)
        if not local_path.is_dir():
            raise InstallerError(f"Path does not exist or is not a folder: {local_path}")
        if not (local_path / "pyproject.toml").exists():
            raise InstallerError(
                "No pyproject.toml in this folder, so it cannot be set up with uv."
            )

        pkg = package_name or read_pyproject_package_name(local_path)
        if not pkg:
            raise InstallerError("Could not read the package name from pyproject.toml.")

        venv_path = local_path / ".venv"
        python_path = Config.venv_python_path(venv_path)

        if run_uv_sync:
            if not cls._has_uv():
                return cls._fail(
                    local_path, venv_path, python_path,
                    "uv is not installed or not on PATH, so the environment "
                    "cannot be built. Install uv, or register with the build step off.",
                )
            progress("uv_sync", "Building the environment with uv sync")
            log("Running uv sync...")
            rc = cls._stream(["uv", "sync", "--extra", "dev"], log, cwd=local_path)
            if rc != 0:
                return cls._fail(local_path, venv_path, python_path,
                                 f"uv sync exited with code {rc}.")
            python_path = Config.venv_python_path(venv_path)

        if not python_path.exists():
            return cls._fail(
                local_path, venv_path, python_path,
                "No .venv found. Re-run with environment build enabled.",
            )

        progress("verify_import", "Verifying the model imports")
        ok, detail = cls.verify_import(python_path, pkg)
        if not ok:
            return cls._fail(local_path, venv_path, python_path,
                             f"Import check failed: {detail}")
        log(f"Imported {import_name(pkg)} ({detail}).")

        progress("register", "Recording the calibration")
        return {
            "ok": True,
            "local_path": str(local_path),
            "venv_path": str(venv_path),
            "python_path": str(python_path),
            "package_name": pkg,
            "commit_sha": cls.git_head_sha(local_path),
            "repo_url": cls.git_remote_url(local_path),
            "version": detail,
            "error": None,
        }

    # ── uv sync helper (register path) ───────────────────────────────────────
    @classmethod
    def _has_uv(cls):
        try:
            out = subprocess.run(
                ["uv", "--version"],
                env=Config.ogc_clean_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
            return out.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    @staticmethod
    def _fail(local_path, venv_path, python_path, message):
        return {
            "ok": False,
            "local_path": str(local_path),
            "venv_path": str(venv_path),
            "python_path": str(python_path),
            "package_name": None,
            "commit_sha": None,
            "repo_url": None,
            "version": None,
            "error": message,
        }
