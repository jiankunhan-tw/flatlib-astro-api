from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from typing import List, Optional
import uvicorn
import math
from datetime import datetime, timezone, timedelta

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
    1: "白羊座", 2: "金牛座", 3: "雙子座", 4: "巨蟹座",
    5: "獅子座", 6: "處女座", 7: "天秤座", 8: "天蠍座",
    9: "射手座", 10: "摩羯座", 11: "水瓶座", 12: "雙魚座"
}

# 行星名稱對照表
PLANET_NAMES = {
    "SUN": "太陽", "MOON": "月亮", "MERCURY": "水星", "VENUS": "金星",
    "MARS": "火星", "JUPITER": "木星", "SATURN": "土星",
    "URANUS": "天王星", "NEPTUNE": "海王星", "PLUTO": "冥王星",
    "ASC": "上升點", "MC": "天頂"
}

# 宮位名稱對照表
HOUSE_NAMES = {
    1: "第一宮", 2: "第二宮", 3: "第三宮", 4: "第四宮",
    5: "第五宮", 6: "第六宮", 7: "第七宮", 8: "第八宮",
    9: "第九宮", 10: "第十宮", 11: "第十一宮", 12: "第十二宮"
}

class ChartRequest(BaseModel):
    date: str
    time: str
    lat: float
    lon: float
    tz: float = 8.0

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

def get_julian_day(year, month, day, hour, minute):
    """計算儒略日"""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jd = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jd + (hour - 12) / 24 + minute / 1440
    return jd

def calculate_sun_position(jd):
    """簡化的太陽位置計算"""
    # 這是一個簡化版本，實際占星需要更精確的計算
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lambda_sun = L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
    return lambda_sun % 360

