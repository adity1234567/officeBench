#!/usr/bin/env bash
# Resume both runs one after the other: gemma4:31b on the WorkBench set, then gemma3:4b on the
# 300 English tasks. gemma3:4b runs locally, so it waits until >= 5 GB of RAM is free.
cd "$(dirname "$0")"
free_gb() { powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)"; }

echo "WB start $(date +%H:%M)"
PYTHONUTF8=1 .venv/Scripts/python wb_bench/run.py --model_name gemma4:31b --tag wb1 >> wb_bench/run_wb1.log 2>&1
PYTHONUTF8=1 .venv/Scripts/python wb_bench/regrade.py --tag wb1 > wb_bench/final_wb1.txt 2>&1
echo "WB done $(date +%H:%M): $(head -2 wb_bench/final_wb1.txt | tr '\n' ' ')"

until [ "$(free_gb | cut -d. -f1)" -ge 5 ]; do echo "waiting for RAM (free $(free_gb) GB) $(date +%H:%M)"; sleep 300; done
echo "gemma3 start $(date +%H:%M)"
bash run_gemma3_4b_en.sh >> logs_gemma3_4b_en_progress.log 2>&1
echo "gemma3 done $(date +%H:%M): $(tail -2 logs_gemma3_4b_en_progress.log | tr '\n' ' ')"
