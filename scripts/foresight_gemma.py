"""Foresight writer (`reports/prereg/2026-11-09-reqclass2-foresight.md`): Gemma 4 31B predicts, from the issue alone, the
behaviours the hidden tests will check.

    .venv-harness/bin/python scripts/foresight_gemma.py research/reqclass/issue_only research/reqclass/foresight_gemma.json

Temperature 0.2, thinking on. Resumes.
"""
import json, os, re, sys
import httpx

PK, OUT = sys.argv[1], sys.argv[2]
URL = "http://127.0.0.1:8000/v1/chat/completions"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
RUBRIC = """Below is a GitHub issue for a Python repository. A developer will fix it, and hidden tests (written by the developer who fixed it) will then check the fix. You cannot see the tests or the fix.

Predict the distinct behaviours the hidden tests most likely check: at most 8, most likely first, each concrete (inputs and expected outputs, names, error types, messages where you can predict them).

Answer with JSON only, no prose: [{"req": "<= 30 words"}, ...]

"""


def rate(text):
    for attempt in range(3):
        r = httpx.post(URL, timeout=900, json={
            "model": MODEL, "temperature": 0.2, "max_tokens": 8192,
            "messages": [{"role": "user", "content": RUBRIC + text}],
            "chat_template_kwargs": {"enable_thinking": True}}).json()
        c = r["choices"][0]["message"]["content"] or ""
        m = re.search(r"\[.*\]", c, re.S)
        if m:
            try:
                reqs = json.loads(m.group(0))
                if reqs and all(isinstance(x, dict) and x.get("req") for x in reqs):
                    return reqs[:8]
            except json.JSONDecodeError:
                pass
    return None


def main():
    ids = json.load(open(f"{PK}/ids.json"))
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for t in ids:
        if t in out:
            continue
        reqs = rate(open(f"{PK}/{t}.md").read())
        if reqs is None:
            print("no valid answer", t, flush=True)
            continue
        out[t] = reqs
        json.dump(out, open(OUT, "w"), indent=1)
        print(t, len(reqs), flush=True)
    print("rated", len(out), "of", len(ids))


if __name__ == "__main__":
    main()
