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
    date: str = Query(...),         # 格式：YYYY-MM-DD
    time: str = Query(...),         # 格式：HH:MM
    lat: str = Query(...),          # 緯度（需為字串）
    lon: str = Query(...),          # 經度（需為字串）
    hsys: str = Query("placidus"),  # 宮位系統
    ids: str = Query(None)          # 星體 ID，可選
):
    try:
        # 強制轉字串避免浮點格式錯誤
        lat = str(lat)
        lon = str(lon)

        dt = Datetime(date, time, '+08:00')
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)
        chart.setHouses(hsys)

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

        planets = {}
        for key in obj_ids:
            p = chart.get(key)
            planets[key] = {
                "sign": p.sign,
                "lon": p.lon,
                "lat": p.lat,
                "house": chart.houseOf(p)
            }

        houses = {
            f"House{i}": {
                "sign": house.sign,
                "lon": house.lon
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
