from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.ephem import swe
from flatlib import const

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # 時區處理
        tz_fixed = parse_timezone(req.tz)
        date = Datetime(req.date, req.time, tz_fixed)

        # 經緯度轉 DMS
        lat_str = deg_to_dms_string(req.lat)
        lon_str = deg_to_dms_string(req.lon)
        pos = GeoPos(lat_str, lon_str)

        # Julian Day
        jd = date.jd

        # ✅ 直接用 swe 低層呼叫
        OBJECTS = ['sun', 'moon', 'mercury', 'venus', 'mars', 
                   'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']

        planets = {}
        for obj in OBJECTS:
            sweObj = swe.getObject(obj, jd, pos.lat, pos.lon)
            planets[obj] = {
                'sign': sweObj.sign,
                'lon': sweObj.lon,
                'lat': sweObj.lat,
                'speed': sweObj.lonspeed
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
