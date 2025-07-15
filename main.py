from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import flatlib.ephem.ephem as ephem  # 👈 新增
ephem._setEphemEngine('builtin')    # 👈 新增
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
        date = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)

        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

        ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC, const.MC
        ]

        result = {}
        for pid in ids:
            obj = chart.get(pid)
            if obj:
                result[pid] = {
                    "sign": obj.sign,
                    "lon": obj.lon,
                    "house": obj.house,
                    "speed": obj.speed
                }
            else:
                result[pid] = {"error": f"'{pid}' not found"}

        return {
            "status": "success",
            "planets": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
