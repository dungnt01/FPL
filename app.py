from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Thông tin giải đấu
LEAGUE_ID = 445763  # ID của giải đấu của bạn

# Lấy thông tin về các vòng đấu
def get_all_events():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["events"]  # Danh sách các vòng đấu
    else:
        return []

# Lấy kết quả Head to Head của một vòng đấu
def get_h2h_matches(event_id):
    url = f"https://fantasy.premierleague.com/api/leagues-h2h-matches/league/{LEAGUE_ID}/?event={event_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["results"]  # Danh sách các trận đấu
    else:
        return []

# Tính điểm cho từng người chơi trong tháng hiện tại
def calculate_current_month_points():
    events = get_all_events()
    player_points = defaultdict(lambda: {"points": 0, "total_score": 0})

    # Lấy tháng và năm hiện tại
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    for event in events:
        event_date = datetime.strptime(event["deadline_time"], "%Y-%m-%dT%H:%M:%SZ")
        if event_date.month == current_month and event_date.year == current_year:
            event_id = event["id"]
            is_event_past = event_date < datetime.now()  # Kiểm tra xem vòng đấu đã diễn ra chưa

            matches = get_h2h_matches(event_id)
            for match in matches:
                entry_1 = match["entry_1_name"]  # Tên đội 1
                entry_2 = match["entry_2_name"]  # Tên đội 2
                entry_1_points = match["entry_1_points"]  # Điểm của đội 1
                entry_2_points = match["entry_2_points"]  # Điểm của đội 2
                entry_1_total_score = match["entry_1_total_score"]  # Tổng điểm của đội 1
                entry_2_total_score = match["entry_2_total_score"]  # Tổng điểm của đội 2

                # Cập nhật điểm cho đội 1
                player_points[entry_1]["points"] += entry_1_points
                player_points[entry_1]["total_score"] += entry_1_total_score

                # Cập nhật điểm cho đội 2
                player_points[entry_2]["points"] += entry_2_points
                player_points[entry_2]["total_score"] += entry_2_total_score

    # Sắp xếp bảng xếp hạng theo điểm giảm dần
    sorted_leaderboard = sorted(player_points.items(), key=lambda x: x[1]["points"], reverse=True)
    return sorted_leaderboard

# Lấy kết quả H2H của vòng đấu mới nhất
def get_latest_h2h_results():
    events = get_all_events()
    latest_event = None

    # Tìm vòng đấu mới nhất đã diễn ra
    for event in events:
        event_date = datetime.strptime(event["deadline_time"], "%Y-%m-%dT%H:%M:%SZ")
        if event_date < datetime.now():
            latest_event = event

    if latest_event:
        event_id = latest_event["id"]
        matches = get_h2h_matches(event_id)
        return matches
    else:
        return []

# Trang chủ
@app.route("/")
def home():
    return render_template("index.html")

# API để lấy dữ liệu bảng xếp hạng
@app.route("/api/leaderboard")
def leaderboard():
    leaderboard_data = calculate_current_month_points()
    return jsonify(leaderboard_data)

# API để lấy kết quả H2H của vòng đấu mới nhất
@app.route("/api/latest_h2h")
def latest_h2h():
    h2h_results = get_latest_h2h_results()
    return jsonify(h2h_results)

if __name__ == "__main__":
    app.run(debug=True)
