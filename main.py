from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import traceback

app = FastAPI()

class ChartRequest(BaseModel):
    date: str       # e.g. '1995-04-04'
    time: str       # e.g. '11:30'
    lat: float      # e.g. 24.968371
    lon: float      # e.g. 121.438034
    tz: float       # e.g. 8.0

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # Step 1: 創建時間與地點物件
        date = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)
        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

        # Step 2: 抓取十顆主要星體
        planet_ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]
        planets = {}
        for pid in planet_ids:
            obj = chart.get(pid)
            planets[pid] = {
                "sign": obj.sign,
                "lon": obj.lon,
                "lat": obj.lat,
                "house": obj.house,
                "speed": obj.speed
            }

        # Step 3: 抓取上升點（ASC）與中天（MC）
        asc = chart.get(const.ASC)
        mc = chart.get(const.MC)

        return {
            "status": "success",
            "ascendant": {
                "sign": asc.sign,
                "lon": asc.lon
            },
            "midheaven": {
                "sign": mc.sign,
                "lon": mc.lon
            },
            "planets": planets
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
