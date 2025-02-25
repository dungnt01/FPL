from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
from collections import defaultdict

# app = Flask(__name__)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Thông tin giải đấu
LEAGUE_ID = 445763  # ID của giải đấu của bạn

# Lấy thông tin về các vòng đấu
def get_all_events():
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Events data:", data["events"])  # In ra danh sách các vòng đấu
        return data["events"]
    else:
        print(f"Failed to fetch events. Status code: {response.status_code}")
        return []
    #     return data["events"]  # Danh sách các vòng đấu
    # else:
    #     return []

# Lấy kết quả Head to Head của một vòng đấu
def get_h2h_matches(LEAGUE_ID, event_id):
    url = f"https://fantasy.premierleague.com/api/leagues-h2h-matches/league/{LEAGUE_ID}/?event={event_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"H2H matches for event {event_id}:", data["results"])  # In ra kết quả các trận đấu
        return data["results"]
    else:
        print(f"Failed to retrieve H2H matches for event {event_id}. Status code: {response.status_code}")
        return []
    #     return data["results"]  # Danh sách các trận đấu
    # else:
    #     print(f"Failed to retrieve H2H matches for event {event_id}. Status code: {response.status_code}")
    #     return []

# Tính điểm cho từng người chơi trong tháng hiện tại


def calculate_current_month_points():
    # Lấy tháng và năm hiện tại
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Lấy danh sách các vòng đấu
    events = get_all_events()

    # Lọc các vòng đấu trong tháng hiện tại
    current_month_events = []
    for event in events:
        event_date = datetime.strptime(event["deadline_time"], "%Y-%m-%dT%H:%M:%SZ")
        if event_date.month == current_month and event_date.year == current_year:
            current_month_events.append(event)

    # Tính điểm cho từng người chơi
    player_points = defaultdict(lambda: {"points": 0, "total_score": 0})

    for event in current_month_events:
        event_id = event["id"]
        event_date = datetime.strptime(event["deadline_time"], "%Y-%m-%dT%H:%M:%SZ")
        is_event_past = event_date < datetime.now()  # Kiểm tra xem vòng đấu đã diễn ra chưa

        matches = get_h2h_matches(LEAGUE_ID, event_id)
        for match in matches:
            entry_1 = match.get("entry_1_name", "Unknown Team 1")  # Tên đội 1
            entry_2 = match.get("entry_2_name", "Unknown Team 2")  # Tên đội 2
            score_1 = match.get("entry_1_points", 0)  # Điểm của đội 1
            score_2 = match.get("entry_2_points", 0)  # Điểm của đội 2

            # Cập nhật tổng điểm (total_score)
            player_points[entry_1]["total_score"] += score_1
            player_points[entry_2]["total_score"] += score_2

            # Chỉ tính điểm thắng, hòa, thua nếu vòng đấu đã diễn ra
            if is_event_past:
                if score_1 > score_2:
                    player_points[entry_1]["points"] += 3
                elif score_1 < score_2:
                    player_points[entry_2]["points"] += 3
                else:
                    player_points[entry_1]["points"] += 1
                    player_points[entry_2]["points"] += 1

    # Sắp xếp bảng điểm theo điểm giảm dần, nếu bằng nhau thì theo tổng điểm giảm dần
    sorted_players = sorted(
        player_points.items(),
        key=lambda x: (x[1]["points"], x[1]["total_score"]),
        reverse=True
    )
    print("Leaderboard data:", sorted_players)  # In ra bảng điểm
    return sorted_players


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
        matches = get_h2h_matches(LEAGUE_ID, event_id)
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
    events = get_all_events()
    now = datetime.now()
    latest_event = None

    # Tìm vòng đấu mới nhất đã kết thúc
    for event in events:
        event_date = datetime.strptime(event["deadline_time"], "%Y-%m-%dT%H:%M:%SZ")
        if event_date < now:
            latest_event = event
        else:
            break

    if latest_event:
        matches = get_h2h_matches(LEAGUE_ID, latest_event["id"])
        return jsonify(matches)
    else:
        return jsonify([])

if __name__ == "__main__":
    app.run(debug=False)
