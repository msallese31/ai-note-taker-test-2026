"""Recompute the side-by-side (secondary) results from sidebyside/out plus meeting 1's v1 runs."""
import json, os, re, statistics as st
from collections import defaultdict
H = os.path.dirname(os.path.abspath(__file__))
TOOLS = ['fireflies', 'granola', 'otter', 'scribbl']; NAME = {t: t.capitalize() for t in TOOLS}
def load(p):
    t = open(p).read().strip(); t = re.sub(r'^```(json)?|```$', '', t).strip(); return json.loads(t)
runs = defaultdict(list)
for pid, m in json.load(open(f'{H}/sidebyside/manifest.json')).items():
    p = f'{H}/sidebyside/out/{pid}.json'
    if os.path.exists(p): runs[m['meeting']].append((m, load(p)))
for pid, m in json.load(open(f'{H}/judge/manifest.json')).items():
    if m['version'] == 'v1-objective' and os.path.exists(f'{H}/judge/out/{pid}.json'):
        runs['IS1008d'].append((dict(m, meeting='IS1008d'), load(f'{H}/judge/out/{pid}.json')))
L = ['## Side-by-side blind judging (v1-objective criteria), first places and mean score', '', '| Meeting | Runs | ' + ' | '.join(NAME[t] for t in TOOLS) + ' |', '|---|---|' + '---|' * 4]
tot_first = defaultdict(int); tot_score = defaultdict(list); n = 0
for mt in ['IS1008d', 'IB4003', 'ES2008b', 'IS1001c', 'TS3012a']:
    rs = runs.get(mt, [])
    if not rs: continue
    first = defaultdict(int); sc = defaultdict(list)
    for m, r in rs:
        mp = m['mapping']; first[mp[r['ranking'][0]]] += 1
        for e in r['evaluations']: sc[mp[e['label']]].append(float(e['overall']))
    n += len(rs)
    for t in TOOLS: tot_first[t] += first[t]; tot_score[t] += sc[t]
    L.append(f'| {mt} | {len(rs)} | ' + ' | '.join(f'{first[t]} first, {st.mean(sc[t]):.1f}' for t in TOOLS) + ' |')
L.append(f'| **All** | {n} | ' + ' | '.join(f'**{tot_first[t]} first, {st.mean(tot_score[t]):.1f}**' for t in TOOLS) + ' |')
L.append('\nMeeting 1 (IS1008d) runs are from 2026-10-12, judged on Scribbl\'s notes as produced (before the name correction; see PROTOCOL.md, Deviations).')
open(f'{H}/RESULTS-sidebyside.md', 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
