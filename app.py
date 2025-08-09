from flask import Flask, jsonify
from flask_cors import CORS
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Allow any origin (no credentials)
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

@app.route("/households", methods=["GET"])
def households():
    sql = "SELECT year, households_with_cars FROM households_cars ORDER BY year ASC"
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/cbd_population", methods=["GET"])
def cbd_population():
    sql = "SELECT year, population FROM melbourne_cbd_population ORDER BY year ASC"
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
