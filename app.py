from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY")

HTML = """<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <title>পাঠ-পরিচিতি বিশ্লেষক (Cerebras)</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #f2ede4; font-family: 'Segoe UI', 'Kalpurush', Georgia, serif; }
        .container { max-width: 960px; margin: 0 auto; padding: 2rem; }
        header { text-align: center; margin-bottom: 2rem; }
        h1 { color: #8b3c28; }
        .grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 2rem; }
        @media (max-width: 700px) { .grid { grid-template-columns: 1fr; } }
        .card { background: #faf7f2; border: 1px solid #ddd3c4; border-radius: 1rem; padding: 1.5rem; }
        input, button { width: 100%; padding: 0.75rem; margin: 0.5rem 0; border-radius: 0.5rem; border: 1px solid #ddd3c4; }
        button { background: #8b3c28; color: white; font-weight: bold; cursor: pointer; }
        button:disabled { opacity: 0.6; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #8b3c28; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .result-card { background: #faf7f2; border: 1px solid #ddd3c4; border-radius: 1rem; }
        .result-header { background: #e5d9cc; padding: 1rem; font-weight: bold; }
        .result-body { padding: 1.5rem; }
        .error-msg { background: #ffe0e0; color: #b00020; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; display: none; }
    </style>
</head>
<body>
<div class="container">
    <header><h1>📚 পাঠ-পরিচিতি বিশ্লেষক (Cerebras)</h1></header>
    <div class="grid">
        <div class="card">
            <label>গল্পের নাম</label><input id="story" placeholder="যেমন: পোস্টমাস্টার">
            <label>লেখকের নাম</label><input id="writer" placeholder="যেমন: রবীন্দ্রনাথ ঠাকুর">
            <button id="btn" onclick="generate()">✨ বিশ্লেষণ করুন</button>
            <div id="error" class="error-msg"></div>
        </div>
        <div id="output"><div class="result-empty" style="text-align:center; padding:2rem;">🏛️ ফর্ম পূরণ করুন</div></div>
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
        output.innerHTML = '<div class="spinner"></div><p style="text-align:center">গভীর বিশ্লেষণ তৈরি হচ্ছে...</p>';
        try {
            const res = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ story, writer })
            });
            const data = await res.json();
            if (data.error) output.innerHTML = '<div style="text-align:center;padding:2rem;">⚠️ ' + data.error + '</div>';
            else output.innerHTML = '<div class="result-card"><div class="result-header">বিশ্লেষণ ফলাফল</div><div class="result-body"><div class="prose">' + marked.parse(data.result) + '</div></div></div>';
        } catch(e) {
            output.innerHTML = '<div style="text-align:center;padding:2rem;">⚠️ সংযোগ সমস্যা</div>';
        }
        btn.disabled = false;
        btn.innerHTML = '✨ বিশ্লেষণ করুন';
    }
</script>
</body>
</html>"""

def call_cerebras(story, writer):
    if not CEREBRAS_API_KEY:
        return None, "Cerebras API Key সেট নেই।"
    prompt = f"""তুমি সাহিত্য বিশেষজ্ঞ। নিচের গল্পটির বিস্তারিত 'পাঠ-পরিচিতি' বাংলায় রচনা করো:

# {story} - {writer}

## রচয়িতা পরিচিতি
## প্রধান চরিত্র
## কাহিনি সংক্ষেপ
## মূল বক্তব্য
## প্রাসঙ্গিকতা

গল্প: {story}
লেখক: {writer}"""
    
    # ✅ এন্ডপয়েন্ট এবং মডেলের নাম ডকুমেন্টেশন অনুযায়ী ঠিক করা হয়েছে
    url = "https://api.cerebras.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b",   # ✅ অফিসিয়াল ডকুমেন্টেশন অনুযায়ী সঠিক নাম[reference:1]
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()['choices'][0]['message']['content'], None
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
        return jsonify({"error": "দুটি ঘর পূরণ করুন"}), 400
    result, error = call_cerebras(story, writer)
    if error:
        return jsonify({"error": error}), 500
    return jsonify({"result": result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


