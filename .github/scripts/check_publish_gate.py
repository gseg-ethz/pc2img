#!/usr/bin/env python3
# .github/scripts/check_publish_gate.py
"""Assert publish steps appear ONLY in allowed files under allowed environments.

Called from the `Lint (pre-commit)` CI job. Exits 0 = clean; exits 1 = violation,
and also 1 when the workflows directory holds no workflow files at all -- a
check that could not read its input has verified nothing, which is a failure
rather than a clean result.

The point is containment, not discovery: a publish step is only ever legitimate in
one of the two files named below, and only under the environment that file is paired
with. A publish step appearing anywhere else -- or in the right file under the wrong
environment -- would publish under an identity the index was never configured to
trust, or under one it was, from a workflow nobody reviewed as a publishing path.
"""

import pathlib
import re
import sys

import yaml  # available on ubuntu-latest runner by default

# Resolved from this file rather than from the process working directory, so the
# containment check always inspects the repository it ships in. A bare relative
# path would make this check disarm itself while still printing OK the moment it
# is invoked from anywhere but the repository root -- a `working-directory:` key,
# a `cd` in the step, or a call from the scripts directory are all enough. The
# invocation contract is unchanged: still no arguments.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# KIT STRUCTURE, NOT A REPOSITORY PARAMETER. Both extensions, because GitHub
# reads both: a `.yaml` publish workflow is a workflow, and nothing anywhere else
# in the kit backstops this module.
WORKFLOWS_DIR = ".github/workflows"
WORKFLOW_GLOBS = ("*.yml", "*.yaml")

ALLOWED: dict[str, str] = {
    "publish-pypi.yml": "pypi",
    "publish-testpypi.yml": "testpypi",
}

PUBLISH_STEP_PATTERNS = [
    r"pypa/gh-action-pypi-publish",  # covers any SHA/tag/branch ref
    r"twine\s+upload",  # covers `run: twine upload dist/*`
]


def get_env_name(env_field: object) -> str | None:
    """Normalize environment: 'pypi' and environment: {name: pypi} both."""
    if isinstance(env_field, str):
        return env_field
    if isinstance(env_field, dict):
        return env_field.get("name")
    return None


def is_publish_step(step: dict[str, object]) -> bool:
    """Return True if the step contains a publish action or twine upload."""
    uses = step.get("uses", "") or ""
    run = step.get("run", "") or ""
    return any(re.search(p, str(uses)) for p in PUBLISH_STEP_PATTERNS) or any(
        re.search(p, str(run)) for p in PUBLISH_STEP_PATTERNS
    )


def check_job(wf_name: str, job_id: str, job: dict[str, object]) -> list[str]:
    """Return the violations one job contributes.

    Split out of :func:`main` so the driver stays a straight line. The verdicts
    are unchanged: a publish step is a violation in any file the allowlist does
    not name, and in an allowed file running under any other environment.
    """
    violations: list[str] = []
    env_name = get_env_name(job.get("environment"))
    allowed_env = ALLOWED.get(wf_name)
    for step in job.get("steps") or []:  # type: ignore[union-attr]
        if not isinstance(step, dict) or not is_publish_step(step):
            continue
        if allowed_env is None:
            violations.append(f"{wf_name} job={job_id}: publish step found in non-allowed file")
        elif env_name != allowed_env:
            violations.append(
                f"{wf_name} job={job_id}: publish step requires environment={allowed_env!r}, got {env_name!r}"
            )
    return violations


def _one_line(error: Exception) -> str:
    """Collapse a parser error to a single line.

    ``yaml.YAMLError`` renders across several lines (problem, mark, context
    mark). A GitHub ``::error::`` annotation ends at the first newline, so an
    embedded one would strand the file and line numbers -- the most useful
    half of the diagnosis -- in the plain log instead of in the annotation.

    Parameters
    ----------
    error
        The parse or read failure to render.

    Returns
    -------
    str
        The error text with every run of whitespace collapsed to one space.
    """
    return " ".join(str(error).split())


def collect_violations(paths: list[pathlib.Path]) -> list[str]:
    """Return every violation across ``paths``.

    A workflow that parses to a well-formed document of the wrong shape --
    not a mapping, or a mapping with no ``jobs`` key -- is SKIPPED rather than
    fatal: these are contributor-controlled files read from a required status
    check, so an unexpected-but-parseable shape must not become a traceback.

    A workflow that cannot be READ or PARSED at all is a **violation**, not a
    skip: a check that skipped it would have verified nothing about it, which
    is exactly the fail-open shape the rest of this module exists to refuse.
    """
    violations: list[str] = []
    for wf_path in paths:
        try:
            # Explicit utf-8, NOT the locale encoding: two sibling parsers
            # (this one and check_ci_config.load_workflows) that disagree
            # about one file's bytes can reach two different verdicts on
            # identical input.
            with wf_path.open(encoding="utf-8") as f:
                wf = yaml.safe_load(f)
        except (OSError, ValueError, yaml.YAMLError) as error:
            # UnicodeDecodeError is a ValueError, so undecodable bytes need no
            # fourth clause here. Fail-closed either way: the point of the
            # guard is that the failure arrives as the annotation the rest of
            # this module emits, not as a traceback the annotation channel
            # never sees.
            violations.append(
                f"{wf_path.name}: could not be read as YAML — {_one_line(error)}. This workflow has "
                f"not been checked, so it cannot be assumed clean."
            )
            continue
        if not isinstance(wf, dict) or "jobs" not in wf:
            continue
        for job_id, job in (wf.get("jobs") or {}).items():
            if isinstance(job, dict):
                violations.extend(check_job(wf_path.name, job_id, job))
    return violations


def main(root: pathlib.Path = REPO_ROOT) -> int:
    """Scan ``root``'s workflows and return 0 when clean, 1 on any violation."""
    workflows_dir = root / WORKFLOWS_DIR
    paths = sorted(p for pattern in WORKFLOW_GLOBS for p in workflows_dir.glob(pattern))

    # An unreadable input is a HARD FAILURE, never a clean result. A containment
    # check that read nothing reporting that it read everything and found nothing
    # is the exact fail-open silhouette the rest of this kit is built to refuse.
    if not paths:
        print(
            f"::error::{workflows_dir} holds no workflow files — the publish containment "
            f"check read nothing, so it has verified nothing. This is a hard failure, "
            f"not a clean result."
        )
        return 1

    violations = collect_violations(paths)
    if violations:
        for v in violations:
            print(f"::error::{v}")
        return 1
    print("check_publish_gate: OK — publish steps found only in allowed files + environments")
    return 0


# The driver runs under `python .github/scripts/check_publish_gate.py`, which is
# the ONLY invocation contract this file has and is unchanged by the guard below.
#
# The guard exists for the reason `check_ci_config.py` states at its own driver:
# without it, importing this module runs the whole scan as an import side effect
# and, on a tree carrying a violation, `sys.exit(1)`s inside the importer before
# the importer's own rules have run. In a branch-protection gate that is a
# wrong-verdict bug. This module is collected by the same `pytest
# .github/scripts/` invocation the other checkers are, so the importer is real.
if __name__ == "__main__":
    sys.exit(main())
