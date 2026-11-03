import os
import time
import json
import subprocess
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from google import genai

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "12345")

UPLOAD_FOLDER = "my_files"
NOTES_FILE = "notes.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(NOTES_FILE):
    with open(NOTES_FILE, "w") as f:
        json.dump([], f)

client = genai.Client(api_key=API_KEY) if API_KEY else None

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sachin's Personal Cloud Server</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 12px; }
        .box { max-width: 550px; margin: auto; background: #1e293b; padding: 18px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.6); }
        h2 { text-align: center; color: #38bdf8; margin: 0 0 12px 0; font-size: 22px; }
        .tabs { display: flex; gap: 6px; margin-top: 12px; }
        .tab-btn { flex: 1; padding: 10px 4px; background: #334155; color: #cbd5e1; border: none; border-radius: 8px; font-weight: bold; font-size: 13px; cursor: pointer; }
        .tab-btn.active { background: #0284c7; color: white; }
        .section { display: none; margin-top: 15px; }
        .section.active { display: block; }
        input, textarea, button { width: 100%; padding: 11px; margin-top: 8px; border-radius: 8px; border: none; box-sizing: border-box; font-size: 15px; }
        input, textarea { background: #334155; color: white; border: 1px solid #475569; }
        button.action { background: #0284c7; color: white; font-weight: bold; cursor: pointer; }
        button.mic { background: #e11d48; color: white; font-weight: bold; }
        button.del { background: #dc2626; width: auto; padding: 5px 10px; font-size: 12px; margin: 0; }
        #chatBox, .list-box, #termOut { height: 270px; overflow-y: auto; background: #0f172a; padding: 12px; border-radius: 8px; margin-top: 10px; border: 1px solid #334155; font-size: 14px; }
        .user { color: #38bdf8; margin: 8px 0; text-align: right; }
        .ai { color: #4ade80; margin: 8px 0; text-align: left; }
        .item { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px; border: 1px solid #334155; word-break: break-all; }
        a { color: #38bdf8; text-decoration: none; }
        pre { margin: 0; white-space: pre-wrap; color: #22c55e; font-family: monospace; }
    </style>
</head>
<body>
    <div class="box">
        <h2>⚡ My Personal Cloud Server</h2>
        <input type="password" id="pass" placeholder="🔑 Apna Server Password dalein">

        <div class="tabs">
            <button class="tab-btn active" onclick="openTab('aiTab', this)">🤖 AI Chat</button>
            <button class="tab-btn" onclick="openTab('fileTab', this); loadFiles();">📁 Files</button>
            <button class="tab-btn" onclick="openTab('noteTab', this); loadNotes();">📝 Notes</button>
            <button class="tab-btn" onclick="openTab('termTab', this)">💻 System</button>
        </div>

        <!-- 1. AI Assistant Tab -->
        <div id="aiTab" class="section active">
            <div id="chatBox"><div class="ai"><b>Server AI:</b> Namaste! Main aapka all-in-one assistant hoon. Bataiye kya kaam karna hai?</div></div>
            <textarea id="msg" rows="2" placeholder="Sawal puchein, code likhwayein ya Mic dabayein..."></textarea>
            <button class="action" onclick="sendMsg()">🚀 Send</button>
            <button class="mic" onclick="startVoice()">🎤 Bolkar Puchein (Voice)</button>
        </div>

        <!-- 2. File Cloud Tab -->
        <div id="fileTab" class="section">
            <input type="file" id="fileInput">
            <button class="action" onclick="uploadFile()">⬆️ Server Par File Upload Karein</button>
            <div class="list-box" id="fileList">Password daal kar refresh karein...</div>
        </div>

        <!-- 3. Notes Tab -->
        <div id="noteTab" class="section">
            <textarea id="noteInput" rows="2" placeholder="Koi bhi zaroori Note, Link ya Code yahan save karein..."></textarea>
            <button class="action" onclick="saveNote()">💾 Save Note</button>
            <div class="list-box" id="noteList">Password daal kar dekhein...</div>
        </div>

        <!-- 4. System & Terminal Tab -->
        <div id="termTab" class="section">
            <input type="text" id="cmdInput" placeholder="Linux command (e.g. df -h, ls -la, uptime)">
            <button class="action" onclick="runCmd()">▶️ Run Command</button>
            <div id="termOut"><pre id="cmdResult">Server terminal ready...</pre></div>
        </div>
    </div>

    <script>
        function getPass() { return document.getElementById('pass').value; }

        function openTab(tabId, btn) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }

        // AI Chat
        async function sendMsg() {
            let msgInput = document.getElementById('msg');
            let msg = msgInput.value.trim();
            let chatBox = document.getElementById('chatBox');
            if(!msg) return;
            chatBox.innerHTML += `<div class='user'><b>You:</b> ${msg}</div>`;
            msgInput.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            let res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), message: msg})
            });
            let data = await res.json();
            chatBox.innerHTML += `<div class='ai'><b>AI:</b> ${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            if ('speechSynthesis' in window) {
                let s = new SpeechSynthesisUtterance(data.reply);
                s.lang = 'hi-IN';
                window.speechSynthesis.speak(s);
            }
        }

        function startVoice() {
            let Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!Rec) { alert("Chrome browser use karein."); return; }
            let rec = new Rec();
            rec.lang = 'hi-IN';
            rec.onresult = e => { document.getElementById('msg').value = e.results[0][0].transcript; sendMsg(); };
            rec.start();
        }

        // Files
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

        // Notes
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

        // Terminal
        async function runCmd() {
            let cmd = document.getElementById('cmdInput').value.trim();
            if(!cmd) return;
            document.getElementById('cmdResult').innerText = "Running...";
            let res = await fetch('/terminal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: getPass(), command: cmd})
            });
            let data = await res.json();
            document.getElementById('cmdResult').innerText = data.output;
        }
    </script>
</body>
</html>
"""

def check_auth(pw):
    return pw == ADMIN_PASS

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not check_auth(data.get("password")):
        return jsonify({"reply": "❌ Galat Password!"})
    if not client:
        return jsonify({"reply": "⚠️ API Key set nahi hai!"})
    
    prompt = f"Tum Sachin ke personal server assistant ho. Hinglish mein chota aur smart jawab do: {data.get('message')}"
    models = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash-lite", "gemini-3.8-flash"]
    
    last_err = ""
    for m in models:
        try:
            res = client.models.generate_content(model=m, contents=prompt)
            return jsonify({"reply": res.text})
        except Exception as e:
            last_err = str(e)
            continue
    return jsonify({"reply": f"⏳ Google AI abhi busy hai, 10 sec baad try karein."})

@app.route("/files")
def list_files():
    if not check_auth(request.args.get("password")):
        return jsonify({"error": "❌ Pehle upar sahi Password dalein!"})
    return jsonify({"files": os.listdir(UPLOAD_FOLDER)})

@app.route("/upload", methods=["POST"])
def upload_file():
    if not check_auth(request.form.get("password")):
        return jsonify({"error": "Unauthorized"}), 403
    f = request.files.get("file")
    if f:
        f.save(os.path.join(UPLOAD_FOLDER, secure_filename(f.filename)))
    return jsonify({"status": "ok"})

@app.route("/download/<filename>")
def download_file(filename):
    if not check_auth(request.args.get("password")):
        return "Unauthorized", 403
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/delete_file", methods=["POST"])
def delete_file():
    data = request.json
    if not check_auth(data.get("password")):
        return jsonify({"error": "Unauthorized"}), 403
    path = os.path.join(UPLOAD_FOLDER, secure_filename(data.get("filename", "")))
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"status": "ok"})

@app.route("/notes", methods=["GET", "POST"])
def handle_notes():
    if request.method == "GET":
        if not check_auth(request.args.get("password")):
            return jsonify({"error": "❌ Pehle upar sahi Password dalein!"})
        with open(NOTES_FILE, "r") as f:
            return jsonify({"notes": json.load(f)})
    else:
        data = request.json
        if not check_auth(data.get("password")):
            return jsonify({"error": "Unauthorized"}), 403
        with open(NOTES_FILE, "r") as f:
            notes = json.load(f)
        notes.append(data.get("note"))
        with open(NOTES_FILE, "w") as f:
            json.dump(notes, f)
        return jsonify({"status": "ok"})

@app.route("/delete_note", methods=["POST"])
def delete_note():
    data = request.json
    if not check_auth(data.get("password")):
        return jsonify({"error": "Unauthorized"}), 403
    with open(NOTES_FILE, "r") as f:
        notes = json.load(f)
    idx = data.get("index", -1)
    if 0 <= idx < len(notes):
        notes.pop(idx)
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f)
    return jsonify({"status": "ok"})

@app.route("/terminal", methods=["POST"])
def terminal():
    data = request.json
    if not check_auth(data.get("password")):
        return jsonify({"output": "❌ Galat Password! Access Denied."})
    try:
        out = subprocess.check_output(data.get("command"), shell=True, stderr=subprocess.STDOUT, timeout=5, text=True)
        return jsonify({"output": out if out else "Command executed successfully (No output)."})
    except Exception as e:
        return jsonify({"output": f"Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
