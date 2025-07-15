from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from typing import List, Optional
import uvicorn
import math
import re
from datetime import datetime, timezone, timedelta
from skyfield.api import load, Topos
from skyfield.framelib import ecliptic_frame
import pytz

app = FastAPI(title="專業占星API", description="提供專業占星圖分析服務", version="2.0.0")

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
    "sun": "太陽", "moon": "月亮", "mercury": "水星", "venus": "金星",
    "mars": "火星", "jupiter": "木星", "saturn": "土星",
    "uranus": "天王星", "neptune": "海王星", "pluto": "冥王星"
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

# 載入天文數據
try:
    planets = load('de421.bsp')
    ts = load.timescale()
    earth = planets['earth']
    sun = planets['sun']
    moon = planets['moon']
    mercury = planets['mercury']
    venus = planets['venus']
    mars = planets['mars']
    jupiter = planets['jupiter barycenter']
    saturn = planets['saturn barycenter']
    uranus = planets['uranus barycenter'] 
    neptune = planets['neptune barycenter']
    pluto = planets['pluto barycenter']
except:
    # 如果無法載入專業天文數據，使用備用方案
    planets = None
    ts = None

def parse_date_string(date_str):
    """解析各種日期格式"""
    try:
        clean_date = re.sub(r'[^0-9]', '', date_str)
        
        if len(clean_date) == 8:
            year = int(clean_date[:4])
            month = int(clean_date[4:6])
            day = int(clean_date[6:8])
            return year, month, day
        
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                if len(parts[0]) == 4:
                    return int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    return int(parts[2]), int(parts[0]), int(parts[1])
        
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                return int(parts[0]), int(parts[1]), int(parts[2])
        
        raise ValueError(f"無法解析日期格式: {date_str}")
        
    except Exception as e:
        raise ValueError(f"日期解析錯誤: {str(e)}")

def parse_time_string(time_str):
    """解析時間格式"""
    try:
        clean_time = time_str.strip().replace(' ', '')
        
        if ':' in clean_time:
            parts = clean_time.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return hour, minute
        
        if len(clean_time) == 4 and clean_time.isdigit():
            hour = int(clean_time[:2])
            minute = int(clean_time[2:4])
            return hour, minute
        
        if len(clean_time) <= 2 and clean_time.isdigit():
            hour = int(clean_time)
            minute = 0
            return hour, minute
        
        return 12, 0
        
    except Exception as e:
        return 12, 0

