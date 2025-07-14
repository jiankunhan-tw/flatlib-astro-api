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

def deg_to_dms_string(degree: float) -> str:
    """將 float 經緯轉成 D:M:S 字串"""
    is_negative = degree < 0
    degree = abs(degree)
    d = int(degree)
    m_float = (degree - d) * 60
    m = int(m_float)
    s = int((m_float - m) * 60)
    dms = f"{'-' if is_negative else ''}{d}:{m}:{s}"
    return dms

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # 處理時間與位置
        date = Datetime(req.date, req.time, req.tz)
        lat_dms = deg_to_dms_string(req.lat)
        lon_dms = deg_to_dms_string(req.lon)
        pos = GeoPos(lat_dms, lon_dms)
        jd = date.jd

        # 只抓10大行星
        OBJECTS = ['sun', 'moon', 'mercury', 'venus', 'mars',
                   'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

        result = {}
        for obj in OBJECTS:
            swe_obj = swe.getObject(obj, jd, pos.lat, pos.lon)
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
