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
            # 取得星體的黃道度數，然後從 houses 找到對應宮位
            house_id = chart.houses.getHousePos(body.lon).id  # ✅ 正確用法
            result.append({
                'name': body.id,
                'sign': body.sign,
                'lon': round(body.lon, 2),
                'house': house_id
            })

        return JSONResponse(content={
            'datetime': f"{date} {time} {tz}",
            'location': {'lat': lat, 'lon': lon},
            'chart': result
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
