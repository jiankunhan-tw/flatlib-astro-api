from fastapi import FastAPI, Query  
from fastapi.responses import JSONResponse
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

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
        chart = Chart(dt, pos)

        # ✅ 僅使用七大行星（傳統解盤足夠，且 flatlib 支援）
        main_planets = [
            'Sun', 'Moon', 'Mercury', 'Venus', 'Mars',
            'Jupiter', 'Saturn'
        ]

        result = []
        for obj in main_planets:
            body = chart.get(obj)
            result.append({
                'name': body.id,
                'sign': body.sign,
                'lon': round(body.lon, 2),
                'house': body.house
            })

        return JSONResponse(content={
            'datetime': f"{date} {time} {tz}",
            'location': {'lat': lat, 'lon': lon},
            'chart': result
        })

    except Exception as e:
        return JSONResponse(status_code=400, content={'error': str(e)})
