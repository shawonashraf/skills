---
name: llm-finetuning
description: >-
  Fine-tune large language models from the Hugging Face Hub using Axolotl (YAML-driven)
  or TRL (Python/programmatic). Provides sane, research-backed defaults for SFT, DPO,
  ORPO, KTO, SimPO, and GRPO, while letting the user override any parameter. Saves
  models/adapters to disk and uploads to the Hugging Face Hub (adapter or merged).
  Use when the user wants to fine-tune an LLM, prepare a training config, run a
  training job, or push a fine-tuned model to the Hub.
license: MIT
---

# LLM Fine-Tuning with Axolotl & TRL

**Expert ML engineer** for fine-tuning Hugging Face LLMs. Two equally valid paths:

- **Axolotl** — a single YAML file drives the whole pipeline (preprocess → train → eval → merge → inference). Best for repeatable, declarative runs; switch SFT↔DPO↔GRPO by changing one key. Wraps Transformers/PEFT/TRL/Accelerate/DeepSpeed.
- **TRL** — programmatic `SFTTrainer` / `DPOTrainer` / `GRPOTrainer` in Python. Best when you need custom logic, dataset manipulation, or a YAML+`TrlParser` script (the modern Hugging Face recommended pattern).

**Default to Axolotl** for standard runs (less code, validated config, built-in packing/kernels). Reach for **TRL** when the run needs custom Python data prep, custom reward functions, or composition with other libraries.

## When to use this skill

- Load a base/instruct model from the HF Hub and fine-tune it.
- Prepare a training config with sane defaults that the user can override.
- Run SFT, DPO, ORPO, KTO, SimPO, or GRPO.
- Save the model/adapter to disk and upload to the HF Hub.

## Prerequisites

### Environment (always use uv — never raw pip/venv)

Follow the `uv-env` skill. Quick version:

```bash
which uv || echo "install uv first"
uv venv
source .venv/bin/activate

# Axolotl path (installs transformers/peft/trl/deepspeed/accelerate/flash-attn)
pip3 install --upgrade pip
pip3 install axolotl              # or: git clone https://github.com/axolotl-ai-cloud/axolotl && pip3 install -e './axolotl[flash-attn,deepspeed]'

# TRL path
uv add trl transformers datasets accelerate peft bitsandbytes sentencepiece
# optional, big wins: uv add flash-attn --no-build-isolation liger-kit
```

### Hugging Face auth

```bash
export HF_TOKEN="hf_..."          # required for private/gated models and for upload
huggingface-cli login            # alternative; writes token to ~/.cache/huggingface/token
# Gated models (Llama, etc.) also need the license accepted on the Hub page.
```

Never hardcode tokens in scripts or configs. Read from `HF_TOKEN`.

### Hardware reality check

| Method | ~VRAM @ 7B, seq 4096 | Notes |
|---|---|---|
| Full FT (bf16) | ~80 GB+ | Needs FSDP/DeepSpeed ZeRO-3 |
| LoRA (16-bit base) | ~20–24 GB | Best quality if it fits |
| QLoRA (4-bit base) | ~8–12 GB | Fits 7B on a single 24 GB / many 12 GB GPUs |
| GRPO | base VRAM + generation buffer | Generation is the bottleneck; tune `num_generations`, `max_completion_length` |

