"""Blind judging of four AI note takers' notes for AMI meeting IS1008d.

Each judge sees the reference transcript and four sets of notes labeled A-D.
Tool names never appear in the prompt. The criteria version used is v1-objective. It runs 4 times per judge,
rotating which tool sits in which slot, so every tool appears once in every
position (controls for position bias).

Usage: .venv/bin/python judge/judge.py <version_id> [<version_id> ...]
       .venv/bin/python judge/judge.py --check <version_id>   (print one prompt, no calls)
"""
import json, os, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = ["scribbl", "granola", "fireflies", "otter"]
LETTERS = ["A", "B", "C", "D"]
BRANDS = re.compile(r"\b(scribbl|granola|fireflies|otter|askfred)\b", re.I)

JUDGES = {
    "claude-opus-5-5": "anthropic",
    "gemini-3.1-pro-preview": "gemini",
}

TRANSCRIPT = open(os.path.join(HERE, "reference-transcript.txt")).read()
NOTES = {t: open(os.path.join(ROOT, "notes", "IS1008d", f"{t}.md")).read() for t in TOOLS}  # meeting 1 notes (moved 2026-10-13)
REFERENCE_NOTES = ""  # not used by v1-objective

PREAMBLE = """You are an expert evaluator of meeting notes.

Below is the reference transcript of a 24-minute product design meeting with four participants (their roles are labeled; names come up in the conversation). After it are four sets of meeting notes, labeled A, B, C and D. Each was written by a different AI note-taking tool from the same recording. You do not know which tools wrote them, and that does not matter: judge only what is on the page.

The transcript is the final authority on what was said, decided and assigned. Read it carefully before judging, and check the notes' claims against it.
"""

COMMON_TAIL = """
Score each set of notes from 1 to 10 on every criterion (10 = excellent). Give an overall score from 1 to 10 that reflects the criteria and weights above, and rank all four from best to worst (no ties). For each set, list specific factual errors or unsupported claims you found (quote or closely paraphrase them; an empty list if none), and its main strengths and weaknesses. Be concrete and consistent across the four.
"""

VERSIONS = {
    "v1-objective": {
        "title": "Objective, general criteria (equal weights)",
        "reference": False,
        "criteria": [
            ("accuracy", 25, "Every statement is supported by the transcript: numbers, names, who said what, what was decided. Errors, wrong attributions and invented content lower this score."),
            ("completeness", 25, "Covers what matters: decisions, action items or next steps, key numbers, open issues and disagreements."),
            ("decisions_and_actions", 25, "States correctly what was decided, what was left open, and who will do what."),
            ("usefulness", 25, "Someone who missed the meeting could understand it and act on it from these notes alone."),
        ],
        "extra": "",
    },
}

SCHEMA = {
    "type": "object",
    "properties": {
        "evaluations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": LETTERS},
                    "criterion_scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"criterion": {"type": "string"}, "score": {"type": "integer"}},
                            "required": ["criterion", "score"],
                            "additionalProperties": False,
                        },
                    },
                    "overall": {"type": "number"},
                    "errors": {"type": "array", "items": {"type": "string"}},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["label", "criterion_scores", "overall", "errors", "strengths", "weaknesses"],
                "additionalProperties": False,
            },
        },
        "ranking": {"type": "array", "items": {"type": "string", "enum": LETTERS}},
        "rationale": {"type": "string"},
    },
    "required": ["evaluations", "ranking", "rationale"],
    "additionalProperties": False,
}


def build_prompt(version, order):
    v = VERSIONS[version]
    crit = "\n".join(f"- {name} (weight {w}%): {desc}" for name, w, desc in v["criteria"])
    parts = [PREAMBLE, "<transcript>\n" + TRANSCRIPT + "</transcript>\n"]
    if v["reference"]:
        parts.append(
            "The researchers who recorded this meeting also wrote short reference notes by hand. Use them as a guide to what mattered; the transcript stays the final authority if they differ.\n<reference_notes>\n"
            + REFERENCE_NOTES + "</reference_notes>\n")
    for letter, tool in zip(LETTERS, order):
        parts.append(f"<notes label=\"{letter}\">\n{NOTES[tool]}</notes>\n")
    parts.append("Criteria:\n" + crit + "\n")
    if v["extra"]:
        parts.append(v["extra"] + "\n")
    parts.append(COMMON_TAIL)
    parts.append("Respond with JSON only, matching this schema:\n" + json.dumps(SCHEMA))
    prompt = "\n".join(parts)
    leaks = BRANDS.findall(prompt)
    assert not leaks, f"tool name leaked into prompt: {set(leaks)}"
    return prompt


