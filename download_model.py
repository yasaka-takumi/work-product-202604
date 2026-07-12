# download_model.py
import os

from dotenv import load_dotenv
from huggingface_hub import hf_hub_download

load_dotenv()

hf_hub_download(
    repo_id="ta-ku-mi/elyza-finetuned-gguf",
    filename="Llama-3-ELYZA-JP-8B.Q4_K_M.gguf",
    local_dir="./elyza-finetuned",
    token=os.getenv("HUGGINGFACE_TOKEN")
)

print("ダウンロード完了！")