# docker 環境構築

### clone

適当な場所でクローンして、ディレクトリに移動する<br>
git clone git@github.com:yasaka-takumi/work-product-202604.git<br>

cd work-product-202604

### model pull (追加)
cd elyza-finetuned<br>

Hugging faceから<br>
ta-ku-mi/elyza-finetuned-gguf<br>
をdownload

### build docker image

コンテナを起動する<br>
docker compose up -d --build<br>
※ 初回だけかなり待つと思われる（体感20分～30分）<br>

### model pull

ollamaから対象のmodelを２つpullする<br>

- model : qwen2.5:3b
- embedding model : mxbai-embed-large<br>

docker compose exec ollama ollama pull qwen2.5:3b<br>
docker compose exec ollama ollama pull mxbai-embed-large<br>
- modelはollama_dataボリュームに保存されるため、上記の操作は初回のみ
- docker compose exec ollama ollama list -> 上記2つのモデルが出力されれば成功

### 4/24 変更
docker compose exec ollama ollama create cat-concierge -f /root/models/Modelfile<br>

### add products

1. docs（Swagger UI）を開く<br>
ブラウザで<br>
http://localhost:8000/docs<br>
にアクセスする<br>

2. work-product-202604/sql/products.json<br>
を開いて、中身を全選択してコピーする

3. Post /admin/products -> Try it out を選択する<br>
Request bodyに2の操作でcopyした内容で上書きして、Executeを実行する
- 201 Createdが返ってくれば成功です

### chat
docsの<br>
/chatのpostからrequestとresponseを確認してみてください<br>

また、streaming機能についてはターミナル(WSL2)から確認をお願いします<br>

- streaming demo code (terminal)<br>
curl -s -N -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "test",
       "session_id": "test",
       "message": "こんにちは！簡単な自己紹介をして",
       "external_data": {}
     }'
