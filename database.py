import json
import os
import base64 # 추가됨

DB_FILE = "users_data.json"

# [신규 기능] 이미지를 HTML에 넣기 위해 base64로 변환하는 함수
def get_image_base64(image_path):
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def load_all_data():
    if not os.path.exists(DB_FILE):
        save_all_data({})
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError:
        return {}

def save_all_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        # database.py (기존 코드 아래에 추가)

def save_report(username, report_data):
    """
    분석된 리포트 데이터를 유저 데이터에 추가하여 저장합니다.
    report_data 구조 예시: {"date": "2023-12-30", "logic": 80, "emotion": 90, "growth": 10, "summary": "..."}
    """
    all_data = load_all_data()
    if username not in all_data:
        all_data[username] = {"messages": [], "reports": []}
    
    # reports 키가 없으면 생성
    if "reports" not in all_data[username]:
        all_data[username]["reports"] = []
        
    all_data[username]["reports"].append(report_data)
    save_all_data(all_data)

def load_reports(username):
    all_data = load_all_data()
    return all_data.get(username, {}).get("reports", [])

# database.py

def update_user_exp(username, earned_exp):
    """
    유저의 총 경험치(total_exp)를 업데이트하고 저장합니다.
    """
    all_data = load_all_data()
    if username not in all_data:
        all_data[username] = {"messages": [], "total_exp": 0}
    
    # 기존에 경험치 항목이 없으면 0으로 시작
    current_exp = all_data[username].get("total_exp", 0)
    all_data[username]["total_exp"] = current_exp + earned_exp
    
    save_all_data(all_data)
    return all_data[username]["total_exp"]

def get_user_exp(username):
    all_data = load_all_data()
    return all_data.get(username, {}).get("total_exp", 0)

# database.py 맨 아래에 추가

def save_mood_entry(username, date_str, mood_data):
    """
    날짜별 감정 데이터를 저장합니다.
    mood_data 예시: {"color": "#FF5733", "emotion": "열정"}
    """
    all_data = load_all_data()
    if "mood_calendar" not in all_data[username]:
        all_data[username]["mood_calendar"] = {}
    
    # 해당 날짜에 덮어쓰기
    all_data[username]["mood_calendar"][date_str] = mood_data
    save_all_data(all_data)

def get_mood_calendar(username):
    all_data = load_all_data()
    return all_data.get(username, {}).get("mood_calendar", {})