def get_zodiac_sign(longitude):
    """根據經度計算星座"""
    sign_number = int(longitude // 30) + 1
    return sign_number

def calculate_simple_houses(asc_lon, lat):
    """簡化的宮位計算"""
    houses = {}
    for i in range(1, 13):
        house_cusp = (asc_lon + (i - 1) * 30) % 360
        houses[i] = house_cusp
    return houses

def get_planet_house(planet_lon, houses):
    """計算行星在哪個宮位"""
    for house_num in range(1, 13):
        next_house = house_num + 1 if house_num < 12 else 1
        house_start = houses[house_num]
        house_end = houses[next_house]
        
        if house_start < house_end:
            if house_start <= planet_lon < house_end:
                return house_num
        else:  # 跨越0度
            if planet_lon >= house_start or planet_lon < house_end:
                return house_num
    return 1  # 預設回傳第一宮

def create_sample_chart(birth_date, birth_time, latitude, longitude):
    """創建一個示例占星圖（簡化版）"""
    try:
        # 解析日期時間
        year = int(birth_date[:4])
        month = int(birth_date[4:6])
        day = int(birth_date[6:8])
        hour = int(birth_time[:2])
        minute = int(birth_time[3:5])
        
        # 計算儒略日
        jd = get_julian_day(year, month, day, hour, minute)
        
        # 計算太陽位置（簡化）
        sun_lon = calculate_sun_position(jd)
        
        # 計算上升點（簡化 - 實際需要更複雜的計算）
        asc_lon = (sun_lon + latitude + longitude/4) % 360
        
        # 計算宮位
        houses = calculate_simple_houses(asc_lon, latitude)
        
        # 創建示例行星位置（這裡用簡化的計算）
        planets = {
            "太陽": {
                "longitude": sun_lon,
                "sign": get_zodiac_sign(sun_lon),
                "house": get_planet_house(sun_lon, houses)
            },
            "月亮": {
                "longitude": (sun_lon + 45) % 360,
                "sign": get_zodiac_sign((sun_lon + 45) % 360),
                "house": get_planet_house((sun_lon + 45) % 360, houses)
            },
            "水星": {
                "longitude": (sun_lon + 15) % 360,
                "sign": get_zodiac_sign((sun_lon + 15) % 360),
                "house": get_planet_house((sun_lon + 15) % 360, houses)
            },
            "金星": {
                "longitude": (sun_lon - 20) % 360,
                "sign": get_zodiac_sign((sun_lon - 20) % 360),
                "house": get_planet_house((sun_lon - 20) % 360, houses)
            },
            "火星": {
                "longitude": (sun_lon + 60) % 360,
                "sign": get_zodiac_sign((sun_lon + 60) % 360),
                "house": get_planet_house((sun_lon + 60) % 360, houses)
            },
            "木星": {
                "longitude": (sun_lon + 120) % 360,
                "sign": get_zodiac_sign((sun_lon + 120) % 360),
                "house": get_planet_house((sun_lon + 120) % 360, houses)
            },
            "土星": {
                "longitude": (sun_lon + 180) % 360,
                "sign": get_zodiac_sign((sun_lon + 180) % 360),
                "house": get_planet_house((sun_lon + 180) % 360, houses)
            },
            "上升點": {
                "longitude": asc_lon,
                "sign": get_zodiac_sign(asc_lon),
                "house": 1
            },
            "天頂": {
                "longitude": (asc_lon + 90) % 360,
                "sign": get_zodiac_sign((asc_lon + 90) % 360),
                "house": 10
            }
        }
        
        return planets
        
    except Exception as e:
        raise Exception(f"計算占星圖時發生錯誤: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "占星API服務正在運行", "version": "1.0.0"}

@app.post("/analyze")
def analyze_user_chart(users: List[UserInput]):
    """
    分析用戶的占星圖，返回最重要的行星宮位資訊
    """
    try:
        if not users or len(users) == 0:
            raise HTTPException(status_code=400, detail="請提供用戶資料")
        
        user = users[0]  # 取第一個用戶
        
        # 創建占星圖
        planets = create_sample_chart(user.birthDate, user.birthTime, user.latitude, user.longitude)
        
        # 格式化回傳資料
        planets_info = {}
        house_distribution = {}
        
        for planet_name, planet_data in planets.items():
            sign_name = SIGN_NAMES.get(planet_data["sign"], f"星座{planet_data['sign']}")
            house_name = HOUSE_NAMES.get(planet_data["house"], f"第{planet_data['house']}宮")
            
            planets_info[planet_name] = {
                "星座": sign_name,
                "宮位": house_name,
                "度數": round(planet_data["longitude"], 2),
                "宮位數字": planet_data["house"]
            }
            
            # 統計宮位分佈
            house_key = house_name
            if house_key not in house_distribution:
                house_distribution[house_key] = []
            house_distribution[house_key].append(planet_name)
        
        # 找出最重要的宮位
        important_houses = sorted(house_distribution.items(), 
                                key=lambda x: len(x[1]), 
                                reverse=True)[:3]
        
        # 重要行星宮位組合
        key_combinations = []
        for house, planets_list in important_houses:
            key_combinations.append({
                "宮位": house,
                "行星": planets_list,
                "重要度": len(planets_list)
            })
        
        return {
            "status": "success",
            "用戶資訊": {
                "姓名": user.name,
                "性別": user.gender,
                "出生日期": f"{user.birthDate[:4]}-{user.birthDate[4:6]}-{user.birthDate[6:8]}",
                "出生時間": user.birthTime,
                "出生地點": user.birthPlace
            },
            "行星宮位": planets_info,
            "重要宮位組合": key_combinations,
            "宮位分佈": house_distribution,
            "注意": "這是簡化版本的占星計算，僅供參考"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    """原始的占星圖分析端點"""
    try:
        # 使用簡化版本的計算
        planets = create_sample_chart(req.date.replace("-", ""), req.time, req.lat, req.lon)
        
        result = {}
        for planet_name, planet_data in planets.items():
            sign_name = SIGN_NAMES.get(planet_data["sign"], f"星座{planet_data['sign']}")
            house_name = HOUSE_NAMES.get(planet_data["house"], f"第{planet_data['house']}宮")
            
            result[planet_name] = {
                "sign": sign_name,
                "house": house_name,
                "longitude": round(planet_data["longitude"], 2),
                "speed": 0.0  # 簡化版本不計算速度
            }
        
        return {
            "status": "success",
            "planets": result,
            "note": "這是簡化版本的占星計算"
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
