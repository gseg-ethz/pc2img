#!/usr/bin/env python3
# .github/scripts/test_check_ruleset_drift.py
r"""Unit tests for `check_ruleset_drift`'s comparator entry point.

Plain pytest with file-backed fixtures written under `tmp_path`: no network. Run
with::

    python -m pytest .github/scripts/test_check_ruleset_drift.py -q

The module lives alongside the script it tests so that `import check_ruleset_drift`
resolves the same way it does for the other CLIs in this directory; the `sys.path`
insertion below makes that work when pytest is invoked from the repo root.

Note that ruff's `per-file-ignores` relax docstring rules under `tests/**` only,
which does not cover `.github/scripts/`, so every test here carries a
numpy-convention docstring by design rather than by accident.
"""

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_ruleset_drift as drift  # noqa: E402  — deliberately after the sys.path insertion above
import ruleset_lib  # noqa: E402

REPO = "gseg-ethz/pc2img"
RULESET_NAME = "protect-main"
# An arbitrary fixture id, resolved by NAME at runtime the same way a live
# ruleset id is, so nothing here should carry a real one.
RULESET_ID = 7654321


def committed_payload() -> dict:
    """Build a minimal committed ruleset payload in the committed files' shape.

    Carries two required contexts, so a removal from the live side is
    observable by a test that drops one of them.

    Returns
    -------
    dict
        A payload carrying exactly the six sendable keys.
    """
    return {
        "name": RULESET_NAME,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "bypass_actors": [],
        "rules": [
            {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": False,
                    "required_status_checks": [
                        {"context": "unit-tests", "integration_id": None},
                        {"context": "lint", "integration_id": None},
                    ],
                },
            },
            {"type": "non_fast_forward"},
        ],
    }


def live_payload() -> dict:
    """Build a live ruleset payload in the shape the API actually returns.

    Its protection content is otherwise identical to `committed_payload` — every
    read-filled and envelope key present here is either dropped by normalisation
    or has a matching committed value, so a straight comparison compares clean.

    Returns
    -------
    dict
        A payload carrying the live envelope keys and the read-filled inner keys.
    """
    return {
        "id": RULESET_ID,
        "name": RULESET_NAME,
        "target": "branch",
        "source_type": "Repository",
        "source": REPO,
        "enforcement": "active",
        "node_id": "RRS_lACkUmVwbw",
        "_links": {"self": {"href": "https://api.github.com/..."}},
        # The epoch, so no reader can mistake a fixture timestamp for a record
        # of when this kit was taken from anywhere. The VALUE is never asserted;
        # only that these live-only envelope keys get dropped.
        "created_at": "1970-01-01T00:00:00.000Z",
        "updated_at": "1970-01-01T00:00:00.000Z",
        "current_user_can_bypass": "always",
        "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
        "bypass_actors": [],
        "rules": [
            {"type": "non_fast_forward"},
            {
                "type": "pull_request",
                "parameters": {
                    "required_approving_review_count": 0,
                    "allowed_merge_methods": ["merge", "squash", "rebase"],
                    "dismissal_restriction": {"enabled": False, "allowed_actors": []},
                    "required_reviewers": [],
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "strict_required_status_checks_policy": False,
                    "required_status_checks": [
                        {"context": "lint"},
                        {"context": "unit-tests"},
                    ],
                },
            },
        ],
    }


def write_json(directory: pathlib.Path, name: str, payload: dict) -> pathlib.Path:
    """Write `payload` as JSON under `directory/name` and return the path written.

    Parameters
    ----------
    directory
        A directory that already exists (`tmp_path` in every caller).
    name
        The file name, e.g. ``"live.json"``.
    payload
        The JSON-serialisable payload to write.

    Returns
    -------
    pathlib.Path
        The path written.
    """
    path = directory / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def spec(name: str, live: pathlib.Path, committed: pathlib.Path) -> str:
    """Build one ``NAME:LIVE:COMMITTED`` positional argument for `drift.main`.

    Parameters
    ----------
    name
        The ruleset name.
    live
        Path to the live payload file.
    committed
        Path to the committed payload file.

    Returns
    -------
    str
        The colon-joined argument in the shape `drift.parse_spec` expects.
    """
    return f"{name}:{live}:{committed}"


