#!/usr/bin/env python3
# .github/scripts/test_check_publish_gate.py
"""Unit tests for the publish containment gate.

``main`` takes a root path, so each test writes a synthetic workflows tree into a
``tmp_path`` fixture and asserts against that tree rather than against the
repository. The gate's own default root stays ``REPO_ROOT``, so the shipped
invocation -- ``python .github/scripts/check_publish_gate.py``, no arguments --
is exactly what these tests exercise, one level down.

Two properties here are not ordinary unit tests and are the reason this module
exists at all. **Import inertness** is checked in a subprocess whose working
directory is a tree carrying a violation: the property under test is that
importing the module neither scans nor exits, and an in-process assertion cannot
witness it because this file has already imported the module by the time any
test runs. **Working-directory invariance** is checked the same way, because a
containment check that silently disarms itself under a different working
directory still prints its OK line, so the verdict alone does not distinguish
the two states.

Run with::

    python -m pytest .github/scripts/test_check_publish_gate.py -q

Note that ruff's ``per-file-ignores`` relax docstring rules under ``tests/**``
only, which does not cover ``.github/scripts/``, so every test here carries a
numpy-convention docstring by design rather than by accident.
"""

import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import check_publish_gate as pg  # noqa: E402  — deliberately after the sys.path insertion above

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

# A publish step in a file that is not on the allowlist. This is the shape the
# gate exists to catch: it would publish under an identity nobody reviewed as a
# publishing path.
ROGUE_WORKFLOW = """\
name: rogue

on: push

jobs:
  ship:
    runs-on: ubuntu-latest
    steps:
      - run: twine upload dist/*
"""

# The same publish action in the file the allowlist names, under the environment
# that file is paired with. This is the one legitimate shape.
ALLOWED_WORKFLOW = """\
name: publish

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b  # v1.14.0
"""

# No publish step anywhere. Present so a "clean" verdict is reached by reading
# workflows and finding nothing, rather than by reading nothing.
INNOCENT_WORKFLOW = """\
name: CI

on: pull_request

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: echo lint
"""


def build_tree(root: pathlib.Path, workflows: dict[str, str]) -> pathlib.Path:
    """Write a synthetic repository tree the gate can run against.

    Parameters
    ----------
    root
        Directory to populate; normally a ``tmp_path`` fixture.
    workflows
        Mapping of workflow filename to file body, written under
        ``.github/workflows``. An empty mapping still creates the directory, so
        the empty-directory case is reachable.

    Returns
    -------
    pathlib.Path
        ``root``, so callers can pass the result straight to ``main``.
    """
    workflows_dir = root / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    for name, body in workflows.items():
        (workflows_dir / name).write_text(body, encoding="utf-8")
    return root


