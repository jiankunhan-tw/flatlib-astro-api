from fastapi import FastAPI
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.chart import Chart
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()

class ChartRequest(BaseModel):
    date: str
    time: str
    lat: float
    lon: float
    tz: str

def parse_timezone(tz):
    try:
        if isinstance(tz, str):
            if ':' in tz:
                return int(tz.replace('+', '').split(':')[0])
            elif tz.startswith('+') or tz.startswith('-'):
                return int(tz)
        return float(tz)
    except:
        return 0.0

def deg_to_dms_string(deg):
    d = int(deg)
    m_float = abs(deg - d) * 60
    m = int(m_float)
    s = int((m_float - m) * 60)
    return f"{d}:{m}:{s}"

# ✅ 用手動安全列表避免 flatlib swe bug
OBJECTS = [
    const.SUN, const.MOON, const.MERCURY, const.VENUS,
    const.MARS, const.JUPITER, const.SATURN,
    const.URANUS, const.NEPTUNE, const.PLUTO
]

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        tz_fixed = parse_timezone(req.tz)
        date = Datetime(req.date, req.time, tz_fixed)

        lat_str = deg_to_dms_string(req.lat)
        lon_str = deg_to_dms_string(req.lon)
        pos = GeoPos(lat_str, lon_str)

        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)

        planets = {}
        for obj in OBJECTS:
            obj_data = chart.get(obj)
            planets[obj] = {
                'sign': obj_data.sign,
                'lon': obj_data.lon,
                'house': obj_data.house
            }

        return {
            "status": "success",
            "planets": planets
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
