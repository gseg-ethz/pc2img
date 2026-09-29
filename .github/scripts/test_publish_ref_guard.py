#!/usr/bin/env python3
# .github/scripts/test_publish_ref_guard.py
"""Execute the publish workflows' own ref guards, extracted verbatim.

Both publish workflows open their ``build`` job with a plain-bash step that
reads a handful of environment variables and decides whether the run may
proceed. This module does not re-implement that logic: it parses the real
workflow YAML, pulls the named step's ``run`` script out, and executes it
under ``bash`` with the same environment variables GitHub Actions would set,
so a change to either workflow that weakens or removes a guard is caught by
running the guard itself, not by re-describing it.

``publish-testpypi.yml``'s guard refuses any dispatch ref but the release
branch. ``publish-pypi.yml`` carries two guards: the first refuses a release
whose ref is not an X.Y.Z version tag, and the second -- run immediately
after checkout, once full history is available -- refuses a tagged commit
that is not reachable from the release branch.

Run with::

    python -m pytest .github/scripts/test_publish_ref_guard.py -q

Note that ruff's ``per-file-ignores`` relax docstring rules under ``tests/**``
only, which does not cover ``.github/scripts/``, so every test here carries a
numpy-convention docstring by design rather than by accident.
"""

from __future__ import annotations

import os
import pathlib
import subprocess

import yaml

WORKFLOWS = pathlib.Path(__file__).resolve().parents[1] / "workflows"


def _load_build_steps(workflow_filename: str) -> list[dict[str, object]]:
    """Return the ``build`` job's step list from a real workflow file."""
    doc = yaml.safe_load((WORKFLOWS / workflow_filename).read_text(encoding="utf-8"))
    steps = doc["jobs"]["build"]["steps"]
    assert isinstance(steps, list) and steps, f"{workflow_filename}: build job has no steps"
    return steps


def _guard_script(workflow_filename: str, step_name: str) -> str:
    """Return the ``run`` script of the build-job step named ``step_name``.

    Parameters
    ----------
    workflow_filename
        Basename of the workflow under ``.github/workflows``.
    step_name
        Exact ``name:`` of the step to extract.

    Returns
    -------
    str
        The step's ``run`` script, exactly as it appears in the workflow.
    """
    for step in _load_build_steps(workflow_filename):
        if step.get("name") == step_name:
            run = step.get("run")
            assert isinstance(run, str), f"{workflow_filename}: step {step_name!r} has no run script"
            return run
    raise AssertionError(f"{workflow_filename}: no step named {step_name!r} found in the build job")


def _first_step_script(workflow_filename: str, step_name: str) -> str:
    """Like :func:`_guard_script`, additionally asserting the step is first."""
    steps = _load_build_steps(workflow_filename)
    first_name = steps[0].get("name")
    assert first_name == step_name, (
        f"{workflow_filename}: expected {step_name!r} to be the first build step, got {first_name!r}"
    )
    run = steps[0].get("run")
    assert isinstance(run, str), f"{workflow_filename}: first step has no run script"
    return run


