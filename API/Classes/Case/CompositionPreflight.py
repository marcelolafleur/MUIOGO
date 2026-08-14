# Classes/Case/CompositionPreflight.py
#
# Static composition linter: checks a scenario composition for provable
# infeasibilities and common data defects BEFORE any solver runs — milliseconds
# of JSON arithmetic instead of hours of simplex on an infeasible LP.
#
# Motivating defect class (observed in a real country case): a user-defined
# EQUALITY constraint encodes a capacity roadmap (e.g. "nuclear = 1.2 GW in
# 2032, 2.4 in 2035") while the composition's investment envelopes
# (TotalAnnualMaxCapacityInvestment) leave too little buildable capacity
# between the target years. The LP is infeasible, but a simplex solver can
# grind for hours before saying so — and the defect is provable statically.
#
# Checks:
#   A. Per-year UDC attainability: for each constraint and each year with an
#      explicit merged RHS, compute the attainable LHS interval from member
#      technologies' capacity bounds (ResidualCapacity, cumulative
#      TotalAnnualMaxCapacityInvestment, TotalAnnualMax/MinCapacity) times the
#      capacity multipliers. Equality RHS outside the interval, or inequality
#      minimum above the RHS, is a provable infeasibility.
#   B. Path transitions for equalities: between consecutive BINDING years the
#      equality pins the member capacity at both ends; without early
#      retirement the capacity can rise at most by what is buildable in the
#      gap. A required rise above that is provably infeasible. Rows with
#      all-zero multipliers and zero RHS are vacuous (0 = 0) and pin nothing —
#      anchoring on them fabricates errors, so only binding years anchor.
#   C. Vacuous rows with nonzero RHS (0 = c, c != 0): provable contradiction.
#   D. TotalTechnologyAnnualActivityLowerLimit above its UpperLimit.
#   E. AnnualEmissionLimit on an emission no technology emits (cap binds
#      nothing — warning, likely a modeling mistake).
#
# Scenario layer merge semantics (validated against generated
# data_processed.txt): layers apply SC_0 (base) first, then active scenarios
# in genData["osy-scenarios"] order; an explicit numeric value in a later
# layer OVERRIDES, None/missing INHERITS. Values >= 9999 are open-bound
# sentinels, treated as unbounded.
#
# Conservative by design: capacity lower bounds ignore forced-build
# (TAMinCI) accumulation because retirement timing is not tracked statically,
# so every "provable" finding is a real impossibility — no false positives
# from retirement arithmetic. Constraint-years with activity multipliers
# (CAM) are reported as skipped, not guessed.

import json
import sys
from pathlib import Path

SENTINEL = 9999  # >= this: open bound, treated as unbounded
INF = float("inf")


def merged(param_map: dict, active_scenario_ids: list) -> dict:
    """Merge scenario layers of one parameter map (explicit overrides, None inherits)."""
    order = ["SC_0"] + [s for s in active_scenario_ids if s != "SC_0"]
    out: dict = {}
    for sc in order:
        for r in param_map.get(sc) or []:
            key = (r.get("TechId"), r.get("MoId"), r.get("EmisId"), r.get("ConId"))
            tgt = out.setdefault(key, {})
            for k, v in r.items():
                if k.isdigit() and isinstance(v, (int, float)):
                    tgt[k] = v
    return out


def by_tech(m: dict) -> dict:
    out: dict = {}
    for (tech, _mo, _emis, _con), years in m.items():
        out.setdefault(tech, {}).update(years)
    return out


def by_con_tech(m: dict) -> dict:
    out: dict = {}
    for (tech, _mo, _emis, con), years in m.items():
        out[(con, tech)] = years
    return out


def _load(case_dir: str, scenario_names: list):
    d = Path(case_dir)
    g = json.load(open(d / "genData.json"))
    name2id = {s["Scenario"]: s["ScenarioId"] for s in g["osy-scenarios"]}
    unknown = [n for n in scenario_names if n not in name2id]
    if unknown:
        raise ValueError(f"unknown scenario(s) {unknown}; case has {list(name2id)}")
    active = [s["ScenarioId"] for s in g["osy-scenarios"] if s["Scenario"] in scenario_names]
    tech_name = {t["TechId"]: t["Tech"] for t in g.get("osy-tech") or []}
    ryt = json.load(open(d / "RYT.json"))
    rytcn = json.load(open(d / "RYTCn.json"))
    rycn = json.load(open(d / "RYCn.json"))
    rye = json.load(open(d / "RYE.json")) if (d / "RYE.json").exists() else {}
    rytem = json.load(open(d / "RYTEM.json")) if (d / "RYTEM.json").exists() else {}
    return g, active, tech_name, ryt, rytcn, rycn, rye, rytem


