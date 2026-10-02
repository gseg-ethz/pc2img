#!/usr/bin/env python3
# .github/scripts/test_preflight_ruleset_apply.py
"""Unit tests for the apply preflight.

Every case here is one of the behaviours the gate exists to guarantee: that it
refuses in BOTH directions (a context nothing produces, and a job removed while a
payload still requires it), that a refusal leaves no send payload behind for the
workflow's send step to pick up, that an unreadable workflow is a violation
rather than a skip, and that the payload it does emit is a schema-valid request
body rather than a comparison artefact.

Run with ``python -m pytest .github/scripts/test_preflight_ruleset_apply.py -q``
from the repository root.
"""

import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import preflight_ruleset_apply as preflight  # noqa: E402  (path shim must precede the import)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def make_payload(
    name: str = "protect-main",
    branch: str = "refs/heads/main",
    contexts: tuple[str, ...] = ("Lint (pre-commit)", "Tests (pytest)"),
) -> dict[str, object]:
    """Build a committed-shaped ruleset payload carrying `contexts`.

    Parameters
    ----------
    name
        The ruleset name.
    branch
        The single included ref name.
    contexts
        Required status-check context strings.

    Returns
    -------
    dict
        A payload with exactly the six sendable keys, in the committed order.
    """
    return {
        "name": name,
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": [branch], "exclude": []}},
        "bypass_actors": [],
        "rules": [
            {"type": "pull_request", "parameters": {"required_approving_review_count": 0}},
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [{"context": c, "integration_id": None} for c in contexts],
                },
            },
            {"type": "non_fast_forward"},
        ],
    }


def write_payload(rulesets_dir: pathlib.Path, filename: str, payload: dict[str, object]) -> pathlib.Path:
    """Write `payload` into `rulesets_dir` as `filename` and return the path.

    Parameters
    ----------
    rulesets_dir
        Directory to create and write into.
    filename
        Basename of the committed payload.
    payload
        The payload object.

    Returns
    -------
    pathlib.Path
        The written file's path.
    """
    rulesets_dir.mkdir(parents=True, exist_ok=True)
    path = rulesets_dir / filename
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_workflow(workflow_dir: pathlib.Path, filename: str, text: str) -> pathlib.Path:
    """Write a raw workflow document into `workflow_dir`.

    Parameters
    ----------
    workflow_dir
        Directory to create and write into.
    filename
        Basename of the workflow file.
    text
        Raw YAML text.

    Returns
    -------
    pathlib.Path
        The written file's path.
    """
    workflow_dir.mkdir(parents=True, exist_ok=True)
    path = workflow_dir / filename
    path.write_text(text, encoding="utf-8")
    return path


CI_YML = """\
name: CI
on:
  pull_request:
jobs:
  lint:
    name: Lint (pre-commit)
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
  tests:
    name: Tests (pytest)
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

CI_YML_WITHOUT_TESTS = """\
name: CI
on:
  pull_request:
jobs:
  lint:
    name: Lint (pre-commit)
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

UNNAMED_JOB_YML = """\
name: Canary
on:
  pull_request:
jobs:
  canary:
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

SCHEDULE_ONLY_YML = """\
name: Scheduled Health
on:
  schedule:
    - cron: '0 3 * * *'
  workflow_dispatch:
jobs:
  ancestry:
    name: Branch ancestry assertion
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

PUSH_ONLY_YML = """\
name: Push only
on:
  push:
jobs:
  pushed:
    name: Push-only check
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

LIST_TRIGGER_YML = """\
name: Listed
on: [push, pull_request]
jobs:
  listed:
    name: Listed check
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

STRING_TRIGGER_YML = """\
name: Stringy
on: pull_request
jobs:
  stringy:
    name: String check
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

PULL_REQUEST_TARGET_YML = """\
name: Targeted
on:
  pull_request_target:
jobs:
  targeted:
    name: Targeted check
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

NO_TRIGGER_YML = """\
name: Broken
jobs:
  lint:
    name: Lint (pre-commit)
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""


def test_a_matching_payload_exits_zero_and_writes_the_send_payload(tmp_path: pathlib.Path) -> None:
    """A payload whose contexts all match job names passes and emits a send payload."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    assert status == 0
    assert out.exists()


