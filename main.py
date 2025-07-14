@app.get("/chart")
def chart(date: str, time: str, lat: float, lon: float, tz: float):
    try:
        date_parts = date.strip().split('/')
        if len(date_parts) != 3:
            raise ValueError("Invalid date format. Must be YYYY/MM/DD")
        year, month, day = map(int, date_parts)

        time_parts = time.strip().split(':')
        if len(time_parts) != 2:
            raise ValueError("Invalid time format. Must be HH:MM")
        hour, minute = map(int, time_parts)

        jd = julian.Day(year, month, day, hour, minute)

        # 以下這裡放你原本用 flatlib 建 chart 的邏輯...
        # chart = Chart(...)

        return {"message": "成功建立命盤！"}  # 這是測試用，記得換成實際回傳

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Invalid date or time format: {str(e)}"})
