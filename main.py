from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from typing import List, Optional
import uvicorn
import re
from datetime import datetime

app = FastAPI(title="專業占星API", description="使用Kerykeion庫提供專業占星圖分析", version="3.0.0")

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
    "Ari": "白羊座", "Tau": "金牛座", "Gem": "雙子座", "Can": "巨蟹座",
    "Leo": "獅子座", "Vir": "處女座", "Lib": "天秤座", "Sco": "天蠍座",
    "Sag": "射手座", "Cap": "摩羯座", "Aqu": "水瓶座", "Pis": "雙魚座",
    "Aries": "白羊座", "Taurus": "金牛座", "Gemini": "雙子座", "Cancer": "巨蟹座",
    "Leo": "獅子座", "Virgo": "處女座", "Libra": "天秤座", "Scorpio": "天蠍座",
    "Sagittarius": "射手座", "Capricorn": "摩羯座", "Aquarius": "水瓶座", "Pisces": "雙魚座"
}

# 宮位名稱對照表
HOUSE_NAMES = {
    1: "第一宮", 2: "第二宮", 3: "第三宮", 4: "第四宮",
    5: "第五宮", 6: "第六宮", 7: "第七宮", 8: "第八宮",
    9: "第九宮", 10: "第十宮", 11: "第十一宮", 12: "第十二宮"
}

# 行星名稱對照表
PLANET_NAMES_CHINESE = {
    "Sun": "太陽", "Moon": "月亮", "Mercury": "水星", "Venus": "金星",
    "Mars": "火星", "Jupiter": "木星", "Saturn": "土星",
    "Uranus": "天王星", "Neptune": "海王星", "Pluto": "冥王星",
    "North_Node": "北交點", "South_Node": "南交點",
    "First_House": "上升點", "Tenth_House": "天頂"
}

# 嘗試導入Kerykeion
try:
    from kerykeion import AstrologicalSubject
    KERYKEION_AVAILABLE = True
except ImportError:
    KERYKEION_AVAILABLE = False
    print("Kerykeion not available, using fallback calculation")

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

