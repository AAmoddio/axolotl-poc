#!/usr/bin/env bash
# Train the Qwen2.5-7B QLoRA adapter on the ResetData FTaaS dataset.
#
# Run from the repo root:
#     bash scripts/train.sh
#
# Or with a different config:
#     bash scripts/train.sh configs/my-other-config.yml
#
# To capture a training log alongside:
#     mkdir -p runs/$(date +%Y-%m-%d) && \
#       bash scripts/train.sh 2>&1 | tee runs/$(date +%Y-%m-%d)/training.log
#
# If `axolotl train` fails (e.g. older install), the equivalent older command is:
#     accelerate launch -m axolotl.cli.train configs/qwen7b-resetdata-qlora.yml

set -euo pipefail

CONFIG="${1:-configs/qwen7b-resetdata-qlora.yml}"

axolotl train "$CONFIG"
