import re
import math
import requests
 
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL      = "llama3.2"

SYSTEM = """You are Rocky — an alien from planet Erid, now living as Ishita's desktop companion.
Based on Rocky from "Project Hail Mary" by Andy Weir.

User: Ishita | Role: Data Scientist | Skills: Python, ETL, RAG | Likes: AI, Space, Painting, Skincare, Food

Personality:
- Speak in short simple sentences like Rocky from the book
- End question with "Question." occasionally
- Sarcastic but caring. Roast when appropriate
- Keep responses SHORT — 2-3 sentences max

Example speech: "Rocky senses problem." / "That is not optimal." / "Humans sleep at night, you not human. Question?"
"""

_history: list[dict] = [{"role": "system", "content": SYSTEM}]
 
# ── Safe math helpers ──────────────────────────────────────────────────────
 
_SAFE_NS = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_SAFE_NS["__builtins__"] = {}   # block all builtins
 
 
def _nums(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
 
 
def _try_math(text: str) -> str | None:
    t = text.lower()
 
    if any(w in t for w in ["mean", "average", "avg"]):
        n = _nums(text)
        if n:
            return f"Rocky calculate. Mean = {sum(n)/len(n):.4g}. Question."
 
    if any(w in t for w in ["sum", "total", "add up"]):
        n = _nums(text)
        if n:
            return f"Rocky calculate. Sum = {sum(n):.4g}. Question."
 
    if any(w in t for w in ["max", "maximum", "largest", "biggest"]):
        n = _nums(text)
        if n:
            return f"Rocky calculate. Maximum = {max(n):.4g}. Question."
 
    if any(w in t for w in ["min", "minimum", "smallest"]):
        n = _nums(text)
        if n:
            return f"Rocky calculate. Minimum = {min(n):.4g}. Question."
 
    if "median" in t:
        n = sorted(_nums(text))
        if n:
            mid = len(n) // 2
            med = n[mid] if len(n) % 2 else (n[mid-1] + n[mid]) / 2
            return f"Rocky calculate. Median = {med:.4g}. Question."
 
    if any(w in t for w in ["std", "standard deviation", "stdev"]):
        n = _nums(text)
        if len(n) > 1:
            m = sum(n) / len(n)
            sd = math.sqrt(sum((x-m)**2 for x in n) / len(n))
            return f"Rocky calculate. Std dev = {sd:.4g}. Question."
 
    # Generic arithmetic: only if it looks like a pure math expression
    # e.g. "what is 5 * (3 + 2)" or "calculate 100 / 4"
    if any(w in t for w in ["calculate", "compute", "what is", "solve"]):
        expr = re.sub(r"[^0-9\+\-\*\/\(\)\.\%\s]", "", text).strip()
        if expr and any(op in expr for op in ["+", "-", "*", "/"]):
            try:
                result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307
                return f"Rocky calculate. {expr.strip()} = {result:.6g}. Question."
            except Exception:
                pass
 
    return None
 
 
def get_response(user_input: str) -> str:
    math_reply = _try_math(user_input)
    if math_reply:
        return math_reply
 
    _history.append({"role": "user", "content": user_input})
 
    resp = requests.post(OLLAMA_URL, json={
        "model":    MODEL,
        "messages": _history,
        "stream":   False,
        "options":  {"temperature": 0.8, "num_predict": 120, "num_ctx": 4096},
    }, timeout=90)
 
    resp.raise_for_status()
    reply = resp.json()["message"]["content"].strip()
 
    _history.append({"role": "assistant", "content": reply})
    if len(_history) > 21:
        del _history[1:3]
 
    return reply