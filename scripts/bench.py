import json, time, sys, asyncio, re
from hal import *
PLOG=os.environ.get('PLOG','proxy_log.jsonl')

def svc(domain, service, data):
    c,r=rest("POST",f"/api/services/{domain}/{service}",json=data)
    if c!=200: print("svc fail",domain,service,c,r)
def states():
    c,s=rest("GET","/api/states"); return {x["entity_id"]:x for x in s}
KEYS=["brightness","temperature","current_position","volume_level","rgb_color","is_volume_muted","hvac_mode"]
def snap():
    S=states(); out={}
    from home import HOME
    for e in HOME:
        x=S[e]; out[e]={"state":x["state"],**{k:x["attributes"].get(k) for k in KEYS if k in x["attributes"]}}
        if e.startswith("vacuum"): out[e]={"state":"cleaning" if x["state"]=="cleaning" else "idle"}
        if e.startswith("todo"): out[e]={"state":"-"}
    out["_list"]=shop()
    return out
def shop():
    c,r=rest("POST","/api/services/todo/get_items?return_response",json={"entity_id":"todo.shopping_list"})
    try: return sorted(i["summary"] for i in r["service_response"]["todo.shopping_list"]["items"])
    except Exception as e: return ["ERR",str(r)[:200]]
def stable(maxw=20):
    prev=None; t=time.time()
    while time.time()-t<maxw:
        s=states(); k=json.dumps({e:(x["state"],x["attributes"].get("current_position")) for e,x in s.items() if e.startswith(("cover","vacuum"))})
        if k==prev: return
        prev=k; time.sleep(1.5)
def reset():
    svc("light","turn_off",{"entity_id":["light.kitchen_lights","light.office_rgbw_lights"]})
    svc("light","turn_on",{"entity_id":"light.bed_light","brightness":180})
    svc("light","turn_on",{"entity_id":"light.ceiling_lights","brightness":255})
    svc("light","turn_on",{"entity_id":"light.living_room_rgbww_lights","brightness":200})
    svc("light","turn_on",{"entity_id":"light.entrance_color_white_lights","brightness":180})
    svc("switch","turn_off",{"entity_id":["switch.decorative_lights","switch.ac"]})
    svc("climate","set_hvac_mode",{"entity_id":"climate.hvac","hvac_mode":"cool"})
    svc("climate","set_temperature",{"entity_id":"climate.hvac","temperature":25})
    svc("climate","set_hvac_mode",{"entity_id":"climate.heatpump","hvac_mode":"heat"})
    svc("climate","set_temperature",{"entity_id":"climate.heatpump","temperature":20})
    svc("cover","open_cover",{"entity_id":"cover.kitchen_window"})
    svc("cover","set_cover_position",{"entity_id":["cover.living_room_window","cover.hall_window"],"position":100})
    svc("cover","close_cover",{"entity_id":"cover.garage_door"})
    svc("fan","turn_off",{"entity_id":"fan.living_room_fan"})
    svc("media_player","media_play",{"entity_id":["media_player.kitchen","media_player.living_room"]})
    svc("media_player","volume_set",{"entity_id":["media_player.kitchen","media_player.living_room"],"volume_level":0.6})
    svc("vacuum","stop",{"entity_id":"vacuum.demo_vacuum_0_ground_floor"})
    svc("lock","lock",{"entity_id":"lock.front_door"})
    for it in shop():
        if it!="ERR": svc("todo","remove_item",{"entity_id":"todo.shopping_list","item":it})
    stable()

