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
        # 建立時間與地點物件
        date = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)

        # 這邊不設 IDs，讓 Flatlib 自動載入主要星體與點
        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

        # 安全地從已載入 chart 物件中撈資料
        target_ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC, const.MC
        ]

        planets = {}
        for pid in target_ids:
            obj = chart.get(pid)
            if obj:
                planets[pid] = {
                    "sign": obj.sign,
                    "lon": obj.lon,
                    "house": obj.house,
                    "speed": obj.speed
                }
            else:
                planets[pid] = {"error": "not found in chart object"}

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
