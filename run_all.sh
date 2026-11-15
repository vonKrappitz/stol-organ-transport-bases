#!/usr/bin/env bash
# Full reproduction of Paper VI.
#
# Runs every script in order, then checks that every announced result file
# exists. Paths are relative to the repository root, so the file can be started
# from any working directory.

set -u
cd "$(dirname "$0")"

missing_lib() {
  # A script is skipped only when it imports a missing library UNCONDITIONALLY.
  # Several map scripts guard the import with try/except and draw a simplified
  # figure without it, so skipping them would lose output for no reason.
  # The test asks Python whether the module actually loads, not whether the
  # source mentions it.
  python3 - "$1" <<'PY'
import ast, importlib.util, sys
src = open(sys.argv[1], encoding="utf-8").read()
try:
    tree = ast.parse(src)
except SyntaxError:
    sys.exit(1)
# Only module-level imports run on every execution. An import inside a
# function or inside try/except may never run, so it must not cause a skip.
need = set()
for node in tree.body:
    if isinstance(node, ast.Import):
        need |= {a.name.split(".")[0] for a in node.names}
    elif isinstance(node, ast.ImportFrom) and node.module:
        need.add(node.module.split(".")[0])
for m in need:
    if importlib.util.find_spec(m) is None:
        sys.exit(0)          # unconditional import of a missing module
sys.exit(1)
PY
}

echo "=== Paper VI: full reproduction ==="
echo "Scripts read from data/ and write results to results/ and figures to figures/"
echo ""

SKIPPED=0
MISSING_LIB=0
RUN=0
FAILED=0
COUNT=0
for s in scripts/0[1-9]_*.py scripts/1[0-9]_*.py scripts/2[0-9]_*.py; do
    [ -e "$s" ] || continue
    COUNT=$((COUNT+1))
    # Script 03 fetches the voivodeship boundaries and geocodes the centres over
    # the network. Its output is already in data/, so it is skipped when present.
    case "$s" in
      *03_geocoding*)
        if [ -s data/voivodeship_boundaries.json ]; then
          echo ">>> $s  [SKIPPED: data/voivodeship_boundaries.json is present, no network needed]"
          echo ""
          SKIPPED=$((SKIPPED+1)); continue
        fi
        ;;
    esac
    if missing_lib "$s"; then
      echo ">>> $s  [SKIPPED: missing library, see requirements.txt]"
      SKIPPED=$((SKIPPED+1)); MISSING_LIB=$((MISSING_LIB+1)); continue
    fi
    RUN=$((RUN+1))
    echo ">>> $s"
    python3 "$s" || { echo ">>> $s FAILED"; FAILED=$((FAILED+1)); }
    echo ""
done

# Coverage check: the loop must reach every script in the directory.
TOTAL=$(ls scripts/*.py 2>/dev/null | wc -l)
if [ "$COUNT" -ne "$TOTAL" ]; then
  echo ">>> WARNING: the loop covered $COUNT of $TOTAL scripts"
fi

echo "=== Check: does every announced output file exist ==="
# A script that announces a file it did not write is worse than one that
# writes nothing: the announcement reads like proof. This compares what the
# scripts SAID they saved against what is actually on disk.
python3 - <<'PY'
import glob, json, os, sys
expected = {
    "results/compare_methods.json", "results/sensitivity.json",
    "results/correlations.json", "results/distance_profile.json",
    "results/minimax_audit.json", "results/night_by_aircraft_class.json",
    "results/free_airfield_choice.json", "results/cost_per_mission.json",
    "results/mission_loss_distribution.json", "results/frechet_invariance.json",
    "results/invariance_boundary.json", "results/margin_perturbation.json",
    "results/lower_bound.json", "results/optimal_set.json",
    "results/feeder_configurations.json", "results/heart_with_overheads.json",
    "results/aircraft_classes.json", "results/source_sets.json",
    "results/coverage_thresholds.json", "results/transport_flows.json",
}
missing = sorted(f for f in expected if not os.path.exists(f))
empty = sorted(f for f in expected if os.path.exists(f) and os.path.getsize(f) < 10)
for f in missing:
    print(f"  MISSING  {f}")
for f in empty:
    print(f"  EMPTY    {f}")
print(f"  result files: {len(expected) - len(missing)} of {len(expected)}")
sys.exit(1 if missing or empty else 0)
PY
CHECK=$?
echo ""
echo "Note: the four-layer validator (_walidator.py) checks the manuscript,"
echo "the supplementary material, the cover letter and the highlights against"
echo "these result files. It lives with the submission package, not here,"
echo "because this repository holds only the code and the data."
echo ""

echo "=== Done ==="
echo "Scripts run:      $RUN of $TOTAL"
echo "Skipped:          $SKIPPED"
echo "Failed:           $FAILED"
echo "Numeric results:  results/*.json"
echo "Figures:          figures/*.png"
if [ "$MISSING_LIB" -gt 0 ]; then
  echo ""
  echo "NOTE: some scripts were skipped for missing libraries."
  echo "Install them with: pip install -r requirements.txt"
fi

# A failed script or a missing result file ends the run with a non-zero code.
if [ "$FAILED" -gt 0 ] || [ "$CHECK" -ne 0 ]; then
  exit 1
fi
