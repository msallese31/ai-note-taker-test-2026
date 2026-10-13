"""Protocol secondary score: blind side-by-side judging (v1-objective criteria, unchanged) for meetings 2-5."""
import json, os, random, re, sys, textwrap, urllib.request
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'judge'))
import judge as J
H = os.path.dirname(os.path.abspath(__file__))
TOOLS = ['fireflies', 'granola', 'otter', 'scribbl']
D = f'{H}/sidebyside'; os.makedirs(f'{D}/prompts', exist_ok=True); os.makedirs(f'{D}/out', exist_ok=True)
MP = f'{D}/manifest.json'
PRE = """You are an expert evaluator of meeting notes.

Below is the reference transcript of a meeting with four participants (their roles or speaker letters are labeled; names may come up in the conversation). After it are four sets of meeting notes, labeled A, B, C and D. Each was written by a different AI note-taking tool from the same recording. You do not know which tools wrote them, and that does not matter: judge only what is on the page.

The transcript is the final authority on what was said, decided and assigned. Read it carefully before judging, and check the notes' claims against it.
"""
def build(mid, order):
    v = J.VERSIONS['v1-objective']
    crit = "\n".join(f"- {n} (weight {w}%): {d}" for n, w, d in v['criteria'])
    tr = open(f'{H}/meetings/{mid}/reference-transcript.txt').read()
    parts = [PRE, "<transcript>\n" + tr + "</transcript>\n"]
    for L, t in zip(J.LETTERS, order):
        parts.append(f'<notes label="{L}">\n' + open(f'{H}/notes/{mid}/{t}.md').read() + "</notes>\n")
    parts += ["Criteria:\n" + crit + "\n", J.COMMON_TAIL, "Respond with JSON only, matching this schema:\n" + json.dumps(J.SCHEMA)]
    p = "\n".join(parts)
    for b in ['scribbl', 'granola', 'fireflies', 'otter', 'askfred']:
        assert not re.search(r'\b' + b + r'\b', p.lower()), (mid, b)
    p = "\n".join(textwrap.fill(l, 1200, break_long_words=False, replace_whitespace=False) if len(l) > 1200 else l for l in p.split("\n"))
    return p + '\n\nAlso add a top-level field "judge_model" with the exact name of the model you are running as.\n'
def make(meetings, judges):
    man = json.load(open(MP)) if os.path.exists(MP) else {}; rng = random.Random(); made = []
    for mid in meetings:
        for j in judges:
            for rot in range(4):
                if any(m['meeting'] == mid and m['judge'] == j and m['rotation'] == rot for m in man.values()): continue
                order = TOOLS[rot:] + TOOLS[:rot]; pid = 's%06x' % rng.getrandbits(24)
                open(f'{D}/prompts/{pid}.txt', 'w').write(build(mid, order))
                man[pid] = {'meeting': mid, 'judge': j, 'rotation': rot, 'mapping': dict(zip(J.LETTERS, order))}; made.append((pid, j))
    json.dump(man, open(MP, 'w'), indent=1); return made
def run_gpt():
    man = json.load(open(MP))
    todo = [p for p, m in man.items() if m['judge'].startswith('gpt') and not os.path.exists(f'{D}/out/{p}.json')]
    def go(p):
        body = {"model": "gpt-6.1-sol", "messages": [{"role": "user", "content": open(f'{D}/prompts/{p}.txt').read()}], "response_format": {"type": "json_object"}, "reasoning_effort": "high"}
        req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["OPENAI_KEY"]})
        d = json.load(urllib.request.urlopen(req, timeout=900)); r = json.loads(d['choices'][0]['message']['content']); r['judge_model_served'] = d.get('model')
        json.dump(r, open(f'{D}/out/{p}.json', 'w'), indent=1); return p
    with ThreadPoolExecutor(8) as ex:
        for p in ex.map(go, todo): pass
    print('gpt done', len(todo))
if __name__ == '__main__':
    if sys.argv[1] == 'make':
        for pid, j in make(['IB4003', 'ES2008b', 'IS1001c', 'TS3012a'], ['opus', 'fable', 'sonnet', 'gpt-6.1-sol']):
            if j != 'gpt-6.1-sol': print(pid, j)
    elif sys.argv[1] == 'gpt': run_gpt()
