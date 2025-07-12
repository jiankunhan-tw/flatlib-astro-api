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
    date: str = Query(...),         # 格式：YYYY-MM-DD
    time: str = Query(...),         # 格式：HH:MM
    lat: str = Query(...),          # 緯度，例如 24.98
    lon: str = Query(...),          # 經度，例如 121.54
    hsys: str = Query("placidus")   # 宮位系統（預設 placidus，可用 wholeSigns 等）
):
    try:
        # 建立時間與地點
        dt = Datetime(date, time, '+08:00')
        pos = GeoPos(float(lat), float(lon))  # ✅ 改成 float 傳入，避免座標錯誤

        # 建立星盤
        chart = Chart(dt, pos)
        chart.setHouses(hsys)

        # 取得行星資料
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

        # 取得宮位資料
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
