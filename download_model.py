# download_model.py
from huggingface_hub import hf_hub_download

hf_hub_download(
    repo_id="ta-ku-mi/elyza-finetuned-gguf",
    filename="Llama-3-ELYZA-JP-8B.Q4_K_M.gguf",
    local_dir="./elyza-finetuned",
    token="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"
)

print("ダウンロード完了！")