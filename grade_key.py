"""Protocol primary score: grade one tool's notes on one meeting against the researchers' answer key. No tool names in prompts."""
import json, os, random, sys, textwrap
HERE=os.path.dirname(os.path.abspath(__file__))
TOOLS=['fireflies','granola','otter','scribbl']
BRANDS=['scribbl','granola','fireflies','otter','askfred']
SCHEMA={"type":"object","properties":{
 "items":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"verdict":{"type":"string","enum":["correct","partial","missed","wrong"]},"evidence":{"type":"string"}},"required":["id","verdict","evidence"]}},
 "errors":{"type":"array","items":{"type":"object","properties":{"claim":{"type":"string"},"why_wrong":{"type":"string"},
   "kind":{"type":"string","enum":["wrong_fact","wrong_person","invented_action_item","other_invented","decision_described_wrongly"]}},"required":["claim","why_wrong","kind"]}},
 "judge_model":{"type":"string"}},"required":["items","errors","judge_model"]}
def build(mid, tool):
    tr=open(f'{HERE}/meetings/{mid}/reference-transcript.txt').read()
    key=json.load(open(f'{HERE}/meetings/{mid}/answer-key.json'))
    notes=open(f'{HERE}/notes/{mid}/{tool}.md').read()
    p=f"""You are grading one set of AI-written meeting notes against an answer key.

Below is the reference transcript of a meeting (speaker roles or letters are labeled; names may come up in conversation), then the notes to grade, then the answer key. The answer key is the notes the researchers who recorded the meeting wrote by hand. The notes to grade were written by an AI note-taking tool from the recording; which tool does not matter.

The transcript is the final authority. If it shows an answer-key point is not quite what happened, grade the notes against what the transcript shows and say so in the evidence.

<transcript>
{tr}</transcript>

<notes>
{notes}</notes>

<answer_key>
""" + "\n".join(f"{i['id']} ({i['section']}): {i['item']}" for i in key) + """
</answer_key>

For every answer-key item give a verdict:
- correct: the notes state it, accurately.
- partial: the notes state part of it, or state it vaguely or without a key detail (for example who will do it).
- missed: the notes do not state it.
- wrong: the notes state something that contradicts it.
Give short evidence: quote the notes, or say what is missing.

Then list every statement in the notes that is wrong or unsupported by the transcript, with a kind:
- wrong_fact: a number, date or detail is wrong
- wrong_person: the wrong speaker, or the wrong owner of a task
- invented_action_item: a task nobody agreed to
- other_invented: something else that did not happen
- decision_described_wrongly: a decision described differently from how it happened (for example "the team agreed" when one person decided over objections)
Only list real errors. A slightly different spelling of the same person's name is not an error. An empty list is fine.

Add a field "judge_model" with the exact name of the model you are running as.

Respond with JSON only, matching this schema:
""" + json.dumps(SCHEMA)
    import re
    for b in BRANDS: assert not re.search(r'\b'+b+r'\b', p.lower()), (mid,tool,b)
    return "\n".join(textwrap.fill(l,1200,break_long_words=False,replace_whitespace=False) if len(l)>1200 else l for l in p.split("\n"))
def make(mid, judges):
    pdir=f'{HERE}/grading/prompts'; os.makedirs(pdir,exist_ok=True); os.makedirs(f'{HERE}/grading/out',exist_ok=True)
    mp=f'{HERE}/grading/manifest.json'; man=json.load(open(mp)) if os.path.exists(mp) else {}
    made=[]; rng=random.Random()
    for j in judges:
        for t in TOOLS:
            if any(m['meeting']==mid and m['tool']==t and m['judge']==j for m in man.values()): continue
            pid='g%06x'%rng.getrandbits(24)
            open(f'{pdir}/{pid}.txt','w').write(build(mid,t)); man[pid]={'meeting':mid,'tool':t,'judge':j}; made.append((pid,j))
    json.dump(man,open(mp,'w'),indent=1); return made
if __name__=='__main__':
    for pid,j in make(sys.argv[1], sys.argv[2:]): print(pid,j)
