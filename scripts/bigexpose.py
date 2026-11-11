import asyncio, sys
from hal import *
from home import HOME
on=sys.argv[1]=="on"
async def m():
    async with WS() as w:
        allst=[s["entity_id"] for s in rest("GET","/api/states")[1]]
        extra=[e for e in allst if e not in HOME and not e.startswith(("conversation.","update.","event.","zone.","person.","sun.","tts.","stt.","notify.","image_processing","geo_location","camera.","text.","date","time.","button.","number.","select.","calendar","remote.","siren","alarm_control_panel"))]
        await w.call("homeassistant/expose_entity",assistants=["conversation"],entity_ids=extra,should_expose=on)
        print("extra",len(extra),on)
asyncio.run(m())
