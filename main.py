from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import traceback

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Flatlib API is running!"}

@app.get("/chart")
def get_chart(
    date: str = Query(...),          # 格式 yyyy-mm-dd
    time: str = Query(...),          # 格式 hh:mm 或 hh:mm:ss
    lat: float = Query(...),         # 緯度（小數格式）
    lon: float = Query(...),         # 經度（小數格式）
    hsys: str = Query("placidus"),   # 宮位系統，預設 placidus
    ids: str = Query(None)           # 想查的星體，例如 "sun,moon,venus"
):
    try:
        # 如果時間格式沒包含秒，補上 ":00"
        if len(time.split(":")) == 2:
            time += ":00"

        # 設定台灣時區 +08:00（你可自行改）
        dt = Datetime(date, time, '+08:00')
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos, hsys=hsys)

        # 可查的星體
        allowed_ids = {
            'sun': const.SUN, 'moon': const.MOON,
            'mercury': const.MERCURY, 'venus': const.VENUS, 'mars': const.MARS,
            'jupiter': const.JUPITER, 'saturn': const.SATURN,
            'uranus': const.URANUS, 'neptune': const.NEPTUNE, 'pluto': const.PLUTO
        }

        if ids:
            input_ids = [x.strip().lower() for x in ids.split(',')]
            obj_ids = [allowed_ids[i] for i in input_ids if i in allowed_ids]
        else:
            obj_ids = list(allowed_ids.values())

        # 取得行星資料
        planets = {}
        for key in obj_ids:
            p = chart.get(key)
            planets[key] = {
                "sign": p.sign,
                "lon": round(p.lon, 2),
                "lat": round(p.lat, 2),
                "house": chart.houseOf(p)
            }

        # 取得12宮資料
        houses = {
            f"House{i}": {
                "sign": house.sign,
                "lon": round(house.lon, 2)
            } for i, house in enumerate(chart.houses, 1)
        }

        return {
            "status": "success",
            "date": date,
            "time": time,
            "planets": planets,
            "houses": houses
        }

    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
