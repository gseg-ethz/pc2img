#!/usr/bin/env bash
# Scratch-clone simulation of the Read the Docs tag-fetch hardening in
# .readthedocs.yaml. It runs the COMMITTED build.jobs.post_checkout and
# build.jobs.post_install commands (extracted from the file, not copied) against
# throwaway clones of this repository, so what is proven is what ships.
#
# Cases:
#   1. shallow clone  -> commands unshallow it and bring the tags in
#   2. complete clone -> commands exit 0 (an unconditional --unshallow is fatal here)
#   3. moved tag      -> `git fetch --tags --force` updates it (plain --tags is rejected)
#   4. post_install   -> shallow assertion passes on a full clone and fails on a
#                        shallow one; version assertion passes on a real version and
#                        fails on setuptools_scm's tagless 0.0.* fallback
#
# Clones go through file:// on purpose: on a local-path clone git prints
# "warning: --depth is ignored in local clones; use file:// instead" and produces
# a complete clone, so the shallow case would test nothing. The case asserts the
# clone IS shallow before the commands run and fails otherwise.
#
# Usage (from anywhere): bash .planning/phases/07-gsegutils-0-6-adoption-0-11-0-release/07-rtd-simulation.sh
# Prints `rtd-sim-ok` as its last line on success.
set -euo pipefail

REPO="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
cd "$REPO"

S="$(mktemp -d)"
trap 'rm -rf "$S"' EXIT

echo "git version: $(git --version)"

# --- extract the committed commands (no yq: awk over the list) -------------------
extract_list() {
  awk -v key="$1" '
    $0 ~ "^    " key ":" { on = 1; next }
    on && /^    [A-Za-z_]+:/ { exit }
    on && /^      - / { sub(/^      - /, ""); print }
  ' "$REPO/.readthedocs.yaml"
}

mapfile -t POST_CHECKOUT < <(extract_list post_checkout)
mapfile -t POST_INSTALL < <(extract_list post_install)
[ "${#POST_CHECKOUT[@]}" -eq 2 ] || { echo "expected 2 post_checkout commands, got ${#POST_CHECKOUT[@]}"; exit 1; }
[ "${#POST_INSTALL[@]}" -eq 2 ] || { echo "expected 2 post_install commands, got ${#POST_INSTALL[@]}"; exit 1; }
echo "post_checkout[0]: ${POST_CHECKOUT[0]}"
echo "post_checkout[1]: ${POST_CHECKOUT[1]}"
echo "post_install[0]: ${POST_INSTALL[0]}"
echo "post_install[1]: ${POST_INSTALL[1]}"

# Run one committed command inside a clone, as RTD would: one command per shell,
# fail-fast. `sh` (dash on ubuntu) is the stricter of the two shells RTD could use.
run_in() {
  local dir="$1" cmd="$2"
  (cd "$dir" && sh -ec "$cmd")
}

is_shallow() { git -C "$1" rev-parse --is-shallow-repository; }

# `python` must resolve for the post_install command; point it at python3.
mkdir "$S/bin"
ln -s "$(command -v python3)" "$S/bin/python"
export PATH="$S/bin:$PATH"

# --- the fake origin --------------------------------------------------------------
git clone --quiet --bare "$REPO" "$S/origin.git"
git -C "$S/origin.git" tag -f v0 HEAD~5 >/dev/null      # a floating tag on an older commit
ORIGIN_COMMITS=$(git -C "$S/origin.git" rev-list --count HEAD)
echo "origin commits: $ORIGIN_COMMITS"
[ "$ORIGIN_COMMITS" -gt 50 ] || { echo "origin too small to make depth 50 shallow"; exit 1; }