def _cap_bounds(tech, y, years_sorted, rc, tamaxci, taminci, tamaxc, taminc):
    """Attainable [total capacity lo, hi] and [new capacity lo, hi] for tech in year y."""
    def val(m, yy, default):
        v = (m.get(tech) or {}).get(yy)
        return default if v is None else v

    resid = val(rc, y, 0.0)
    hi = resid
    for yy in years_sorted:
        if int(yy) > int(y):
            break
        mx = val(tamaxci, yy, INF)
        if mx >= SENTINEL:
            hi = INF
            break
        hi += mx
    tmaxc = val(tamaxc, y, INF)
    if tmaxc < SENTINEL:
        hi = min(hi, tmaxc)
    lo = max(resid, val(taminc, y, 0.0))
    n_lo = val(taminci, y, 0.0)
    n_hi = val(tamaxci, y, INF)
    if n_hi >= SENTINEL:
        n_hi = INF
    return lo, hi, n_lo, n_hi


def lint_composition(case_dir: str, scenario_names: list) -> dict:
    """Lint a scenario composition of a case. Returns
    {"errors": [...], "warnings": [...], "skipped": [...]} of message strings.
    Errors are PROVABLE infeasibilities or contradictions; a nonempty errors
    list means the composition cannot solve as data'd."""
    g, active, tech_name, ryt, rytcn, rycn, rye, rytem = _load(case_dir, scenario_names)

    def tn(t):
        return tech_name.get(t, t)

    rc = by_tech(merged(ryt.get("RC") or {}, active))
    tamaxci = by_tech(merged(ryt.get("TAMaxCI") or {}, active))
    taminci = by_tech(merged(ryt.get("TAMinCI") or {}, active))
    tamaxc = by_tech(merged(ryt.get("TAMaxC") or {}, active))
    taminc = by_tech(merged(ryt.get("TAMinC") or {}, active))
    tau = by_tech(merged(ryt.get("TAU") or {}, active))
    tal = by_tech(merged(ryt.get("TAL") or {}, active))
    ccm = by_con_tech(merged(rytcn.get("CCM") or {}, active))
    cncm = by_con_tech(merged(rytcn.get("CNCM") or {}, active))
    cam = by_con_tech(merged(rytcn.get("CAM") or {}, active))
    ucc: dict = {}
    for (_t, _m, _e, con), yrs in merged(rycn.get("UCC") or {}, active).items():
        ucc.setdefault(con, {}).update(yrs)

    all_years = sorted({y for m in (rc, tamaxci) for t in m for y in m[t]}, key=int)
    errors, warnings, skipped = [], [], []

    for con in g.get("osy-constraints") or []:
        cid, cname, tag = con.get("ConId"), con.get("Con"), int(con.get("Tag", 0))
        members = con.get("CM") or []
        rhs_years = ucc.get(cid) or {}

        # --- A: per-year attainability ---
        for y, rhs in sorted(rhs_years.items(), key=lambda kv: int(kv[0])):
            act_dep = [t for t in members if (cam.get((cid, t)) or {}).get(y)]
            if act_dep:
                skipped.append(
                    f"{cname} [{y}]: activity-dependent (CAM on "
                    f"{', '.join(tn(t) for t in act_dep[:3])}) — not statically provable")
                continue
            lo = hi = 0.0
            detail = []
            for t in members:
                c_cap = (ccm.get((cid, t)) or {}).get(y) or 0.0
                c_new = (cncm.get((cid, t)) or {}).get(y) or 0.0
                if c_cap == 0.0 and c_new == 0.0:
                    continue
                tlo, thi, nlo, nhi = _cap_bounds(
                    t, y, all_years, rc, tamaxci, taminci, tamaxc, taminc)
                for coef, blo, bhi in ((c_cap, tlo, thi), (c_new, nlo, nhi)):
                    if coef == 0.0:
                        continue
                    a, b = coef * blo, coef * bhi
                    lo += min(a, b)
                    hi += max(a, b)
                detail.append(f"{tn(t)}: cap∈[{tlo:g},{thi:g}] × {c_cap:g}")
            eps = 1e-6 * max(1.0, abs(rhs))
            if tag == 1 and (rhs < lo - eps or rhs > hi + eps):
                errors.append(
                    f"EQUALITY UNATTAINABLE: {cname} [{y}] requires {rhs:g}, "
                    f"attainable LHS ∈ [{lo:g}, {hi:g}]  ({'; '.join(detail)})")
            elif tag == 0 and lo > rhs + eps:
                errors.append(
                    f"INEQUALITY UNSATISFIABLE: {cname} [{y}] requires LHS ≤ {rhs:g}, "
                    f"minimum attainable LHS = {lo:g}  ({'; '.join(detail)})")

        # --- B/C: binding-year path transitions + vacuous rows ---
        if tag != 1:
            continue
        binding = []
        for y, rhs in sorted(rhs_years.items(), key=lambda kv: int(kv[0])):
            coefs = {t: (ccm.get((cid, t)) or {}).get(y) or 0.0 for t in members}
            nz = {t: c for t, c in coefs.items() if c != 0.0}
            has_other = any(
                ((cncm.get((cid, t)) or {}).get(y) or (cam.get((cid, t)) or {}).get(y))
                for t in members)
            if not nz and not has_other:
                if abs(rhs) > 1e-12:
                    errors.append(
                        f"VACUOUS ROW WITH NONZERO RHS: {cname} [{y}] demands {rhs:g} "
                        f"but every member multiplier is zero — 0 = {rhs:g}")
                continue
            if has_other:
                binding.append(None)  # non-capacity terms break the chain; stay honest
                continue
            uniq = set(nz.values())
            binding.append((y, rhs, nz, uniq.pop() if len(uniq) == 1 else None))
        chain = [b for b in binding if b is not None]
        for (y0, r0, nz0, c0), (y1, r1, nz1, c1) in zip(chain, chain[1:]):
            if c0 is None or c1 is None or c0 != c1 or set(nz0) != set(nz1):
                continue  # mixed coefficients: covered by the static check only
            s0, s1 = r0 / c0, r1 / c1
            buildable = 0.0
            for t in nz1:
                for yy in all_years:
                    if int(y0) < int(yy) <= int(y1):
                        v = (tamaxci.get(t) or {}).get(yy)
                        v = INF if v is None or v >= SENTINEL else v
                        buildable += v
                if buildable == INF:
                    break
            eps = 1e-6 * max(1.0, abs(s0), abs(s1))
            if s1 > s0 + buildable + eps:
                errors.append(
                    f"EQUALITY PATH UNREACHABLE: {cname} pins member capacity to {s0:g} "
                    f"in {y0} and demands {s1:g} in {y1}, but only {buildable:g} is "
                    f"buildable in ({y0},{y1}] — max attainable {s0 + buildable:g}")

    # --- D: activity lower bound above upper bound ---
    for t in sorted(set(tal) & set(tau)):
        for y in sorted(set(tal[t]) & set(tau[t]), key=int):
            lo_, hi_ = tal[t][y], tau[t][y]
            if hi_ >= SENTINEL:
                continue
            if lo_ > hi_ + 1e-9:
                errors.append(
                    f"TAL>TAU: {tn(t)} [{y}] activity lower bound {lo_:g} "
                    f"exceeds upper bound {hi_:g}")

    # --- E: emission caps with no coverage ---
    ael: dict = {}
    for (_t, _m, emis, _c), yrs in merged(rye.get("AEL") or {}, active).items():
        ael.setdefault(emis, {}).update(yrs)
    covered = set()
    for (_t, _m, emis, _c), yrs in merged(rytem.get("EAR") or {}, active).items():
        if any(abs(v) > 1e-12 for v in yrs.values()):
            covered.add(emis)
    for emis, yrs in ael.items():
        live = [y for y, v in yrs.items() if v < SENTINEL]
        if live and emis not in covered:
            warnings.append(
                f"EMISSION CAP WITHOUT COVERAGE: {emis} has AnnualEmissionLimit in "
                f"{len(live)} year(s) but no technology has a nonzero emission "
                f"activity ratio for it")

    return {"errors": errors, "warnings": warnings, "skipped": skipped}


def main(argv: list) -> int:
    """CLI: python -m Classes.Case.CompositionPreflight <case_dir> <SCENARIO> [...]
    Exit codes: 2 provable infeasibility, 1 warnings only, 0 clean."""
    if len(argv) < 3:
        print(main.__doc__)
        return 1
    case_dir, scenario_names = argv[1], argv[2:]
    res = lint_composition(case_dir, scenario_names)
    comp = "+".join(scenario_names)
    print(f"CompositionPreflight: {Path(case_dir).name} [{comp}] — "
          f"{len(res['errors'])} error(s), {len(res['warnings'])} warning(s), "
          f"{len(res['skipped'])} skipped")
    for e in res["errors"]:
        print(f"  ERROR   {e}")
    for w in res["warnings"]:
        print(f"  WARNING {w}")
    for s in res["skipped"]:
        print(f"  skipped {s}")
    return 2 if res["errors"] else (1 if res["warnings"] else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