def test_the_ok_line_names_the_payload_the_branch_and_the_context_count(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clean preflight prints one trailing OK line carrying its four facts."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert line.startswith("preflight_ruleset_apply: OK")
    assert "main.json" in line
    assert "refs/heads/main" in line
    assert "2" in line
    assert str(out) in line


def test_a_context_no_job_produces_is_refused_and_named(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A required context outside the matchable set exits non-zero and is named."""
    rulesets = tmp_path / "rulesets"
    payload = make_payload(contexts=("Lint (pre-commit)", "Tests (pytest)", "Docs (sphinx -W)"))
    payload_path = write_payload(rulesets, "main.json", payload)
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    captured = capsys.readouterr()
    assert status == 1
    assert "Docs (sphinx -W)" in captured.out
    assert "main.json" in captured.out
    assert "refs/heads/main" in captured.out


def test_every_offending_context_is_named_in_one_run(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Violations accumulate: two missing contexts are both reported before the single exit."""
    rulesets = tmp_path / "rulesets"
    payload = make_payload(contexts=("Docs (sphinx -W)", "Nothing produces this either"))
    payload_path = write_payload(rulesets, "main.json", payload)
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    captured = capsys.readouterr()
    assert status == 1
    assert "Docs (sphinx -W)" in captured.out
    assert "Nothing produces this either" in captured.out


def test_a_removed_job_produces_the_same_refusal(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A job deleted from the target tip while the payload still requires it is refused."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML_WITHOUT_TESTS)
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    captured = capsys.readouterr()
    assert status == 1
    assert "Tests (pytest)" in captured.out
    assert not out.exists()


def test_a_refusal_writes_no_output_file(tmp_path: pathlib.Path) -> None:
    """A refusal leaves no send payload for the workflow's send step to find."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload(contexts=("Nothing produces this",)))
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    assert preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets) == 1
    assert not out.exists()


def test_a_stale_output_file_is_removed_by_a_refusal(tmp_path: pathlib.Path) -> None:
    """A pre-existing send payload does not survive a refusal."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload(contexts=("Nothing produces this",)))
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"
    out.write_text('{"stale": true}\n', encoding="utf-8")

    assert preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets) == 1
    assert not out.exists()


def test_an_unresolvable_trigger_block_is_reported_rather_than_skipped(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A workflow with no `on:` under either key form is a violation, not a pass."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    write_workflow(workflows, "broken.yml", NO_TRIGGER_YML)
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    captured = capsys.readouterr()
    assert status == 1
    assert "broken.yml" in captured.out
    assert not out.exists()


def test_a_quoted_on_key_resolves(tmp_path: pathlib.Path) -> None:
    """The quoted `"on":` key form resolves, so a quoted workflow is not reported."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload(contexts=("Lint (pre-commit)",)))
    workflows = tmp_path / "wf"
    write_workflow(workflows, "quoted.yml", CI_YML.replace("\non:", '\n"on":'))
    out = tmp_path / "send.json"

    assert preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets) == 0


def test_a_job_without_a_name_contributes_its_job_id(tmp_path: pathlib.Path) -> None:
    """An unnamed job matches on its bare job id, which is what GitHub reports."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload(contexts=("canary",)))
    workflows = tmp_path / "wf"
    write_workflow(workflows, "canary.yml", UNNAMED_JOB_YML)
    out = tmp_path / "send.json"

    assert preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets) == 0


def test_the_emitted_payload_has_exactly_the_six_sendable_keys_in_committed_order(tmp_path: pathlib.Path) -> None:
    """The send payload carries the six sendable keys and nothing else, in committed order."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    emitted = json.loads(out.read_text(encoding="utf-8"))
    assert list(emitted) == ["name", "target", "enforcement", "conditions", "bypass_actors", "rules"]


def test_the_emitted_payload_has_no_null_integration_id(tmp_path: pathlib.Path) -> None:
    """The send payload strips the null integration id the API schema rejects."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    emitted = json.loads(out.read_text(encoding="utf-8"))
    checks = [
        entry
        for rule in emitted["rules"]
        if rule.get("type") == "required_status_checks"
        for entry in rule["parameters"]["required_status_checks"]
    ]
    assert checks
    assert not any("integration_id" in entry for entry in checks)


def test_the_emitted_payload_keeps_rules_a_list(tmp_path: pathlib.Path) -> None:
    """The send payload's `rules` stays a list -- the comparison mapping is not a valid body."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)

    assert isinstance(json.loads(out.read_text(encoding="utf-8"))["rules"], list)


def test_a_payload_outside_the_rulesets_directory_is_refused_before_it_is_read(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A path outside the committed rulesets directory is refused without being parsed."""
    rulesets = tmp_path / "rulesets"
    rulesets.mkdir()
    outside = tmp_path / "outside.json"
    # Deliberately unparseable: if the guard read the file first, the failure
    # would be a JSON error rather than the containment refusal asserted below.
    outside.write_text("this is not json", encoding="utf-8")
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    status = preflight.main([str(outside), str(workflows), str(out)], rulesets_dir=rulesets)

    captured = capsys.readouterr()
    assert status == 1
    assert "outside.json" in captured.out
    assert "rulesets" in captured.out
    # The refusal is the containment rule, NOT a parse failure -- which is the
    # evidence that the file was never opened.
    assert "could not be read as JSON" not in captured.out
    assert not out.exists()


def test_a_symlink_escaping_the_rulesets_directory_is_refused(tmp_path: pathlib.Path) -> None:
    """Containment resolves symlinks, so a link out of the rulesets directory is refused."""
    rulesets = tmp_path / "rulesets"
    rulesets.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(make_payload()), encoding="utf-8")
    link = rulesets / "sneaky.json"
    link.symlink_to(outside)
    workflows = tmp_path / "wf"
    write_workflow(workflows, "ci.yml", CI_YML)
    out = tmp_path / "send.json"

    assert preflight.main([str(link), str(workflows), str(out)], rulesets_dir=rulesets) == 1
    assert not out.exists()


def test_a_missing_workflow_directory_is_refused(tmp_path: pathlib.Path) -> None:
    """An absent workflow directory cannot be cross-referenced, so it is a refusal."""
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload())
    out = tmp_path / "send.json"

    assert preflight.main([str(payload_path), str(tmp_path / "absent"), str(out)], rulesets_dir=rulesets) == 1
    assert not out.exists()


