"""Rater 2 for the requirement classification (`reports/prereg/2026-11-08-reqclass.md`): Gemma 4 31B on the local vLLM.

    .venv-harness/bin/python scripts/rate_reqs_gemma.py research/reqclass/packets research/reqclass/rater_gemma.json

Same rubric as the Claude rater, temperature 0.2, thinking on. Resumes: tasks already in the output are skipped.
"""
import json, os, re, sys
import httpx

PK, OUT = sys.argv[1], sys.argv[2]
URL = "http://127.0.0.1:8000/v1/chat/completions"
MODEL = "gemma-4-31b-it-qat-w4a16-ct"
RUBRIC = """You are a blind rater for a research study. Below are a GitHub issue (the only thing a coding agent is given) and the test patch that the hidden tests apply.

List the distinct behavioural requirements the new or changed tests impose (one per distinct checked behaviour, at most 8, merge trivially repeated cases) and classify each:
- I: stated or directly implied by the issue text;
- R: not in the issue, but a competent developer would infer it from the issue plus the repository's existing code, docs or conventions;
- C: a defensible choice among reasonable alternatives that the issue leaves open (another reasonable developer could have chosen differently);
- A: arbitrary or incidental: exact wording of a message, a new name or signature not in the issue and not dictated by existing code, a test-only artefact.
Be calibrated and strict: if the issue does not say it and the repository would not dictate it, it is not I or R.

Answer with JSON only, no prose: [{"req": "<= 25 words", "class": "I|R|C|A", "why": "<= 20 words"}, ...]

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
                if all(x.get("class") in ("I", "R", "C", "A") for x in reqs) and reqs:
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
