import os
from flask import Flask, render_template_string, request, jsonify
from google import genai

app = Flask(__name__)

# Security aur API Key (Render ki settings se aayengi)
API_KEY = os.environ.get("GEMINI_API_KEY", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "12345") # Default password

client = genai.Client(api_key=API_KEY) if API_KEY else None

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Personal AI Server</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 15px; }
        .box { max-width: 500px; margin: auto; background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { text-align: center; color: #38bdf8; margin-top: 0; }
        input, textarea, button { width: 100%; padding: 12px; margin-top: 10px; border-radius: 8px; border: none; box-sizing: border-box; font-size: 16px; }
        input, textarea { background: #334155; color: white; }
        button { background: #0284c7; color: white; font-weight: bold; cursor: pointer; }
        button.mic { background: #e11d48; }
        #chatBox { height: 320px; overflow-y: auto; background: #0f172a; padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid #334155; }
        .user { color: #38bdf8; margin: 8px 0; text-align: right; }
        .ai { color: #4ade80; margin: 8px 0; text-align: left; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🤖 My AI & Cloud Hub</h2>
        <input type="password" id="pass" placeholder="Apna Server Password dalein">
        <div id="chatBox"><div class="ai"><b>AI:</b> System Ready! Password daal kar baat shuru karein.</div></div>
        <textarea id="msg" rows="2" placeholder="Yahan likhein ya Mic dabayein..."></textarea>
        <button onclick="sendMsg()">🚀 Send Message</button>
        <button class="mic" onclick="startVoice()">🎤 Speak (Voice Input)</button>
    </div>

    <script>
        async function sendMsg() {
            let pass = document.getElementById('pass').value;
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
                body: JSON.stringify({password: pass, message: msg})
            });
            let data = await res.json();
            chatBox.innerHTML += `<div class='ai'><b>AI:</b> ${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            // Voice Output (AI bolega)
            if ('speechSynthesis' in window) {
                let speech = new SpeechSynthesisUtterance(data.reply);
                speech.lang = 'hi-IN';
                window.speechSynthesis.speak(speech);
            }
        }

        function startVoice() {
            let Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!Recognition) { alert("Aapke browser mein Voice input support nahi hai. Chrome use karein."); return; }
            let rec = new Recognition();
            rec.lang = 'hi-IN';
            rec.onresult = function(e) {
                document.getElementById('msg').value = e.results[0][0].transcript;
                sendMsg();
            };
            rec.start();
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if data.get("password") != ADMIN_PASS:
        return jsonify({"reply": "❌ Galat Password! Access Denied."})
    if not client:
        return jsonify({"reply": "⚠️ API Key set nahi hai!"})
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=f"Tum mera personal AI assistant aur server manager ho. Hinglish mein chota aur smart jawab do: {data.get('message')}"
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
