from flask import Flask, request, render_template
from openai import OpenAI
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# ✅ 環境変数からAPIキーを取得
openai_api_key = os.getenv("OPENAI_API_KEY")

#  読み込みエラー対策を追加
if openai_api_key is None:
    raise ValueError("❌ OPENAI_API_KEY  が .env  に設定されていません")

# ✅ クライアントを作成
client = OpenAI(api_key=openai_api_key)

app = Flask(__name__)

# 単語帳を生成する関数 (GPT API)
def generate_vocab(text):
    prompt = f"""
次の英文から重要な英単語を5つ抽出し、それぞれの意味(日本語)と例文(英語)を出力してください


形式：
単語 | 意味 | 例文

英文:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = response.choices[0].message.content.strip()

    with open("vocab_log.txt", "w", encoding="utf-8") as f:
        f.write("ユーザー入力:\n")
        f.write(text + "\n\n")
        f.write("生成結果:\n")
        f.write(result_text + "\n")

    # パース処理(後で分割するため)
    vocab_list = []
    for line in result_text.split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                vocab_list.append({
                    "word": parts[0],
                    "meaning": parts[1],
                    "example": parts[2]
                })
    
    return vocab_list

@app.route("/", methods=["GET", "POST"])
def index():
    vocab_list = []
    user_input = ""
    if request.method == "POST":
        user_input = request.form["english_text"]
        vocab_list = generate_vocab(user_input)
    return render_template("index.html", vocab_list=vocab_list, user_input=user_input)

if __name__ == "__main__":
    app.run(debug=True)
