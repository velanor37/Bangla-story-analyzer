from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY")

HTML = """<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>পাঠ-পরিচিতি বিশ্লেষক (Cerebras)</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f2ede4; font-family: 'Segoe UI', 'Kalpurush', 'Noto Sans Bengali', Georgia, serif; color: #2c1f12; }
        .container { max-width: 960px; margin: 0 auto; padding: 2rem; }
        header { text-align: center; margin-bottom: 2rem; }
        h1 { font-size: 2.2rem; color: #8b3c28; margin-bottom: 0.5rem; }
        .grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem; }
        @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
        .card { background: #faf7f2; border: 1px solid #ddd3c4; border-radius: 1rem; padding: 1.5rem; }
        input, button { width: 100%; padding: 0.75rem; margin: 0.5rem 0; border: 1px solid #ddd3c4; border-radius: 0.5rem; font-size: 1rem; }
        button { background: #8b3c28; color: white; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #a04830; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .result-empty { text-align: center; padding: 3rem; border: 2px dashed #ddd3c4; border-radius: 1rem; color: #9b8070; }
        .loading { text-align: center; padding: 2rem; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #8b3c28; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
        @keyframes spin { 0% { transform: rotate(0); } 100% { transform: rotate(360deg); } }
        .result-card { background: #faf7f2; border: 1px solid #ddd3c4; border-radius: 1rem; overflow: hidden; }
        .result-header { background: #e5d9cc; padding: 1rem; font-weight: bold; }
        .result-body { padding: 1.5rem; }
        .prose { font-family: 'Noto Sans Bengali', Georgia, serif; line-height: 1.6; }
        .prose h2 { color: #8b3c28; margin: 1rem 0 0.5rem; }
        .error-msg { background: #ffe0e0; color: #b00020; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; display: none; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>📚 পাঠ-পরিচিতি বিশ্লেষক (Cerebras AI)</h1>
        <p>দারুণ গতিতে গল্প ও উপন্যাসের গভীর বিশ্লেষণ</p>
    </header>
    <div class="grid">
        <div class="card">
            <h3>📖 গল্পের তথ্য দিন</h3>
            <label>গল্পের নাম</label>
            <input type="text" id="story" placeholder="যেমন: পোস্টমাস্টার">
            <label>লেখকের নাম</label>
            <input type="text" id="writer" placeholder="যেমন: রবীন্দ্রনাথ ঠাকুর">
            <button id="btn" onclick="generate()">✨ পাঠ-পরিচিতি তৈরি করুন</button>
            <div id="error" class="error-msg"></div>
        </div>
        <div id="output">
            <div class="result-empty">🏛️ বিশ্লেষণ দেখতে ফর্ম পূরণ করুন</div>
        </div>
    </div>
</div>
<script>
    async function generate() {
        const story = document.getElementById('story').value.trim();
        const writer = document.getElementById('writer').value.trim();
        const btn = document.getElementById('btn');
        const errDiv = document.getElementById('error');
        const output = document.getElementById('output');
        errDiv.style.display = 'none';
        if (!story || !writer) {
            errDiv.innerText = 'গল্পের নাম ও লেখকের নাম লিখুন';
            errDiv.style.display = 'block';
            return;
        }
        btn.disabled = true;
        btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px"></div> বিশ্লেষণ চলছে...';
        output.innerHTML = '<div class="loading"><div class="spinner"></div><p>গভীর বিশ্লেষণ তৈরি হচ্ছে...</p><small>এটি কয়েক সেকেন্ড সময় নিতে পারে</small></div>';
        try {
            const res = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ story, writer })
            });
            const data = await res.json();
            if (data.error) {
                output.innerHTML = '<div class="result-empty">⚠️ ' + data.error + '</div>';
            } else {
                output.innerHTML = '<div class="result-card"><div class="result-header">বিশ্লেষণ ফলাফল</div><div class="result-body"><div class="prose">' + marked.parse(data.result) + '</div></div></div>';
            }
        } catch(e) {
            output.innerHTML = '<div class="result-empty">⚠️ সংযোগ সমস্যা হয়েছে। আবার চেষ্টা করুন।</div>';
        }
        btn.disabled = false;
        btn.innerHTML = '✨ পাঠ-পরিচিতি তৈরি করুন';
    }
</script>
</body>
</html>"""

def call_cerebras(story_name, writer_name):
    """Cerebras API ব্যবহার করে বিশ্লেষণ তৈরি করে"""
    if not CEREBRAS_API_KEY:
        return None, "Cerebras API Key সেট নেই। Render-এ 'CEREBRAS_API_KEY' ভেরিয়েবল যোগ করুন।"

    prompt = f"""তুমি একজন সাহিত্য বিশেষজ্ঞ ও বাংলা গল্পের বিশ্লেষক। নিচের গল্পটির একটি পেশাদার, বিস্তারিত ও আকর্ষণীয় 'পাঠ-পরিচিতি' বাংলায় রচনা করো। নিচের কাঠামো অনুসরণ করবে:

# {story_name} - {writer_name}

## 📖 রচয়িতা পরিচিতি
- লেখকের জন্ম ও মৃত্যু সাল, পৈতৃক বা কর্মস্থল।
- তাঁর ২-৩টি উল্লেখযোগ্য সাহিত্যকর্ম।
- তাঁর লেখার মূল বৈশিষ্ট্য ও বাংলা সাহিত্যে অবদান।

## 👥 প্রধান চরিত্রসমূহ
- বুলেট পয়েন্টে নাম ও সংক্ষিপ্ত বিবরণ।

## 📜 গল্পের পটভূমি ও কাহিনি সংক্ষেপ
### প্রেক্ষাপট
### কাহিনির সূত্রপাত
### ঘটনাপ্রবাহ ও সংগ্রাম
### পরিণতি (স্পয়লার না দিয়ে)

## 💡 মূল বক্তব্য ও শিক্ষা
১.
২.
৩.

## ✨ প্রাসঙ্গিকতা ও গুরুত্ব
- কেন এখনও পড়ার মতো?

## 📝 পাঠপরামর্শ (টিপস)
- ২-৩টি টিপস

গল্পের নাম: {story_name}
লেখকের নাম: {writer_name}"""

    # সঠিক এন্ডপয়েন্ট এবং মডেল (ডট ছাড়া)
    url = "https://inference.cerebras.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CEREBRAS_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3.3-70b",   # গুরুত্বপূর্ণ: "llama-3.3-70b" না, বরং "llama3.3-70b"
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'], None
    except Exception as e:
        return None, f"Cerebras API ত্রুটি: {str(e)}"

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    story = data.get('story', '').strip()
    writer = data.get('writer', '').strip()
    if not story or not writer:
        return jsonify({"error": "গল্পের নাম ও লেখকের নাম লিখুন"}), 400
    result, error = call_cerebras(story, writer)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
