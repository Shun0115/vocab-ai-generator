from flask import Flask, request, render_template,redirect, url_for, Response
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

HISTORY_FILE = "vocab_history.json"
def save_history(entry):
    
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    else:
        history = []

    history.insert(0, entry)  # 新しいエントリを先頭に追加
    history = history[:10]  # 最新の10件のみ保持

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2) 

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                return history[:10]  # 最新の10件のみ返す
        except json.JSONDecodeError:
            return []
    return []

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

    # パース処理(後で分割するため)
    vocab_list = []
    for line in result_text.split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                vocab_list.append({
                    "word": parts[0],
                    "meaning": parts[1].replace("意味:", "").strip(),
                    "example": parts[2].replace("例文:", "").strip()
                })

    save_history({
        "input": text,
        "vocab": vocab_list
    })

    return vocab_list

@app.route("/", methods=["GET", "POST"])
def index():
    vocab_list = []
    user_input = ""
    if request.method == "POST":
        user_input = request.form["english_text"]
        vocab_list = generate_vocab(user_input)
    history = load_history()
    return render_template("index.html", vocab_list=vocab_list, user_input=user_input, history=history)

@app.route("/delete/<int:index>", methods=["POST"])
def delete_entry(index):
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        if 0 <= index < len(history):
            del history[index]
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
    return redirect(url_for("index"))

@app.route("/delete_all", methods=["POST"])
def delete_all():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    return redirect(url_for("index"))

@app.route("/download_csv")
def download_csv():
    history = load_history()
    if not history:
        return "履歴がありません", 404

    vocab_list = history[0]["vocab"]

    csv_content = "単語,意味,例文\n"
    for item in vocab_list:
        csv_content += f"{item['word']},{item['meaning']},{item['example']}\n"

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=vocab.csv"}
    )

if __name__ == "__main__":
    app.run(debug=True)


