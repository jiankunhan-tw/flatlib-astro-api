from fastapi import FastAPI, Query
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
    date: str = Query(...),    # YYYY-MM-DD
    time: str = Query(...),    # HH:MM
    lat: str = Query(...),     # 緯度（可輸入 float 或如 25n02）
    lon: str = Query(...)      # 經度（可輸入 float 或如 121e31）
):
    try:
        dt = Datetime(date, time, '+08:00')

        def parse_coord(val: str, is_lat=True):
            if any(c.isalpha() for c in val):  # 已是 flatlib 格式
                return val.lower()
            else:
                val = float(val)
                deg = abs(int(val))
                minutes = int((abs(val) - deg) * 60)
                direction = (
                    'n' if is_lat and val >= 0 else
                    's' if is_lat and val < 0 else
                    'e' if not is_lat and val >= 0 else
                    'w'
                )
                return f"{deg}{direction}{minutes:02}"

        # ➤ 轉換經緯度格式
        lat_str = parse_coord(lat, is_lat=True)
        lon_str = parse_coord(lon, is_lat=False)

        # ➤ Debug Log：可在 Zeabur log 查看
        print("⚠️ [debug] dt =", dt)
        print("⚠️ [debug] lat_str =", lat_str)
        print("⚠️ [debug] lon_str =", lon_str)

        # ➤ 建立星盤（指定 Placidus 宮位制）
        pos = GeoPos(lat_str, lon_str)
        chart = Chart(dt, pos, hsys=const.PLACIDUS)

        # ➤ 星體列表
        star_list = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO
        ]

        planets = {}
        for obj in star_list:
            try:
                planet = chart.get(obj)
                planets[obj] = {
                    "sign": planet.sign,
                    "lon": planet.lon,
                    "lat": planet.lat,
                    "house": chart.houseOf(planet)
                }
            except Exception as inner:
                planets[obj] = {"error": str(inner)}

        # ➤ ASC / MC
        asc = chart.get(const.ASC)
        mc = chart.get(const.MC)

        angles = {
            "ASC": {
                "sign": asc.sign,
                "lon": asc.lon
            },
            "MC": {
                "sign": mc.sign,
                "lon": mc.lon
            }
        }

        # ➤ 12 宮宮頭（House cusps）
        house_cusps = {}
        for i, house in enumerate(chart.houses, start=1):
            house_cusps[f"House{i}"] = {
                "sign": house.sign,
                "lon": house.lon
            }

        return {
            "status": "success",
            "placidus": True,
            "tropical": True,
            "angles": angles,
            "houses": house_cusps,
            "planets": planets
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
