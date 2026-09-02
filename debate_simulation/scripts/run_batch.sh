#!/usr/bin/env bash
#
# Batch experiment runner — leave it going overnight.
#
# Runs every (topic x pair) cell in both conditions, with the judge.
# Each cell is independent: a failure in one does not stop the others, and
# re-running the script skips nothing (every run creates a new experiment_id),
# so check the summary at the end for cells that failed.
#
# Usage:
#   ./scripts/run_batch.sh                    # defaults below
#   TURNS=6 PAIRS=4 ./scripts/run_batch.sh    # override
#   TOPICS="Abortion" ./scripts/run_batch.sh  # single topic
#
# Progress is written to experiments/batch_<timestamp>.log; the terminal
# shows one line per cell.

set -uo pipefail

cd "$(dirname "$0")/.." || exit 1

TURNS="${TURNS:-8}"
PAIRS="${PAIRS:-6}"
PROFILE="${PROFILE:-local}"
JUDGE_RUNS="${JUDGE_RUNS:-3}"
TOPICS="${TOPICS:-Abortion|Drug Legalization}"

PYTHON=".venv/bin/python"
[ -x "$PYTHON" ] || PYTHON="python3"

STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="experiments/batch_${STAMP}.log"
mkdir -p experiments

# Split TOPICS on '|' so topic names may contain spaces.
IFS='|' read -r -a TOPIC_LIST <<< "$TOPICS"

TOTAL=$(( ${#TOPIC_LIST[@]} * PAIRS ))
DONE=0
FAILED=0
FAILED_CELLS=()

echo "=========================================================="
echo " Batch run — ${STAMP}"
echo "=========================================================="
echo " profile    : $PROFILE"
echo " turns      : $TURNS"
echo " pairs      : $PAIRS  (persona-index 0..$((PAIRS-1)))"
echo " topics     : ${TOPIC_LIST[*]}"
echo " judge runs : $JUDGE_RUNS"
echo " cells      : $TOTAL  (${TOTAL} x 2 conditions = $((TOTAL*2)) debates)"
echo " log        : $LOG"
echo "=========================================================="
echo

# Fail fast if the model server is unreachable — better now than at 3am.
if ! curl -sf http://localhost:11434/api/version >/dev/null 2>&1; then
  echo "ERROR: Ollama is not responding on http://localhost:11434"
  echo "Start it with 'ollama serve' (keep that terminal open) and retry."
  exit 1
fi

START_ALL=$(date +%s)

for topic in "${TOPIC_LIST[@]}"; do
  for (( i=0; i<PAIRS; i++ )); do
    pair=$(printf "pair-%02d" "$i")
    cell_start=$(date +%s)
    printf "[%2d/%2d] %-20s %s ... " "$((DONE+1))" "$TOTAL" "$topic" "$pair"

    echo "=== $(date '+%F %T')  $topic  $pair ===" >> "$LOG"
    "$PYTHON" scripts/run_debate.py \
      --profile "$PROFILE" \
      --topic "$topic" \
      --pair "$pair" \
      --persona-index "$i" \
      --turns "$TURNS" \
      --judge \
      --judge-runs "$JUDGE_RUNS" >> "$LOG" 2>&1
    status=$?
    echo "--- exit: $status ---" >> "$LOG"

    elapsed=$(( $(date +%s) - cell_start ))
    if [ $status -eq 0 ]; then
      printf "ok (%dm%02ds)\n" $((elapsed/60)) $((elapsed%60))
    else
      printf "FAILED (%dm%02ds) — see %s\n" $((elapsed/60)) $((elapsed%60)) "$LOG"
      FAILED=$((FAILED+1))
      FAILED_CELLS+=("$topic / $pair")
    fi
    DONE=$((DONE+1))
  done
done

TOTAL_ELAPSED=$(( $(date +%s) - START_ALL ))

echo
echo "=========================================================="
echo " Finished in $((TOTAL_ELAPSED/3600))h $(((TOTAL_ELAPSED%3600)/60))m"
echo " cells: $DONE   failed: $FAILED"
if [ ${#FAILED_CELLS[@]} -gt 0 ]; then
  echo
  echo " Failed cells:"
  for c in "${FAILED_CELLS[@]}"; do echo "   - $c"; done
fi
echo "=========================================================="
echo
echo " Inspect the results with:"
echo "   uv run python scripts/show_results.py"
echo "   uv run python scripts/show_results.py --compare"
echo
echo " Full log: $LOG"