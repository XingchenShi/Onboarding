import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_conn():
    ssl_params = {}
    if os.getenv("DB_SSL_CA"):
        ssl_params = {"ssl": {"ca": os.getenv("DB_SSL_CA")}}
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
        **ssl_params
    )

def parse_now_and_tz():
    tzname = request.args.get("tz", os.getenv("DEFAULT_TZ", "Australia/Melbourne"))
    now_param = request.args.get("now")

    tz = ZoneInfo(tzname)
    if now_param:
        try:
            try:
                dt = datetime.fromisoformat(now_param)
            except ValueError:
                dt = datetime.fromisoformat(now_param.replace("T", " "))
        except Exception:
            raise ValueError("invalid now parameter")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        else:
            dt = dt.astimezone(tz)
    else:
        dt = datetime.now(tz)

    return dt, tzname

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/parking/active")
def api_parking_active():
    try:
        now_dt, tzname = parse_now_and_tz()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    weekday_iso = now_dt.isoweekday()
    now_time_str = now_dt.strftime("%H:%M:%S")

    sql = """
    SELECT
      CAST(`Zone_Number` AS DOUBLE)             AS `Zone_Number`,
      `KerbsideID`,
      `Location_sensor`,
      CAST(`Latitude_sensor` AS DOUBLE)         AS `Latitude_sensor`,
      CAST(`Longitude_sensor` AS DOUBLE)        AS `Longitude_sensor`,
      CAST(`RoadSegmentID` AS DOUBLE)           AS `RoadSegmentID`,
      `RoadSegmentDescription`,
      `Restriction_Days`,
      TIME_FORMAT(`Time_Restrictions_Start`, '%%H:%%i:%%s') AS `Time_Restrictions_Start`,
      TIME_FORMAT(`Time_Restrictions_Finish`, '%%H:%%i:%%s') AS `Time_Restrictions_Finish`,
      `Restriction_Display`
    FROM `parking_restrictions`
    WHERE
      (
        (`Restriction_Days` = 'Mon-Fri' AND %s BETWEEN 1 AND 5)
        OR
        (`Restriction_Days` = 'Sat-Sun' AND %s IN (6, 7))
        OR
        (`Restriction_Days` IN ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')
          AND (
            (`Restriction_Days`='Mon' AND %s=1) OR
            (`Restriction_Days`='Tue' AND %s=2) OR
            (`Restriction_Days`='Wed' AND %s=3) OR
            (`Restriction_Days`='Thu' AND %s=4) OR
            (`Restriction_Days`='Fri' AND %s=5) OR
            (`Restriction_Days`='Sat' AND %s=6) OR
            (`Restriction_Days`='Sun' AND %s=7)
          )
        )
      )
      AND
      (
        (`Time_Restrictions_Start` <= `Time_Restrictions_Finish`
          AND %s BETWEEN `Time_Restrictions_Start` AND `Time_Restrictions_Finish`)
        OR
        (`Time_Restrictions_Start` > `Time_Restrictions_Finish`
          AND (%s >= `Time_Restrictions_Start` OR %s <= `Time_Restrictions_Finish`))
      )
    """

    params = (
        weekday_iso, weekday_iso,
        weekday_iso, weekday_iso, weekday_iso, weekday_iso, weekday_iso, weekday_iso, weekday_iso,
        now_time_str, now_time_str, now_time_str,
    )

    if os.getenv("DEBUG_SQL") == "1":
        print("SQL:\n", sql)
        print("Params:", params)

    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        # Deduplicate by KerbsideID
        seen = set()
        unique_rows = []
        for row in rows:
            if row["KerbsideID"] not in seen:
                seen.add(row["KerbsideID"])
                unique_rows.append(row)
        rows = unique_rows
        # If count > 200, randomly sample between 100 and 200
        if len(rows) > 200:
            sample_size = random.randint(100, 200)
            rows = random.sample(rows, min(sample_size, len(rows)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return jsonify({
        "now": now_dt.isoformat(),
        "tz": tzname,
        "count": len(rows),
        "items": rows,
    })

@app.get("/api/parking/debug/daytime")
def api_parking_debug_daytime():
    try:
        now_dt, tzname = parse_now_and_tz()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "now": now_dt.isoformat(),
        "tz": tzname,
        "weekday_iso": now_dt.isoweekday(),
        "time": now_dt.strftime("%H:%M:%S"),
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)