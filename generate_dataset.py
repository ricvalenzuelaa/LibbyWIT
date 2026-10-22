import json, csv, requests, os

# Automatically use installed model ("llama3:latest" or "llama3.1" if available)
MODEL = os.getenv("OLLAMA_MODEL", "llama3:latest")

intents = {
    "book_availability": "Student asks whether a specific book is available or checked out.",
    "operating_hours": "Student asks when the library opens, closes, or is open on certain days.",
    "library_card_lost": "Student lost, damaged, or forgot their library card.",
    "overdue_fines": "Student asks about penalties or payment for late books.",
    "citation_apa": "Student asks how to cite sources in APA format.",
    "borrowing_rules": "Student asks how many books they can borrow or for how long.",
}

PROMPT = """You are helping build a training dataset for an intent-based library chatbot.
Generate 30 different questions a student might type for this intent.

Intent: {tag}
Description: {desc}

Rules:
- Write like real students type: casual, short, sometimes with typos.
- Mix English and Filipino/Taglish (about 20% Taglish).
- Vary sentence structure and length.
- Do not answer the questions.
- Output only a JSON array of strings, nothing else."""

rows = set()
for tag, desc in intents.items():
    print(f"Generating questions for intent: {tag}...")
    for run in range(3):  # 3 runs per intent
        try:
            r = requests.post("http://localhost:11434/api/generate", json={
                "model": MODEL,
                "prompt": PROMPT.format(tag=tag, desc=desc),
                "format": "json",
                "stream": False,
            }, timeout=60)
            data = json.loads(r.json()["response"])
            if isinstance(data, dict):
                data = next(iter(data.values()))
            for q in data:
                if isinstance(q, str):
                    rows.add((q.strip(), tag))
        except Exception as e:
            print(f"Skipped a bad batch for {tag} (run {run+1}):", e)

out_file = "generated_intents.csv"
with open(out_file, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["text", "intent"])
    w.writerows(sorted(rows))

print(f"\nDone! {len(rows)} unique questions saved to {out_file}")