def run_in_subprocess(cwd: pathlib.Path, code: str) -> subprocess.CompletedProcess[str]:
    """Run ``code`` in a fresh interpreter whose working directory is ``cwd``.

    Parameters
    ----------
    cwd
        Working directory for the child process. Choosing a directory that is
        NOT the gate's own repository is what makes the working-directory
        properties observable.
    code
        Python source passed to ``-c``.

    Returns
    -------
    subprocess.CompletedProcess
        The completed child process, with stdout and stderr captured as text.
    """
    return subprocess.run(  # noqa: S603 — fixed argv, no shell, test-local source
        [sys.executable, "-c", code],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


# --------------------------------------------------------------------------
# Import inertness — the module must not scan or exit inside its importer
# --------------------------------------------------------------------------


def test_importing_the_module_is_inert_on_a_tree_that_would_fail(tmp_path: pathlib.Path) -> None:
    """Importing runs no scan and raises no SystemExit, violation present or not.

    Before the ``if __name__`` guard the whole driver was module level, so this
    exact invocation exited 1 inside the importer, having scanned the child's
    working directory. That is a wrong-verdict bug in a branch-protection gate:
    an importer's own rules never run.
    """
    root = build_tree(tmp_path, {"publish-rogue.yml": ROGUE_WORKFLOW})
    code = (
        f"import sys; sys.path.insert(0, {str(SCRIPT_DIR)!r})\n"
        "import check_publish_gate as g\n"
        "print('INERT', hasattr(g, 'main'))\n"
    )
    proc = run_in_subprocess(root, code)
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "INERT True" in proc.stdout, proc.stdout
    assert "::error::" not in proc.stdout, proc.stdout
    assert "check_publish_gate: OK" not in proc.stdout, proc.stdout


# --------------------------------------------------------------------------
# Working-directory invariance — the gate reads the repository it ships in
# --------------------------------------------------------------------------


def test_repo_root_is_resolved_from_the_module_not_the_working_directory() -> None:
    """``REPO_ROOT`` is the module's own repository root, two levels up from it."""
    assert pg.REPO_ROOT == SCRIPT_DIR.parents[1]
    assert (pg.REPO_ROOT / pg.WORKFLOWS_DIR).is_dir()


def test_the_verdict_is_the_same_from_a_foreign_working_directory(tmp_path: pathlib.Path) -> None:
    """Invoking the gate from elsewhere returns the shipped tree's verdict, not that directory's.

    A bare relative workflows path made an invocation from any other directory
    glob nothing, leave the violation list empty, and print the OK line -- a
    check that read nothing reporting that it read everything.
    """
    root = build_tree(tmp_path, {"publish-rogue.yml": ROGUE_WORKFLOW})
    code = (
        f"import sys; sys.path.insert(0, {str(SCRIPT_DIR)!r})\n"
        "import check_publish_gate as g\n"
        "print('VERDICT', g.main())\n"
    )
    from_foreign = run_in_subprocess(root, code)
    from_root = run_in_subprocess(pg.REPO_ROOT, code)
    assert from_foreign.returncode == 0, (from_foreign.stdout, from_foreign.stderr)
    assert "VERDICT" in from_foreign.stdout, from_foreign.stdout
    assert from_foreign.stdout == from_root.stdout, (from_foreign.stdout, from_root.stdout)


# --------------------------------------------------------------------------
# The allowlist — the one legitimate shape, and the two ways it goes wrong
# --------------------------------------------------------------------------


def test_an_allowed_file_under_its_allowed_environment_is_clean(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A publish step in the file the allowlist names, under its paired environment, passes."""
    root = build_tree(tmp_path, {"publish-pypi.yml": ALLOWED_WORKFLOW, "ci.yml": INNOCENT_WORKFLOW})
    assert pg.main(root) == 0
    assert "check_publish_gate: OK" in capsys.readouterr().out


def test_an_allowed_file_under_the_wrong_environment_names_the_expected_environment(
    tmp_path: pathlib.Path,
    capsys,  # noqa: ANN001
) -> None:
    """The right file under the wrong environment is a violation that says which was expected."""
    wrong = ALLOWED_WORKFLOW.replace("environment: pypi", "environment: staging", 1)
    root = build_tree(tmp_path, {"publish-pypi.yml": wrong})
    assert pg.main(root) == 1
    out = capsys.readouterr().out
    assert "publish-pypi.yml" in out, out
    assert "'pypi'" in out, out
    assert "'staging'" in out, out


def test_an_allowed_file_with_no_environment_at_all_is_a_violation(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """An omitted environment is the wrong environment, not an absent question."""
    bare = ALLOWED_WORKFLOW.replace("    environment: pypi\n", "", 1)
    root = build_tree(tmp_path, {"publish-pypi.yml": bare})
    assert pg.main(root) == 1
    assert "publish-pypi.yml" in capsys.readouterr().out


def test_a_publish_step_in_a_non_allowed_file_is_a_violation(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A publish step outside the allowlist is named, whatever environment it runs under."""
    root = build_tree(tmp_path, {"publish-rogue.yml": ROGUE_WORKFLOW, "ci.yml": INNOCENT_WORKFLOW})
    assert pg.main(root) == 1
    out = capsys.readouterr().out
    assert "publish-rogue.yml" in out, out
    assert "non-allowed file" in out, out


# --------------------------------------------------------------------------
# Both workflow extensions — GitHub reads `.yaml`, so this gate must too
# --------------------------------------------------------------------------


def test_workflow_globs_cover_both_extensions() -> None:
    """The glob tuple names both extensions GitHub accepts."""
    assert set(pg.WORKFLOW_GLOBS) == {"*.yml", "*.yaml"}


def test_a_yaml_suffixed_non_allowed_file_is_a_violation(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A rogue publish workflow named ``.yaml`` is a violation, not an invisible file.

    Nothing else in the kit backstops this module -- ``assert_no_skip.py`` does
    not invoke it -- so a ``.yaml`` blind spot here is outside every check the
    kit ships.
    """
    root = build_tree(tmp_path, {"publish-rogue.yaml": ROGUE_WORKFLOW})
    assert pg.main(root) == 1
    assert "publish-rogue.yaml" in capsys.readouterr().out


def test_the_yaml_and_yml_twins_produce_the_same_verdict(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A byte-identical rogue file gets the same verdict under either extension."""
    yml_root = build_tree(tmp_path / "yml", {"publish-rogue.yml": ROGUE_WORKFLOW})
    yaml_root = build_tree(tmp_path / "yaml", {"publish-rogue.yaml": ROGUE_WORKFLOW})
    assert pg.main(yml_root) == 1
    yml_out = capsys.readouterr().out
    assert pg.main(yaml_root) == 1
    yaml_out = capsys.readouterr().out
    assert yml_out.replace("publish-rogue.yml", "X") == yaml_out.replace("publish-rogue.yaml", "X")


# --------------------------------------------------------------------------
# An unreadable input is a hard failure, never a clean result
# --------------------------------------------------------------------------


def test_an_empty_workflows_directory_is_a_hard_failure(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A workflows directory holding no workflow files exits 1 with a named error."""
    root = build_tree(tmp_path, {})
    assert pg.main(root) == 1
    out = capsys.readouterr().out
    assert "::error::" in out, out
    assert "verified nothing" in out, out
    assert "check_publish_gate: OK" not in out, out


def test_a_missing_workflows_directory_is_a_hard_failure(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """An absent workflows directory is the same hard failure as an empty one."""
    assert pg.main(tmp_path) == 1
    assert "::error::" in capsys.readouterr().out


def test_a_directory_holding_only_non_workflow_files_is_a_hard_failure(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """Files that are not workflows do not count as having read something."""
    root = build_tree(tmp_path, {})
    (root / ".github" / "workflows" / "README.md").write_text("not a workflow\n", encoding="utf-8")
    assert pg.main(root) == 1
    assert "::error::" in capsys.readouterr().out


# --------------------------------------------------------------------------
# Malformed input is skipped, not fatal
# --------------------------------------------------------------------------


def test_a_workflow_that_is_not_a_mapping_is_skipped_rather_than_crashing(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A YAML document that parses to a list, or to nothing, is skipped.

    The gate reads untrusted contributor-controlled files, so a parse result it
    did not expect must not become a traceback in a required status check.
    """
    root = build_tree(
        tmp_path,
        {
            "a-list.yml": "- one\n- two\n",
            "empty.yml": "\n",
            "no-jobs.yml": "name: x\non: push\n",
            "publish-pypi.yml": ALLOWED_WORKFLOW,
        },
    )
    assert pg.main(root) == 0
    assert "check_publish_gate: OK" in capsys.readouterr().out


def test_a_job_that_is_not_a_mapping_is_skipped_rather_than_crashing(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """A jobs mapping whose value is not a mapping is skipped, not fatal.

    Skipped means skipped: the file WAS read, so this is a clean verdict rather
    than the hard failure an unreadable directory produces.
    """
    root = build_tree(tmp_path, {"odd.yml": "name: x\non: push\njobs:\n  broken: not-a-mapping\n"})
    assert pg.main(root) == 0
    out = capsys.readouterr().out
    assert "check_publish_gate: OK" in out, out
    assert "verified nothing" not in out, out


# --------------------------------------------------------------------------
# A file that cannot be READ or PARSED at all is a violation, never a skip --
# distinct from the well-formed-but-wrong-shape documents the tests above
# cover, which stay a clean skip.
# --------------------------------------------------------------------------


def test_a_malformed_workflow_is_a_named_violation_not_a_traceback(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """Malformed YAML that ``yaml.safe_load`` cannot parse is a named violation.

    Pre-fix, ``collect_violations`` let ``yaml.YAMLError`` propagate out of
    ``main`` as a traceback -- a required status check crashing rather than
    reporting a verdict. The clean allowed workflow living alongside it proves
    the malformed file did not stop the rest of the tree from being read.
    """
    root = build_tree(
        tmp_path,
        {"bad.yml": "name: [unclosed", "publish-pypi.yml": ALLOWED_WORKFLOW},
    )
    assert pg.main(root) == 1
    out = capsys.readouterr().out
    assert "Traceback" not in out, out
    assert "::error::bad.yml" in out, out
    assert "cannot be assumed clean" in out, out


def test_an_undecodable_workflow_is_a_named_violation_not_a_traceback(tmp_path: pathlib.Path, capsys) -> None:  # noqa: ANN001
    """Bytes that are not valid utf-8 are a named violation, not a ``UnicodeDecodeError``.

    Pre-fix, ``wf_path.open()`` inherited the process locale encoding rather
    than reading explicit utf-8, so an undecodable file raised inside the
    ``open``/``read`` call itself, before ``yaml.safe_load`` ever ran. The
    clean allowed workflow living alongside it proves the undecodable file did
    not stop the rest of the tree from being read.
    """
    root = build_tree(tmp_path, {"publish-pypi.yml": ALLOWED_WORKFLOW})
    (root / ".github" / "workflows" / "bytes.yml").write_bytes(b"\xff\xfe\x00name: x\n")
    assert pg.main(root) == 1
    out = capsys.readouterr().out
    assert "Traceback" not in out, out
    assert "UnicodeDecodeError" not in out, out
    assert "::error::bytes.yml" in out, out
    assert "cannot be assumed clean" in out, out