def get_timezone_name(latitude, longitude):
    """根據經緯度推測時區"""
    # 簡化的時區推測，基於經度
    timezone_offset = round(longitude / 15)
    
    # 一些主要城市的時區映射
    city_timezones = {
        # 亞洲
        (25.0, 121.5): "Asia/Taipei",      # 台北
        (39.9, 116.4): "Asia/Shanghai",    # 北京
        (35.7, 139.7): "Asia/Tokyo",       # 東京
        (1.3, 103.8): "Asia/Singapore",    # 新加坡
        # 美洲
        (40.7, -74.0): "America/New_York", # 紐約
        (34.1, -118.2): "America/Los_Angeles", # 洛杉磯
        # 歐洲
        (51.5, -0.1): "Europe/London",     # 倫敦
        (48.9, 2.3): "Europe/Paris",       # 巴黎
    }
    
    # 找最接近的城市
    min_distance = float('inf')
    best_timezone = "UTC"
    
    for (city_lat, city_lon), timezone in city_timezones.items():
        distance = ((latitude - city_lat) ** 2 + (longitude - city_lon) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            best_timezone = timezone
    
    # 如果沒有找到接近的城市，使用UTC偏移
    if min_distance > 10:  # 如果距離太遠，使用UTC偏移
        if timezone_offset >= 0:
            best_timezone = f"Etc/GMT-{timezone_offset}"
        else:
            best_timezone = f"Etc/GMT+{abs(timezone_offset)}"
    
    return best_timezone

def decimal_to_degrees_minutes(decimal_degrees):
    """將小數度數轉換為度分格式"""
    degrees = int(decimal_degrees)
    minutes = int((decimal_degrees - degrees) * 60)
    return degrees, minutes

def format_degree_minute(longitude):
    """格式化度數為 度° 分' 格式"""
    sign_degree = longitude % 30
    degrees, minutes = decimal_to_degrees_minutes(sign_degree)
    return f"{degrees}° {minutes:02d}'"

def calculate_kerykeion_chart(birth_date, birth_time, latitude, longitude, name="User"):
    """使用Kerykeion計算專業占星圖"""
    try:
        if not KERYKEION_AVAILABLE:
            raise Exception("Kerykeion庫不可用")
        
        year, month, day = parse_date_string(birth_date)
        hour, minute = parse_time_string(birth_time)
        
        # 驗證日期時間
        if not (1 <= month <= 12):
            month = 1
        if not (1 <= day <= 31):
            day = 1
        if not (0 <= hour <= 23):
            hour = 12
        if not (0 <= minute <= 59):
            minute = 0
        
        # 獲取時區
        timezone = get_timezone_name(latitude, longitude)
        
        # 創建占星主體
        subject = AstrologicalSubject(
            name=name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            latitude=latitude,
            longitude=longitude,
            tz_str=timezone,
            houses_system="P"  # Placidus宮位制
        )
        
        # 提取行星資料
        result = {}
        
        # 處理主要行星
        for planet_data in subject.planets_degrees_ut:
            planet_name = planet_data['name']
            chinese_name = PLANET_NAMES_CHINESE.get(planet_name, planet_name)
            
            # 獲取星座名稱
            sign_name = SIGN_NAMES.get(planet_data['sign'], planet_data['sign'])
            
            # 獲取宮位
            house_num = planet_data.get('house', 1)
            house_name = HOUSE_NAMES.get(house_num, f"第{house_num}宮")
            
            # 格式化度數
            longitude = planet_data['pos_abs_ut']
            degree_format = format_degree_minute(longitude)
            
            result[chinese_name] = {
                "longitude": round(longitude, 2),
                "sign": planet_data['sign'],
                "sign_name": sign_name,
                "house": house_num,
                "house_name": house_name,
                "degree_format": degree_format,
                "speed": round(planet_data.get('speed', 0), 4)
            }
        
        # 處理宮位點（上升點、天頂等）
        if hasattr(subject, 'houses_degrees_ut'):
            for house_data in subject.houses_degrees_ut:
                if house_data['name'] in ['First_House', 'Tenth_House']:
                    chinese_name = "上升點" if house_data['name'] == 'First_House' else "天頂"
                    
                    sign_name = SIGN_NAMES.get(house_data['sign'], house_data['sign'])
                    longitude = house_data['pos_abs_ut']
                    degree_format = format_degree_minute(longitude)
                    house_num = 1 if house_data['name'] == 'First_House' else 10
                    
                    result[chinese_name] = {
                        "longitude": round(longitude, 2),
                        "sign": house_data['sign'],
                        "sign_name": sign_name,
                        "house": house_num,
                        "house_name": HOUSE_NAMES[house_num],
                        "degree_format": degree_format,
                        "speed": 0.0
                    }
        
        return result
        
    except Exception as e:
        raise Exception(f"Kerykeion計算錯誤: {str(e)}")

def create_fallback_chart(birth_date, birth_time, latitude, longitude):
    """備用的改進計算（如果Kerykeion不可用）"""
    import math
    
    try:
        year, month, day = parse_date_string(birth_date)
        hour, minute = parse_time_string(birth_time)
        
        # 驗證日期時間
        if not (1 <= month <= 12):
            month = 1
        if not (1 <= day <= 31):
            day = 1
        if not (0 <= hour <= 23):
            hour = 12
        if not (0 <= minute <= 59):
            minute = 0
        
        # 計算儒略日
        if month <= 2:
            year -= 1
            month += 12
        
        A = year // 100
        B = 2 - A + A // 4
        JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
        JD += (hour + minute / 60.0) / 24.0
        
        # 簡化的行星位置計算
        n = JD - 2451545.0
        T = n / 36525.0
        
        # 太陽位置
        L = (280.460 + 0.9856474 * n) % 360
        g = math.radians((357.528 + 0.9856003 * n) % 360)
        sun_lon = (L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)) % 360
        
        # 簡化的行星位置
        planet_positions = {
            "太陽": sun_lon,
            "月亮": (218.316 + 13.176396 * n + 6.289 * math.sin(math.radians(134.963 + 13.064993 * n))) % 360,
            "水星": (252.250906 + 149472.6746358 * T) % 360,
            "金星": (181.979801 + 58517.8156760 * T) % 360,
            "火星": (355.433000 + 19140.2993039 * T) % 360,
            "木星": (34.351519 + 3034.9056606 * T) % 360,
            "土星": (50.077444 + 1222.1138488 * T) % 360,
        }
        
        # 計算上升點
        GMST = (280.46061837 + 360.98564736629 * n) % 360
        LST = (GMST + longitude) % 360
        asc_lon = (LST + sun_lon / 4) % 360
        mc_lon = (LST + 90) % 360
        
        planet_positions["上升點"] = asc_lon
        planet_positions["天頂"] = mc_lon
        
        # 格式化結果
        result = {}
        sign_names_by_number = {
            1: "白羊座", 2: "金牛座", 3: "雙子座", 4: "巨蟹座",
            5: "獅子座", 6: "處女座", 7: "天秤座", 8: "天蠍座",
            9: "射手座", 10: "摩羯座", 11: "水瓶座", 12: "雙魚座"
        }
        
        for planet_name, longitude in planet_positions.items():
            longitude = longitude % 360
            sign_num = int(longitude // 30) + 1
            sign_name = sign_names_by_number[sign_num]
            degree_format = format_degree_minute(longitude)
            
            # 簡化的宮位計算
            house_num = int((longitude - asc_lon + 360) // 30) + 1
            if house_num > 12:
                house_num -= 12
            
            result[planet_name] = {
                "longitude": round(longitude, 2),
                "sign": sign_name[:3],
                "sign_name": sign_name,
                "house": house_num,
                "house_name": HOUSE_NAMES[house_num],
                "degree_format": degree_format,
                "speed": 0.0
            }
        
        return result
        
    except Exception as e:
        raise Exception(f"備用計算錯誤: {str(e)}")

@app.get("/")
def read_root():
    kerykeion_status = "可用" if KERYKEION_AVAILABLE else "不可用（使用備用計算）"
    return {
        "message": "專業占星API服務正在運行", 
        "version": "3.0.0",
        "kerykeion_status": kerykeion_status
    }

@app.post("/analyze")
def analyze_user_chart(users: List[UserInput]):
    """分析用戶的占星圖，使用Kerykeion專業計算"""
    try:
        if not users or len(users) == 0:
            raise HTTPException(status_code=400, detail="請提供用戶資料")
        
        user = users[0]
        
        # 嘗試使用Kerykeion，失敗則使用備用計算
        try:
            if KERYKEION_AVAILABLE:
                chart_data = calculate_kerykeion_chart(
                    user.birthDate, 
                    user.birthTime, 
                    user.latitude, 
                    user.longitude,
                    user.name
                )
                calculation_method = "Kerykeion專業計算"
            else:
                raise Exception("Kerykeion不可用")
        except Exception as e:
            print(f"Kerykeion計算失敗: {e}")
            chart_data = create_fallback_chart(
                user.birthDate, 
                user.birthTime, 
                user.latitude, 
                user.longitude
            )
            calculation_method = "改進版備用計算"
        
        # 格式化輸出
        formatted_chart = {}
        house_distribution = {}
        
        for planet_name, data in chart_data.items():
            formatted_chart[planet_name] = {
                "星座": data["sign_name"],
                "宮位": data["house_name"],
                "度數": data["degree_format"],
                "黃經": data["longitude"],
                "宮位數字": data["house"],
                "速度": data["speed"]
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
        
        # 嘗試使用Kerykeion
        try:
            if KERYKEION_AVAILABLE:
                chart_data = calculate_kerykeion_chart(clean_date, req.time, req.lat, req.lon)
                calculation_method = "Kerykeion專業計算"
            else:
                raise Exception("Kerykeion不可用")
        except Exception as e:
            chart_data = create_fallback_chart(clean_date, req.time, req.lat, req.lon)
            calculation_method = "改進版備用計算"
        
        result = {}
        for planet_name, data in chart_data.items():
            result[planet_name] = {
                "sign": data["sign_name"],
                "house": data["house_name"],
                "longitude": data["longitude"],
                "degree_format": data["degree_format"],
                "speed": data["speed"]
            }
        
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
    return {
        "status": "healthy", 
        "service": "professional-astrology-api",
        "kerykeion_available": KERYKEION_AVAILABLE
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
