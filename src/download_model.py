import os
from huggingface_hub import login, hf_hub_download

token = os.getenv("HF_TOKEN")
if not token:
    raise ValueError("❌ HF_TOKEN not provided during build.")

login(token=token)

os.makedirs("./models", exist_ok=True)

model_path = hf_hub_download(
    repo_id="TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    filename="mistral-7b-instruct-v0.2.Q5_K_M.gguf",
    local_dir="./models",
    token=token,
    local_dir_use_symlinks=False
)

print(f"✅ Model downloaded at {model_path}")