Flash Attention 2+ requires Ampere (A100/RTX 30xx+) or newer. On older GPUs drop `flash_attention` and `sample_packing` (packing's correct masking needs FA2+).

---

## Sane defaults (override anything)

These are the research-backed starting points. Present them; let the user change any value.

### Method selection

| Goal | Method | `rl:` (axolotl) / trainer (trl) | Needs ref model? |
|---|---|---|---|
| Instruction / chat tuning | SFT | — / `SFTTrainer` | no |
| Align to preferences (chosen vs rejected) | DPO | `dpo` / `DPOTrainer` | yes |
| SFT + preference in **one pass**, lowest memory | ORPO | `orpo` / `ORPOTrainer` | **no** |
| Unpaired preference (good/bad labels) | KTO | `kto` / `KTOTrainer` | no |
| RL with verifiable rewards (math, code) | GRPO | `grpo` / `GRPOTrainer` | no (β=0 default) |

When unsure, start with **SFT (LoRA)**; for alignment add **ORPO** (cheaper than DPO — no reference model, single pass).

### Universal training defaults

| Parameter | Sane default | Why |
|---|---|---|
| `sequence_len` | 4096 (2048 if OOM) | Long enough for chat; halving roughly halves attention memory |
| `micro_batch_size` / `per_device_train_batch_size` | 2 (drop to 1 on OOM) | |
| `gradient_accumulation_steps` | 8 | effective batch = 2×8 = 16 |
| `num_epochs` / `num_train_epochs` | 1–3 (1 often enough with good data) | |
| `lr_scheduler` | `cosine` (TRL: `cosine_with_min_lr`) | |
| `warmup_ratio` | 0.05 | |
| `optimizer` | `adamw_torch_fused` (Ampere+) else `adamw_torch` | |
| `weight_decay` | 0.01 | |
| `max_grad_norm` | 1.0 | |
| `bf16` | `auto` / `True` | Don't use fp16 if base is bf16 — mismatched dtypes hurt |
| `tf32` | `auto` / `True` (Ampere+) | |
| `flash_attention` | `true` | O(n²)→O(n) memory; ~30%+ speedup. Off only on pre-Ampere |
| `gradient_checkpointing` | `true` | Trades compute for ~30–50% VRAM |
| `sample_packing` / `packing` | `true` | 3–5× throughput on short-seq data; **requires Flash Attention 2+** |
| `seed` | 42 | reproducibility |
| `logging_steps` | 10 | |
| `save_strategy` | `steps`, `save_steps` 100–200, `save_total_limit` 3 | |
| `eval_steps` | 50–100, `val_set_size` 0.05 | |

### Learning rates by method (critical — don't reuse across methods)

| Method | Full fine-tune | With LoRA (≈10×) |
|---|---|---|
| SFT | 2e-5 | **2e-4** |
| DPO | 5e-7 | 5e-6 |
| ORPO | 5e-6 (β/λ=0.1) | ~1e-5 |
| GRPO | 1e-6 | 1e-5 |
| Prompt Tuning | — | 1e-2 to 3e-2 |

LoRA trains far fewer params, so it needs a higher LR to move comparably. Mixing these up is the #1 cause of "loss won't decrease" / "model collapsed".

### LoRA defaults

```yaml
adapter: lora            # qlora for 4-bit base (saves VRAM, ~same quality if it fits in 16-bit)
lora_r: 32               # rank; 16 for speed, 64 for capacity
lora_alpha: 64           # rule of thumb: 2× rank (effective LR scales as alpha/rank)
lora_dropout: 0.05
lora_target_linear: true # apply to ALL linear layers — beats q_proj/v_proj-only for instruction tuning
# explicit modules (if target_linear unsupported): q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj
```

QLoRA note: 4-bit base lets large models fit small GPUs, but if a model already fits in 16-bit, plain LoRA or full FT can converge better. Match method to VRAM budget.

### Dataset format

Prefer **conversational/chat-template** format (the modern standard):

```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

- Train on **assistant turns only**: axolotl `roles_to_train: ["assistant"]` + `train_on_inputs: false`; TRL `assistant_only_loss=True` (needs `{% generation %}` tags in the chat template — TRL auto-patches known families like Qwen3).
- For prompt/completion datasets, TRL `completion_only_loss` (default True) masks the prompt automatically.
- **Always set the chat template to match the base model.** Qwen/Gemma/Llama3 ship one in the tokenizer; if absent, set `chat_template: chatml` (axolotl) or pass `chat_template_path`/use `setup_chat_format` (TRL). A mismatched template garbles the signal.
- **Align the EOS token** with the chat template: e.g. Qwen2.5 → `eos_token="<|im_end|>"` in TRL `SFTConfig`.

### Distributed strategy (pick exactly ONE — never combine)

- **LoRA** → FSDP2 (`fsdp_version: 2` in axolotl; `accelerate` FSDP config in TRL). Recommended for new runs.
- **Full FT of large models** → DeepSpeed ZeRO-3 (`deepspeed: deepspeed_configs/zero3_bf16.json`). ZeRO-1 shards optimizer, ZeRO-2 adds grads, ZeRO-3 shards params too.
- ZeRO-3 + QLoRA needs special handling; see axolotl `fsdp_qlora` docs.
- Multi-node → `torchrun` or `--launcher ray`.

---

## Workflow phases

### Phase 1 — Prepare data & validate format

1. Put data in conversational JSONL (or HF dataset repo).
2. **Run `axolotl preprocess config.yml` first** (or load + print one tokenized sample in TRL). This surfaces format/template errors before burning GPU hours. Set `dataset_prepared_path:` to cache.
3. Sanity check: print one raw and one tokenized example; confirm roles, lengths, and that the loss mask covers the assistant response only.

### Phase 2 — Load model & fine-tune

#### Path A: Axolotl (declarative YAML)

Minimal SFT-LoRA config (`config.yml`):

```yaml
# --- model ---
base_model: Qwen/Qwen2.5-1.5B          # any HF Hub id; gated models need HF_TOKEN + accepted license
trust_remote_code: false

# --- method / adapter ---
adapter: lora                           # remove for full FT; use qlora + load_in_4bit: true for low VRAM
load_in_4bit: false
load_in_8bit: false

# --- data ---
datasets:
  - path: data/train.jsonl              # local file/dir or HF dataset repo
    type: chat_template
    chat_template: tokenizer_default    # use the model's built-in template; or chatml
    field_messages: messages
    message_field_role: role
    message_field_content: content
    roles_to_train: ["assistant"]
    train_on_eos: turn
train_on_inputs: false
val_set_size: 0.05
dataset_prepared_path: last_run_prepared

# --- sequence / packing ---
sequence_len: 4096
sample_packing: true                    # needs flash_attention
pad_to_sequence_len: true

# --- LoRA ---
lora_r: 32
lora_alpha: 64
lora_dropout: 0.05
lora_target_linear: true

# --- training ---
micro_batch_size: 2
gradient_accumulation_steps: 8
num_epochs: 3
learning_rate: 2e-4                     # LoRA ≈ 10× full FT
lr_scheduler: cosine
warmup_ratio: 0.05
optimizer: adamw_torch_fused
weight_decay: 0.01
max_grad_norm: 1.0

# --- precision / memory ---
bf16: auto
tf32: auto
flash_attention: true
gradient_checkpointing: true

# --- logging / checkpoints ---
logging_steps: 10
save_steps: 200
save_total_limit: 3
eval_steps: 100
output_dir: ./outputs/lora-out

# --- Hub (optional; needs HF_TOKEN) ---
# hub_model_id: your-username/your-model
# hub_strategy: end                       # checkpoint|all|end|every_save
# save_safetensors: true
# hf_use_auth_token: true
```

Run:

```bash
axolotl fetch examples            # grab reference configs once
axolotl preprocess config.yml    # validate + cache data FIRST
axolotl train config.yml
# resume if interrupted: axolotl train config.yml --resume-from-checkpoint outputs/lora-out/checkpoint-XXX
```

Switch method by changing a few keys:

```yaml
# DPO  (dataset needs chosen/rejected; or a chat dataset of chosen vs rejected turns)
rl: dpo
trl:
  beta: 0.1
learning_rate: 5e-6              # LoRA DPO
datasets:
  - path: dpo_data.jsonl
    type: chat_template
    field_messages: messages     # or use chosen/rejected fields

# ORPO  (single pass SFT+preference, no ref model — lowest memory)
rl: orpo
trl:
  beta: 0.1                     # λ in the paper
learning_rate: 1e-5             # LoRA ORPO

# GRPO  (verifiable rewards; needs vLLM or in-process generation)
rl: grpo
trl:
  beta: 0.0                     # KL off by default (R1-Zero/DAPO practice)
  num_generations: 8
  max_completion_length: 2048
  use_vllm: false               # colocate/server for multi-GPU; in-process for single
  reward_funcs: [./reward.py]   # importable; or built-in math_verify
learning_rate: 1e-5             # LoRA GRPO
```

Merging LoRA into the base (for a standalone merged model):

```bash
axolotl merge-lora config.yml --lora-model-dir=./outputs/lora-out
# merged model lands in {output_dir}/merged
axolotl inference config.yml --lora-model-dir=./outputs/lora-out   # quick test before merging
```

#### Path B: TRL (programmatic, modern HF pattern)

The recommended pattern (per Hugging Face) is a small `run_sft.py` driven by a YAML via `TrlParser` — one script handles full/LoRA/QLoRA. Minimal equivalent:

```python
# run_sft.py
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer
from peft import LoraConfig

peft_config = LoraConfig(
    r=32, lora_alpha=64, lora_dropout=0.05, bias="none",
    task_type="CAUSAL_LM", target_modules="all-linear",
)

cfg = SFTConfig(
    output_dir="./outputs/sft-out",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=8,
    learning_rate=2e-4,                 # LoRA ≈ 10× full FT
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    logging_steps=10,
    save_steps=200, save_total_limit=3,
    eval_strategy="steps", eval_steps=100,
    bf16=True, tf32=True,
    gradient_checkpointing=True,
    packing=True,                      # needs FA2+
    assistant_only_loss=True,         # train on assistant turns only
    eos_token="<|im_end|>",            # align with chat template for Qwen; omit if unnecessary
    # push_to_hub=True, hub_model_id="your-username/your-model",
    report_to="tensorboard",
    seed=42,
)

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-1.5B",         # HF Hub id or loaded model
    args=cfg,
    train_dataset=load_dataset("json", data_files="data/train.jsonl", split="train"),
    eval_dataset=None,                 # or pass a held-out split
    peft_config=peft_config,           # omit for full FT; pass for LoRA/QLoRA
)

