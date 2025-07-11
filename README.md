# 📘 Vocab AI Generator

英語の文章から重要な単語を抽出し、日本語の意味と英文例を表示するFlaskアプリです。OpenAI APIを使用しています。

## 🔧 機能
- 英文から重要単語を5つ抽出
- 各単語の意味（日本語）と例文（英語）を表示
- 結果をファイルに保存

## 🚀 使用方法

### 1. クローン & セットアップ
```bash
git clone https://github.com/Shun0115/vocab-ai-generator.git
cd vocab-ai-generator
pip install -r requirements.txt
2. .env ファイルを作成
OPENAI_API_KEY=your-api-key-here
3. アプリ起動
python app.py
ブラウザで http://localhost:5000 にアクセスしてください。
🧪 使用技術
Python 3.x
Flask
OpenAI API
dotenv
📄 ライセンス
MIT License