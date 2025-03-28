from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("motor.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motor_parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            speed INTEGER DEFAULT 1000,
            voltage REAL DEFAULT 220.0,
            current REAL DEFAULT 10.0
        )
    """)
    # 기본 데이터 삽입 (한 개의 행만 유지)
    cursor.execute("SELECT * FROM motor_parameters")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO motor_parameters (speed, voltage, current) VALUES (1000, 220.0, 10.0)")
    conn.commit()
    conn.close()

# 모터 파라미터 조회
def get_motor_parameters():
    conn = sqlite3.connect("motor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM motor_parameters LIMIT 1")
    motor_data = cursor.fetchone()
    conn.close()
    return motor_data

# 모터 파라미터 업데이트 및 변경 로그 출력
def update_motor_parameters(new_speed, new_voltage, new_current):
    conn = sqlite3.connect("motor.db")
    cursor = conn.cursor()

    # 기존 값 가져오기
    cursor.execute("SELECT speed, voltage, current FROM motor_parameters WHERE id=1")
    old_speed, old_voltage, old_current = cursor.fetchone()

    # 변경 사항 출력
    if int(new_speed) != old_speed:
        print(f"모터 파라미터 변경: 속도 - {old_speed} → {new_speed}")
    if float(new_voltage) != old_voltage:
        print(f"모터 파라미터 변경: 전압 - {old_voltage} → {new_voltage}")
    if float(new_current) != old_current:
        print(f"모터 파라미터 변경: 전류 - {old_current} → {new_current}")

    # 값 업데이트
    cursor.execute("UPDATE motor_parameters SET speed=?, voltage=?, current=? WHERE id=1",
                   (new_speed, new_voltage, new_current))
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        speed = request.form["speed"]
        voltage = request.form["voltage"]
        current = request.form["current"]
        update_motor_parameters(speed, voltage, current)
        return redirect(url_for("index"))

    motor_data = get_motor_parameters()
    return render_template("index.html", motor=motor_data)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

