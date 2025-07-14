from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.chart import Chart
from flatlib import const
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
import uvicorn

app = FastAPI()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChartRequest(BaseModel):
    date: str       # "1995/04/04"
    time: str       # "11:35"
    tz: str         # "+08:00" 或 "8"
    lat: float      # 25.0132
    lon: float      # 121.4654

@app.post("/chart")
def get_chart(req: ChartRequest):
    try:
        dt = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)

        result = {
            "ascendant": chart.get(const.ASC).sign,
            "midheaven": chart.get(const.MC).sign,
            "sun": chart.get(const.SUN).sign,
            "moon": chart.get(const.MOON).sign,
            "houses": {},
            "planets": {}
        }

        # 宮位資訊
        for i in range(1, 13):
            house = chart.getHouse(i)
            result["houses"][f"house_{i}"] = house.sign

        # 行星資訊
        for obj in [const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
                    const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO]:
            item = chart.get(obj)
            result["planets"][obj] = {
                "sign": item.sign,
                "house": item.house
            }

        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
