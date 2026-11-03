import os
import json
import urllib.request
import urllib.parse
import subprocess
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from google import genai

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
ADMIN_PASS = os.environ.get("ADMIN_PASS", "12345").strip()

UPLOAD_FOLDER = "my_files"
WEB_HOST_FOLDER = "hosted_web"
NOTES_FILE = "notes.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(WEB_HOST_FOLDER, exist_ok=True)

if not os.path.exists(NOTES_FILE):
    with open(NOTES_FILE, "w") as f:
        json.dump([], f)

client = genai.Client(api_key=API_KEY) if API_KEY else None

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sachin's Superfast Server Hub</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 12px; }
        .box { max-width: 550px; margin: auto; background: #1e293b; padding: 18px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
        h2 { text-align: center; color: #38bdf8; margin: 0 0 12px 0; font-size: 22px; }
        .tabs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 12px; }
        .tab-btn { padding: 10px 4px; background: #334155; color: #cbd5e1; border: none; border-radius: 8px; font-weight: bold; font-size: 11px; cursor: pointer; text-align: center; }
        .tab-btn.active { background: #0284c7; color: white; }
        .section { display: none; margin-top: 15px; }
        .section.active { display: block; }
        input, textarea, button { width: 100%; padding: 11px; margin-top: 8px; border-radius: 8px; border: none; box-sizing: border-box; font-size: 14px; }
        input, textarea { background: #334155; color: white; border: 1px solid #475569; }
        button.action { background: #0284c7; color: white; font-weight: bold; cursor: pointer; }
        button.mic { background: #e11d48; color: white; font-weight: bold; }
        button.del { background: #dc2626; width: auto; padding: 5px 10px; font-size: 12px; margin: 0; color: white; border-radius: 4px; cursor: pointer; }
        #chatBox, .list-box { height: 260px; overflow-y: auto; background: #0f172a; padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid #334155; font-size: 14px; }
        .user { color: #38bdf8; margin: 8px 0; text-align: right; }
        .ai { color: #4ade80; margin: 8px 0; text-align: left; }
        .item { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #334155; word-break: break-all; }
        a { color: #38bdf8; text-decoration: none; }
        #calcScreen { font-size: 20px; font-weight: bold; text-align: right; background: #0f172a; border-radius: 8px; padding: 12px; border: 1px solid #334155; margin-bottom: 8px; min-height: 50px; color: #4ade80; }
        .calc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
        .calc-btn { padding: 15px; font-size: 16px; background: #334155; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; margin-top: 0; }
        .calc-btn.op { background: #f97316; }
        .calc-btn.eq { background: #10b981; grid-column: span 2; }
    </style>
</head>
<body>
    <div class="box">
        <h2>⚡ Sachin's Superfast Hub</h2>
        <input type="password" id="pass" placeholder="🔑 Apna Server Password dalein">

        <div class="tabs">
            <button class="tab-btn active" onclick="openTab('aiTab', this)">🤖 Fast AI</button>
            <button class="tab-btn" onclick="openTab('fileTab', this); loadFiles();">📁 Files</button>
            <button class="tab-btn" onclick="openTab('noteTab', this); loadNotes();">📝 Notes</button>
            <button class="tab-btn" onclick="openTab('dlTab', this)">📥 Downloader</button>
            <button class="tab-btn" onclick="openTab('hostTab', this); loadHostedPages();">🌐 Web Host</button>
            <button class="tab-btn" onclick="openTab('calcTab', this)">🧮 Calculator</button>
        </div>

        <!-- 1. AI Assistant Tab -->
        <div id="aiTab" class="section active">
            <div id="chatBox"><div class="ai"><b>AI:</b> Superfast AI Ready! (Bina API Key ke bhi chalega). Password daal kar puchein!</div></div>
            <textarea id="msg" rows="2" placeholder="Yahan likhein ya Mic dabayein..."></textarea>
            <button class="action" id="sendBtn" onclick="sendMsg()">🚀 Send Message</button>
            <button class="mic" onclick="startVoice()">🎤 Bolkar Puchein (Voice)</button>
        </div>

        <!-- 2. File Cloud Tab -->
        <div id="fileTab" class="section">
            <input type="file" id="fileInput">
            <button class="action" onclick="uploadFile()">⬆️ Server Par File Upload Karein</button>
            <div class="list-box" id="fileList">Password daal kar dekhein...</div>
        </div>

        <!-- 3. Notes Tab -->
        <div id="noteTab" class="section">
            <textarea id="noteInput" rows="2" placeholder="Note ya Link save karein..."></textarea>
            <button class="action" onclick="saveNote()">💾 Save Note</button>
            <div class="list-box" id="noteList">Password daal kar dekhein...</div>
        </div>

        <!-- 4. Downloader Tab -->
        <div id="dlTab" class="section">
            <input type="text" id="videoUrl" placeholder="Video Link paste karein">
            <button class="action" onclick="downloadVideo()">📥 Video Server Pe Save Karein</button>
            <div class="list-box" id="downloadStatus" style="height: 100px;">Ready...</div>
        </div>

        <!-- 5. Mini Web Hosting Tab -->
        <div id="hostTab" class="section">
            <input type="text" id="webFilename" placeholder="Page Name (e.g. index.html)">
            <textarea id="webCode" rows="4" placeholder="HTML code paste karein..."></textarea>
            <button class="action" onclick="saveWebPage()">🌐 Page Live Karein</button>
            <div class="list-box" id="hostedList">Ready...</div>
        </div>

        <!-- 6. Calculator Tab -->
        <div id="calcTab" class="section">
            <div id="calcScreen">0</div>
            <div class="calc-grid">
                <button class="calc-btn op" onclick="clearCalc()">C</button>
                <button class="calc-btn op" onclick="pressCalc('(')">(</button>
                <button class="calc-btn op" onclick="pressCalc(')')">)</button>
                <button class="calc-btn op" onclick="pressCalc('/')">/</button>
                <button class="calc-btn" onclick="pressCalc('7')">7</button>
                <button class="calc-btn" onclick="pressCalc('8')">8</button>
                <button class="calc-btn" onclick="pressCalc('9')">9</button>
                <button class="calc-btn op" onclick="pressCalc('*')">*</button>
                <button class="calc-btn" onclick="pressCalc('4')">4</button>
                <button class="calc-btn" onclick="pressCalc('5')">5</button>
                <button class="calc-btn" onclick="pressCalc('6')">6</button>
                <button class="calc-btn op" onclick="pressCalc('-')">-</button>
                <button class="calc-btn" onclick="pressCalc('1')">1</button>
                <button class="calc-btn" onclick="pressCalc('2')">2</button>
                <button class="calc-btn" onclick="pressCalc('3')">3</button>
                <button class="calc-btn op" onclick="pressCalc('+')">+</button>
                <button class="calc-btn" onclick="pressCalc('0')">0</button>
                <button class="calc-btn" onclick="pressCalc('.')">.</button>
                <button class="calc-btn eq" onclick="solveCalc()">=</button>
            </div>
        </div>
    </div>

    <script>
        function getPass() { return document.getElementById('pass').value.trim(); }

        function openTab(tabId, btn) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }

        async function sendMsg() {
            let msgInput = document.getElementById('msg');
            let msg = msgInput.value.trim();
            let chatBox = document.getElementById('chatBox');
            let btn = document.getElementById('sendBtn');
            if(!msg) return;

            chatBox.innerHTML += `<div class='user'><b>You:</b> ${msg}</div>`;
            msgInput.value = '';
            btn.innerText = "⏳ Soch raha hai...";
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                let res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: getPass(), message: msg})
                });
                let data = await res.json();
                chatBox.innerHTML += `<div class='ai'><b>AI:</b> ${data.reply}</div>`;
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    let s = new SpeechSynthesisUtterance(data.reply);
                    s.lang = 'hi-IN';
                    window.speechSynthesis.speak(s);
                }
            } catch (err) {
                chatBox.innerHTML += `<div class='ai'><b>AI:</b> ⚠️ Network error, dubara Send dabayein.</div>`;
            }
            btn.innerText = "🚀 Send Message";
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function startVoice() {
            let Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!Rec) { alert("Chrome browser use karein."); return; }
            let rec = new Rec();
            rec.lang = 'hi-IN';
            rec.onresult = e => { document.getElementById('msg').value = e.results[0][0].transcript; sendMsg(); };
            rec.start();
        }

        async function loadFiles() {
            let res = await fetch('/files?password=' + encodeURIComponent(getPass()));
            let data = await res.json();
            let box = document.getElementById('fileList');
            if(data.error) { box.innerHTML = data.error; return; }
            box.innerHTML = data.files.length ? '' : 'Koi file nahi hai.';
            data.files.forEach(f => {
                box.innerHTML += `<div class="item">
                    <a href="/download/${encodeURIComponent(f)}?password=${encodeURIComponent(getPass())}" target="_blank">📄 ${f}</a>
                    <button class="del" onclick="delFile('${f}')">Delete</button>
                </div>`;
            });
        }

        async function uploadFile() {
            let file = document.getElementById('fileInput').files[0];
            if(!file) return alert("Pehle file select karein!");
            let fd = new FormData();
            fd.append("file", file);
            fd.append("password", getPass());
            await fetch('/upload', {method: 'POST', body: fd});
            document.getElementById('fileInput').value = '';
            loadFiles();
        }

        async function delFile(name) {
            await fetch('/delete_file', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), filename: name})
            });
            loadFiles();
        }

        async function loadNotes() {
            let res = await fetch('/notes?password=' + encodeURIComponent(getPass()));
            let data = await res.json();
            let box = document.getElementById('noteList');
            if(data.error) { box.innerHTML = data.error; return; }
            box.innerHTML = data.notes.length ? '' : 'Koi note save nahi hai.';
            data.notes.forEach((n, i) => {
                box.innerHTML += `<div class="item"><span>📌 ${n}</span><button class="del" onclick="delNote(${i})">X</button></div>`;
            });
        }

        async function saveNote() {
            let text = document.getElementById('noteInput').value.trim();
            if(!text) return;
            await fetch('/notes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), note: text})
            });
            document.getElementById('noteInput').value = '';
            loadNotes();
        }

        async function delNote(idx) {
            await fetch('/delete_note', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), index: idx})
            });
            loadNotes();
        }

        async function downloadVideo() {
            let url = document.getElementById('videoUrl').value.trim();
            if(!url) return alert("Link daalein!");
            let status = document.getElementById('downloadStatus');
            status.innerHTML = "⏳ Video download ho rahi hai...";
            let res = await fetch('/download_v', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), url: url})
            });
            let data = await res.json();
            status.innerHTML = data.status || data.error;
            document.getElementById('videoUrl').value = '';
        }

        async function loadHostedPages() {
            let res = await fetch('/hosted_list?password=' + encodeURIComponent(getPass()));
            let data = await res.json();
            let box = document.getElementById('hostedList');
            if(data.error) { box.innerHTML = data.error; return; }
            box.innerHTML = data.pages.length ? '' : 'Abhi koi site live nahi hai.';
            data.pages.forEach(p => {
                let liveUrl = window.location.origin + '/web/' + p + '?password=' + encodeURIComponent(getPass());
                box.innerHTML += `<div class="item">
                    <a href="${liveUrl}" target="_blank">🌐 View: ${p}</a>
                    <button class="del" onclick="delPage('${p}')">Delete</button>
                </div>`;
            });
        }

        async function saveWebPage() {
            let name = document.getElementById('webFilename').value.trim();
            let code = document.getElementById('webCode').value.trim();
            if(!name || !code) return alert("Name aur code dono chahiye!");
            await fetch('/save_web', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), filename: name, code: code})
            });
            document.getElementById('webFilename').value = '';
            document.getElementById('webCode').value = '';
            loadHostedPages();
        }

        async function delPage(name) {
            await fetch('/delete_page', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), filename: name})
            });
            loadHostedPages();
        }

        let calcVal = "";
        function pressCalc(v) { calcVal += v; document.getElementById('calcScreen').innerText = calcVal; }
        function clearCalc() { calcVal = ""; document.getElementById('calcScreen').innerText = "0"; }
        function solveCalc() {
            try {
                let ans = eval(calcVal);
                document.getElementById('calcScreen').innerText = ans;
                calcVal = String(ans);
            } catch(e) { document.getElementById('calcScreen').innerText = "Error"; calcVal = ""; }
        }
    </script>
