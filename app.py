from flask import Flask, request, render_template,redirect, url_for, Response
from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re
import random

SCORE_FILE = "test_score.json"

def load_score():
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # ファイルが空または壊れている場合、初期スコアにする
            return {"correct": 0, "total": 0}
    return {"correct": 0, "total": 0}

def save_score(correct_increment):
    score = load_score()
    score["correct"] += correct_increment
    score["total"] += 1
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(score, f, ensure_ascii=False, indent=2)
    return score

HISTORY_FILE = "vocab_history.json"
def save_history(entry):
    
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    else:
        history = []

    history.insert(0, entry)  # 新しいエントリを先頭に追加
    history = history[:5000]  

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2) 

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                return history[:10000]
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
    if not text.strip():
        return []
    
    prompt = f"""
次の英文から重要な英単語を5つ抽出し、それぞれの意味(日本語)と例文(英語)を出力してください


形式：
単語 | 意味 | 例文

英文:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
    except Exception as e:
        print("OpenAI API error:", e)
        return []

    result_text = response.choices[0].message.content.strip()

    # パース処理(後で分割するため)
    vocab_list = []
    for line in result_text.split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 3:
                vocab_list.append({
                    "word": re.sub(r"^\d+\.\s*", "", parts[0]),
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
        user_input = request.form["english_text"].strip()
    
        if user_input:
            vocab_list = generate_vocab(user_input)
            
    return render_template("index.html", vocab_list=vocab_list, user_input=user_input)

@app.route("/download_csv")
def download_csv():
    history = load_history()
    if not history:
        return "履歴がありません", 404
    
    seen_words = set()
    unique_vocab = []
    
    for record in history:
        for item in record["vocab"]:
            word = item["word"]
            if word not in seen_words:
                seen_words.add(word)
                unique_vocab.append(item)

    csv_content = "単語,意味,例文\n"
    for item in unique_vocab:
        word = item['word'].replace(',', ', ')
        meaning = item['meaning'].replace(',', ', ')
        example = item['example'].replace(',', ', ')
        csv_content += f"{word},{meaning},{example}\n"                          

    bom_encoded = csv_content.encode("utf-8-sig")
    
    return Response(
        bom_encoded,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=vocab_unique.csv"}
    )

@app.route("/clear_history", methods=["POST"])
def clear_history():
    with open("vocab_history.json", "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
    return redirect(url_for("index", cleared="1"))

import random  # すでに import されています

@app.route("/test", methods=["GET", "POST"])
def test():
    history = load_history()
    all_vocab = [item for record in history for item in record["vocab"]]

    if not all_vocab:
        return render_template("test.html", question=None)

    if request.method == "POST":
        answer = request.form["answer"]
        correct_word = request.form["correct_word"]
        correct_meaning = request.form["correct_meaning"]
        is_correct = answer.strip() == correct_meaning.strip()
        
        score = save_score(1 if is_correct else 0)
        
        # ✅ 元の問題を再構築（再度ランダムにしない）
        question = {
            "word": correct_word,
            "meaning": correct_meaning
        }

        other_meanings = list({v["meaning"] for v in all_vocab if v["word"] != correct_word})
        distractors = random.sample(other_meanings, min(3, len(other_meanings)))
        options = [correct_meaning] + distractors
        random.shuffle(options)

        question["options"] = options

        result = {
            "your_answer": answer,
            "correct_answer": correct_meaning,
            "correct": is_correct
        }

        return render_template("test.html", question=question, result=result, score=score)

    else:
        question = random.choice(all_vocab)
        other_meanings = list({v["meaning"] for v in all_vocab if v["word"] != question["word"]})
        distractors = random.sample(other_meanings, min(3, len(other_meanings)))
        options = [question["meaning"]] + distractors
        random.shuffle(options)
        question["options"] = options
        score = load_score()

        return render_template("test.html", question=question, score=score)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)