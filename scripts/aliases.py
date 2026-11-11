import asyncio, sys
from hal import *
AREA={"Кухня":["кухне","кухню","кухни"],"Гостиная":["гостиной","гостиную"],"Спальня":["спальне","спальню","спальни"],"Детская":["детской","детскую"],"Прихожая":["прихожей","прихожую"],"Ванная":["ванной","ванную"],"Кабинет":["кабинете"],"Гараж":["гараже"]}
ENT={"light.ceiling_lights":["люстру"],"light.office_rgbw_lights":["RGB-ленту","ленту"],"switch.ac":["теплый пол"],"vacuum.demo_vacuum_0_ground_floor":["пылесос"],"switch.decorative_lights":["гирлянду"],"cover.kitchen_window":["штору"],"todo.shopping_list":["список покупок"]}
on=sys.argv[1]=="on"
async def m():
    async with WS() as w:
        for a in await w.call("config/area_registry/list"):
            if a["name"] in AREA: await w.call("config/area_registry/update",area_id=a["area_id"],aliases=AREA[a["name"]] if on else [])
        for e,al in ENT.items():
            try: await w.call("config/entity_registry/update",entity_id=e,aliases=([None]+al) if on else [None])
            except Exception as ex: print(e,ex)
asyncio.run(m()); print("aliases",on)
