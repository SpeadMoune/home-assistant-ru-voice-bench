import os, asyncio, json, requests, websockets
PORT=os.environ.get("HA_PORT","8123")
B="http://127.0.0.1:"+PORT
def access():
    if os.path.exists("llat.txt"): return open("llat.txt").read().strip()
    rt=open("refresh.txt").read().strip()
    return requests.post(B+"/auth/token",data={"grant_type":"refresh_token","refresh_token":rt,"client_id":B+"/"}).json()["access_token"]
class WS:
    async def __aenter__(self):
        self.ws=await websockets.connect("ws://127.0.0.1:"+PORT+"/api/websocket",max_size=2**26)
        await self.ws.recv(); await self.ws.send(json.dumps({"type":"auth","access_token":access()})); r=json.loads(await self.ws.recv()); assert r["type"]=="auth_ok",r
        self.i=0; return self
    async def __aexit__(self,*a): await self.ws.close()
    async def call(self,type,**kw):
        self.i+=1; await self.ws.send(json.dumps({"id":self.i,"type":type,**kw}))
        while True:
            r=json.loads(await self.ws.recv())
            if r.get("id")==self.i and r["type"]=="result":
                if not r["success"]: raise Exception(r)
                return r.get("result")
def rest(method,path,**kw):
    r=requests.request(method,B+path,headers={"Authorization":"Bearer "+access()},**kw); 
    try: return r.status_code, r.json()
    except: return r.status_code, r.text
