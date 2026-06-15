from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

# ⚙️ ক্লাউডে দিলে এনভায়রনমেন্ট ভেরিয়েবল হিসেবে সেট করবেন
# লোকাল টেস্টের জন্য নিচের লাইনটি আনকমেন্ট করে API কী বসিয়ে দিন:
# GROQ_API_KEY = "gsk_xxxxxxxxxxxx"
# অথবা সিস্টেম এনভায়রনমেন্ট ভেরিয়েবল থেকে নিবে (প্রডাকশনে ভালো)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

HTML = """<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>পাঠ-পরিচিতি বিশ্লেষক</title>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Georgia, 'Kalpurush', serif;
      background: #f2ede4;
      color: #2c1f12;
      min-height: 100vh;
    }
    .container {
      max-width: 960px;
      margin: 0 auto;
      padding: 48px 20px;
    }
    header {
      text-align: center;
      margin-bottom: 48px;
    }
    header .icon {
      width: 64px; height: 64px;
      background: rgba(139,60,40,0.12);
      border-radius: 16px;
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 20px;
      font-size: 28px;
    }
    h1 {
      font-size: 2.6rem;
      font-weight: bold;
      color: #2c1f12;
      margin-bottom: 12px;
    }
    header p {
      font-size: 1.1rem;
      color: #7a6352;
      max-width: 560px;
      margin: 0 auto;
    }
    .grid {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 32px;
      align-items: start;
    }
    @media (max-width: 700px) {
      .grid { grid-template-columns: 1fr; }
      h1 { font-size: 1.8rem; }
    }
    .card {
      background: #faf7f2;
      border: 1px solid #ddd3c4;
      border-radius: 12px;
      padding: 28px;
      box-shadow: 0 4px 20px rgba(139,60,40,0.06);
    }
    .card-title {
      font-size: 1.3rem;
      font-weight: bold;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .card-desc {
      font-size: 0.88rem;
      color: #7a6352;
      margin-bottom: 24px;
      font-family: sans-serif;
    }
    label {
      display: block;
      font-family: sans-serif;
      font-size: 0.9rem;
      font-weight: 600;
      margin-bottom: 6px;
      color: #2c1f12;
    }
    .input-wrap {
      position: relative;
      margin-bottom: 20px;
    }
    .input-wrap span {
      position: absolute;
      left: 12px; top: 50%;
      transform: translateY(-50%);
      font-size: 15px;
      color: #9b8070;
    }
    input[type="text"] {
      width: 100%;
      padding: 10px 12px 10px 36px;
      border: 1px solid #ddd3c4;
      border-radius: 8px;
      font-family: Georgia, serif;
      font-size: 0.95rem;
      background: #f9f6f0;
      color: #2c1f12;
      outline: none;
      transition: border 0.2s, box-shadow 0.2s;
    }
    input[type="text"]:focus {
      border-color: #8b3c28;
      box-shadow: 0 0 0 3px rgba(139,60,40,0.12);
    }
    button {
      width: 100%;
      padding: 13px;
      background: #8b3c28;
      color: #faf7f2;
      border: none;
      border-radius: 8px;
      font-family: Georgia, serif;
      font-size: 1.05rem;
      font-weight: bold;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: background 0.2s, transform 0.1s;
    }
    button:hover { background: #a04830; }
    button:active { transform: scale(0.98); }
    button:disabled { background: #c4a090; cursor: not-allowed; }
    .result-empty {
      min-height: 420px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      border: 2px dashed #ddd3c4;
      border-radius: 12px;
      background: rgba(139,60,40,0.02);
      color: #9b8070;
      gap: 12px;
    }
    .result-empty .big-icon { font-size: 48px; opacity: 0.3; }
    .result-empty p { font-size: 1rem; }
    .loading {
      min-height: 420px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
      color: #7a6352;
    }
    .spinner {
      width: 48px; height: 48px;
      border: 4px solid rgba(139,60,40,0.15);
      border-top-color: #8b3c28;
      border-radius: 50%;
      animation: spin 0.9s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .loading p { font-size: 1.1rem; color: #2c1f12; }
    .loading small { font-family: sans-serif; font-size: 0.82rem; color: #9b8070; }
    .result-card {
      background: #faf7f2;
      border: 1px solid #ddd3c4;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 6px 30px rgba(139,60,40,0.08);
      animation: fadeUp 0.5s ease;
    }
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(12px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .result-header {
      background: rgba(139,60,40,0.06);
      border-bottom: 1px solid #ddd3c4;
      padding: 18px 28px;
      font-size: 1.1rem;
      font-weight: bold;
      color: #8b3c28;
    }
    .result-body {
      padding: 32px;
    }
    .prose h1 { font-size: 1.7rem; color: #8b3c28; margin-bottom: 6px; margin-top: 0; }
    .prose h2 { font-size: 1.25rem; color: #8b3c28; margin-top: 28px; margin-bottom: 8px; border-bottom: 1px solid #e5d9cc; padding-bottom: 4px; }
    .prose h3 { font-size: 1.05rem; color: #5c3820; margin-top: 16px; margin-bottom: 4px; }
    .prose p { line-height: 1.8; margin-bottom: 10px; color: #2c1f12; }
    .prose ul, .prose ol { padding-left: 22px; margin-bottom: 10px; }
    .prose li { margin-bottom: 4px; line-height: 1.7; }
    .prose strong { font-weight: bold; }
    .error-msg {
      background: #fde8e8;
      border: 1px solid #f5c6c6;
      color: #8b1a1a;
      border-radius: 8px;
      padding: 16px 20px;
      font-family: sans-serif;
      font-size: 0.9rem;
      margin-top: 12px;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="icon">📚</div>
      <h1>পাঠ-পরিচিতি বিশ্লেষক</h1>
      <p>আপনার প্রিয় বাংলা গল্প ও উপন্যাসের একটি গভীর, কৃত্রিম বুদ্ধিমত্তা-চালিত সাহিত্যিক বিশ্লেষণ।</p>
    </header>

    <div class="grid">
      <div class="card">
        <div class="card-title">📖 গল্পের তথ্য</div>
        <div class="card-desc">যে গল্পের পরিচিতি জানতে চান তার বিস্তারিত লিখুন।</div>
        <label for="story">গল্পের নাম</label>
        <div class="input-wrap">
          <span>📘</span>
          <input type="text" id="story" placeholder="যেমন: পোস্টমাস্টার" />
        </div>
        <label for="writer">লেখকের নাম</label>
        <div class="input-wrap">
          <span>✒️</span>
          <input type="text" id="writer" placeholder="যেমন: রবীন্দ্রনাথ ঠাকুর" />
        </div>
        <button id="btn" onclick="generate()">
          ✨ পাঠ-পরিচিতি তৈরি করুন
        </button>
        <div id="error" class="error-msg" style="display:none"></div>
      </div>

      <div id="output">
        <div class="result-empty">
          <div class="big-icon">🏛️</div>
          <p>বিশ্লেষণ দেখতে বাম দিকের ফর্মে তথ্য প্রদান করুন</p>
        </div>
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
        errDiv.textContent = 'গল্পের নাম ও লেখকের নাম দুটোই লিখুন।';
        errDiv.style.display = 'block';
        return;
      }

      btn.disabled = true;
      btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:3px"></div> বিশ্লেষণ চলছে...';

      output.innerHTML = `
        <div class="loading">
          <div class="spinner"></div>
          <p>গভীর বিশ্লেষণ তৈরি হচ্ছে...</p>
          <small>এটি কয়েক সেকেন্ড সময় নিতে পারে</small>
        </div>`;

      try {
        const res = await fetch('/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ story, writer })
        });
        const data = await res.json();

        if (data.error) {
          output.innerHTML = `<div class="result-empty"><div class="big-icon">⚠️</div><p>${data.error}</p></div>`;
        } else {
          output.innerHTML = `
            <div class="result-card">
              <div class="result-header">বিশ্লেষণ ফলাফল</div>
              <div class="result-body">
                <div class="prose">${marked.parse(data.result)}</div>
              </div>
            </div>`;
        }
      } catch (e) {
        output.innerHTML = `<div class="result-empty"><div class="big-icon">⚠️</div><p>সংযোগে সমস্যা হয়েছে। আবার চেষ্টা করুন।</p></div>`;
      }

      btn.disabled = false;
      btn.innerHTML = '✨ পাঠ-পরিচিতি তৈরি করুন';
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') generate();
    });
  </script>
</body>
</html>"""


