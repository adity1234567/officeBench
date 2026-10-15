#!/usr/bin/env bash
# Run all 300 OfficeBench tasks in English with gemma3:4b on local Ollama, then evaluate.
# Uses the unmodified agent_interact.py; finished tasks are skipped on rerun (mode=default).
cd "$(dirname "$0")"
export VLLM_BASE_URL=http://127.0.0.1:11434/v1 VLLM_API_KEY=ollama
export OFFICEBENCH_LLM_BASE_URL=http://host.docker.internal:11434/v1 OFFICEBENCH_LLM_API_KEY=ollama
export PYTHONPATH=results PYTHONUTF8=1
MODEL=gemma3:4b TAG=en
mkdir -p logs/gemma3_4b_en
configs=$(ls tasks/*/subtasks/*.json | sort -t/ -k2,2V -k4,4V)
total=$(echo "$configs" | wc -l); i=0
for cfg in $configs; do
  i=$((i+1)); task=$(echo "$cfg" | cut -d/ -f2); sub=$(basename "$cfg" .json)
  echo "[$i/$total] $task/$sub $(date +%H:%M:%S)"
  .venv/Scripts/python agent_interact.py --docker_name officebench --container_name officebench-gemma3-en \
    --model_name $MODEL --task_dir tasks/$task --config_file "$cfg" --tag $TAG --max_iter 20 --mode default \
    > "logs/gemma3_4b_en/${task}_${sub}.log" 2>&1 || echo "  failed (see log)"
done
.venv/Scripts/python evaluation.py --model_name $MODEL --tag_name $TAG > logs/gemma3_4b_en/evaluation.log 2>&1
grep -c '"is_pass": true' results/gemma3_4b_en_result.jsonl | xargs echo "passed:"
echo DONE
