from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import traceback

app = FastAPI()

class ChartRequest(BaseModel):
    date: str
    time: str
    lat: float
    lon: float
    tz: float

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # Step 1: 基本資訊
        date = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)

        # Step 2: 建立空 Chart（不自動加天體）
        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS, IDs=[])

        # Step 3: 自己加上安全的十顆星與點
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
