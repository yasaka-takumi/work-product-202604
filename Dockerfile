FROM python:3.11-slim

# ローカルのタイムゾーン設定など（必要に応じて）
ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /workspace

# Pythonのパッケージインストールをキャッシュ効率良く行うため、先にrequirements.txtをコピー
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ソースコードやDBなどの関連ファイルをコンテナ内にコピー
COPY . .

# FastAPIのポートを公開
EXPOSE 8000

# コンテナ起動時にFastAPIサーバーを起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
