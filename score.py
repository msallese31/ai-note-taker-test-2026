"""Recompute every protocol number from the raw grader outputs (grading/out) and write RESULTS.md."""
import json, os, re, statistics as st
from collections import defaultdict
H = os.path.dirname(os.path.abspath(__file__))
TOOLS = ['fireflies', 'granola', 'otter', 'scribbl']
NAME = {'fireflies': 'Fireflies', 'granola': 'Granola', 'otter': 'Otter', 'scribbl': 'Scribbl'}
KINDS = ['wrong_fact', 'wrong_person', 'invented_action_item', 'other_invented', 'decision_described_wrongly']
PTS = {'correct': 1, 'partial': 0.5}

def load(p):
    t = open(p).read().strip(); t = re.sub(r'^```(json)?|```$', '', t).strip(); return json.loads(t)

man = json.load(open(f'{H}/grading/manifest.json'))
PROV = {m['meeting'] for m in man.values() if m['tool'] == 'scribbl-corrected'}  # see PROTOCOL.md deviations
score = defaultdict(dict)   # (meeting, tool) -> judge -> fraction
errs = defaultdict(lambda: defaultdict(list))  # (meeting, tool) -> judge -> errors
for pid, m in man.items():
    p = f'{H}/grading/out/{pid}.json'
    if not os.path.exists(p): continue
    if m['tool'] == 'scribbl' and m['meeting'] in PROV: continue
    if m['tool'] == 'scribbl-corrected': m = dict(m, tool='scribbl')
    r = load(p); n = len(json.load(open(f"{H}/meetings/{m['meeting']}/answer-key.json")))
    score[(m['meeting'], m['tool'])][m['judge']] = sum(PTS.get(i['verdict'], 0) for i in r['items']) / n
    errs[(m['meeting'], m['tool'])][m['judge']] = r['errors']

meetings = [x for x in ['IS1008d', 'IB4003', 'ES2008b', 'IS1001c', 'TS3012a'] if any(k[0] == x for k in score)]
L = ['# Results (recomputed by score.py from grading/out)', '', '## Answer-key score per meeting (share of the researchers\' points, averaged across graders)', '',
     '| Meeting | ' + ' | '.join(NAME[t] for t in TOOLS) + ' | Graders |', '|---|' + '---|' * (len(TOOLS) + 1)]
overall = defaultdict(list)
for mt in meetings:
    row = []
    for t in TOOLS:
        v = score.get((mt, t), {})
        if v: m_ = st.mean(v.values()); overall[t].append(m_); row.append(f'{m_*100:.0f}%')
        else: row.append('-')
    gs = sorted({j for t in TOOLS for j in score.get((mt, t), {})})
    L.append(f'| {mt} | ' + ' | '.join(row) + f' | {", ".join(gs)} |')
L.append('| **Average** | ' + ' | '.join(f'**{st.mean(overall[t])*100:.0f}%**' if overall[t] else '-' for t in TOOLS) + ' | |')
L += ['', '## Error counts (summed across meetings, averaged across graders)', '', '| Kind | ' + ' | '.join(NAME[t] for t in TOOLS) + ' |', '|---|' + '---|' * len(TOOLS)]
for k in KINDS + ['total']:
    row = []
    for t in TOOLS:
        tot = 0
        for mt in meetings:
            per = [sum(1 for e in es if k == 'total' or e['kind'] == k) for es in errs[(mt, t)].values()]
            tot += st.mean(per) if per else 0
        row.append(f'{tot:.1f}')
    L.append(f'| {k} | ' + ' | '.join(row) + ' |')
L += ['', '## Every error each grader listed', '']
for mt in meetings:
    for t in TOOLS:
        for j, es in sorted(errs[(mt, t)].items()):
            L.append(f'**{mt}, {NAME[t]}, {j}:** ' + ('none' if not es else ''))
            for e in es: L.append(f"- [{e['kind']}] {e['claim']} -- {e['why_wrong']}")
open(f'{H}/RESULTS.md', 'w').write('\n'.join(L) + '\n')
print('\n'.join(L[:20 + len(KINDS)]))