trainer.train()
trainer.save_model("./outputs/sft-out/final")          # saves adapter + tokenizer (PEFT)
# trainer.push_to_hub()                                # if push_to_hub=True set above
```

Run single-GPU: `python run_sft.py`
Run multi-GPU with FSDP: `accelerate launch --config_file fsdp_config.yaml run_sft.py`
Run with DeepSpeed: `accelerate launch --config_file ds_config.yaml run_sft.py` (or `--deepspeed ds_zero3.json`)

For QLoRA add at model load:

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B", quantization_config=bnb)
# then pass `model=model` to SFTTrainer instead of the string id
```

For DPO/ORPO/GRPO swap `SFTTrainer`→`DPOTrainer`/`ORPOTrainer`/`GRPOTrainer`, `SFTConfig`→`DPOConfig`/`ORPOConfig`/`GRPOConfig`, and use the matching LR from the table above. DPO/ORPO/GRPO configs default to `gradient_checkpointing=True`, `bf16=True`, `logging_steps=10`, `learning_rate=1e-6`.

### Phase 3 — Save to disk

- **Axolotl** auto-saves to `output_dir` (checkpoints) and the final adapter at `output_dir/`. Merged model at `{output_dir}/merged` after `merge-lora`.
- **TRL**: `trainer.save_model(path)` saves adapter + tokenizer for PEFT runs, full weights for full FT. `save_safetensors=True` (default) — safetensors is mandatory on the Hub.
- Verify the saved dir contains `adapter_config.json` + `adapter_model.safetensors` (PEFT) or `model.safetensors`(+ `config.json`, `tokenizer*`).
- Keep `save_total_limit` low (3) to avoid filling disk.