def _run(
    script: str,
    env: dict[str, str],
    cwd: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute an extracted guard script under bash, as the runner would.

    Parameters
    ----------
    script
        The guard's ``run`` script, read verbatim from the workflow.
    env
        The environment variables GitHub Actions would set for this step —
        the ONLY inputs the guard reads, per its own contract.
    cwd
        Working directory for the script; only the ancestry guard needs one.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The completed process, with captured text output.
    """
    minimal_env = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")}
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        env={**minimal_env, **env},
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _git(args: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _build_ancestry_fixture(tmp_path: pathlib.Path) -> tuple[pathlib.Path, str, str]:
    """Build a bare origin plus a clone with a main branch and a side branch.

    Returns
    -------
    tuple[pathlib.Path, str, str]
        The clone's working directory, the tip commit of ``main``, and the
        tip commit of the side branch ``feature`` -- one commit ahead of
        ``main`` and never merged into it.
    """
    origin = tmp_path / "origin.git"
    clone = tmp_path / "clone"
    subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "init.defaultBranch=main", "init", "-q", str(clone)],
        check=True,
        capture_output=True,
    )
    _git(["remote", "add", "origin", str(origin)], cwd=clone)
    _git(["config", "user.name", "pc2img-test"], cwd=clone)
    _git(["config", "user.email", "pc2img-test@example.com"], cwd=clone)

    (clone / "README.md").write_text("main\n", encoding="utf-8")
    _git(["add", "-A"], cwd=clone)
    _git(["commit", "-q", "-m", "main commit"], cwd=clone)
    _git(["push", "-q", "origin", "main"], cwd=clone)
    main_sha = _git(["rev-parse", "HEAD"], cwd=clone).stdout.strip()

    _git(["checkout", "-q", "-b", "feature"], cwd=clone)
    (clone / "feature.txt").write_text("feature\n", encoding="utf-8")
    _git(["add", "-A"], cwd=clone)
    _git(["commit", "-q", "-m", "feature commit"], cwd=clone)
    _git(["push", "-q", "origin", "feature"], cwd=clone)
    feature_sha = _git(["rev-parse", "HEAD"], cwd=clone).stdout.strip()

    _git(["checkout", "-q", "main"], cwd=clone)
    return clone, main_sha, feature_sha


# --- publish-testpypi.yml: dispatch-ref guard -------------------------------


def test_testpypi_guard_accepts_a_dispatch_from_the_release_branch() -> None:
    """Dispatching the rehearsal from the release branch proceeds."""
    script = _first_step_script("publish-testpypi.yml", "Refuse a dispatch from any ref but the release branch")
    result = _run(script, {"DISPATCH_REF": "refs/heads/main"})
    assert result.returncode == 0, result.stdout + result.stderr


def test_testpypi_guard_refuses_a_dispatch_from_a_different_branch() -> None:
    """Dispatching from any other branch is refused with an annotation."""
    script = _first_step_script("publish-testpypi.yml", "Refuse a dispatch from any ref but the release branch")
    result = _run(script, {"DISPATCH_REF": "refs/heads/develop-gsd"})
    assert result.returncode != 0
    assert "::error::" in result.stdout


def test_testpypi_guard_refuses_a_dispatch_from_a_tag() -> None:
    """A tag ref is not the release branch, so it is refused too."""
    script = _first_step_script("publish-testpypi.yml", "Refuse a dispatch from any ref but the release branch")
    result = _run(script, {"DISPATCH_REF": "refs/tags/v0.11.0"})
    assert result.returncode != 0


# --- publish-pypi.yml: version-tag guard ------------------------------------


def test_pypi_tag_guard_accepts_a_version_tag() -> None:
    """An X.Y.Z tag release proceeds."""
    script = _first_step_script("publish-pypi.yml", "Refuse a release that is not a version tag")
    result = _run(script, {"REF_TYPE": "tag", "REF_NAME": "v0.11.0"})
    assert result.returncode == 0, result.stdout + result.stderr


def test_pypi_tag_guard_refuses_a_branch_ref() -> None:
    """A branch is never a release, whatever its name."""
    script = _first_step_script("publish-pypi.yml", "Refuse a release that is not a version tag")
    result = _run(script, {"REF_TYPE": "branch", "REF_NAME": "main"})
    assert result.returncode != 0
    assert "::error::" in result.stdout


def test_pypi_tag_guard_refuses_a_floating_major_minor_tag() -> None:
    """A rolling major/minor tag is not a release tag."""
    script = _first_step_script("publish-pypi.yml", "Refuse a release that is not a version tag")
    result = _run(script, {"REF_TYPE": "tag", "REF_NAME": "v0"})
    assert result.returncode != 0


def test_pypi_tag_guard_refuses_a_pre_release_archive_tag() -> None:
    """An archive/* pre-release tag does not match the release-tag shape."""
    script = _first_step_script("publish-pypi.yml", "Refuse a release that is not a version tag")
    result = _run(script, {"REF_TYPE": "tag", "REF_NAME": "archive/v2.0.0a5"})
    assert result.returncode != 0


# --- publish-pypi.yml: ancestry-of-main guard -------------------------------


def test_pypi_ancestry_guard_accepts_the_tip_of_main(tmp_path: pathlib.Path) -> None:
    """The tip of the release branch is reachable from itself."""
    clone, main_sha, _feature_sha = _build_ancestry_fixture(tmp_path)
    script = _guard_script("publish-pypi.yml", "Refuse a release commit that is not on the release branch")
    result = _run(script, {"HEAD_SHA": main_sha}, cwd=clone)
    assert result.returncode == 0, result.stdout + result.stderr


def test_pypi_ancestry_guard_refuses_a_commit_only_on_a_side_branch(tmp_path: pathlib.Path) -> None:
    """A commit that only exists on a side branch is not reachable from main."""
    clone, _main_sha, feature_sha = _build_ancestry_fixture(tmp_path)
    script = _guard_script("publish-pypi.yml", "Refuse a release commit that is not on the release branch")
    result = _run(script, {"HEAD_SHA": feature_sha}, cwd=clone)
    assert result.returncode != 0
    assert "::error::" in result.stdout
