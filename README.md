# axolotyl-POC

A reproducible Qwen2.5-7B QLoRA fine-tuning harness, built to validate the workflow for ResetData's planned Fine-Tuning as a Service (FTaaS) capability.

## What this is

100 instruction/output examples about ResetData's services and platform are used to fine-tune `Qwen/Qwen2.5-7B-Instruct` with a QLoRA adapter. The harness ships:

- The dataset (100 alpaca-format examples)
- A pinned axolotl config (lora_r=16, 3 epochs, bf16, gradient checkpointing)
- Exact dependency lock for the environment that produced the original successful run
- Eval scripts that compare the **baseline** (untrained) model against the **fine-tuned** model on the same 10 questions

The point isn't the model itself — it's that someone can clone this repo and reproduce the exact training run, then use that as the starting point for FTaaS platform work.

## Hardware

### Canonical setup — what produced the original run
- **GPU:** NVIDIA L40S (48GB VRAM)
- **Host:** ResetData internal VM (`ove-linux-l40-newclaw`)
- **Driver:** 580.65.06
- **CUDA:** 12.8
- **Python:** 3.11

A QLoRA run with these settings on the L40S uses ~12–15GB VRAM and takes a few minutes for 3 epochs on 100 examples.

### Alternative — running at home on an RTX 3080
The 7B QLoRA config will *technically* fit on a 10GB RTX 3080 but it's tight and prone to OOM on longer sequences. For local experimentation, swap in a smaller base model:

| Base model | 4-bit footprint | Fits comfortably on |
|---|---|---|
| `Qwen/Qwen2.5-7B-Instruct` (canonical) | ~4GB | L40S, A100, 4090, 24GB+ cards |
| `Qwen/Qwen2.5-3B-Instruct` | ~1.7GB | 3080 (10GB), 4070, 3060 12GB |
| `Qwen/Qwen2.5-1.5B-Instruct` | ~0.9GB | Anything with 8GB+, also CPU-feasible |

If you switch base models, also lower `sequence_len` to 512 in the YAML (the data is short, you don't need 1024) and consider raising `gradient_accumulation_steps` to keep effective batch size meaningful.

## Setup

Build a fresh Python venv from the locked dependencies:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --extra-index-url https://download.pytorch.org/whl/cu128 -r requirements-lock.txt
```

This installs the exact 200 packages (including `torch==2.7.0+cu128`, `axolotl==0.16.1`, `transformers==5.5.0`, etc.) from the original L40S run.

**Shortcut for ResetData engineers on the company L40S VM:** the venv already exists at `/home/brady/Fine-Tuning/axolotl-big/.venv` — `source` that instead of building your own. Don't rely on this for anything serious; it could be rebuilt or moved.

### A note on HuggingFace cache
The first run will download Qwen2.5-7B-Instruct (~15GB) into `~/.cache/huggingface/hub/`. Subsequent runs reuse the cache. The `.gitignore` excludes it; don't worry about it polluting the repo.

## Run training

From the repo root:

```bash
bash scripts/train.sh
```

This trains for 3 epochs and writes the QLoRA adapter to `./outputs/qwen7b-resetdata-qlora/`. To also capture a log file:

```bash
mkdir -p runs/$(date +%Y-%m-%d) && \
  bash scripts/train.sh 2>&1 | tee runs/$(date +%Y-%m-%d)/training.log
```

## Evaluate

Two scripts, run them in order:

```bash
# Untrained Qwen2.5-7B-Instruct, 10 ResetData questions → baseline_outputs.txt
python scripts/baseline_test.py

# Same 10 questions, this time with the QLoRA adapter loaded → finetuned_outputs.txt
python scripts/finetuned_test.py
```

Diff `baseline_outputs.txt` against `finetuned_outputs.txt` to see what the fine-tune learned. Expect the fine-tuned model to give noticeably more ResetData-specific, terminology-correct answers — especially on direct factual questions ("what does ResetData provide?") and on questions referencing internal concepts like GPUaaS vs LLMaaS.

## What "it worked" looks like

A successful training run produces:
- Final training loss ~0.5–1.5 (highly dependent on data; not a hard target)
- An `outputs/qwen7b-resetdata-qlora/` directory containing the adapter weights (`adapter_model.safetensors`), tokenizer, and config
- Fine-tuned eval outputs that mention ResetData by name, reference its services accurately, and don't hallucinate generic AI-platform features

A known-good training log will live under `runs/` once we capture one.

## Known limitations

- **No eval/validation split.** Training runs blind — no signal on overfitting. With only 100 examples, splitting off 10% to evaluate would leave very little training data, but for a real product this needs `val_set_size` in the YAML.
- **Eval uses sampling (`do_sample=True`, `temperature=0.2`).** Same question gives slightly different answers across runs. For regression-testing the fine-tune, switch to greedy decoding (`do_sample=False`) or set a torch seed.
- **No flash-attention.** Not installed in the canonical environment. Adding `flash-attn` would speed training by ~20–30% but requires a separate `pip install` and matching CUDA wheels.
- **Hardcoded paths.** Eval scripts assume the adapter lives at `./outputs/qwen7b-resetdata-qlora` and write outputs to the CWD. Fine for a PoC; would need CLI flags for the platform.
- **Only one method tested.** This is QLoRA. The platform will eventually need to also support full fine-tuning, LoRA, DPO, ORPO, etc. — each with its own config shape.

## Repo layout

```
axolotyl-POC/
├── README.md
├── .gitignore
├── requirements.txt          # human-readable top-level pins
├── requirements-lock.txt     # exact 200-package lock
├── configs/
│   └── qwen7b-resetdata-qlora.yml   # the axolotl training config
├── data/
│   ├── resetdata_platform_100_alpaca.jsonl   # 100 instruction/output examples
│   └── resetdata_platform_100_preview.md     # human-readable preview
├── scripts/
│   ├── train.sh             # wraps `axolotl train`
│   ├── baseline_test.py     # eval untrained model
│   └── finetuned_test.py    # eval with QLoRA adapter
└── runs/                    # known-good training logs (created after first run)
```
