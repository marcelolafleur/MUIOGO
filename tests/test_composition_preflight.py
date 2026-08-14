"""
Acceptance tests for Classes.Case.CompositionPreflight on synthetic minimal cases.

All cases: one technology NUKE, one user-defined equality constraint TARGET with
capacity multiplier -1, years 2030-2036, capacity targets 1.2 @ 2032 and
2.4 @ 2035, vacuous rows (0 = 0) elsewhere.

  tight_gap      - investment envelopes open before 2032, near-closed 2033-2035
                   (0.1/yr). The real-world defect shape: the 2032 target is
                   attainable, the 2032->2035 spacing is not. Must flag exactly
                   one PATH error.
  opened_prefix  - same, but the pre-2032 envelope opened even wider (a
                   plausible but wrong "fix"). The equality PIN at 2032 makes
                   pre-2032 capacity irrelevant; a naive running-maximum check
                   goes quiet here. Must still flag the 2032->2035 transition.
  feasible       - envelopes open 2033-2035 (1.0/yr, 3.0 total >= the 1.2
                   needed). Must report zero errors.
  vacuous_rhs    - nonzero RHS in a year where every member multiplier is zero
                   (0 = -0.5). Must flag the vacuous-row error.
"""

import json

import pytest

from Classes.Case.CompositionPreflight import lint_composition

YEARS = [str(y) for y in range(2030, 2037)]


def build_case(root, name, tamaxci_by_year, ucc_extra=None):
    d = root / name
    d.mkdir()
    yrs0 = {y: 0 for y in YEARS}
    gendata = {
        "osy-casename": name,
        "osy-years": [int(y) for y in YEARS],
        "osy-scenarios": [
            {"ScenarioId": "SC_0", "Scenario": "BASE"},
            {"ScenarioId": "SC_re", "Scenario": "RE"},
        ],
        "osy-tech": [{"TechId": "T_NUKE", "Tech": "NUKE"}],
        "osy-constraints": [
            {"ConId": "CO_t", "Con": "TARGET", "Tag": 1, "CM": ["T_NUKE"]}
        ],
    }
    json.dump(gendata, open(d / "genData.json", "w"))
    ucc_years = dict(yrs0)
    ucc_years.update({"2032": -1.2, "2035": -2.4})
    ucc_years.update(ucc_extra or {})
    json.dump(
        {"UCC": {"SC_0": [], "SC_re": [dict(ConId="CO_t", **ucc_years)]}},
        open(d / "RYCn.json", "w"),
    )
    ccm_years = dict(yrs0)
    ccm_years.update({"2032": -1, "2035": -1})
    json.dump(
        {
            "CCM": {"SC_re": [dict(TechId="T_NUKE", ConId="CO_t", **ccm_years)]},
            "CNCM": {},
            "CAM": {},
        },
        open(d / "RYTCn.json", "w"),
    )
    json.dump(
        {
            "RC": {"SC_0": [dict(TechId="T_NUKE", **yrs0)]},
            "TAMaxCI": {"SC_0": [dict(TechId="T_NUKE", **tamaxci_by_year)]},
            "TAMinCI": {},
            "TAMaxC": {},
            "TAMinC": {},
            "TAU": {},
            "TAL": {},
        },
        open(d / "RYT.json", "w"),
    )
    return d


@pytest.fixture()
def tight_envelope():
    t = {y: 0 for y in YEARS}
    t.update({"2030": 999999, "2031": 999999, "2032": 999999,
              "2033": 0.1, "2034": 0.1, "2035": 0.1})
    return t


@pytest.fixture()
def feasible_envelope():
    t = {y: 0 for y in YEARS}
    t.update({"2030": 999999, "2031": 999999, "2032": 999999,
              "2033": 1.0, "2034": 1.0, "2035": 1.0})
    return t


def test_tight_gap_flags_exactly_the_spacing_transition(tmp_path, tight_envelope):
    case = build_case(tmp_path, "tight_gap", tight_envelope)
    res = lint_composition(str(case), ["BASE", "RE"])
    path_errors = [e for e in res["errors"] if "PATH UNREACHABLE" in e]
    assert len(path_errors) == 1
    assert "2032" in path_errors[0] and "2035" in path_errors[0]
    assert res["errors"] == path_errors  # nothing else fabricated


def test_opened_prefix_is_not_a_fix(tmp_path, tight_envelope):
    # Opening the pre-2032 envelope wider cannot help: the 2032 equality pins
    # capacity to exactly 1.2, so the 2032->2035 gap still lacks 1.2 buildable.
    case = build_case(tmp_path, "opened_prefix", dict(tight_envelope, **{"2030": 999999}))
    res = lint_composition(str(case), ["BASE", "RE"])
    assert sum("PATH UNREACHABLE" in e for e in res["errors"]) == 1


def test_feasible_spacing_is_clean(tmp_path, feasible_envelope):
    case = build_case(tmp_path, "feasible", feasible_envelope)
    res = lint_composition(str(case), ["BASE", "RE"])
    assert res["errors"] == []


def test_vacuous_row_with_nonzero_rhs(tmp_path, feasible_envelope):
    case = build_case(tmp_path, "vacuous_rhs", feasible_envelope,
                      ucc_extra={"2033": -0.5})
    res = lint_composition(str(case), ["BASE", "RE"])
    assert any("VACUOUS ROW" in e for e in res["errors"])


def test_unknown_scenario_raises(tmp_path, feasible_envelope):
    case = build_case(tmp_path, "unknown_scn", feasible_envelope)
    with pytest.raises(ValueError):
        lint_composition(str(case), ["BASE", "NOPE"])
