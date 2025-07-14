from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.ephem import swe
import traceback

app = FastAPI()

class ChartRequest(BaseModel):
    date: str       # 例如 '1995-04-04'
    time: str       # 例如 '11:30'
    lat: float      # 例如 24.968371
    lon: float      # 例如 121.539595
    tz: float       # 例如 8.0

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # 組合時間
        date = Datetime(req.date, req.time, req.tz)
        jd = date.jd

        # 只抓10大行星
        OBJECTS = ['sun', 'moon', 'mercury', 'venus', 'mars',
                   'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

        result = {}
        for obj in OBJECTS:
            swe_obj = swe.sweObject(obj, jd)
            result[obj] = {
                'sign': swe_obj.sign,
                'lon': swe_obj.lon,
                'lat': swe_obj.lat,
                'speed': swe_obj.lonspeed
            }

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
