from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import traceback

app = FastAPI()

class ChartRequest(BaseModel):
    date: str       # 例如 '1995-04-04'
    time: str       # 例如 '11:30'
    lat: float      # 例如 24.968371
    lon: float      # 例如 121.438034
    tz: float       # 例如 8.0

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # Step 1: 時間與地點處理
        date = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)

        # Step 2: 空 chart（不預設加天體）
        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS, IDs=[])

        # Step 3: 安全指定要哪些星體與點
        safe_objects = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC, const.MC
        ]

        planets = {}
        for pid in safe_objects:
            try:
                obj = chart.getObject(pid)
                planets[pid] = {
                    "sign": obj.sign,
                    "lon": obj.lon,
                    "house": obj.house,
                    "speed": obj.speed
                }
            except Exception as e:
                planets[pid] = {"error": str(e)}

        return {
            "status": "success",
            "planets": planets
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