def call_groq(story_name, writer_name):
    if not GROQ_API_KEY:
        return None, "❌ GROQ_API_KEY সেট নেই। অনুগ্রহ করে Secrets-এ আপনার Groq API কী যোগ করুন। (console.groq.com থেকে ফ্রি নিন)"

    prompt = f"""তুমি একজন সাহিত্য বিশেষজ্ঞ ও বাংলা গল্পের বিশ্লেষক। নিচের গল্পটির একটি পেশাদার, বিস্তারিত ও আকর্ষণীয় 'পাঠ-পরিচিতি' বাংলায় রচনা করো। নিচের কাঠামো অনুসরণ করবে:

# {story_name} - {writer_name}

## 📖 রচয়িতা পরিচিতি
- লেখকের জন্ম, মৃত্যু, পৈতৃক বা কর্মস্থল।
- তাঁর ২-৩টি উল্লেখযোগ্য সাহিত্যকর্ম।
- তাঁর লেখার মূল বৈশিষ্ট্য ও সাহিত্যে অবদান।

## 👥 প্রধান চরিত্রসমূহ
- বুলেট পয়েন্টে নাম ও সংক্ষিপ্ত বিবরণ।

## 📜 গল্পের পটভূমি ও কাহিনি সংক্ষেপ
### প্রেক্ষাপট
### কাহিনির সূত্রপাত
### ঘটনাপ্রবাহ ও সংগ্রাম
### পরিণতি (স্পয়লার না দিয়ে)

## 💡 মূল বক্তব্য ও শিক্ষা
১. ২. ৩.

## ✨ প্রাসঙ্গিকতা ও গুরুত্ব
- কেন এখনও পড়ার মতো?

## 📝 পাঠপরামর্শ (টিপস)
- ২-৩টি টিপস

গল্পের নাম: {story_name}
লেখকের নাম: {writer_name}"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'], None
    except Exception as e:
        return None, f"❌ ত্রুটি: {str(e)}"


@app.route('/')
def home():
    return render_template_string(HTML)


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    story = data.get('story', '').strip()
    writer = data.get('writer', '').strip()
    if not story or not writer:
        return jsonify({"error": "দুটি ঘরই পূরণ করুন"}), 400
    result, error = call_groq(story, writer)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})


if __name__ == '__main__':
    # ক্লাউড প্ল্যাটফর্মে PORT এনভায়রনমেন্ট ভেরিয়েবল থাকে
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)