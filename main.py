from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback
from typing import List, Optional
import uvicorn
import math
import re
from datetime import datetime, timezone, timedelta

app = FastAPI(title="改進版占星API", description="提供改進版占星圖分析服務", version="2.0.0")

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

def get_julian_day(year, month, day, hour, minute):
    """精確的儒略日計算"""
    try:
        # 調整月份和年份
        if month <= 2:
            year -= 1
            month += 12
        
        # 格里高利曆修正
        A = year // 100
        B = 2 - A + A // 4
        
        # 計算儒略日
        JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5
        
        # 加入時間
        JD += (hour + minute / 60.0) / 24.0
        
        return JD
    except Exception as e:
        return 2451545.0

def calculate_sun_position(jd):
    """改進的太陽位置計算"""
    try:
        # 從J2000.0開始的天數
        n = jd - 2451545.0
        
        # 太陽的平黃經
        L = (280.460 + 0.9856474 * n) % 360
        
        # 太陽的平近點角
        g = math.radians((357.528 + 0.9856003 * n) % 360)
        
        # 太陽的真黃經
        lambda_sun = L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)
        
        return lambda_sun % 360
    except Exception as e:
        return 0.0

def calculate_moon_position(jd):
    """改進的月亮位置計算"""
    try:
        n = jd - 2451545.0
        
        # 月亮的平黃經
        L = (218.316 + 13.176396 * n) % 360
        
        # 月亮的平近點角
        M = (134.963 + 13.064993 * n) % 360
        
        # 太陽的平近點角
        M_sun = (357.528 + 0.9856003 * n) % 360
        
        # 月亮的升交點黃經
        F = (93.272 + 13.229350 * n) % 360
        
        # 計算擾動項
        M_rad = math.radians(M)
        M_sun_rad = math.radians(M_sun)
        F_rad = math.radians(F)
        
        # 主要擾動項
        perturbations = (
            6.289 * math.sin(M_rad) +
            1.274 * math.sin(2 * math.radians(L - 282.9)) +
            0.658 * math.sin(2 * F_rad) +
            0.214 * math.sin(2 * M_rad) +
            -0.186 * math.sin(M_sun_rad) +
            -0.059 * math.sin(2 * M_rad - 2 * F_rad) +
            -0.057 * math.sin(M_rad - 2 * F_rad + M_sun_rad)
        )
        
        lambda_moon = (L + perturbations) % 360
        return lambda_moon
    except Exception as e:
        return 0.0

def calculate_planet_position(jd, planet):
    """改進的行星位置計算（基於VSOP87簡化版）"""
    try:
        n = jd - 2451545.0
        T = n / 36525.0  # 世紀數
        
        # 行星軌道參數（簡化版VSOP87）
        planet_data = {
            "mercury": {
                "L0": 252.250906, "L1": 149472.6746358, "L2": -0.00000536,
                "e": 0.20563069, "a": 0.38709893, "period": 87.969
            },
            "venus": {
                "L0": 181.979801, "L1": 58517.8156760, "L2": 0.00000165,
                "e": 0.00677323, "a": 0.72333199, "period": 224.701
            },
            "mars": {
                "L0": 355.433000, "L1": 19140.2993039, "L2": 0.00000262,
                "e": 0.09341233, "a": 1.52366231, "period": 686.98
            },
            "jupiter": {
                "L0": 34.351519, "L1": 3034.9056606, "L2": -0.00000857,
                "e": 0.04839266, "a": 5.20336301, "period": 4332.59
            },
            "saturn": {
                "L0": 50.077444, "L1": 1222.1138488, "L2": 0.00000021,
                "e": 0.05415060, "a": 9.53707032, "period": 10759.22
            },
            "uranus": {
                "L0": 314.055005, "L1": 428.4669983, "L2": -0.00000486,
                "e": 0.04716771, "a": 19.19126393, "period": 30688.5
            },
            "neptune": {
                "L0": 304.348665, "L1": 218.4862002, "L2": 0.00000059,
                "e": 0.00858587, "a": 30.06896348, "period": 60182
            },
            "pluto": {
                "L0": 238.928, "L1": 145.18, "L2": 0.0,
                "e": 0.2488, "a": 39.48, "period": 90560
            }
        }
        
        if planet not in planet_data:
            return 0.0
        
        data = planet_data[planet]
        
        # 計算平黃經
        L = (data["L0"] + data["L1"] * T + data["L2"] * T * T) % 360
        
        # 計算平近點角
        M = (L - data["L0"]) % 360
        M_rad = math.radians(M)
        
        # 計算真近點角（開普勒方程簡化解）
        E = M_rad + data["e"] * math.sin(M_rad)
        
        # 計算真黃經
        nu = 2 * math.atan(math.sqrt((1 + data["e"]) / (1 - data["e"])) * math.tan(E / 2))
        lambda_planet = (math.degrees(nu) + data["L0"]) % 360
        
        return lambda_planet
    except Exception as e:
        return 0.0

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
    """改進的Placidus宮位制計算"""
    try:
        houses = {}
        
        # 基本軸點
        houses[1] = asc_longitude  # 上升點
        houses[10] = mc_longitude  # 天頂
        houses[7] = (asc_longitude + 180) % 360  # 下降點
        houses[4] = (mc_longitude + 180) % 360  # 天底
        
        # 計算其他宮位（改進版Placidus）
        lat_rad = math.radians(latitude)
        
        # 恆星時角度計算
        asc_mc_diff = (mc_longitude - asc_longitude) % 360
        if asc_mc_diff > 180:
            asc_mc_diff -= 360
        
        # 第2、3宮計算
        try:
            theta2 = math.atan(math.tan(math.radians(asc_mc_diff) / 3) * math.sin(lat_rad))
            theta3 = math.atan(math.tan(math.radians(asc_mc_diff) * 2 / 3) * math.sin(lat_rad))
            
            houses[2] = (asc_longitude + math.degrees(theta2)) % 360
            houses[3] = (asc_longitude + math.degrees(theta3)) % 360
        except:
            houses[2] = (asc_longitude + asc_mc_diff / 3) % 360
            houses[3] = (asc_longitude + asc_mc_diff * 2 / 3) % 360
        
        # 第5、6宮計算（相對於天頂）
        try:
            mc_asc_diff = -asc_mc_diff
            theta5 = math.atan(math.tan(math.radians(mc_asc_diff) / 3) * math.sin(lat_rad))
            theta6 = math.atan(math.tan(math.radians(mc_asc_diff) * 2 / 3) * math.sin(lat_rad))
            
            houses[11] = (mc_longitude + math.degrees(theta5)) % 360
            houses[12] = (mc_longitude + math.degrees(theta6)) % 360
        except:
            houses[11] = (mc_longitude + asc_mc_diff / 3) % 360
            houses[12] = (mc_longitude + asc_mc_diff * 2 / 3) % 360
        
        # 對宮（相差180度）
        houses[5] = (houses[11] + 180) % 360
        houses[6] = (houses[12] + 180) % 360
        houses[8] = (houses[2] + 180) % 360
        houses[9] = (houses[3] + 180) % 360
        
        return houses
    except Exception as e:
        # 備用等宮制
        return {i: (asc_longitude + (i-1) * 30) % 360 for i in range(1, 13)}