### Phase 4 — Upload to Hugging Face Hub

**Authenticate first** (`HF_TOKEN` env or `huggingface-cli login`). Two strategies:

1. **Adapter only (recommended for production):** decouples your weights from the base; if the base is patched, you can re-apply the adapter. Document the base model + revision in the card.
2. **Merged model:** standalone, faster to load, ~base-model-sized. Use `merge_and_unload()` (TRL) or `axolotl merge-lora` first.

Axolotl — push during training (set in config):

```yaml
hub_model_id: your-username/your-model
hub_strategy: end              # checkpoint | all | end | every_save
save_safetensors: true
hf_use_auth_token: true
```

TRL — push from the trainer or directly:

```python
trainer.push_to_hub()                                   # if push_to_hub=True in args
# or after training:
model.push_to_hub("your-username/your-model", token=token, safe_serialization=True)
tokenizer.push_to_hub("your-username/your-model", token=token)   # ALWAYS push tokenizer too
```

Upload a local folder (works for merged or adapter):

```bash
huggingface-cli upload your-username/your-model ./outputs/merged .  # . = repo root
```

**MUST do when uploading:**
- **Push the tokenizer alongside the model** — missing/wrong tokenizer → chat-template mismatch → garbled outputs.
- **Add a `README.md` model card** with: base model + revision, method (SFT/DPO/...), LoRA r/alpha, dataset, LR, epochs, usage snippet, limitations. `push_to_hub()` auto-generates hyperparameter sections; enrich it.
- **Pin the base model revision** for adapters so they don't silently load stale base weights later.
- **Test loading from CPU** after push to catch device-dependent pickling bugs:
  ```python
  from transformers import AutoModelForCausalLM, AutoTokenizer
  m = AutoModelForCausalLM.from_pretrained("your-username/your-model")
  t = AutoTokenizer.from_pretrained("your-username/your-model")
  print(t.apply_chat_template([{"role":"user","content":"hi"}], tokenize=False))
  ```
- For PEFT, `push_to_hub()` on a `PeftModel` uploads the adapter; verify `adapter_config.json` landed in the repo.

---

## Constraints

### MUST DO
- Run preprocessing / a one-sample sanity check **before** a full run — catch format/template errors early.
- Match the chat template and EOS token to the base model.
- Use the **method-correct learning rate** (see table). LoRA ≠ full FT LRs.
- Enable `flash_attention` + `sample_packing`/`packing` on Ampere+ (huge throughput). Disable both on older GPUs (packing needs FA2+).
- Pick **one** distributed strategy (FSDP2 for LoRA, DeepSpeed ZeRO-3 for big full FT). Never both.
- Train on assistant turns only (`roles_to_train`/`assistant_only_loss`/`completion_only_loss`).
- Push tokenizer + model + model card; pin base model revision for adapters.
- Set `seed`; save the config next to the artifact for reproducibility.

