import aiohttp, json, time, sys
from aiohttp import web
UP="https://openai.bothub.chat/v1"
LOG=open(sys.argv[2] if len(sys.argv)>2 else "proxy_log.jsonl","a")
async def handle(req):
    path=req.match_info["p"]; body=await req.read(); t0=time.time()
    hdr={"Authorization":req.headers.get("Authorization",""),"Content-Type":"application/json"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300),trust_env=True) as s:
        async with s.request(req.method,f"{UP}/{path}",data=body or None,headers=hdr,params=req.query) as r:
            ct=r.headers.get("Content-Type","")
            if "event-stream" in ct:
                resp=web.StreamResponse(status=r.status,headers={"Content-Type":ct}); await resp.prepare(req)
                chunks=[]
                async for line in r.content:
                    chunks.append(line.decode("utf-8","replace")); await resp.write(line)
                await resp.write_eof(); out="".join(chunks)
            else:
                out=await r.text(); resp=web.Response(status=r.status,text=out,content_type=ct.split(";")[0] or "application/json")
    rec={"t":t0,"dur":time.time()-t0,"path":path,"status":r.status,"key":hdr["Authorization"][-6:]}
    try: rec["req"]=json.loads(body) if body else None
    except: rec["req"]=body.decode()[:2000]
    rec["resp"]=out if path!="models" else out[:200]
    LOG.write(json.dumps(rec,ensure_ascii=False)+"\n"); LOG.flush()
    return resp
app=web.Application(client_max_size=50*2**20); app.router.add_route("*","/v1/{p:.*}",handle)
web.run_app(app,host="127.0.0.1",port=int(sys.argv[1]) if len(sys.argv)>1 else 9000,print=None)