def test_an_identical_live_read_compares_clean_and_prints_the_ok_line(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A live read identical in protection content to the committed payload compares clean.

    This is the passing control every other polarity in this module is measured
    against: if this test were ever red, every other test's verdict about drift
    would be unreliable too.
    """
    live = write_json(tmp_path, "live.json", live_payload())
    committed = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main([spec(RULESET_NAME, live, committed)])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "check_ruleset_drift: OK" in out
    assert "0 differences surviving" in out
    assert "::error::" not in out


def test_a_populated_bypass_actors_list_is_surviving_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A populated bypass-actors list on the live side is surviving drift, never silently accepted.

    This is the floor's first prohibition: a bypass actor added outside git —
    in the GitHub UI, under pressure, without a matching commit — must alarm,
    not compare clean.
    """
    live = live_payload()
    live["bypass_actors"] = [{"actor_id": 1, "actor_type": "Team"}]
    live_path = write_json(tmp_path, "live.json", live)
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main([spec(RULESET_NAME, live_path, committed_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    error_lines = [line for line in out.splitlines() if line.startswith("::error::")]
    assert any("drift survives normalisation" in line and "bypass_actors" in line for line in error_lines), out


def test_a_required_context_missing_from_the_live_read_is_surviving_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dropping one required context from the live read is surviving drift, not a rounding error.

    A missing required-status-check context is exactly what an emergency UI
    edit under pressure would remove; a shrunk list must never compare clean.
    """
    live = live_payload()
    for rule in live["rules"]:
        if rule["type"] == "required_status_checks":
            rule["parameters"]["required_status_checks"] = [
                check for check in rule["parameters"]["required_status_checks"] if check["context"] != "lint"
            ]
    live_path = write_json(tmp_path, "live.json", live)
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main([spec(RULESET_NAME, live_path, committed_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    error_lines = [line for line in out.splitlines() if line.startswith("::error::")]
    assert any("drift survives normalisation" in line and "required_status_checks" in line for line in error_lines), out


def test_an_api_error_envelope_is_a_named_read_failure_never_no_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A refused read is reported as a named failure and never rendered as a clean comparison.

    The live payload is fetched to disk by an earlier workflow step, so a
    refused request lands here as perfectly valid JSON that would otherwise
    look like success.
    """
    envelope = {
        "message": "Upgrade to GitHub Pro or make this repository public to enable this feature.",
        "documentation_url": "https://docs.github.com/rest/repos/rules#create-a-repository-ruleset",
        "status": ruleset_lib.RULESETS_UNAVAILABLE_STATUS,
    }
    live_path = write_json(tmp_path, "live.json", envelope)
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main([spec(RULESET_NAME, live_path, committed_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "OK" not in out
    error_lines = [line for line in out.splitlines() if line.startswith("::error::")]
    assert any(
        "API error envelope" in line and f'"{ruleset_lib.RULESETS_UNAVAILABLE_STATUS}"' in line for line in error_lines
    ), out


def test_an_absent_bypass_actors_key_is_a_hard_failure_never_an_empty_list(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An absent bypass-actors key on the live side is a hard failure, never an empty list.

    GitHub returns this key only to a requester with write access to the
    ruleset; a read-scoped token receives a payload missing it entirely, and
    that absence must never compare equal to a committed empty list.
    """
    live = live_payload()
    del live[ruleset_lib.BYPASS_ACTORS_KEY]
    live_path = write_json(tmp_path, "live.json", live)
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main([spec(RULESET_NAME, live_path, committed_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "OK" not in out
    error_lines = [line for line in out.splitlines() if line.startswith("::error::")]
    assert any(ruleset_lib.BYPASS_ACTORS_KEY in line for line in error_lines), out


def test_a_missing_or_non_object_live_file_is_a_named_read_failure(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A live path that cannot be read, and one that parses to a non-object, are both named failures.

    Two distinct read failures share one exception type in the comparator;
    this test pins that both surface worded for what actually went wrong
    rather than a generic message.
    """
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    missing_live = tmp_path / "does-not-exist.json"
    exit_code = drift.main([spec(RULESET_NAME, missing_live, committed_path)])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "could not be read as JSON" in out

    list_live = tmp_path / "list-live.json"
    list_live.write_text(json.dumps([]), encoding="utf-8")
    exit_code = drift.main([spec(RULESET_NAME, list_live, committed_path)])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "expected a JSON object" in out


def test_a_malformed_pair_argument_is_reported_and_the_remaining_pairs_still_run(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A malformed pair argument is reported by itself; the well-formed pairs after it still run.

    One bad argument must not silence the report for every pair that follows
    it in the same invocation — proving the loop over `argv` continues past a
    parse failure instead of aborting the whole run.
    """
    live_path = write_json(tmp_path, "live.json", live_payload())
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main(["bad-spec", spec(RULESET_NAME, live_path, committed_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "malformed pair" in captured.out
    assert "normalised away" in captured.err


def test_a_live_only_key_that_normalisation_does_not_drop_is_reported_as_drift(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A brand-new top-level key GitHub adds to the live schema is reported as drift, not ignored.

    The comparator's current predicate is equality after normalisation, and
    this test pins that predicate as it stands today: normalisation drops a
    fixed, named set of keys, and anything outside that set — including a key
    the API has not invented yet — compares. Whether equality or containment
    is the right predicate for a schema GitHub keeps extending is a design
    question tracked separately and is NOT resolved by this test. If the
    predicate is ever changed to containment, this is the test to change
    first.
    """
    live = live_payload()
    live["some_new_github_field"] = True
    live_path = write_json(tmp_path, "live.json", live)
    committed_path = write_json(tmp_path, "committed.json", committed_payload())

    exit_code = drift.main([spec(RULESET_NAME, live_path, committed_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    error_lines = [line for line in out.splitlines() if line.startswith("::error::")]
    assert any("some_new_github_field" in line for line in error_lines), out


def test_no_arguments_prints_usage_and_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    """Calling `main` with no positional arguments reports usage and exits 1.

    Measured against the comparator as it stands today: the usage line is
    written to stderr rather than stdout, so this test reads the combined
    capture instead of assuming a stream the comparator does not use for it.
    """
    exit_code = drift.main([])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "usage:" in (captured.out + captured.err)