# --- case 1: shallow clone --------------------------------------------------------
echo "== case 1: shallow clone"
git clone --quiet --depth 50 "file://$S/origin.git" "$S/shallow"
BEFORE=$(is_shallow "$S/shallow")
echo "is-shallow-repository before commands: $BEFORE"
[ "$BEFORE" = "true" ] || { echo "shallow case is not shallow"; exit 1; }
SHALLOW_COMMITS=$(git -C "$S/shallow" rev-list --count HEAD)
echo "commits before commands: $SHALLOW_COMMITS of $ORIGIN_COMMITS"
[ "$SHALLOW_COMMITS" -lt "$ORIGIN_COMMITS" ] || { echo "shallow clone already holds the whole history; case is vacuous"; exit 1; }
for cmd in "${POST_CHECKOUT[@]}"; do run_in "$S/shallow" "$cmd"; done
AFTER=$(is_shallow "$S/shallow")
echo "is-shallow-repository after commands: $AFTER"
[ "$AFTER" = "false" ] || { echo "shallow clone was left shallow"; exit 1; }
[ "$(git -C "$S/shallow" tag -l v0)" = "v0" ] || { echo "tag v0 missing after fetch"; exit 1; }
FULL_COMMITS=$(git -C "$S/shallow" rev-list --count HEAD)
echo "commits after commands: $FULL_COMMITS"
[ "$FULL_COMMITS" -eq "$ORIGIN_COMMITS" ] || { echo "history incomplete after unshallow"; exit 1; }
echo "case 1 ok: unshallowed to the full history, v0 present"

# --- case 2: complete clone -------------------------------------------------------
echo "== case 2: complete clone"
git clone --quiet "file://$S/origin.git" "$S/full"
BEFORE=$(is_shallow "$S/full")
echo "is-shallow-repository before commands: $BEFORE"
[ "$BEFORE" = "false" ] || { echo "complete case is shallow"; exit 1; }
# Negative control: the old unconditional unshallow is fatal on a complete clone.
if (cd "$S/full" && git fetch --unshallow >/dev/null 2>&1); then
  echo "control failed: unconditional --unshallow succeeded on a complete clone"
  exit 1
fi
echo "control ok: unconditional --unshallow is fatal on a complete clone"
for cmd in "${POST_CHECKOUT[@]}"; do run_in "$S/full" "$cmd"; done
echo "case 2 ok: both commands exit 0 on a complete clone"

# --- case 3: moved tag ------------------------------------------------------------
echo "== case 3: moved floating tag"
git -C "$S/origin.git" tag -f v0 HEAD >/dev/null
ORIGIN_HEAD=$(git -C "$S/origin.git" rev-parse HEAD)
# Negative control: a plain `git fetch --tags` rejects the moved tag.
if (cd "$S/full" && git fetch --tags >/dev/null 2>&1); then
  echo "control failed: plain --tags accepted a moved tag"
  exit 1
fi
echo "control ok: plain 'git fetch --tags' rejects the moved tag"
[ "$(git -C "$S/full" rev-parse v0)" != "$ORIGIN_HEAD" ] || { echo "v0 already moved; case is vacuous"; exit 1; }
for cmd in "${POST_CHECKOUT[@]}"; do run_in "$S/full" "$cmd"; done
[ "$(git -C "$S/full" rev-parse v0)" = "$ORIGIN_HEAD" ] || { echo "v0 was not force-updated"; exit 1; }
echo "case 3 ok: v0 force-updated to $ORIGIN_HEAD"

# --- case 4: post_install ---------------------------------------------------------
echo "== case 4: post_install assertions"
# Shallow assertion: passes on the full clone, fails on a shallow one.
run_in "$S/full" "${POST_INSTALL[1]}"
git clone --quiet --depth 50 "file://$S/origin.git" "$S/shallow2"
[ "$(is_shallow "$S/shallow2")" = "true" ] || { echo "shallow2 is not shallow"; exit 1; }
if run_in "$S/shallow2" "${POST_INSTALL[1]}"; then
  echo "control failed: the shallow assertion passed on a shallow clone"
  exit 1
fi
echo "shallow assertion ok: passes on a full clone, fails on a shallow one"

# Version assertion: substitute the installed-version lookup so the result does
# not depend on what is installed here. A real version passes, 0.0.* fails.
substitute_version() { printf '%s' "${POST_INSTALL[0]/m.version(\'pc2img\')/\'$1\'}"; }
GOOD=$(substitute_version "0.11.0")
BAD=$(substitute_version "0.0.post41")
[ "$GOOD" != "${POST_INSTALL[0]}" ] || { echo "substitution did not apply"; exit 1; }
run_in "$S/full" "$GOOD"
if run_in "$S/full" "$BAD"; then
  echo "control failed: version 0.0.post41 passed the assertion"
  exit 1
fi
echo "version assertion ok: 0.11.0 passes, 0.0.post41 fails"

echo "rtd-sim-ok"
