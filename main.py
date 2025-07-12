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
    lat: str = Query(...),          # 緯度
    lon: str = Query(...),          # 經度
    hsys: str = Query("placidus"),  # 宮位系統
    ids: str = Query(None)          # 星體 ID（可選）
):
    try:
        # 轉換時間與位置
        dt = Datetime(date, time, '+08:00')
        pos = GeoPos(float(lat), float(lon))  # 🔧 修正：強制轉為 float

        # 建立命盤並設置宮位系統
        chart = Chart(dt, pos)
        chart.setHouses(hsys)

        # 可用星體列表
        allowed_ids = {
            'sun': const.SUN, 'moon': const.MOON,
            'mercury': const.MERCURY, 'venus': const.VENUS, 'mars': const.MARS,
            'jupiter': const.JUPITER, 'saturn': const.SATURN,
            'uranus': const.URANUS, 'neptune': const.NEPTUNE, 'pluto': const.PLUTO
        }

        # 如果有指定要回傳哪些星體
        if ids:
            input_ids = [x.strip().lower() for x in ids.split(',')]
            obj_ids = [allowed_ids[i] for i in input_ids if i in allowed_ids]
        else:
            obj_ids = list(allowed_ids.values())

        # 回傳星體資訊
        planets = {}
        for key in obj_ids:
            p = chart.get(key)
            planets[key] = {
                "sign": p.sign,
                "lon": p.lon,
                "lat": p.lat,
                "house": chart.houseOf(p)
            }

        # 回傳宮位資訊
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