</body>
</html>
"""

def check_auth(pw):
    return str(pw).strip() == ADMIN_PASS

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    if not check_auth(data.get("password", "")):
        return jsonify({"reply": "❌ Galat Password! Upar sahi Server Password dalein."})
    
    user_msg = data.get("message", "")
    prompt = f"Tum Sachin ke personal server assistant ho. Hinglish mein chota aur smart jawab do: {user_msg}"

    # 1. Pehle Bina API Key wala Superfast Free AI try karega (100% Working & Fast)
    try:
        encoded = urllib.parse.quote(prompt)
        req = urllib.request.Request(
            f"https://text.pollinations.ai/{encoded}",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            reply_text = response.read().decode("utf-8").strip()
            if reply_text:
                return jsonify({"reply": reply_text})
    except Exception:
        pass

    # 2. Backup: Agar Gemini API Key hai toh latest Gemini 3.8 model chalayega
    if client:
        for m in ["gemini-3.8-flash", "gemini-2.5-flash"]:
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                return jsonify({"reply": res.text})
            except Exception as e:
                continue

    return jsonify({"reply": "⚠️ Server busy hai, ek baar phir Send dabayein."})

@app.route("/files")
def list_files():
    if not check_auth(request.args.get("password", "")):
        return jsonify({"error": "❌ Upar sahi Password dalein!"})
    return jsonify({"files": os.listdir(UPLOAD_FOLDER)})

@app.route("/upload", methods=["POST"])
def upload_file():
    if not check_auth(request.form.get("password", "")):
        return jsonify({"error": "Unauthorized"}), 403
    f = request.files.get("file")
    if f:
        f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
    return jsonify({"status": "ok"})

@app.route("/download/<filename>")
def download_file(filename):
    if not check_auth(request.args.get("password", "")):
        return "Unauthorized", 403
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/delete_file", methods=["POST"])
def delete_file():
    data = request.json or {}
    if not check_auth(data.get("password", "")):
        return jsonify({"error": "Unauthorized"}), 403
    path = os.path.join(UPLOAD_FOLDER, secure_filename(data.get("filename", "")))
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"status": "ok"})

@app.route("/notes", methods=["GET", "POST"])
def handle_notes():
    if request.method == "GET":
        if not check_auth(request.args.get("password", "")):
            return jsonify({"error": "❌ Password dalein!"})
        with open(NOTES_FILE, "r") as f:
            return jsonify({"notes": json.load(f)})
    else:
        data = request.json or {}
        if not check_auth(data.get("password", "")):
            return jsonify({"error": "Unauthorized"}), 403
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
        notes.append(data.get("note"))
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f)
        return jsonify({"status": "ok"})

@app.route("/delete_note", methods=["POST"])
def delete_note():
    data = request.json or {}
    if not check_auth(data.get("password", "")):
        return jsonify({"error": "Unauthorized"}), 403
    with open(NOTES_FILE, "r") as f:
        notes = json.load(f)
    idx = data.get("index", -1)
    if 0 <= idx < len(notes):
        notes.pop(idx)
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f)
    return jsonify({"status": "ok"})

@app.route("/download_v", methods=["POST"])
def download_video():
    data = request.json or {}
    if not check_auth(data.get("password", "")):
        return jsonify({"error": "Unauthorized"}), 403
    url = data.get("url")
    try:
        cmd = f"yt-dlp -P {UPLOAD_FOLDER} -o '%(title)s.%(ext)s' --max-filesize 50M '{url}'"
        subprocess.Popen(cmd, shell=True)
        return jsonify({"status": "📥 Download chalu ho gaya! Thodi der mein Files tab check karein."})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"})

@app.route("/hosted_list")
def hosted_list():
    if not check_auth(request.args.get("password", "")):
        return jsonify({"error": "❌ Password dalein!"})
    return jsonify({"pages": [f for f in os.listdir(WEB_HOST_FOLDER) if f.endswith('.html')]})

@app.route("/save_web", methods=["POST"])
def save_web():
    data = request.json or {}
    if not check_auth(data.get("password", "")):
        return jsonify({"error": "Unauthorized"}), 403
    filename = secure_filename(data.get("filename", ""))
    if not filename.endswith('.html'):
        filename += '.html'
    code = data.get("code", "")
    with open(os.path.join(WEB_HOST_FOLDER, filename), "w") as f:
        f.write(code)
    return jsonify({"status": "ok"})

@app.route("/web/<filename>")
def view_hosted_page(filename):
    if not check_auth(request.args.get("password", "")):
        return "Unauthorized", 403
    return send_from_directory(WEB_HOST_FOLDER, filename)

@app.route("/delete_page", methods=["POST"])
def delete_page():
    data = request.json or {}
    if not check_auth(data.get("password", "")):
        return jsonify({"error": "Unauthorized"}), 403
    path = os.path.join(WEB_HOST_FOLDER, secure_filename(data.get("filename", "")))
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