def call_anthropic(model, prompt):
    import anthropic
    client = anthropic.Anthropic()
    schema = dict(SCHEMA)
    with client.messages.stream(
        model=model,
        max_tokens=64000,
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason != "end_turn":
        raise RuntimeError(f"stop_reason={msg.stop_reason}")
    text = next(b.text for b in msg.content if b.type == "text")
    return json.loads(text), {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}


def call_gemini(model, prompt):
    key = os.environ["GEMINI_API_KEY"]
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseJsonSchema": SCHEMA},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    for attempt in range(4):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=600))
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 503) and attempt < 3:
                time.sleep(20 * (attempt + 1)); continue
            raise RuntimeError(f"gemini HTTP {e.code}: {e.read()[:300]}")
    cand = d["candidates"][0]
    text = "".join(p.get("text", "") for p in cand["content"]["parts"] if not p.get("thought"))
    usage = d.get("usageMetadata", {})
    return json.loads(text), {"input_tokens": usage.get("promptTokenCount"), "output_tokens": usage.get("candidatesTokenCount")}


def run_one(version, judge, rot):
    order = TOOLS[rot:] + TOOLS[:rot]
    out_dir = os.path.join(HERE, "results", version)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{judge}_r{rot}.json")
    if os.path.exists(path):
        return path, "cached"
    prompt = build_prompt(version, order)
    fn = call_anthropic if JUDGES[judge] == "anthropic" else call_gemini
    t0 = time.time()
    result, usage = fn(judge, prompt)
    mapping = dict(zip(LETTERS, order))
    json.dump({"version": version, "judge": judge, "rotation": rot, "mapping": mapping,
               "seconds": round(time.time() - t0), "usage": usage, "result": result},
              open(path, "w"), indent=1)
    return path, "done"


def main():
    args = sys.argv[1:]
    if args and args[0] == "--check":
        print(build_prompt(args[1], TOOLS))
        return
    jobs = [(v, j, r) for v in args for j in JUDGES for r in range(4)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(run_one, *job): job for job in jobs}
        for f, job in futs.items():
            try:
                print(job, *f.result(), flush=True)
            except Exception as e:
                print(job, "FAILED", repr(e)[:400], flush=True)


if __name__ == "__main__":
    main()


def write_prompt_files(plan):
    """plan: list of (version, judge_label, rotation). Writes judge/prompts/<id>.txt and a manifest.
    Ids are random so file names reveal nothing about version, slot order or judge."""
    import random, textwrap
    pdir = os.path.join(HERE, "prompts"); os.makedirs(pdir, exist_ok=True)
    mpath = os.path.join(HERE, "manifest.json")
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    rng = random.Random()
    made = []
    for version, judge, rot in plan:
        if any(m["version"] == version and m["judge"] == judge and m["rotation"] == rot for m in manifest.values()):
            continue
        order = TOOLS[rot:] + TOOLS[:rot]
        pid = "%06x" % rng.getrandbits(24)
        prompt = build_prompt(version, order)
        wrapped = "\n".join(textwrap.fill(l, 1200, break_long_words=False, replace_whitespace=False) if len(l) > 1200 else l
                            for l in prompt.split("\n"))
        wrapped += '\n\nAlso add a top-level field "judge_model" to your JSON with the exact name of the model you are running as.\n'
        open(os.path.join(pdir, pid + ".txt"), "w").write(wrapped)
        manifest[pid] = {"version": version, "judge": judge, "rotation": rot, "mapping": dict(zip(LETTERS, order))}
        made.append((pid, version, judge, rot))
    json.dump(manifest, open(mpath, "w"), indent=1)
    return made
