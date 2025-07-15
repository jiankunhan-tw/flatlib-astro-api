from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from typing import List, Optional
import uvicorn
import math
import re
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

def parse_date_string(date_str):
    """解析各種日期格式"""
    try:
        # 移除所有非數字字符，只保留數字
        clean_date = re.sub(r'[^0-9]', '', date_str)
        
        # 確保是8位數字
        if len(clean_date) == 8:
            year = int(clean_date[:4])
            month = int(clean_date[4:6])
            day = int(clean_date[6:8])
            return year, month, day
        
        # 如果不是8位，嘗試其他格式
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                # 假設格式是 YYYY/MM/DD 或 MM/DD/YYYY
                if len(parts[0]) == 4:  # YYYY/MM/DD
                    return int(parts[0]), int(parts[1]), int(parts[2])
                else:  # MM/DD/YYYY
                    return int(parts[2]), int(parts[0]), int(parts[1])
        
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                # 假設格式是 YYYY-MM-DD
                return int(parts[0]), int(parts[1]), int(parts[2])
        
        # 如果都不匹配，拋出錯誤
        raise ValueError(f"無法解析日期格式: {date_str}")
        
    except Exception as e:
        raise ValueError(f"日期解析錯誤: {str(e)}")

def parse_time_string(time_str):
    """解析時間格式"""
    try:
        # 移除空格並處理各種分隔符
        clean_time = time_str.strip().replace(' ', '')
        
        # 處理冒號分隔的時間
        if ':' in clean_time:
            parts = clean_time.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return hour, minute
        
        # 處理4位數字時間 (HHMM)
        if len(clean_time) == 4 and clean_time.isdigit():
            hour = int(clean_time[:2])
            minute = int(clean_time[2:4])
            return hour, minute
        
        # 處理2位數字時間 (HH)
        if len(clean_time) <= 2 and clean_time.isdigit():
            hour = int(clean_time)
            minute = 0
            return hour, minute
        
        # 默認返回12:00
        return 12, 0
        
    except Exception as e:
        # 出錯時返回默認時間
        return 12, 0

def get_julian_day(year, month, day, hour, minute):
    """計算儒略日"""
    try:
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        jd = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        jd = jd + (hour - 12) / 24 + minute / 1440
        return jd
    except Exception as e:
        # 如果計算失敗，返回一個默認值
        return 2451545.0  # 2000年1月1日12:00 UTC

def calculate_sun_position(jd):
    """簡化的太陽位置計算"""
    try:
        n = jd - 2451545.0
        L = (280.460 + 0.9856474 * n) % 360
        g = math.radians((357.528 + 0.9856003 * n) % 360)
        lambda_sun = L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
        return lambda_sun % 360
    except Exception as e:
        # 如果計算失敗，返回一個默認值
        return 0.0

def get_zodiac_sign(longitude):
    """根據經度計算星座"""
    try:
        longitude = longitude % 360  # 確保在0-360範圍內
        sign_number = int(longitude // 30) + 1
        return min(max(sign_number, 1), 12)  # 確保在1-12範圍內
    except Exception as e:
        return 1  # 默認返回白羊座

def calculate_simple_houses(asc_lon, lat):
    """簡化的宮位計算"""
    try:
        houses = {}
        for i in range(1, 13):
            house_cusp = (asc_lon + (i - 1) * 30) % 360
            houses[i] = house_cusp
        return houses
    except Exception as e:
        # 返回默認宮位
        return {i: i * 30 for i in range(1, 13)}

def get_planet_house(planet_lon, houses):
    """計算行星在哪個宮位"""
    try:
        planet_lon = planet_lon % 360  # 確保在0-360範圍內
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
    except Exception as e:
        return 1  # 預設回傳第一宮

def create_sample_chart(birth_date, birth_time, latitude, longitude):
    """創建一個示例占星圖（簡化版）"""
    try:
        # 解析日期時間
        year, month, day = parse_date_string(birth_date)
        hour, minute = parse_time_string(birth_time)
        
        # 驗證日期時間的有效性
        if not (1 <= month <= 12):
            month = 1
        if not (1 <= day <= 31):
            day = 1
        if not (0 <= hour <= 23):
            hour = 12
        if not (0 <= minute <= 59):
            minute = 0
        
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
        # 清理日期字符串，移除所有非數字字符
        clean_date = re.sub(r'[^0-9]', '', req.date)
        
        # 如果清理後的日期不是8位數字，嘗試從原始字符串中解析
        if len(clean_date) != 8:
            try:
                # 嘗試解析不同的日期格式
                if '/' in req.date:
                    parts = req.date.split('/')
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  # YYYY/MM/DD
                            clean_date = f"{parts[0]}{parts[1].zfill(2)}{parts[2].zfill(2)}"
                        else:  # MM/DD/YYYY
                            clean_date = f"{parts[2]}{parts[0].zfill(2)}{parts[1].zfill(2)}"
                elif '-' in req.date:
                    parts = req.date.split('-')
                    if len(parts) == 3:  # YYYY-MM-DD
                        clean_date = f"{parts[0]}{parts[1].zfill(2)}{parts[2].zfill(2)}"
            except:
                # 如果解析失敗，使用默認日期
                clean_date = "20000101"
        
        # 使用簡化版本的計算
        planets = create_sample_chart(clean_date, req.time, req.lat, req.lon)
        
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
    uvicorn.run(app, host="0.0.0.0", port=8080)
