import json
import os
import re  # Added re module to strip markdown formatting
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import config
from library_data import get_verified_knowledge_text, get_intent_answer, VERIFIED_LIBRARY_DATA
from topic_validator import validate_user_query, EXACT_REFUSAL_MESSAGE
from ollama_client import query_ollama

ROOT = Path(__file__).resolve().parent

def clean_markdown(text: str) -> str:
    """Utility function to strip asterisks (*) and underscores (_) from text."""
    if not text:
        return ""
    return re.sub(r'[\*_]{1,2}', '', text)

def classify(message: str, history=None, use_llm: bool = True) -> dict:
    """
    Main classification and response generation function.
    Maintains compatibility with test scripts and front-end interface.
    1. Validates whether the topic is library-related before calling Ollama.
    2. Rejects unrelated topics immediately with exact mandated refusal string.
    3. Handles ambiguous queries by returning clarification prompts.
    4. Handles polite conversational courtesies.
    5. Sends accepted library queries to Ollama (llama3:latest) with verified library facts.
    """
    cleaned_message = (message or "").strip()
    if not cleaned_message:
        return {
            "intent": "ambiguous",
            "confidence": 0.1,
            "answer": "Please enter a question or topic related to the WIT Library, books, research, or library services."
        }

    # Step 1: Backend Topic Validation (Strict Library-Only Filter)
    val = validate_user_query(cleaned_message)
    status = val["status"]
    intent = val["intent"]
    is_mixed = val.get("is_mixed", False)

    # Step 2: Handle Refusal for Unrelated Topics without calling Ollama
    if status == "REJECTED":
        return {
            "intent": "fallback",
            "confidence": 0.20,
            "answer": clean_markdown(EXACT_REFUSAL_MESSAGE)
        }

    # Step 3: Handle Ambiguous Queries
    if status == "AMBIGUOUS":
        return {
            "intent": "ambiguous",
            "confidence": 0.50,
            "answer": clean_markdown(val["answer"])
        }

    # Step 4: Handle Conversational Courtesies (Greetings, Goodbyes, Thanks)
    if status == "CONVERSATIONAL":
        return {
            "intent": intent,
            "confidence": 0.99,
            "answer": clean_markdown(val["answer"])
        }

    # Step 5: Accepted Library Query -> Call Ollama API
    if use_llm:
        res = query_ollama(
            user_message=cleaned_message,
            intent=intent,
            is_mixed=is_mixed,
            history=history
        )
        answer = res.get("answer")
        confidence = 0.95 if res.get("success") else 0.70
        return {
            "intent": intent,
            "confidence": confidence,
            "answer": clean_markdown(answer)
        }
    else:
        # Fast non-LLM path for offline evaluation if needed
        verified_ans = get_intent_answer(intent) or "Verified WIT Library information is available at the circulation desk."
        return {
            "intent": intent,
            "confidence": 1.0,
            "answer": clean_markdown(verified_ans)
        }


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WIT Library Chatbot</title>
<style>
body{font-family:Tahoma,Arial,sans-serif;margin:0;padding:28px 16px;background:linear-gradient(135deg,#fff4e8,#ffe3c3);color:#3a271d;min-height:100vh;box-sizing:border-box}
.shell{max-width:900px;margin:0 auto;min-height:calc(100vh - 56px);background:#fff;border:1px solid #f3c79e;border-radius:22px;overflow:hidden;box-shadow:0 18px 45px #b85b1d2b;display:flex;flex-direction:column}
.topbar{padding:30px 38px 26px;background:linear-gradient(135deg,#f58b27,#d95f02);color:#fff;position:relative}
.topbar:after{content:'WIT';position:absolute;right:38px;top:26px;font-size:42px;font-weight:bold;opacity:.16;pointer-events:none}
h1{font-size:28px;letter-spacing:.2px;margin:0 0 8px;color:#fff}
.subtitle{margin:0;color:#fff4e8;font-size:15px;line-height:1.4}
.status{display:inline-block;margin-top:15px;padding:5px 12px;border-radius:999px;background:#ffffff26;color:#fff;font-size:11px;font-weight:bold;letter-spacing:0.3px}
.chat{flex:1;min-height:360px;padding:28px 38px 18px;background:#fffdfb;overflow-y:auto}
.bot,.user{max-width:76%;padding:14px 17px;border-radius:17px;margin:16px 0;line-height:1.5;white-space:pre-wrap;box-shadow:0 4px 12px #4b24100d;word-break:break-word}
.bot{background:#fff4e8;border:1px solid #f4d2b0;color:#55351f;margin-right:auto;border-bottom-left-radius:5px}
.user{background:linear-gradient(135deg,#f58b27,#df6509);color:#fff;margin-left:auto;border-bottom-right-radius:5px}
.meta{font-size:11px;color:#8a6a58;margin-top:7px}
.user .meta{color:#fff0e2}
.suggestions{padding:18px 38px 24px;background:#fff8f0;border-top:1px solid #f3dfcc}
.suggestions-title{font-size:12px;font-weight:bold;color:#8a6a58;margin-bottom:12px}
.suggestion-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.suggestion{padding:13px 15px;border:1px solid #f1c79f;border-radius:12px;background:#fff;color:#9a4b12;text-align:left;cursor:pointer;box-shadow:0 3px 8px #b85b1d10;transition:transform .15s,background .15s,border-color .15s;font-size:13.5px}
.suggestion:hover:not(:disabled){background:#fff0e2;border-color:#e87511;transform:translateY(-1px)}
.suggestion:disabled{opacity:0.6;cursor:not-allowed}
.composer{display:flex;align-items:center;gap:14px;padding:20px 38px 28px;background:#fff8f0;border-top:1px solid #f3dfcc}
input{flex:1;min-width:0;padding:14px 16px;border:1px solid #e5b17d;border-radius:12px;background:#fff;font:inherit;outline:none;transition:border-color .15s,box-shadow .15s}
input:focus{border-color:#e87511;box-shadow:0 0 0 3px #e8751122}
button{padding:14px 24px;border:0;border-radius:12px;background:#e87511;color:white;font-weight:bold;cursor:pointer;box-shadow:0 5px 10px #c95d0533;transition:background .15s,transform .15s}
button:hover:not(:disabled){background:#c95d05;transform:translateY(-1px)}
button:disabled{opacity:0.6;cursor:not-allowed}

/* Messenger Typing Indicator */
.typing-bubble{display:inline-flex;align-items:center;gap:5px;padding:12px 18px;border-radius:18px;background:#fff4e8;border:1px solid #f4d2b0;border-bottom-left-radius:5px;box-shadow:0 4px 12px #4b24100d;margin:16px 0}
.typing-dot{width:7px;height:7px;border-radius:50%;background:#e87511;animation:typingBounce 1.3s infinite ease-in-out}
.typing-dot:nth-child(2){animation-delay:0.2s}
.typing-dot:nth-child(3){animation-delay:0.4s}
@keyframes typingBounce{
  0%,60%,100%{transform:translateY(0);opacity:0.35}
  30%{transform:translateY(-6px);opacity:1}
}

@media(max-width:600px){
  body{padding:0}
  .shell{min-height:100vh;border-radius:0;border-left:0;border-right:0}
  .topbar,.chat,.suggestions,.composer{padding-left:18px;padding-right:18px}
  .topbar:after{right:18px}
  .suggestion-grid{grid-template-columns:1fr}
  .bot,.user{max-width:88%}
}
</style>
</head>
<body>
<main class='shell'>
  <header class='topbar'>
    <h1>LibbyWIT</h1>
    <p class='subtitle'>Ask, Discover, Learn.</p>
    <div class='status'>● Online &bull; Powered by Ollama llama3</div>
  </header>
  <section id='chat' class='chat' aria-live='polite'>
    <div class='bot'>
      <b>LibbyWIT Assistant</b><br>
      Hello! How can I help you today? I can answer routine questions about library hours, borrowing, overdue items, library cards, catalog availability, and citation help.
      <div class='meta'>For account-specific or complex concerns, please contact library staff.</div>
    </div>
  </section>
  <section class='suggestions'>
    <div class='suggestions-title'>Try one of these questions:</div>
    <div class='suggestion-grid'>
      <button class='suggestion' data-question='What time does the library open?'>What time does the library open?</button>
      <button class='suggestion' data-question='Do you have books about artificial intelligence?'>Do you have books about artificial intelligence?</button>
      <button class='suggestion' data-question='How many books can I borrow?'>How many books can I borrow?</button>
      <button class='suggestion' data-question='How much is the overdue fine?'>How much is the overdue fine?</button>
    </div>
  </section>
  <form id='form' class='composer'>
    <input id='message' placeholder='Type your question here...' autocomplete='off' maxlength='500'>
    <button id='sendBtn' type='submit'>Send</button>
  </form>
</main>

<script>
const f = document.getElementById('form');
const m = document.getElementById('message');
const c = document.getElementById('chat');
const btn = document.getElementById('sendBtn');
const suggestionBtns = document.querySelectorAll('.suggestion');

let isGenerating = false;
const conversationHistory = [];

function showTyping(){
  const t = document.createElement('div');
  t.id = 'typing-indicator';
  t.className = 'typing-bubble';
  t.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  c.appendChild(t);
  c.scrollTop = c.scrollHeight;
}

function removeTyping(){
  const t = document.getElementById('typing-indicator');
  if(t) t.remove();
}

function typewrite(element, text, speed = 10){
  return new Promise(resolve => {
    let i = 0;
    function type(){
      if(i < text.length){
        element.textContent += text.charAt(i);
        i++;
        c.scrollTop = c.scrollHeight;
        setTimeout(type, speed);
      } else {
        resolve();
      }
    }
    type();
  });
}

function setControlsDisabled(disabled){
  isGenerating = disabled;
  btn.disabled = disabled;
  suggestionBtns.forEach(b => b.disabled = disabled);
}

async function ask(text){
  text = (text || '').trim();
  if(!text || isGenerating) return;
  setControlsDisabled(true);

  // Append user message bubble
  const userBubble = document.createElement('div');
  userBubble.className = 'user';
  userBubble.textContent = text;
  c.appendChild(userBubble);
  
  m.value = '';
  showTyping();

  const t = performance.now();
  try {
    const payload = {
      message: text,
      history: conversationHistory
    };

    const r = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });

    if(!r.ok) {
      throw new Error('Server returned HTTP ' + r.status);
    }

    const d = await r.json();
    const ms = (performance.now() - t).toFixed(1);
    
    removeTyping();

    // Create the bot response bubble
    const botBubble = document.createElement('div');
    botBubble.className = 'bot';
    
    const botLabel = document.createElement('b');
    botLabel.textContent = 'Library Assistant';
    botBubble.appendChild(botLabel);
    botBubble.appendChild(document.createElement('br'));
    
    const textSpan = document.createElement('span');
    textSpan.className = 'bot-text';
    botBubble.appendChild(textSpan);

    const metaDiv = document.createElement('div');
    metaDiv.className = 'meta';
    metaDiv.textContent = `Intent: ${d.intent} | confidence: ${d.confidence} | response: ${ms} ms`;
    botBubble.appendChild(metaDiv);

    c.appendChild(botBubble);
    
    // Type out the answer smoothly
    await typewrite(textSpan, d.answer);

    // Save turn to history
    conversationHistory.push({role: 'user', content: text});
    conversationHistory.push({role: 'assistant', content: d.answer});

  } catch(err) {
    removeTyping();
    const errBubble = document.createElement('div');
    errBubble.className = 'bot';
    errBubble.innerHTML = '<b>Library Assistant</b><br>Sorry, something went wrong while connecting to the assistant. Please make sure the local Ollama service is running, or visit the WIT Library circulation desk for help.<div class="meta">Error connecting to service</div>';
    c.appendChild(errBubble);
  } finally {
    setControlsDisabled(false);
    m.focus();
    c.scrollTop = c.scrollHeight;
  }
}

f.addEventListener('submit', e => {
  e.preventDefault();
  ask(m.value);
});

suggestionBtns.forEach(b => {
  b.addEventListener('click', () => ask(b.dataset.question));
});
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean custom logging
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/chat":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        message = ""
        history = None

        # Parse either application/json or application/x-www-form-urlencoded
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                data = json.loads(raw_body)
                message = data.get("message", "")
                history = data.get("history", [])
            except Exception:
                message = ""
        else:
            parsed_form = parse_qs(raw_body)
            message = parsed_form.get("message", [""])[0]

        start_time = time.perf_counter()
        result = classify(message, history=history, use_llm=True)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 3)
        result["server_ms"] = elapsed_ms

        response_bytes = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

def run_server(host=config.SERVER_HOST, port=config.SERVER_PORT):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, Handler)
    print(f"WIT Library Chatbot running at http://{host}:{port}")
    print(f"Ollama connected to {config.OLLAMA_BASE_URL} (Model: {config.OLLAMA_MODEL})")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()