#!/usr/bin/env bash
# Rerun all 300 OfficeBench tasks in Bangla with the re-translated instructions
# (analysis/bn_cache.json, guidelines v2): gemma4:31b first, then gpt-oss:20b, then evaluate.
# Both models go through the endpoint in .env (Ollama cloud), as in the original Bangla runs.
# Tag bn2 keeps the original *_bn outputs untouched; finished tasks are skipped on rerun.
cd "$(dirname "$0")"
export PYTHONPATH=results PYTHONUTF8=1 PYTHONWARNINGS=ignore
TAG=bn2
CONTAINER=officebench-bn2
configs=$(ls tasks/*/subtasks/*.json | sort -t/ -k2,2V -k4,4V)
total=$(echo "$configs" | wc -l)
for MODEL in gemma4:31b gpt-oss:20b; do
  LOG=logs/${MODEL//[:\/]/_}_$TAG
  mkdir -p "$LOG"
  echo "=== $MODEL $(date +%H:%M:%S)"
  i=0
  for cfg in $configs; do
    i=$((i+1)); task=$(echo "$cfg" | cut -d/ -f2); sub=$(basename "$cfg" .json)
    echo "[$MODEL $i/$total] $task/$sub $(date +%H:%M:%S)"
    .venv/Scripts/python agent_interact.py --docker_name officebench --container_name $CONTAINER \
      --model_name $MODEL --task_dir tasks/$task --config_file "$cfg" --tag $TAG --max_iter 20 \
      --mode default --lang bn > "$LOG/${task}_${sub}.log" 2>&1 || echo "  failed (see log)"
    if grep -q "429" "$LOG/${task}_${sub}.log"; then echo "  usage limit (429) hit; stopping"; exit 2; fi
  done
  .venv/Scripts/python evaluation.py --model_name $MODEL --tag_name $TAG > "$LOG/evaluation.log" 2>&1
  echo "$MODEL passed: $(grep -c '"is_pass": true' results/${MODEL//[:\/]/_}_${TAG}_result.jsonl) / $total"
done
echo DONE