def test_wrong_argument_count_is_refused(tmp_path: pathlib.Path) -> None:
    """The three-argument invocation contract is enforced."""
    assert preflight.main([str(tmp_path)], rulesets_dir=tmp_path) == 1


def copy_target_tip_workflows(destination: pathlib.Path, *, omit: str | None = None) -> pathlib.Path:
    """Copy this repository's real workflow files into `destination`.

    Stands in for the apply workflow's fetch step, which lists the WHOLE
    ``.github/workflows`` directory at the target ref and reads each entry raw.
    Copying every file rather than a chosen subset is what makes the two cases
    below a measurement of the real fetch-plus-glob behaviour rather than a
    restatement of it.

    Parameters
    ----------
    destination
        Directory to create and populate.
    omit
        A filename to leave out, standing in for a workflow absent from the
        target branch tip.

    Returns
    -------
    pathlib.Path
        The populated directory.
    """
    destination.mkdir(parents=True, exist_ok=True)
    for source in sorted((REPO_ROOT / ".github/workflows").glob("*.yml")):
        if source.name == omit:
            continue
        (destination / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return destination


# A minimal synthetic `integrity.yml`, in a trigger shape
# `preflight_ruleset_apply.matchable_job_names` accepts: the continuous-enforcement
# component's integrity workflow fires from the base repository's
# `pull_request_target` trigger, which does report a check run on the pull request
# (the preflight inspects which event, so a push-only file would not count).
# Stands in for the continuous-enforcement component's own file when `core`'s
# tree carries none of its own: the conformance layer is opt-in, so
# `integrity.yml` ships with the continuous-enforcement component rather than
# core, and the two tests below can no longer rely on finding it among this
# repository's own committed workflows.
SYNTHETIC_INTEGRITY_YML = """\
on:
  pull_request_target:
jobs:
  integrity:
    name: Integrity (base-ref)
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
"""


def _main_payload_with_integrity_context() -> dict[str, object]:
    """Return `core`'s own committed `main.json`, with `Integrity (base-ref)` appended if absent.

    The continuous-enforcement component ships `main.json` carrying the
    integrity context as a full replacement -- a component ships full
    replacement files, never patches; `core`'s own copy does not, because
    core's payload requires only what core produces, and `integrity.yml` ships
    with the continuous-enforcement component instead. This is what lets the
    two tests below exercise the anti-skip resolution and refusal shapes
    against `core`'s own tree regardless of which payload variant it carries
    -- appending is a no-op on a tree whose payload already carries the
    context.
    """
    payload = json.loads((REPO_ROOT / ".github/rulesets/main.json").read_text(encoding="utf-8"))
    for rule in payload["rules"]:
        if rule["type"] != "required_status_checks":
            continue
        contexts = rule["parameters"]["required_status_checks"]
        if not any(c["context"] == "Integrity (base-ref)" for c in contexts):
            contexts.append({"context": "Integrity (base-ref)", "integration_id": None})
    return payload


def test_the_real_committed_main_payload_resolves_the_anti_skip_context_from_the_target_tip(
    tmp_path: pathlib.Path,
) -> None:
    """The anti-skip context resolves from a target tip carrying `integrity.yml`.

    MEASURED, not assumed from how the fetch happens to be written. The apply
    workflow lists the whole workflow directory at the target ref and this
    preflight globs both accepted extensions, so a workflow file present on the
    tip is already in scope -- but that is a property of two pieces of code that
    could each change independently, so it is pinned here. Without this test the
    preflight could quietly stop resolving the anti-skip context and refuse a
    correct apply, which under `bypass_actors: []` is a branch nobody can merge.

    The payload is `core`'s own `main.json` with the integrity context appended
    if `core`'s own copy lacks it, and the tip is `core`'s own workflows plus a
    synthetic `integrity.yml` if `core`'s own tree carries none -- see
    :func:`_main_payload_with_integrity_context` and
    :data:`SYNTHETIC_INTEGRITY_YML`.
    """
    payload_path = write_payload(tmp_path / "rulesets", "main.json", _main_payload_with_integrity_context())
    workflows = copy_target_tip_workflows(tmp_path / "wf")
    if not (workflows / "integrity.yml").is_file():
        write_workflow(workflows, "integrity.yml", SYNTHETIC_INTEGRITY_YML)
    assert (workflows / "integrity.yml").is_file(), "the excepted workflow must be on the tip for this case"
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=payload_path.parent)

    assert status == 0
    assert out.exists()
    assert "Integrity (base-ref)" in json.dumps(json.loads(out.read_text(encoding="utf-8")))


