from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

# Render-এ MISTRAL_API_KEY নামে এনভায়রনমেন্ট ভেরিয়েবল সেট করুন
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")

# Mistral API এন্ডপয়েন্ট
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL_NAME = "mistral-small-latest"

HTML = """<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>পাঠ-পরিচিতি বিশ্লেষক</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f2ede4; font-family: 'Segoe UI', 'Kalpurush', 'Noto Sans Bengali', Georgia, serif; color: #2c1f12; }
        .container { max-width: 960px; margin: 0 auto; padding: 2rem; }
        header { text-align: center; margin-bottom: 2rem; }
        h1 { font-size: 2.2rem; color: #8b3c28; margin-bottom: 0.5rem; }
        .subtitle { color: #5c3820; font-size: 1.1rem; }
        .grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem; }
        @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
        .card { background: #faf7f2; border: 1px solid #ddd3c4; border-radius: 1rem; padding: 1.5rem; }
        .card-title { font-size: 1.3rem; font-weight: bold; color: #8b3c28; margin-bottom: 0.5rem; }
        label { display: block; font-weight: 600; margin-top: 0.5rem; color: #2c1f12; }
        input { width: 100%; padding: 0.75rem; margin: 0.25rem 0 0.75rem 0; border: 1px solid #ddd3c4; border-radius: 0.5rem; font-size: 1rem; background: #f9f6f0; }
        input:focus { outline: none; border-color: #8b3c28; box-shadow: 0 0 0 3px rgba(139,60,40,0.12); }
        button { width: 100%; padding: 0.75rem; background: #8b3c28; color: white; font-weight: bold; border: none; border-radius: 0.5rem; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #a04830; }
        button:disabled { opacity: 0.6; cursor: not-allowed; }
        .result-empty { text-align: center; padding: 3rem; border: 2px dashed #ddd3c4; border-radius: 1rem; color: #9b8070; }
        .loading { text-align: center; padding: 2rem; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #8b3c28; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 1rem; }
        @keyframes spin { 0% { transform: rotate(0); } 100% { transform: rotate(360deg); } }
        .result-card { background: #faf7f2; border: 1px solid #ddd3c4; border-radius: 1rem; overflow: hidden; }
        .result-header { background: #e5d9cc; padding: 1rem; font-weight: bold; color: #2c1f12; }
        .result-body { padding: 1.5rem; }
        .prose { font-family: 'Noto Sans Bengali', Georgia, serif; line-height: 1.8; }
        .prose h1 { font-size: 1.8rem; color: #8b3c28; }
        .prose h2 { color: #8b3c28; margin: 1.5rem 0 0.5rem 0; border-bottom: 2px solid #e5d9cc; padding-bottom: 0.3rem; }
        .prose h3 { color: #5c3820; margin: 1rem 0 0.3rem 0; }
        .prose ul { padding-left: 1.5rem; margin: 0.5rem 0; }
        .prose li { margin: 0.3rem 0; }
        .error-msg { background: #ffe0e0; color: #b00020; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; display: none; }
        .footer { text-align: center; margin-top: 2rem; color: #9b8070; font-size: 0.9rem; }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>📚 পাঠ-পরিচিতি বিশ্লেষক</h1>
        <p class="subtitle">NCTB ইন্টার ১ম বর্ষের বাংলা সাহিত্যের গল্প বিশ্লেষণ</p>
    </header>
    <div class="grid">
        <div class="card">
            <div class="card-title">📖 গল্পের তথ্য দিন</div>
            <label>গল্পের নাম</label>
            <input type="text" id="story" placeholder="যেমন: পোস্টমাস্টার" />
            <label>লেখকের নাম</label>
            <input type="text" id="writer" placeholder="যেমন: রবীন্দ্রনাথ ঠাকুর" />
            <button id="btn" onclick="generate()">✨ পাঠ-পরিচিতি তৈরি করুন</button>
            <div id="error" class="error-msg"></div>
        </div>
        <div id="output">
            <div class="result-empty">🏛️ বিশ্লেষণ দেখতে ফর্ম পূরণ করুন</div>
        </div>
    </div>
    <div class="footer">NCTB ইন্টার ১ম বর্ষ · সহজ ও সংক্ষিপ্ত বিশ্লেষণ</div>
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
        btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px;display:inline-block;"></div> বিশ্লেষণ চলছে...';
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
                output.innerHTML = '<div class="result-card"><div class="result-header">📝 বিশ্লেষণ ফলাফল</div><div class="result-body"><div class="prose">' + marked.parse(data.result) + '</div></div></div>';
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

def call_mistral(story_name, writer_name):
    """Mistral API কল করে বিশ্লেষণ তৈরি করে"""
    if not MISTRAL_API_KEY:
        return None, "MISTRAL_API_KEY সেট নেই। Render-এ Environment Variable যোগ করুন।"

    prompt = f"""তুমি একজন বাংলা সাহিত্যের শিক্ষক। তুমি NCTB (জাতীয় শিক্ষাক্রম ও পাঠ্যপুস্তক বোর্ড) এর ইন্টার ১ম বর্ষের 'বাংলা সাহিত্য' বইয়ের ভিত্তিতে গল্প বিশ্লেষণ করবে।

