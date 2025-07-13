from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Flatlib API is running."}


def get_house_by_lon(houses, lon):
    """
    根據黃道度數回傳星體落入的宮位
    """
    for i in range(1, 13):
        h1 = houses.getHouse(i)
        h2 = houses.getHouse(i % 12 + 1)
        start = h1.lon
        end = h2.lon if h2.lon > start else h2.lon + 360

        if start <= lon < end:
            return i
    return None


@app.get("/chart")
def get_chart(
    date: str = Query(..., example="1995-04-04"),
    time: str = Query(..., example="11:30"),
    lat: float = Query(..., example=25.03),
    lon: float = Query(..., example=121.56),
    tz: str = Query("+08:00")
):
    try:
        # 建立星盤
        dt = Datetime(date, time, tz)
        pos = GeoPos(lat, lon)
        chart = Chart(dt, pos, hsys=const.HOUSES_PLACIDUS)

        # 七大星體
        planets = [
            const.SUN, const.MOON,
            const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN
        ]

        planet_result = []
        for obj in planets:
            body = chart.get(obj)
            house_num = get_house_by_lon(chart.houses, body.lon)
            planet_result.append({
                'name': body.id,
                'sign': body.sign,
                'lon': round(body.lon, 2),
                'house': house_num
            })

        # 十二宮起點資訊
        house_result = []
        for i in range(1, 13):
            h = chart.houses.getHouse(i)
            house_result.append({
                'house': i,
                'sign': h.sign,
                'lon': round(h.lon, 2)
            })

        # 上升、天頂
        asc = chart.get(const.ASC)
        mc = chart.get(const.MC)

        return JSONResponse(content={
            'datetime': f"{date} {time} {tz}",
            'location': {'lat': lat, 'lon': lon},
            'asc': {
                'sign': asc.sign,
                'lon': round(asc.lon, 2)
            },
            'mc': {
                'sign': mc.sign,
                'lon': round(mc.lon, 2)
            },
            'chart': planet_result,
            'houses': house_result
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
