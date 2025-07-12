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
    lat: str = Query(...),          # 緯度，例如 24.98
    lon: str = Query(...),          # 經度，例如 121.54
    hsys: str = Query("placidus"),  # 宮位系統（預設 placidus）
    ids: str = Query(None)          # 星體 ID，可選，格式："sun,moon,mer,..."
):
    try:
        # 建立時間與地點
        dt = Datetime(date, time, '+08:00')
        pos = GeoPos(float(lat), float(lon))

        # 建立星盤與宮位系統
        chart = Chart(dt, pos)
        chart.setHouses(hsys)

        # 處理星體清單
        default_ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS,
            const.MARS, const.JUPITER, const.SATURN,
            const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        obj_ids = ids.split(',') if ids else default_ids

        # 行星資料
        planets = {}
        for obj in obj_ids:
            try:
                obj = obj.strip().lower()
                mapped = {
                    'sun': const.SUN, 'moon': const.MOON, 'mer': const.MERCURY,
                    'venus': const.VENUS, 'ven': const.VENUS,
                    'mars': const.MARS, 'jup': const.JUPITER, 'jupiter': const.JUPITER,
                    'sat': const.SATURN, 'saturn': const.SATURN,
                    'ura': const.URANUS, 'uranus': const.URANUS,
                    'nep': const.NEPTUNE, 'neptune': const.NEPTUNE,
                    'plu': const.PLUTO, 'pluto': const.PLUTO
                }
                key = mapped.get(obj, obj)
                p = chart.get(key)
                planets[obj] = {
                    "sign": p.sign,
                    "lon": p.lon,
                    "lat": p.lat,
                    "house": chart.houseOf(p)
                }
            except Exception as e:
                planets[obj] = {"error": str(e)}

        # 宮位資料
        houses = {}
        try:
            for i, house in enumerate(chart.houses, 1):
                houses[f"House{i}"] = {
                    "sign": house.sign,
                    "lon": house.lon
                }
        except Exception as e:
            houses = {"error": str(e)}

        return {
            "status": "success",
            "date": date,
            "time": time,
            "hsys": hsys,
            "planets": planets,
            "houses": houses
        }

    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
