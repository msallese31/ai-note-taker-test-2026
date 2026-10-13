"""Build the reference transcript and the researchers' answer key for one AMI meeting from the corpus files."""
import re, sys, json, os, xml.etree.ElementTree as ET
SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)),'ami-source')
ROLE={'PM':'Project Manager','ID':'Industrial Designer','UI':'User Interface Designer','ME':'Marketing Expert'}
def roles(mid):
    r=ET.parse(f'{SRC}/meetings.xml').getroot()
    for m in r.iter():
        if m.tag.endswith('meeting') and m.get('observation')==mid:
            return {sp.get('nxt_agent'): ROLE.get(sp.get('role')) or f"Speaker {sp.get('nxt_agent')}" for sp in m}
def transcript(mid):
    rl=roles(mid); segs=[]
    for spk in sorted(rl):
        wp=f'{SRC}/{mid}.{spk}.words.xml'
        if not os.path.exists(wp): continue
        order=[];words={}
        for w in ET.parse(wp).getroot():
            wid=w.get('{http://nite.sourceforge.net/}id'); order.append(wid); words[wid]=w
        idx={w:i for i,w in enumerate(order)}
        for seg in ET.parse(f'{SRC}/{mid}.{spk}.segments.xml').getroot():
            st=float(seg.get('transcriber_start'))
            for ch in seg:
                m=re.search(r'id\(([^)]+)\)(?:\.\.id\(([^)]+)\))?',ch.get('href'))
                a,b=m.group(1),m.group(2) or m.group(1); toks=[]
                for wid in order[idx[a]:idx[b]+1]:
                    w=words[wid]
                    if w.tag.split('}')[-1]=='w' and w.text:
                        t=w.text.replace('_','')
                        if w.get('punc')=='true' and toks: toks[-1]+=t
                        else: toks.append(t)
                txt=' '.join(toks).strip()
                if txt: segs.append((st,spk,txt))
    segs.sort(); out=[]; cur=None
    for st,spk,txt in segs:
        if cur and cur[1]==spk: cur[2]+=' '+txt
        else:
            if cur: out.append(cur)
            cur=[st,spk,txt]
    out.append(cur)
    return '\n'.join(f"[{int(st//60):02d}:{int(st%60):02d}] {rl[s]}: {t}" for st,s,t in out)+'\n'
def answer_key(mid):
    r=ET.parse(f'{SRC}/{mid}.abssumm.xml').getroot(); items=[]
    pre={'abstract':'S','actions':'A','decisions':'D','problems':'P'}
    for sec in r:
        tag=sec.tag.split('}')[-1]; n=0
        for s in sec.iter():
            if s.tag.endswith('sentence') and s.text and s.text.strip() not in ('NA.','NA','N/A'):
                n+=1; items.append({'id':f'{pre[tag]}{n}','section':tag,'item':s.text.strip()})
    return items
if __name__=='__main__':
    for mid in sys.argv[1:]:
        d=os.path.join(os.path.dirname(os.path.abspath(__file__)),'meetings',mid); os.makedirs(d,exist_ok=True)
        open(f'{d}/reference-transcript.txt','w').write(transcript(mid))
        k=answer_key(mid); json.dump(k,open(f'{d}/answer-key.json','w'),indent=1)
        print(mid, len(k),'key items', {s:sum(1 for i in k if i['section']==s) for s in ('abstract','actions','decisions','problems')}, len(open(f'{d}/reference-transcript.txt').read()),'chars')
