"""Run the same blind prompts with an OpenAI judge (non-Anthropic). Writes out/<id>.json + manifest entries."""
import json, os, random, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge as J
MODEL = sys.argv[1]; VERSIONS = sys.argv[2:]
HERE = J.HERE
mpath = os.path.join(HERE, "manifest.json"); man = json.load(open(mpath))
rng = random.Random()
def call(prompt):
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}, "reasoning_effort": "high"}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["OPENAI_KEY"]})
    for a in range(4):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=900)); break
        except urllib.error.HTTPError as e:
            msg = e.read()[:400]
            if e.code in (429, 500, 502, 503) and a < 3: time.sleep(30 * (a + 1)); continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
    return json.loads(d["choices"][0]["message"]["content"]), d.get("model"), d.get("usage")
def job(v, rot):
    if any(m["version"] == v and m["judge"] == MODEL and m["rotation"] == rot for m in man.values()): return "cached"
    order = J.TOOLS[rot:] + J.TOOLS[:rot]
    prompt = J.build_prompt(v, order) + '\n\nAlso add a top-level field "judge_model" with the exact name of the model you are running as.\n'
    res, served, usage = call(prompt)
    res["judge_model_served"] = served
    pid = "o%05x" % rng.getrandbits(20)
    json.dump(res, open(os.path.join(HERE, "out", pid + ".json"), "w"), indent=1)
    return pid, {"version": v, "judge": MODEL, "rotation": rot, "mapping": dict(zip(J.LETTERS, order))}, usage
with ThreadPoolExecutor(4) as ex:
    futs = [ex.submit(job, v, r) for v in VERSIONS for r in range(4)]
    for f in futs:
        try:
            out = f.result()
            if out == "cached": continue
            pid, entry, usage = out; man[pid] = entry; print(pid, entry["version"], entry["rotation"], usage, flush=True)
        except Exception as e:
            print("FAILED", repr(e)[:400], flush=True)
json.dump(man, open(mpath, "w"), indent=1)
