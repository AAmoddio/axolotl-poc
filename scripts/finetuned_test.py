"""Fine-tuned evaluation — loads the base model + the QLoRA adapter and runs the same questions.

Run from the repo root, AFTER training has produced the adapter:
    python scripts/finetuned_test.py

Writes finetuned_outputs.txt in the CWD.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model = "Qwen/Qwen2.5-7B-Instruct"
adapter_path = "./outputs/qwen7b-resetdata-qlora"

questions = [
    "What services does ResetData currently provide for AI workloads?",
    "How could ResetData position a future FTaaS offering?",
    "What is the difference between ResetData GPUaaS and LLMaaS?",
    "When should ResetData recommend RAG instead of fine-tuning to a customer?",
    "How could ResetData integrate fine-tuned models into its inference platform?",
    "What would a customer need to provide before starting a fine-tuning job with ResetData?",
    "Why might a customer choose ResetData instead of managing their own GPU infrastructure?",
    "How does sovereign AI relate to ResetData's platform strategy?",
    "What operational challenges would ResetData face when offering FTaaS?",
    "What would an end-to-end ResetData fine-tuning workflow look like?",
]

tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)

model = AutoModelForCausalLM.from_pretrained(
    base_model,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)

model = PeftModel.from_pretrained(model, adapter_path)
model.eval()

with open("finetuned_outputs.txt", "w", encoding="utf-8") as f:
    for i, q in enumerate(questions, 1):
        messages = [
            {"role": "system", "content": "You are a helpful enterprise AI platform assistant."},
            {"role": "user", "content": q},
        ]

        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=300,
                temperature=0.2,
                do_sample=True,
                top_p=0.9,
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True,
        )

        block = f"\n\n### Question {i}\n{q}\n\n### Fine-tuned Answer\n{response.strip()}\n"
        print(block)
        f.write(block)

print("\nSaved fine-tuned outputs to finetuned_outputs.txt")
