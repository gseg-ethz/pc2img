"""Pin release-archive version derivation against floating major/minor tags.

A GitHub "Source code" archive of a tagged commit is not built from the tag
name GitHub used to reach it -- it is built from a `git describe` substitution
performed at archive time, driven by ``.git_archival.txt``'s ``export-subst``
value. If more than one annotated tag points at the same commit, `git
describe` picks the most recently created one, not the one a human would
expect. A release automation step that also drops rolling major/minor tags
(``v0``, ``v0.11``) on the exact commit tagged ``v0.11.0`` therefore makes the
archive substitute the rolling tag instead of the release tag, and the
build's own version parser rejects a rolling tag outright.

These tests build a small scratch repository carrying exactly that tag
collision, in the same creation order automated tooling uses (release tag
first, then the rolling tags), and prove two things: what the substituted
value actually is, and that the project's own version-tag pattern accepts it.
A third test asserts the archival glob and the checkout-time glob are kept as
one literal string, so a checkout and an archive of the same commit can never
disagree about which tag describes it.
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import tarfile
import tomllib
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ARCHIVAL_FILE = ".git_archival.txt"
_ATTRIBUTES_FILE = ".gitattributes"

# The three tag names collide on one commit in this order: the release tag is
# created first, then the two rolling tags -- the exact order a "tag major and
# minor versions" automation step runs in after a release is cut.
_TAG_NAMES = ("v0.11.0", "v0.11", "v0")
_TAG_DATES = (
    "2026-01-01T00:00:00",
    "2026-01-01T00:00:10",
    "2026-01-01T00:00:20",
)


def _run_git(args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def _build_tagged_scratch_repo(tmp_path: Path) -> Path:
    """Build a one-commit repository carrying the three colliding tags.

    Copies this repository's own archival files into the scratch repository
    so the test exercises the real describe pattern, not a reconstruction of
    it, then creates the three tags with strictly increasing tagger dates.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-q"], cwd=repo)
    _run_git(["config", "user.name", "pc2img-test"], cwd=repo)
    _run_git(["config", "user.email", "pc2img-test@example.com"], cwd=repo)

    (repo / _ARCHIVAL_FILE).write_bytes((_REPO_ROOT / _ARCHIVAL_FILE).read_bytes())
    (repo / _ATTRIBUTES_FILE).write_bytes((_REPO_ROOT / _ATTRIBUTES_FILE).read_bytes())
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "init"], cwd=repo)

    for name, date in zip(_TAG_NAMES, _TAG_DATES, strict=True):
        env = {
            "GIT_AUTHOR_NAME": "pc2img-test",
            "GIT_AUTHOR_EMAIL": "pc2img-test@example.com",
            "GIT_COMMITTER_NAME": "pc2img-test",
            "GIT_COMMITTER_EMAIL": "pc2img-test@example.com",
            "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_DATE": date,
            "PATH": os.environ.get("PATH", ""),
            "HOME": os.environ.get("HOME", ""),
        }
        _run_git(["tag", "-a", name, "-m", name], cwd=repo, env=env)

    return repo


def _archive_describe_name(repo: Path) -> str:
    """Return the substituted ``describe-name:`` value from a real archive."""
    raw_stdout = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"],
        cwd=repo,
        capture_output=True,
        check=True,
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(raw_stdout)) as tar:
        member = tar.extractfile(_ARCHIVAL_FILE)
        assert member is not None, "archive did not contain the archival file"
        content = member.read().decode("utf-8")
    match = re.search(r"^describe-name:(.*)$", content, re.MULTILINE)
    assert match is not None, f"no describe-name line in archived file:\n{content}"
    return match.group(1).strip()


def _tag_regex() -> re.Pattern[str]:
    config = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pattern = config["tool"]["setuptools_scm"]["tag_regex"]
    return re.compile(pattern)


def _archival_match_glob() -> str:
    text = (_REPO_ROOT / _ARCHIVAL_FILE).read_text(encoding="utf-8")
    match = re.search(r"match=(.+?)\)\$", text)
    assert match is not None, "no match= glob found in the archival describe format"
    return match.group(1)


def _checkout_match_glob() -> str:
    config = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    command = config["tool"]["setuptools_scm"]["git_describe_command"]
    match = re.search(r"--match\s+'([^']+)'", command)
    assert match is not None, "no --match glob found in git_describe_command"
    return match.group(1)


def test_archive_of_floating_tagged_commit_substitutes_release_tag(tmp_path: Path) -> None:
    """A real archive of the three-tag commit substitutes the release tag."""
    repo = _build_tagged_scratch_repo(tmp_path)
    describe_name = _archive_describe_name(repo)
    assert describe_name == "v0.11.0", (
        f"expected the release tag v0.11.0 to be substituted, got {describe_name!r} -- "
        f"a rolling major/minor tag on the same commit won instead"
    )


def test_release_tag_regex_parses_release_tag_only() -> None:
    """The project's own tag pattern accepts the release tag and rejects the rolling ones."""
    pattern = _tag_regex()

    release_match = pattern.match("v0.11.0")
    assert release_match is not None
    assert release_match.group("version") == "0.11.0"

    assert pattern.match("v0") is None
    assert pattern.match("v0.11") is None


def test_archival_glob_matches_checkout_glob() -> None:
    """The archive-time and checkout-time describe globs are one shared string."""
    archival_glob = _archival_match_glob()
    checkout_glob = _checkout_match_glob()
    assert archival_glob == checkout_glob == r"v[0-9]*.[0-9]*.[0-9]*", (
        f"archival glob {archival_glob!r} and checkout glob {checkout_glob!r} must both be "
        r"the literal v[0-9]*.[0-9]*.[0-9]* so a checkout and an archive of the same commit "
        "can never disagree about the tag they describe"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
