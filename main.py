from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from flatlib import const
import flatlib.ephem.ephem as ephem
import traceback
from typing import List, Optional
import uvicorn

# 強制使用 flatlib 內建運算，不調用 swe
ephem._setEphemEngine('builtin')

app = FastAPI(title="占星API", description="提供占星圖分析服務", version="1.0.0")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 星座名稱對照表
SIGN_NAMES = {
    const.ARIES: "白羊座",
    const.TAURUS: "金牛座", 
    const.GEMINI: "雙子座",
    const.CANCER: "巨蟹座",
    const.LEO: "獅子座",
    const.VIRGO: "處女座",
    const.LIBRA: "天秤座",
    const.SCORPIO: "天蠍座",
    const.SAGITTARIUS: "射手座",
    const.CAPRICORN: "摩羯座",
    const.AQUARIUS: "水瓶座",
    const.PISCES: "雙魚座"
}

# 行星名稱對照表
PLANET_NAMES = {
    const.SUN: "太陽",
    const.MOON: "月亮",
    const.MERCURY: "水星",
    const.VENUS: "金星",
    const.MARS: "火星",
    const.JUPITER: "木星",
    const.SATURN: "土星",
    const.URANUS: "天王星",
    const.NEPTUNE: "海王星",
    const.PLUTO: "冥王星",
    const.ASC: "上升點",
    const.MC: "天頂"
}

# 宮位名稱對照表
HOUSE_NAMES = {
    const.HOUSE1: "第一宮",
    const.HOUSE2: "第二宮",
    const.HOUSE3: "第三宮",
    const.HOUSE4: "第四宮",
    const.HOUSE5: "第五宮",
    const.HOUSE6: "第六宮",
    const.HOUSE7: "第七宮",
    const.HOUSE8: "第八宮",
    const.HOUSE9: "第九宮",
    const.HOUSE10: "第十宮",
    const.HOUSE11: "第十一宮",
    const.HOUSE12: "第十二宮"
}

class ChartRequest(BaseModel):
    date: str
    time: str
    lat: float
    lon: float
    tz: float = 8.0  # 預設台灣時區

class UserInput(BaseModel):
    userId: str
    name: str
    gender: str
    birthDate: str  # format: YYYYMMDD
    birthTime: str  # format: HH:MM
    career: Optional[str] = ""
    birthPlace: str
    targetName: Optional[str] = ""
    targetGender: Optional[str] = ""
    targetBirthDate: Optional[str] = ""
    targetBirthTime: Optional[str] = ""
    targetCareer: Optional[str] = ""
    targetBirthPlace: Optional[str] = ""
    content: str
    contentType: str = "unknown"
    ready: bool = True
    latitude: float
    longitude: float

@app.get("/")
def read_root():
    return {"message": "占星API服務正在運行", "version": "1.0.0"}

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    try:
        date = Datetime(req.date, req.time, req.tz)
        pos = GeoPos(req.lat, req.lon)
        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)
        
        ids = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.URANUS, const.NEPTUNE, const.PLUTO,
            const.ASC, const.MC
        ]
        
        result = {}
        for pid in ids:
            obj = chart.get(pid)
            planet_name = PLANET_NAMES.get(pid, pid)
            sign_name = SIGN_NAMES.get(obj.sign, obj.sign)
            house_name = HOUSE_NAMES.get(obj.house, f"第{obj.house}宮")
            
            result[planet_name] = {
                "sign": sign_name,
                "house": house_name,
                "longitude": round(obj.lon, 2),
                "speed": round(obj.speed, 4)
            }
        
        return {
            "status": "success",
            "planets": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

@app.post("/analyze")
def analyze_user_chart(users: List[UserInput]):
    """
    分析用戶的占星圖，返回最重要的行星宮位資訊
    """
    try:
        if not users or len(users) == 0:
            raise HTTPException(status_code=400, detail="請提供用戶資料")
        
        user = users[0]  # 取第一個用戶
        
        # 解析出生日期和時間
        birth_date = user.birthDate  # YYYYMMDD
        birth_time = user.birthTime  # HH:MM
        
        # 格式化日期為 flatlib 需要的格式
        formatted_date = f"{birth_date[:4]}/{birth_date[4:6]}/{birth_date[6:8]}"
        
        # 創建 DateTime 和 GeoPos 物件
        date = Datetime(formatted_date, birth_time, 8.0)  # 台灣時區 UTC+8
        pos = GeoPos(user.latitude, user.longitude)
        
        # 創建占星圖
        chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS)
        
        # 主要行星 ID
        main_planets = [
            const.SUN, const.MOON, const.MERCURY, const.VENUS, const.MARS,
            const.JUPITER, const.SATURN, const.ASC, const.MC
        ]
        
        planets_info = {}
        house_distribution = {}
        
        for pid in main_planets:
            obj = chart.get(pid)
            planet_name = PLANET_NAMES.get(pid, pid)
            sign_name = SIGN_NAMES.get(obj.sign, obj.sign)
            house_name = HOUSE_NAMES.get(obj.house, f"第{obj.house}宮")
            
            planets_info[planet_name] = {
                "星座": sign_name,
                "宮位": house_name,
                "度數": round(obj.lon, 2),
                "宮位數字": obj.house
            }
            
            # 統計宮位分佈
            house_key = f"第{obj.house}宮"
            if house_key not in house_distribution:
                house_distribution[house_key] = []
            house_distribution[house_key].append(planet_name)
        
        # 找出最重要的宮位（行星數量最多的宮位）
        important_houses = sorted(house_distribution.items(), 
                                key=lambda x: len(x[1]), 
                                reverse=True)[:3]
        
        # 重要行星宮位組合
        key_combinations = []
        for house, planets in important_houses:
            key_combinations.append({
                "宮位": house,
                "行星": planets,
                "重要度": len(planets)
            })
        
        return {
            "status": "success",
            "用戶資訊": {
                "姓名": user.name,
                "性別": user.gender,
                "出生日期": f"{birth_date[:4]}-{birth_date[4:6]}-{birth_date[6:8]}",
                "出生時間": birth_time,
                "出生地點": user.birthPlace
            },
            "行星宮位": planets_info,
            "重要宮位組合": key_combinations,
            "宮位分佈": house_distribution
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "astrology-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