⚠️ গুরুত্বপূর্ণ নির্দেশনা:
১. উত্তরটি যেন ইন্টার ১ম বর্ষের শিক্ষার্থীদের উপযোগী ভাষায় হয় – সহজ, স্পষ্ট ও সংক্ষিপ্ত।
২. প্রতিটি অংশে ৩-৫টি বুলেট পয়েন্ট ব্যবহার করো।
৩. 'পরিণতি' অংশে গল্পের শেষ স্পয়লার করবে না, শুধু ইঙ্গিত দেবে।
৪. সব তথ্য NCTB পাঠ্যবই অনুযায়ী দিতে হবে। যদি কোনো তথ্য বইয়ে না থাকে, তাহলে 'NCTB বইয়ে উল্লেখ নেই' লিখে দেবে।
৫. উত্তর সম্পূর্ণ বাংলায় হতে হবে এবং প্রতিটি অংশ হেডিং দিয়ে স্পষ্টভাবে বিভক্ত থাকতে হবে।
৬. শিক্ষার্থীরা যেন সহজে মুখস্থ করতে পারে, সেজন্য প্রতিটি পয়েন্ট ছোট ও সহজ বাক্যে লিখতে হবে।
৭. পাঠপরামর্শ অংশে পড়ার সময় কী কী বিষয় খেয়াল রাখতে হবে, তা বলতে হবে।

নিচের কাঠামোটি ঠিকভাবে অনুসরণ করো:

# {story_name} - {writer_name}

## 📖 রচয়িতা পরিচিতি
- লেখকের জন্ম-মৃত্যু, গ্রাম/জেলা (যদি NCTB বইয়ে থাকে)।
- তাঁর ২টি উল্লেখযোগ্য রচনা (NCTB বইয়ের ভিত্তিতে)।
- বাংলা সাহিত্যে তাঁর অবদান (সংক্ষেপে)।

## 👥 প্রধান চরিত্রসমূহ
- ২-৩টি প্রধান চরিত্রের নাম ও তাদের ভূমিকা (সংক্ষেপে)।

## 📜 গল্পের পটভূমি ও কাহিনি সংক্ষেপ
### প্রেক্ষাপট
- গল্পের সময়, স্থান ও পটভূমি (NCTB বই অনুযায়ী)।
### কাহিনির সূত্রপাত
### ঘটনাপ্রবাহ
### পরিণতি (স্পয়লার মুক্ত)

## 💡 মূল বক্তব্য ও শিক্ষা
১.
২.
৩.

## ✨ গল্পের প্রাসঙ্গিকতা
- কেন এই গল্প ইন্টার ১ম বর্ষের শিক্ষার্থীদের পড়া উচিত?

## 📝 পরীক্ষার জন্য গুরুত্বপূর্ণ টিপস
- এই গল্প থেকে কী ধরনের প্রশ্ন আসতে পারে?
- কোন অংশগুলো মুখস্থ করা জরুরি?

গল্পের নাম: {story_name}
লেখকের নাম: {writer_name}"""

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 2500
    }
    try:
        response = requests.post(MISTRAL_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'], None
    except Exception as e:
        return None, f"Mistral API ত্রুটি: {str(e)}"

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
    result, error = call_mistral(story, writer)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
