import json,os,urllib.request
from concurrent.futures import ThreadPoolExecutor
H=os.path.dirname(os.path.abspath(__file__))
man=json.load(open(f'{H}/grading/manifest.json'))
todo=[p for p,m in man.items() if m['judge'].startswith('gpt') and not os.path.exists(f'{H}/grading/out/{p}.json')]
def run(p):
    body={"model":"gpt-6.1-sol","messages":[{"role":"user","content":open(f'{H}/grading/prompts/{p}.txt').read()}],"response_format":{"type":"json_object"},"reasoning_effort":"high"}
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","Authorization":"Bearer "+os.environ["OPENAI_KEY"]})
    d=json.load(urllib.request.urlopen(req,timeout=900)); r=json.loads(d['choices'][0]['message']['content']); r['judge_model_served']=d.get('model')
    json.dump(r,open(f'{H}/grading/out/{p}.json','w'),indent=1); return p
with ThreadPoolExecutor(6) as ex:
    for p in ex.map(run,todo): print('done',p,man[p]['meeting'],man[p]['tool'])
