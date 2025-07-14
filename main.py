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
except Exception as e:
    return JSONResponse(status_code=400, content={"error": f"Invalid date or time format: {str(e)}"})
