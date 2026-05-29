# Run notes — 2026-05-27 on NVIDIA L40S

The canonical reference run for this harness. If you want to compare a future run to a "known good" output, this is what you compare against.

## What ran

- **Config:** `configs/qwen7b-resetdata-qlora.yml`
- **Base model:** `Qwen/Qwen2.5-7B-Instruct`
- **Method:** QLoRA (4-bit quant + LoRA adapter, r=16, alpha=32, all-linear targets)
- **Dataset:** `data/resetdata_platform_100_alpaca.jsonl` (100 alpaca-format examples)
- **Hardware:** NVIDIA L40S (sm_89, 48GB VRAM), driver 580.65.06
- **Host:** `ove-linux-l40-newclaw` VM, venv at `/home/brady/Fine-Tuning/axolotl-big/.venv`
- **Trained by:** Adrian Amoddio

## Headline metrics

| Metric | Value |
|---|---|
| Wall-clock training time | **97.94 seconds** (1m 38s, pure training; +~10s setup/save) |
| Steps | 150 (3 epochs × 100 examples / batch_size 2) |
| Throughput | 1.65 iterations/sec, 3.06 samples/sec |
| Tokens/sec/GPU | ~50–80 |
| Peak GPU memory | **6.05 GiB** (out of L40S's 48GB — ~12% utilisation) |
| Final reported `train_loss` | 1.192 (averaged across all 150 steps) |
| Final per-step losses (epoch 3) | 0.04 – 0.50, mostly 0.1 – 0.3 |

The pulled-up average loss reflects high values from epoch 1; by mid-epoch 2 onwards, per-step losses are mostly under 0.3. No divergence, no NaN spikes, smooth cosine LR decay from 2e-4 to ~0.

## Output produced

- Adapter weights: `outputs/qwen7b-resetdata-qlora/adapter_model.safetensors` (~150MB) — kept on the VM, not committed to this repo (see `.gitignore`).
- Checkpoints at steps 50, 100, 150 — intermediate, can be deleted.

## Eval outcome — does the fine-tune actually work?

See `baseline_outputs.txt` vs `finetuned_outputs.txt` in this directory. Three clear wins:

1. **Acronym disambiguation.** Baseline guessed FTaaS = "File Transfer as a Service" and wrote a whole answer about encryption + bandwidth (Q2, Q9). Fine-tuned correctly knows FTaaS = Fine-Tuning as a Service. Single cleanest demonstration of fine-tuning value.
2. **ResetData-specific framing.** Fine-tuned names actual services (GPUaaS, LLMaaS), uses internal positioning language, stays on-domain. Baseline gives generic AI-consultant boilerplate.
3. **Style transfer.** Fine-tuned answers are crisp and factual (matching the training data tone). Baseline produces verbose hedged essays, several of which get truncated mid-word at the 300-token limit.

## What this tells us about the L40S as a fine-tuning substrate

- **Headroom.** Peak 6 GiB on 48 GB means we could train much larger models (up to ~70B with QLoRA) or use much longer sequence lengths, on the same hardware.
- **Speed.** Sub-2-minute training for 100 examples means the platform could comfortably run dozens of customer fine-tunes per hour per L40S.
- **No flash-attention.** Throughput would likely improve 20–30% with flash-attn installed. Worth doing for the platform.

## What's missing from this record

- **Full training log.** Only the head (config dump) and tail (final 50 steps + completion) are saved here as `training.log.headtail.txt`. The middle ~267 lines (epochs 0–2.1) are not captured. Re-running training with `tee` to a log file would produce a complete log next time.
- **Auto-generated model card.** Axolotl writes a README.md into the output dir with training args + dataset stats. Not captured here yet.
- **Inference timing.** The eval scripts ran but I didn't capture how long each model took to produce its 10 answers. Future runs should `time` the eval too.
