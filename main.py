from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Flatlib API is running!"}

def get_house_by_lon(houses, lon):
    """
    根據黃道度數回傳星體落入的宮位
    """
    for i in range(1, 13):
        h1 = houses.get(str(i))
        h2 = houses.get(str(i % 12 + 1))  # 下一宮
        start = h1.lon
        end = h2.lon if h2.lon > start else h2.lon + 360

        if start <= lon < end:
            return i
    return None

@app.get("/chart")
def get_chart(
    date: str = Query(...),
    time: str = Query(...),
    lat: float = Query(...),
    lon: float = Query(...),
    tz: str = Query("+08:00")
):
    try:
        dt = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)

        safe_objects = [
            const.SUN, const.MOON,
            const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN
        ]

        result = []
        for obj in safe_objects:
            body = chart.get(obj)
            house_num = get_house_by_lon(chart.houses, body.lon)
            result.append({
                'name': body.id,
                'sign': body.sign,
                'lon': round(body.lon, 2),
                'house': house_num
            })

        return JSONResponse(content={
            'datetime': f"{date} {time} {tz}",
            'location': {'lat': lat, 'lon': lon},
            'chart': result
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
