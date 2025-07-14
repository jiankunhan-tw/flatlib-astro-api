from fastapi import FastAPI, Query
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.chart import Chart
from flatlib import const

app = FastAPI()


class ChartRequest(BaseModel):
    date: str       # 格式：1995/04/04
    time: str       # 格式：11:35
    lat: float      # 緯度
    lon: float      # 經度
    tz: str         # 時區（+08:00 或 8）

def parse_timezone(tz):
    try:
        if isinstance(tz, str):
            # 若是 "+08:00" 或 "+8:00"
            if ':' in tz:
                return int(tz.replace('+', '').split(':')[0])
            elif tz.startswith('+') or tz.startswith('-'):
                return int(tz)
        return float(tz)
    except:
        return 0.0


@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        # 修正時區格式為 float（避免 tuple index error）
        tz_fixed = parse_timezone(req.tz)

        # 建立 Datetime 物件
        date = Datetime(req.date, req.time, tz_fixed)

        # 建立星盤
        chart = Chart(date, (req.lat, req.lon), hsys=const.HOUSES_PLACIDUS)

        # 提取行星資訊
        planets = {}
        for obj in const.LIST_OBJECTS:
            obj_data = chart.get(obj)
            planets[obj] = {
                'sign': obj_data.sign,
                'lon': obj_data.lon,
                'house': obj_data.house
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