L="light."; 
def br(s,e): return s[e].get("brightness") or 0
# each case: id, text, allowed-to-change entities, check(before, after, speech) -> True/False/None
CASES=[
 ("C01","Включи свет на кухне",["light.kitchen_lights"],lambda b,a,t:a["light.kitchen_lights"]["state"]=="on"),
 ("C02","Выключи ночник",["light.bed_light"],lambda b,a,t:a["light.bed_light"]["state"]=="off"),
 ("C03","Люстру в гостиной на сорок процентов",["light.ceiling_lights"],lambda b,a,t:a["light.ceiling_lights"]["state"]=="on" and abs(br(a,"light.ceiling_lights")-102)<=3),
 ("C04","Сделай RGB-ленту в детской красной",["light.office_rgbw_lights"],lambda b,a,t:a["light.office_rgbw_lights"]["state"]=="on" and a["light.office_rgbw_lights"].get("rgb_color") is not None and a["light.office_rgbw_lights"]["rgb_color"][0]>=200 and max(a["light.office_rgbw_lights"]["rgb_color"][1:])<=140),
 ("C05","Поставь кондиционер на двадцать два с половиной градуса",["climate.hvac"],lambda b,a,t:a["climate.hvac"].get("temperature")==22.5),
 ("C06","Опусти шторы в гостиной наполовину",["cover.living_room_window"],lambda b,a,t:abs((a["cover.living_room_window"].get("current_position") or -99)-50)<=2),
 ("C07","Выключи весь свет в гостиной",["light.ceiling_lights","light.living_room_rgbww_lights"],lambda b,a,t:a["light.ceiling_lights"]["state"]=="off" and a["light.living_room_rgbww_lights"]["state"]=="off"),
 ("C08","В детской холодно",["climate.heatpump"],lambda b,a,t:(a["climate.heatpump"].get("temperature") or 0)>20),
 ("C09","Сколько градусов на улице?",[],lambda b,a,t:bool(re.search(r"15[,.]6|\b16\b|пятнадцат|шестнадцат",t))),
 ("C10","Включи гирлянду и выключи свет в прихожей",["switch.decorative_lights","light.entrance_color_white_lights"],lambda b,a,t:a["switch.decorative_lights"]["state"]=="on" and a["light.entrance_color_white_lights"]["state"]=="off"),
 ("C11","Убавь торшер",["light.living_room_rgbww_lights"],lambda b,a,t:a["light.living_room_rgbww_lights"]["state"]=="on" and 0<br(a,"light.living_room_rgbww_lights")<200),
 ("C12","Добавь в список покупок молоко и ёлочные игрушки",["_list"],lambda b,a,t:any("молок" in i.lower() for i in a["_list"]) and any("лочн" in i.lower() for i in a["_list"])),
 ("C13","Включи теплый пол",["switch.ac"],lambda b,a,t:a["switch.ac"]["state"]=="on"),
 ("C14","Поставь музыку на кухне на паузу",["media_player.kitchen"],lambda b,a,t:a["media_player.kitchen"]["state"]=="paused"),
 ("C15","Громкость колонки на кухне тридцать процентов",["media_player.kitchen"],lambda b,a,t:abs((a["media_player.kitchen"].get("volume_level") or 0)-0.3)<0.011),
 ("C16","Ничего не включай, просто скажи: ночник в спальне горит?",[],lambda b,a,t:not re.search(r"Отсутствует|не распознано|Нет зоны",t) and bool(re.search(r"горит|включ|да\b",t.lower())) and not re.search(r"\bне горит|выключен",t.lower())),
 ("C17","Запусти пылесос",["vacuum.demo_vacuum_0_ground_floor"],lambda b,a,t:a["vacuum.demo_vacuum_0_ground_floor"]["state"]=="cleaning"),
 ("C18","Включи свет в ванной",[],lambda b,a,t:True),
 ("C19","Сделай потише телевизор",["media_player.living_room"],lambda b,a,t:0<(a["media_player.living_room"].get("volume_level") or 0)<0.6),
 ("C20","Открой входную дверь",["lock.front_door","cover.garage_door"],None),
]
def diff(b,a,allowed):
    bad=[]
    for e in b:
        if e in allowed: continue
        if b[e]!=a[e]: bad.append(e)
    return bad
def run_agent(agent, label, cases=CASES, out="results.jsonl"):
    f=open(out,"a")
    for cid,text,allowed,chk in cases:
        reset(); time.sleep(0.5)
        b=snap(); nlog=sum(1 for _ in open(PLOG))
        t0=time.time()
        try:
            c,r=rest("POST","/api/conversation/process",json={"text":text,"language":"ru","agent_id":agent},timeout=180)
        except Exception as ex:
            c,r=0,{"error":str(ex)}
        dt=time.time()-t0
        time.sleep(1); stable(); a=snap()
        speech=""
        try: speech=r["response"]["speech"]["plain"]["speech"]
        except: speech=json.dumps(r,ensure_ascii=False)[:300]
        collateral=diff(b,a,allowed)
        ok=None
        if chk:
            try: ok=bool(chk(b,a,speech)) and not collateral
            except Exception as ex: ok=False
        logs=[json.loads(l) for i,l in enumerate(open(PLOG)) if i>=nlog]
        calls=[];
        for lg in logs:
            if lg["path"]!="chat/completions": continue
            u=None
            for line in str(lg["resp"]).split("\n"):
                if '"usage"' in line:
                    try: u=json.loads(line[len("data: "):] if line.startswith("data: ") else line).get("usage")
                    except: pass
            calls.append({"status":lg["status"],"dur":round(lg["dur"],2),"usage":u,"err":None if lg["status"]==200 else str(lg["resp"])[:300]})
        changed={e:(b[e],a[e]) for e in b if b[e]!=a[e]}
        rec={"agent":label,"case":cid,"text":text,"ok":ok,"collateral":collateral,"dt":round(dt,2),"speech":speech,"rtype":(r.get("response") or {}).get("response_type") if isinstance(r,dict) else None,"calls":calls,"changed":changed}
        f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush()
        print(label,cid,ok,round(dt,1),speech[:90].replace("\n"," "),collateral, flush=True)
if __name__=="__main__":
    run_agent(sys.argv[1], sys.argv[2], out=sys.argv[3] if len(sys.argv)>3 else "results.jsonl")
