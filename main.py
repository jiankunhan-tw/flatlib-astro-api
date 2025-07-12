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

def to_coord(val: str, is_lat=True):
    try:
        val = float(val)
        deg = abs(int(val))
        minutes = int(round((abs(val) - deg) * 60))
        direction = (
            'n' if is_lat and val >= 0 else
            's' if is_lat and val < 0 else
            'e' if not is_lat and val >= 0 else
            'w'
        )
        return f"{deg}{direction}{minutes:02}"
    except:
        return val  # assume already formatted

@app.get("/chart")
def get_chart(
    date: str = Query(...),
    time: str = Query(...),
    lat: str = Query(...),
    lon: str = Query(...),
    hsys: str = Query("wholeSigns")
):
    try:
        dt = Datetime(date, time, '+08:00')
        lat_str = to_coord(lat, is_lat=True)
        lon_str = to_coord(lon, is_lat=False)
        pos = GeoPos(lat_str, lon_str)

        if hsys not in ['wholeSigns', 'placidus']:
            hsys = 'wholeSigns'

        chart = Chart(dt, pos, hsys)

        planets = {}
        for obj in [const.SUN, const.MOON, const.MERCURY, const.VENUS,
                    const.MARS, const.JUPITER, const.SATURN]:
            try:
                p = chart.get(obj)
                planets[obj] = {
                    "sign": p.sign,
                    "lon": p.lon,
                    "lat": p.lat,
                    "house": chart.houseOf(p)
                }
            except Exception as e:
                planets[obj] = {"error": str(e)}

        houses = {}
        try:
            for i, house in enumerate(chart.houses, 1):
                houses[f"House{i}"] = {
                    "sign": house.sign,
                    "lon": house.lon
                }
        except:
            houses = {"error": "failed to load houses"}

        return {
            "status": "success",
            "date": date,
            "time": time,
            "hsys": hsys,
            "planets": planets,
            "houses": houses
        }

    except Exception as e:
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