def test_the_same_payload_is_refused_when_the_integrity_workflow_is_absent_from_the_tip(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The companion refusal: the payload requires the context, the tip stops producing it.

    This is the ordering constraint made mechanical. `integrity.yml` must be
    merged to the protected branch BEFORE the payload requiring its context is
    applied -- a workflow that is not on the default branch never fires, so the
    context would sit perpetually pending and, under an empty bypass-actor list,
    the branch would be unmergeable by anyone including an admin. The preflight
    refusing here is what stands between a dispatch and that state.

    The payload is the same integrity-context-carrying payload as the pass
    case above; the tip is `core`'s own workflows with `integrity.yml`
    (real or synthetic) omitted.
    """
    payload_path = write_payload(tmp_path / "rulesets", "main.json", _main_payload_with_integrity_context())
    workflows = copy_target_tip_workflows(tmp_path / "wf", omit="integrity.yml")
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=payload_path.parent)

    captured = capsys.readouterr()
    assert status == 1
    assert "Integrity (base-ref)" in captured.out
    assert not out.exists()


def test_the_real_committed_main_payload_cross_references_cleanly_against_the_target_tip(
    tmp_path: pathlib.Path,
) -> None:
    """`core`'s own committed `main.json` cross-references cleanly against `core`'s own workflows.

    This is the working-minimum property made mechanical: core's payload
    requires only what core produces, so every context `core`'s own
    `main.json` requires is produced by a job `core`'s own workflows declare,
    and a `core`-only assembly's payload is always applyable as shipped. It
    holds in every assembly, not just `core`-only, because each component that
    adds a required context also adds the workflow that produces it -- this
    test pins the base case.
    """
    workflows = copy_target_tip_workflows(tmp_path / "wf")
    out = tmp_path / "send.json"

    status = preflight.main([str(REPO_ROOT / ".github/rulesets/main.json"), str(workflows), str(out)])

    assert status == 0
    assert out.exists()


def test_the_real_committed_develop_payload_passes_against_the_real_ci_yml(tmp_path: pathlib.Path) -> None:
    """The repository's own develop payload cross-references cleanly against its own `ci.yml`.

    `develop.json` requires only the lint and tests contexts, both of which are job
    names in the committed `ci.yml` shipped by the CI-shape component.
    """
    workflows = tmp_path / "wf"
    workflows.mkdir()
    (workflows / "ci.yml").write_text(
        (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    out = tmp_path / "send.json"

    status = preflight.main([str(REPO_ROOT / ".github/rulesets/develop.json"), str(workflows), str(out)])

    assert status == 0
    assert json.loads(out.read_text(encoding="utf-8"))["name"] == "protect-develop-gsd"


# --------------------------------------------------------------------------
# Only workflows that fire on a pull request can satisfy a required context
# --------------------------------------------------------------------------


def _run_single_workflow(
    tmp_path: pathlib.Path, text: str, context: str, filename: str = "w.yml"
) -> tuple[int, pathlib.Path]:
    """Preflight a payload requiring ``context`` against a tip holding one workflow.

    Parameters
    ----------
    tmp_path
        Scratch directory for the payload, workflow and send file.
    text
        Raw YAML of the single workflow on the tip.
    context
        The one required context the payload carries.
    filename
        Basename the workflow is written under.

    Returns
    -------
    tuple
        The exit status and the send-payload path (which exists only on success).
    """
    rulesets = tmp_path / "rulesets"
    payload_path = write_payload(rulesets, "main.json", make_payload(contexts=(context,)))
    workflows = tmp_path / "wf"
    write_workflow(workflows, filename, text)
    out = tmp_path / "send.json"
    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=rulesets)
    return status, out


def test_a_schedule_only_workflow_job_is_not_a_matchable_context(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A context only a ``schedule`` + ``workflow_dispatch`` workflow produces is refused and named.

    Such a job never reports a check run on a pull request, so a ruleset
    requiring it leaves the branch unmergeable under an empty bypass list. Before
    the trigger filter this exited 0.
    """
    status, out = _run_single_workflow(tmp_path, SCHEDULE_ONLY_YML, "Branch ancestry assertion")

    captured = capsys.readouterr()
    assert status == 1
    assert "Branch ancestry assertion" in captured.out
    assert "skipped" in captured.err
    assert not out.exists()


def test_a_push_only_workflow_job_is_not_a_matchable_context(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ``push``-only workflow's job name is likewise refused."""
    status, out = _run_single_workflow(tmp_path, PUSH_ONLY_YML, "Push-only check")

    assert status == 1
    assert "Push-only check" in capsys.readouterr().out
    assert not out.exists()


def test_a_list_form_trigger_containing_pull_request_is_matchable(tmp_path: pathlib.Path) -> None:
    """``on: [push, pull_request]`` contributes its job names."""
    status, out = _run_single_workflow(tmp_path, LIST_TRIGGER_YML, "Listed check")

    assert status == 0
    assert out.exists()


def test_a_string_form_pull_request_trigger_is_matchable(tmp_path: pathlib.Path) -> None:
    """``on: pull_request`` (a bare string) contributes its job names."""
    status, out = _run_single_workflow(tmp_path, STRING_TRIGGER_YML, "String check")

    assert status == 0
    assert out.exists()


def test_a_mapping_form_pull_request_trigger_is_matchable(tmp_path: pathlib.Path) -> None:
    """``on: {pull_request: ...}`` (the mapping form) contributes its job names."""
    status, out = _run_single_workflow(tmp_path, CI_YML, "Lint (pre-commit)", filename="ci.yml")

    assert status == 0
    assert out.exists()


def test_a_quoted_on_key_with_a_list_trigger_is_matchable(tmp_path: pathlib.Path) -> None:
    """The quoted ``"on":`` key form contributes its job names for a list trigger too."""
    quoted = LIST_TRIGGER_YML.replace("\non:", '\n"on":')
    status, _ = _run_single_workflow(tmp_path, quoted, "Listed check")

    assert status == 0


def test_a_pull_request_target_workflow_is_matchable(tmp_path: pathlib.Path) -> None:
    """``pull_request_target`` contributes: it reports a check run on the pull request."""
    status, out = _run_single_workflow(tmp_path, PULL_REQUEST_TARGET_YML, "Targeted check")

    assert status == 0
    assert out.exists()


def test_trigger_events_normalises_the_three_block_shapes() -> None:
    """A string, a list and a mapping each yield their event names; anything else yields none."""
    assert preflight.trigger_events("push") == {"push"}
    assert preflight.trigger_events(["push", "pull_request"]) == {"push", "pull_request"}
    assert preflight.trigger_events({"pull_request": None, "schedule": [{"cron": "0 3 * * *"}]}) == {
        "pull_request",
        "schedule",
    }
    assert preflight.trigger_events(None) == set()
    assert preflight.trigger_events(42) == set()


def test_the_real_scheduled_health_workflow_does_not_make_its_job_matchable(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The real ``scheduled-health.yml`` on the tip does not satisfy ``Branch ancestry assertion``.

    This is the reproduced accepted risk: the context exists as a job name on the
    tip, but the workflow only runs on a schedule, so it never reports on a pull
    request. The tip is this repository's own workflows, copied whole.
    """
    payload_path = write_payload(
        tmp_path / "rulesets", "main.json", make_payload(contexts=("Branch ancestry assertion",))
    )
    workflows = copy_target_tip_workflows(tmp_path / "wf")
    assert (workflows / "scheduled-health.yml").is_file()
    out = tmp_path / "send.json"

    status = preflight.main([str(payload_path), str(workflows), str(out)], rulesets_dir=payload_path.parent)

    assert status == 1
    assert "Branch ancestry assertion" in capsys.readouterr().out
    assert not out.exists()
