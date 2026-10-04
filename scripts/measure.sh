#!/usr/bin/env bash
# Records one progress measurement for the Tortoise ORM rewrite.
#
# Usage: scripts/measure.sh <path-to-mealie-clone> <member> <workflow> <session>
#   e.g. scripts/measure.sh ~/mealie-rewrite haodong wf-b s03
#
# Appends one row to members/<member>/<workflow>/progress.csv and keeps the raw output in
# members/<member>/<workflow>/runs/<session>/.
set -uo pipefail

BASELINE=e365efc71
CLONE=$(cd "${1:?path to the mealie clone}" && pwd)
MEMBER=${2:?member, e.g. haodong}
WORKFLOW=${3:?workflow: wf-a, wf-b or wf-c}
SESSION=${4:?session, e.g. s01}
WORKERS=${PYTEST_WORKERS:-4}

EVIDENCE=$(cd "$(dirname "$0")/.." && pwd)
OUT="$EVIDENCE/members/$MEMBER/$WORKFLOW/runs/$SESSION"
CSV="$EVIDENCE/members/$MEMBER/$WORKFLOW/progress.csv"
mkdir -p "$OUT"
cd "$CLONE"

commit=$(git rev-parse --short HEAD)
if [ -n "$(git status --porcelain)" ]; then
  echo "warning: uncommitted changes in $CLONE; commit first so the row matches a commit" >&2
fi

# --- tests -------------------------------------------------------------------------------
# keep the test database off slow bind mounts; --dist loadfile because tests in one file
# depend on each other
export DATA_DIR=$(mktemp -d)
start=$(date +%s)
timeout 45m uv run pytest -n "$WORKERS" --dist loadfile -p no:cacheprovider \
  --junitxml="$OUT/junit.xml" > "$OUT/pytest-full.log" 2>&1
test_exit=$?
test_seconds=$(( $(date +%s) - start ))
grep -E "^(FAILED|ERROR) " "$OUT/pytest-full.log" > "$OUT/failures.txt"
tail -n 60 "$OUT/pytest-full.log" > "$OUT/pytest-tail.log"
rm -f "$OUT/pytest-full.log"

read -r passed failed errors skipped < <(python3 - "$OUT/junit.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
try:
    root = ET.parse(sys.argv[1]).getroot()
except Exception:
    print("0 0 0 0"); sys.exit()
s = root if root.tag == "testsuite" else root.find("testsuite")
t, f, e, k = (int(s.get(x, 0)) for x in ("tests", "failures", "errors", "skipped"))
print(t - f - e - k, f, e, k)
PY
)
rm -f "$OUT/junit.xml"
if [ "$test_exit" -eq 124 ]; then failed="timeout"; fi
# a collection or import error leaves no junit report at all
if [ "$passed$failed$errors$skipped" = "0000" ]; then failed="no-report"; fi

# --- types -------------------------------------------------------------------------------
uv run mypy mealie > "$OUT/mypy.log" 2>&1
mypy_errors=$(grep -oE 'Found [0-9]+ error' "$OUT/mypy.log" | grep -oE '[0-9]+' || echo 0)
tail -n 1 "$OUT/mypy.log" > "$OUT/mypy-summary.txt"
rm -f "$OUT/mypy.log"

# --- rewrite progress --------------------------------------------------------------------
sqla_files=$(grep -rlE '^\s*(from|import) sqlalchemy' mealie --include=*.py | grep -v '^mealie/alembic/' | wc -l | tr -d ' ')
sqla_models=$(grep -rhE '^class \w+\(.*SqlAlchemyBase' mealie/db/models --include=*.py 2>/dev/null | wc -l | tr -d ' ')
tortoise_models=$(grep -rlE '^\s*from tortoise|^\s*import tortoise' mealie --include=*.py 2>/dev/null \
  | xargs -r grep -hE '^class \w+\(.*\b(models\.)?Model\b' | wc -l | tr -d ' ')

# --- test integrity: catches deleted, skipped or weakened tests ----------------------------
test_files=$(find tests -name 'test_*.py')
test_funcs=$(cat $test_files | grep -cE '^\s*(async )?def test_')
asserts=$(cat $test_files | grep -cE '^\s*assert\b')
skips=$(grep -rhoE 'pytest\.(mark\.)?(skip|skipif|xfail)\b' tests --include=*.py | wc -l | tr -d ' ')
changed_test_files=$(git diff --numstat "$BASELINE" -- 'tests/**/test_*.py' 'tests/test_*.py' | awk '{s+=$1+$2} END {print s+0}')
changed_test_setup=$(git diff --numstat "$BASELINE" -- tests | awk '{s+=$1+$2} END {print s+0}')
changed_test_setup=$(( changed_test_setup - changed_test_files ))
git diff "$BASELINE" -- tests > "$OUT/tests.diff"

[ -f "$CSV" ] || echo "time,member,workflow,session,commit,passed,failed,errors,skipped,mypy_errors,sqlalchemy_files,sqlalchemy_models,tortoise_models,test_functions,asserts,skip_markers,test_file_lines_changed,test_setup_lines_changed,test_seconds" > "$CSV"
row="$(date -Iseconds),$MEMBER,$WORKFLOW,$SESSION,$commit,$passed,$failed,$errors,$skipped,$mypy_errors,$sqla_files,$sqla_models,$tortoise_models,$test_funcs,$asserts,$skips,$changed_test_files,$changed_test_setup,$test_seconds"
echo "$row" >> "$CSV"

echo "$row"
echo "baseline:  3177 passed, 0 failed, 0 mypy errors, 109 SQLAlchemy files, 56 SQLAlchemy models, 0 Tortoise models, 1159 test functions, 3845 asserts"
