import os
import sys
from huggingface_hub import login, hf_hub_download

token = os.getenv('HF_TOKEN')
if not token:
    sys.exit('❌ No HF_TOKEN provided!')

login(token=token)

model_dir = './models'
os.makedirs(model_dir, exist_ok=True)

model_path = hf_hub_download(
    repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF',
    filename='mistral-7b-instruct-v0.2.Q5_K_M.gguf',
    local_dir=model_dir,
    token=token,
    local_dir_use_symlinks=False
)

print(f'✅ Model downloaded and saved at {model_path}')