### MUST NOT DO
- Don't use `fp16` if the base model is `bf16` — dtype mismatch degrades results.
- Don't mix DeepSpeed and FSDP in one run.
- Don't enable `sample_packing` without Flash Attention 2+ (cross-sample contamination).
- Don't reuse a full-FT LR (2e-5) for LoRA (use 2e-4) or vice versa.
- Don't push a merged model and expect PEFT metadata to remain — `merge_and_unload()` strips it. Push the adapter **before** merging if you need both.
- Don't hardcode `HF_TOKEN` in scripts/configs or commit it to git.
- Don't skip the model card or the tokenizer on upload.
- Don't assume base-model immutability when shipping an adapter.

## Common mistakes & fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| CUDA OOM | batch/seq too big | `micro_batch_size: 1`; enable `gradient_checkpointing`; QLoRA; halve `sequence_len` |
| Loss won't decrease | wrong LR for method, or template mismatch | use method's LoRA LR (2e-4 for SFT-LoRA); verify chat template + `roles_to_train` |
| Loss explodes (>>2× start) | LR too high / instability | lower LR; add warmup; `loss_watchdog_threshold` (axolotl) to abort early |
| Model outputs garbage after load | tokenizer/chat template not pushed, or EOS misaligned | push tokenizer; set `eos_token` to match template; test `apply_chat_template` |
| Packing cross-contamination | packing without Flash Attention | turn on `flash_attention` or off `sample_packing` |
| Adapter "dangling"/stale base | pushed adapter without pinning base revision | document/pin base `revision` in model card; or ship merged model |
| Slow GRPO generation | generation dominates | tune `num_generations`, `max_completion_length`; try vLLM colocate or continuous batching (`use_transformers_continuous_batching=True`, `max_memory_percent` 0.3–0.4) |
| Qwen/gated model 403 | license not accepted / no token | `HF_TOKEN` set + accept license on Hub page |

## Verification checklist

- [ ] Data printed: one raw + one tokenized example, loss mask on assistant only
- [ ] Preprocessing ran clean (`axolotl preprocess` / TRL sample check)
- [ ] LR matches method (LoRA = 10× full FT)
- [ ] Chat template + EOS aligned to base model
- [ ] `flash_attention` + `packing` consistent (both on, or both off on old GPUs)
- [ ] Distributed strategy is exactly one (FSDP2 or DeepSpeed, not both)
- [ ] `output_dir` has `adapter_config.json`+`adapter_model.safetensors` (PEFT) or `model.safetensors`
- [ ] Pushed model **and** tokenizer **and** model card
- [ ] Base model revision pinned in card (for adapters)
- [ ] Load test from CPU succeeds; `apply_chat_template` produces sane text

## Quick reference

| Task | Axolotl | TRL |
|---|---|---|
| Validate data | `axolotl preprocess config.yml` | print `tokenize` one sample |
| Train | `axolotl train config.yml` | `python run_sft.py` / `accelerate launch ...` |
| Resume | `--resume-from-checkpoint <dir>` | `trainer.train(resume_from_checkpoint=...)` |
| Merge LoRA | `axolotl merge-lora config.yml --lora-model-dir=...` | `model.merge_and_unload()` |
| Test inference | `axolotl inference config.yml` | `model.generate(...)` |
| Push to Hub | `hub_model_id` + `hub_strategy` in YAML | `trainer.push_to_hub()` / `model.push_to_hub()` |
| Config schema | `axolotl config-schema` / `axolotl config-schema --field adapter` | `TrlParser` YAML |

## References
- Axolotl docs: https://docs.axolotl.ai/  · Config reference: https://docs.axolotl.ai/docs/config-reference.html  · GitHub: https://github.com/axolotl-ai-cloud/axolotl
- TRL SFT Trainer: https://huggingface.co/docs/trl/sft_trainer  · PEFT integration: https://huggingface.co/docs/trl/peft_integration  · DPO/GRPO trainers under /docs/trl/
- Fine-tune in 2025 (Philipp Schmid): https://www.philschmid.de/fine-tune-llms-in-2025
- Model sharing / upload: https://huggingface.co/docs/transformers/main/model_sharing  · https://huggingface.co/docs/hub/models-uploading