def calculate_ascendant_mc(jd, latitude, longitude):
    """計算上升點和天頂"""
    try:
        # 計算恆星時
        T = (jd - 2451545.0) / 36525.0
        
        # 格林威治平恆星時
        GMST = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 
                0.000387933 * T * T - T * T * T / 38710000.0) % 360
        
        # 當地恆星時
        LST = (GMST + longitude) % 360
        
        # 計算太陽位置用於修正
        sun_lon = calculate_sun_position(jd)
        
        # 簡化的上升點計算
        lat_rad = math.radians(latitude)
        lst_rad = math.radians(LST)
        
        # 上升點計算（簡化版）
        asc_lon = (LST + sun_lon / 4 + latitude / 2) % 360
        
        # 天頂計算（簡化版）
        mc_lon = (LST + 90 + latitude / 4) % 360
        
        return asc_lon, mc_lon
    except Exception as e:
        # 備用計算
        sun_lon = calculate_sun_position(jd)
        asc_lon = (sun_lon + latitude + longitude/4) % 360
        mc_lon = (asc_lon + 90) % 360
        return asc_lon, mc_lon

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
    """改進版占星圖計算"""
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
        jd = get_julian_day(year, month, day, hour, minute)
        
        # 計算行星位置
        planet_positions = {
            "太陽": calculate_sun_position(jd),
            "月亮": calculate_moon_position(jd),
            "水星": calculate_planet_position(jd, "mercury"),
            "金星": calculate_planet_position(jd, "venus"),
            "火星": calculate_planet_position(jd, "mars"),
            "木星": calculate_planet_position(jd, "jupiter"),
            "土星": calculate_planet_position(jd, "saturn"),
            "天王星": calculate_planet_position(jd, "uranus"),
            "海王星": calculate_planet_position(jd, "neptune"),
            "冥王星": calculate_planet_position(jd, "pluto"),
        }
        
        # 計算上升點和天頂
        asc_lon, mc_lon = calculate_ascendant_mc(jd, latitude, longitude)
        planet_positions["上升點"] = asc_lon
        planet_positions["天頂"] = mc_lon
        
        # 計算北交點（簡化）
        n = jd - 2451545.0
        north_node = (125.04 - 0.052954 * n) % 360
        planet_positions["北交點"] = north_node
        
        # 計算宮位
        houses = calculate_houses_placidus(asc_lon, mc_lon, latitude)
        
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
    return {"message": "改進版占星API服務正在運行", "version": "2.0.0"}

@app.post("/analyze")
def analyze_user_chart(users: List[UserInput]):
    """分析用戶的占星圖，返回改進格式的行星位置"""
    try:
        if not users or len(users) == 0:
            raise HTTPException(status_code=400, detail="請提供用戶資料")
        
        user = users[0]
        
        # 使用改進計算
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
        
        return {
            "status": "success",
            "計算方法": "改進版天文計算",
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
    """原始的占星圖分析端點（改進版）"""
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
        
        return {
            "status": "success",
            "calculation_method": "改進版天文計算",
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
    return {"status": "healthy", "service": "improved-astrology-api"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
