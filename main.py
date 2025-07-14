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

# 🛡️ 安全取得宮位（避免出錯）
def safe_get_house(chart, i):
    try:
        return chart.houses.get(i)
    except Exception:
        return None

# 🎯 根據行度取得星體所在宮位
def get_house_by_lon(chart, lon):
    try:
        for i in range(1, 13):
            h1 = safe_get_house(chart, i)
            h2 = safe_get_house(chart, i + 1 if i < 12 else 1)
            if not h1 or not h2:
                continue
            start = h1.lon
            end = h2.lon if h2.lon > start else h2.lon + 360
            lon_adj = lon if lon >= start else lon + 360
            if start <= lon_adj < end:
                return i
    except Exception:
        return None
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

        planets = [
            const.SUN, const.MOON, const.MERCURY,
            const.VENUS, const.MARS, const.JUPITER, const.SATURN
        ]

        planet_result = []
        for obj in planets:
            body = chart.get(obj)
            house_num = get_house_by_lon(chart, body.lon)
            planet_result.append({
                'name': body.id,
                'sign': body.sign,
                'lon': round(body.lon, 2),
                'house': house_num
            })

        house_result = []
        for i in range(1, 13):
            h = safe_get_house(chart, i)
            if h:
                house_result.append({
                    'house': i,
                    'sign': h.sign,
                    'lon': round(h.lon, 2)
                })

        asc = chart.get(const.ASC)
        mc = chart.get(const.MC)

        return JSONResponse(content={
            'datetime': f"{date} {time} {tz}",
            'location': {'lat': lat, 'lon': lon},
            'asc': {'sign': asc.sign, 'lon': round(asc.lon, 2)},
            'mc': {'sign': mc.sign, 'lon': round(mc.lon, 2)},
            'chart': planet_result,
            'houses': house_result
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
@app.get("/ping")
def ping():
    return {"status": "ok", "version": "v2025-07-14"}

