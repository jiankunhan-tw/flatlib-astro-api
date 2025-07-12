from fastapi import FastAPI, Query  
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
import traceback

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Flatlib API is running!"}

@app.get("/chart")
def get_chart(
    date: str = Query(...),         
    time: str = Query(...),         
    lat: float = Query(...),        # ✅ 改為 float，不再用 str
    lon: float = Query(...),        # ✅ 改為 float，不再用 str
    hsys: str = Query("placidus"),  
    ids: str = Query(None)          
):
    try:
        # ⛑️ 若缺秒數則補 ":00"
        if len(time.split(":")) == 2:
            time += ":00"

        dt = Datetime(date, time, '+08:00')
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos)
        chart.setHouses(hsys)

        allowed_ids = {
            'sun': const.SUN, 'moon': const.MOON,
            'mercury': const.MERCURY, 'venus': const.VENUS, 'mars': const.MARS,
            'jupiter': const.JUPITER, 'saturn': const.SATURN,
            'uranus': const.URANUS, 'neptune': const.NEPTUNE, 'pluto': const.PLUTO
        }

        if ids:
            input_ids = [x.strip().lower() for x in ids.split(',')]
            obj_ids = [allowed_ids[i] for i in input_ids if i in allowed_ids]
        else:
            obj_ids = list(allowed_ids.values())

        planets = {}
        for key in obj_ids:
            p = chart.get(key)
            planets[key] = {
                "sign": p.sign,
                "lon": p.lon,
                "lat": p.lat,
                "house": chart.houseOf(p)
            }

        houses = {
            f"House{i}": {
                "sign": house.sign,
                "lon": house.lon
            } for i, house in enumerate(chart.houses, 1)
        }

        return {
            "status": "success",
            "date": date,
            "time": time,
            "planets": planets,
            "houses": houses
        }

    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