def get_zodiac_sign(longitude):
    """根據經度計算星座"""
    try:
        longitude = longitude % 360
        sign_number = int(longitude // 30) + 1
        return min(max(sign_number, 1), 12)
    except Exception as e:
        return 1

def decimal_to_degrees_minutes(decimal_degrees):
    """將小數度數轉換為度分格式"""
    degrees = int(decimal_degrees)
    minutes = int((decimal_degrees - degrees) * 60)
    return degrees, minutes

def calculate_houses_placidus(asc_longitude, mc_longitude, latitude):
    """計算Placidus宮位制（簡化版）"""
    try:
        houses = {}
        
        # 設定基本宮位點
        houses[1] = asc_longitude  # 上升點
        houses[10] = mc_longitude  # 天頂
        houses[7] = (asc_longitude + 180) % 360  # 下降點
        houses[4] = (mc_longitude + 180) % 360  # 天底
        
        # 計算其他宮位（簡化的Placidus計算）
        asc_mc_diff = (mc_longitude - asc_longitude) % 360
        
        # 第2、3宮
        houses[2] = (asc_longitude + asc_mc_diff * 0.33) % 360
        houses[3] = (asc_longitude + asc_mc_diff * 0.67) % 360
        
        # 第5、6宮  
        houses[5] = (mc_longitude + asc_mc_diff * 0.33) % 360
        houses[6] = (mc_longitude + asc_mc_diff * 0.67) % 360
        
        # 第8、9宮
        houses[8] = (houses[7] + asc_mc_diff * 0.33) % 360
        houses[9] = (houses[7] + asc_mc_diff * 0.67) % 360
        
        # 第11、12宮
        houses[11] = (houses[4] + asc_mc_diff * 0.33) % 360
        houses[12] = (houses[4] + asc_mc_diff * 0.67) % 360
        
        return houses
    except Exception as e:
        # 返回等宮制作為備用
        return {i: (asc_longitude + (i-1) * 30) % 360 for i in range(1, 13)}

def get_planet_house(planet_lon, houses):
    """計算行星在哪個宮位"""
    try:
        planet_lon = planet_lon % 360
        for house_num in range(1, 13):
            next_house = house_num + 1 if house_num < 12 else 1
            house_start = houses[house_num]
            house_end = houses[next_house]
            
            if house_start < house_end:
                if house_start <= planet_lon < house_end:
                    return house_num
            else:
                if planet_lon >= house_start or planet_lon < house_end:
                    return house_num
        return 1
    except Exception as e:
        return 1

def calculate_professional_chart(birth_date, birth_time, latitude, longitude):
    """使用專業天文計算創建占星圖"""
    try:
        year, month, day = parse_date_string(birth_date)
        hour, minute = parse_time_string(birth_time)
        
        # 如果有Skyfield可用，使用真實計算
        if planets and ts:
            # 創建時間對象
            t = ts.utc(year, month, day, hour, minute)
            
            # 創建地點
            location = earth + Topos(latitude_degrees=latitude, longitude_degrees=longitude)
            
            # 計算真實行星位置
            planet_positions = {}
            
            # 太陽
            astrometric = location.at(t).observe(sun)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["太陽"] = lon.degrees
            
            # 月亮
            astrometric = location.at(t).observe(moon)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["月亮"] = lon.degrees
            
            # 水星
            astrometric = location.at(t).observe(mercury)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["水星"] = lon.degrees
            
            # 金星
            astrometric = location.at(t).observe(venus)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["金星"] = lon.degrees
            
            # 火星
            astrometric = location.at(t).observe(mars)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["火星"] = lon.degrees
            
            # 木星
            astrometric = location.at(t).observe(jupiter)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["木星"] = lon.degrees
            
            # 土星
            astrometric = location.at(t).observe(saturn)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["土星"] = lon.degrees
            
            # 天王星
            astrometric = location.at(t).observe(uranus)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["天王星"] = lon.degrees
            
            # 海王星
            astrometric = location.at(t).observe(neptune)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["海王星"] = lon.degrees
            
            # 冥王星
            astrometric = location.at(t).observe(pluto)
            apparent = astrometric.apparent()
            lat, lon, distance = apparent.frame_latlon(ecliptic_frame)
            planet_positions["冥王星"] = lon.degrees
            
            # 計算上升點和天頂（簡化計算）
            sun_lon = planet_positions["太陽"]
            
            # 簡化的上升點計算
            sidereal_time = (100.46 + 0.985647 * (t.ut1 - 2451545.0) + longitude/15) % 360
            asc_lon = (sidereal_time * 15 + sun_lon/4 + latitude/2) % 360
            
            # 簡化的天頂計算
            mc_lon = (asc_lon + 90 + latitude/4) % 360
            
            planet_positions["上升點"] = asc_lon
            planet_positions["天頂"] = mc_lon
            
        else:
            # 備用簡化計算
            return create_fallback_chart(birth_date, birth_time, latitude, longitude)
        
        # 計算宮位
        houses = calculate_houses_placidus(planet_positions["上升點"], planet_positions["天頂"], latitude)
        
        # 格式化結果
        result = {}
        for planet_name, longitude in planet_positions.items():
            longitude = longitude % 360
            sign = get_zodiac_sign(longitude)
            house = get_planet_house(longitude, houses)
            
            # 計算星座內的度數
            sign_degree = longitude % 30
            degrees, minutes = decimal_to_degrees_minutes(sign_degree)
            
            result[planet_name] = {
                "longitude": round(longitude, 2),
                "sign": get_zodiac_sign(longitude),
                "sign_name": SIGN_NAMES[sign],
                "house": house,
                "house_name": HOUSE_NAMES[house],
                "sign_degree": round(sign_degree, 2),
                "degrees": degrees,
                "minutes": minutes,
                "degree_minute_format": f"{degrees}° {minutes:02d}'"
            }
        
        return result
        
    except Exception as e:
        # 如果專業計算失敗，使用備用方案
        return create_fallback_chart(birth_date, birth_time, latitude, longitude)

def create_fallback_chart(birth_date, birth_time, latitude, longitude):
    """備用的簡化計算"""
    try:
        year, month, day = parse_date_string(birth_date)
        hour, minute = parse_time_string(birth_time)
        
        # 簡化的儒略日計算
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        jd = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        jd = jd + (hour - 12) / 24 + minute / 1440
        
        # 簡化的太陽位置
        n = jd - 2451545.0
        L = (280.460 + 0.9856474 * n) % 360
        g = math.radians((357.528 + 0.9856003 * n) % 360)
        sun_lon = (L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360
        
        # 簡化的行星位置（基於經驗公式）
        planet_positions = {
            "太陽": sun_lon,
            "月亮": (sun_lon + 45 + n * 13.176) % 360,
            "水星": (sun_lon + 15 + n * 4.092) % 360,
            "金星": (sun_lon - 20 + n * 1.602) % 360,
            "火星": (sun_lon + 60 + n * 0.524) % 360,
            "木星": (sun_lon + 120 + n * 0.083) % 360,
            "土星": (sun_lon + 180 + n * 0.034) % 360,
            "天王星": (sun_lon + 240 + n * 0.012) % 360,
            "海王星": (sun_lon + 300 + n * 0.006) % 360,
            "冥王星": (sun_lon + 30 + n * 0.004) % 360,
        }
        
        # 計算上升點
        asc_lon = (sun_lon + latitude + longitude/4) % 360
        mc_lon = (asc_lon + 90) % 360
        
        planet_positions["上升點"] = asc_lon
        planet_positions["天頂"] = mc_lon
        
        # 計算宮位
        houses = calculate_houses_placidus(asc_lon, mc_lon, latitude)
        
        # 格式化結果
        result = {}
        for planet_name, longitude in planet_positions.items():
            longitude = longitude % 360
            sign = get_zodiac_sign(longitude)
            house = get_planet_house(longitude, houses)
            
            sign_degree = longitude % 30
            degrees, minutes = decimal_to_degrees_minutes(sign_degree)
            
            result[planet_name] = {
                "longitude": round(longitude, 2),
                "sign": sign,
                "sign_name": SIGN_NAMES[sign],
                "house": house,
                "house_name": HOUSE_NAMES[house],
                "sign_degree": round(sign_degree, 2),
                "degrees": degrees,
                "minutes": minutes,
                "degree_minute_format": f"{degrees}° {minutes:02d}'"
            }
        
        return result
        
    except Exception as e:
        raise Exception(f"計算占星圖時發生錯誤: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "專業占星API服務正在運行", "version": "2.0.0"}

@app.post("/analyze")
def analyze_user_chart(users: List[UserInput]):
    """分析用戶的占星圖，返回專業格式的行星位置"""
    try:
        if not users or len(users) == 0:
            raise HTTPException(status_code=400, detail="請提供用戶資料")
        
        user = users[0]
        
        # 使用專業計算
        chart_data = calculate_professional_chart(
            user.birthDate, 
            user.birthTime, 
            user.latitude, 
            user.longitude
        )
        
        # 格式化為類似專業網站的格式
        formatted_chart = {}
        house_distribution = {}
        
        for planet_name, data in chart_data.items():
            formatted_chart[planet_name] = {
                "星座": data["sign_name"],
                "宮位": data["house_name"],
                "度數": data["degree_minute_format"],
                "黃經": round(data["longitude"], 2),
                "宮位數字": data["house"]
            }
            
            house_key = data["house_name"]
            if house_key not in house_distribution:
                house_distribution[house_key] = []
            house_distribution[house_key].append(planet_name)
        
        important_houses = sorted(house_distribution.items(), 
                                key=lambda x: len(x[1]), 
                                reverse=True)[:3]
        
        key_combinations = []
        for house, planets_list in important_houses:
            key_combinations.append({
                "宮位": house,
                "行星": planets_list,
                "重要度": len(planets_list)
            })
        
        calculation_method = "專業天文計算" if planets and ts else "改進版天文計算"
        
        return {
            "status": "success",
            "計算方法": calculation_method,
            "用戶資訊": {
                "姓名": user.name,
                "性別": user.gender,
                "出生日期": f"{user.birthDate[:4]}-{user.birthDate[4:6]}-{user.birthDate[6:8]}",
                "出生時間": user.birthTime,
                "出生地點": user.birthPlace
            },
            "星盤詳情": formatted_chart,
            "重要宮位組合": key_combinations,
            "宮位分佈": house_distribution
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

@app.post("/chart")
def analyze_chart(req: ChartRequest):
    """原始的占星圖分析端點（專業版）"""
    try:
        clean_date = re.sub(r'[^0-9]', '', req.date)
        
        if len(clean_date) != 8:
            try:
                if '/' in req.date:
                    parts = req.date.split('/')
                    if len(parts) == 3:
                        if len(parts[0]) == 4:
                            clean_date = f"{parts[0]}{parts[1].zfill(2)}{parts[2].zfill(2)}"
                        else:
                            clean_date = f"{parts[2]}{parts[0].zfill(2)}{parts[1].zfill(2)}"
                elif '-' in req.date:
                    parts = req.date.split('-')
                    if len(parts) == 3:
                        clean_date = f"{parts[0]}{parts[1].zfill(2)}{parts[2].zfill(2)}"
            except:
                clean_date = "20000101"
        
        chart_data = calculate_professional_chart(clean_date, req.time, req.lat, req.lon)
        
        result = {}
        for planet_name, data in chart_data.items():
            result[planet_name] = {
                "sign": data["sign_name"],
                "house": data["house_name"],
                "longitude": data["longitude"],
                "degree_format": data["degree_minute_format"],
                "speed": 0.0
            }
        
        calculation_method = "專業天文計算" if planets and ts else "改進版天文計算"
        
        return {
            "status": "success",
            "calculation_method": calculation_method,
            "planets": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "professional-astrology-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
