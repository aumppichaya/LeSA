import numpy as np
from fastapi import FastAPI, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from collections import Counter
import pickle
import time
from collections import defaultdict
import random
import string

# ✅ Global Time Variables
test_start_time = datetime(2025, 2, 7, 8, 00, 15)  # ✅ Test case start time
test_real_start = time.time()  # ✅ Real-world start time (for elapsed test time)
time_threshold = None
# ✅ Define Mode: AI-Based vs. Rule-Based
use_rule_based = True  # ✅ Set to `True` to use rule-based logic instead o

def calculate_time_threshold(test_mode: bool):
    """Calculate global time threshold based on test mode."""
    global time_threshold
    if test_mode:
        elapsed_time = time.time() - test_real_start
        simulated_current_time = test_start_time + timedelta(seconds=elapsed_time)
        simulated_past_time = simulated_current_time - timedelta(seconds=30)

        time_threshold = {"$gte": simulated_past_time, "$lte": simulated_current_time}  # ✅ Rolling window
    else:
        # ✅ Real-time mode (fetching last 1 minute)
        real_time_threshold = datetime.utcnow() - timedelta(seconds=30)
        time_threshold = {"$gte": real_time_threshold}

    print(f"🔄 Global time threshold set: {time_threshold}")  # ✅ Debugging print

    return time_threshold

#Load Random Forest Model
with open("LeSA.pkl", "rb") as model_file:
    lesa_model = pickle.load(model_file) 

uname=quote_plus('pichayapromla')
pw = quote_plus('@Ump27082525')
uri= f'mongodb+srv://{uname}:{pw}@lesa.z03pz.mongodb.net/?retryWrites=true&w=majority&appName=LeSA'
client = AsyncIOMotorClient(uri)
db = client['student_behavior']
collection = db['behaviors']


app = FastAPI(title="LeSA API Document", description="ระบบติดตามระดับสมาธิจดจ่อของผู้เรียนในสภาพแวดล้อมการเรียนรู้ออนไลน์แบบประสานเวลา",version="1.0.0")

@app.get('/class-list')
async def get_class_list(generate_new: bool = False):
    """
    Fetch existing class codes and optionally generate a unique 6-character class code.
    """

    # ✅ Generate a unique class code (6 random uppercase letters/numbers)
    new_class_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    existing_class = await collection.find_one({'class_code': new_class_code}, {'_id': 1})
    if not existing_class:
        return {'class_code':new_class_code}
    else:
        return {'class_code':''}




def get_total_models_values(entry):
    """Extracts and sums all numeric values from LeDro, LeEmo, and LeET correctly."""
    total = 0

    # Sum all values inside LeDro
    if "LeDro" in entry:
        total += sum(entry["LeDro"].values())

    # Sum emo_change + all emotion values inside LeEmo
    if "LeEmo" in entry:
        total += entry["LeEmo"].get("emo_change", 0)  # ✅ Sum emo_change
        total += sum(entry["LeEmo"].get("emotion", {}).values())  # ✅ Sum all emotions

    #Sum all values inside LeET
    if "LeET" in entry:
        total += sum(entry["LeET"].values())

    return total

@app.get('/monitor/{class_code}')
async def get_monitor_data(class_code: str, test_mode: bool = False, threshold=Depends(calculate_time_threshold)):
    """Fetch student attention level, screen focus, and online students in a single API call."""
    #Fetch Data from MongoDB (Fetch ONLY Required Fields)
    data_cursor = collection.find(
        {'class_code': class_code, 'timestamp': threshold},
        {'_id': 0, 'student_id': 1, 'LeDro.active': 1, 'LeEmo.emo_change': 1, 
         'LeEmo.emotion': 1, 'LeET.blink_count': 1, 'LeET.eye_close_count': 1, 
         'LeET.on_screen': 1, 'LeET.off_screen': 1}  # ✅ Fetch only required fields
    )
    data = await data_cursor.to_list(length=100)

    if not data:
        return {"message": "No recent student data found.", "error_code": "s01"}

    # ✅ Use defaultdict to avoid redundant key checks
    student_attention = defaultdict(list)
    student_screen_data = defaultdict(list)
    student_active_data = defaultdict(list)
    student_eye_closure_data = defaultdict(list)
    student_emotion_data = defaultdict(list)
    absence = {}

    student_ids = set()

    # ✅ Process Data in a Single Loop
    for entry in data:
        student_id = entry["student_id"]
        student_ids.add(student_id)

        # ✅ Check Absence
        total_models_values = get_total_models_values(entry)
        if total_models_values == 0:
            absence[student_id] = 1
            continue

        # ✅ Use AI Model
        if not use_rule_based:
            # ✅ Predict Attention Level
            predicted_level = lesa_model.predict(np.array([[
                entry["LeDro"]["active"],
                entry["LeEmo"]["emo_change"],
                entry["LeET"]["blink_count"],
                entry["LeET"]["eye_close_count"],
                entry["LeET"]["on_screen"],
                entry["LeET"]["off_screen"]
            ]]))[0]
          # ✅ Use Rule-Based System
        else:
            active = entry["LeDro"]["active"]  
            emo_change = entry["LeEmo"]["emo_change"]  
            blink_count = entry["LeET"]["blink_count"]  
            eye_close_count = entry["LeET"]["eye_close_count"]  
            on_screen = entry["LeET"]["on_screen"]  

            # ✅ High Attention
            if (active >= 40 and
                emo_change <= 10 and
                1 <= blink_count <= 6 and  # ✅ Normal blinking per 3 sec
                eye_close_count <= 1 and
                on_screen >= 41 ):  # ✅ Mostly on-screen
                predicted_level = 3  # ✅ High Attention

            # ✅ Medium Attention
            elif (20 <= active  and
                10 < emo_change <= 20 and
                blink_count <= 20 and  # ✅ Slightly more/less than normal
                eye_close_count <= 3  and
                20 <on_screen ):  # ✅ Sometimes off-screen
                predicted_level = 2  # ✅ Medium Attention

            # ✅ Low Attention
            else:
                predicted_level = 1  # ✅ Low Attention
        student_attention[student_id].append(predicted_level)
        print(f'student_attention[{student_id}] = {predicted_level}')
        # ✅ Screen Focus & Active Data
        student_screen_data[student_id].append(entry["LeET"]["on_screen"])
        student_active_data[student_id].append(entry["LeDro"]["active"])

        # ✅ Track Eye Closure (Convert to Binary: 1 = Closed, 0 = Open)
        student_eye_closure_data[student_id].append(1 if entry["LeET"]["eye_close_count"] > 0 else 0)
        if len(student_eye_closure_data[student_id]) > 6:
            student_eye_closure_data[student_id].pop(0)

        # ✅ Extract the dominant emotion for this timestamp
        emotion_dict = entry["LeEmo"]["emotion"]
        dominant_emotion = max(emotion_dict, key=emotion_dict.get)
        student_emotion_data[student_id].append(dominant_emotion)


    total_students = len(student_ids)

    # ✅ Calculate Attention Level Distribution
    student_mode_levels = [Counter(levels).most_common(1)[0][0] for levels in student_attention.values()]
    attention_count = Counter(student_mode_levels)

    # ✅ Compute Attention Percentages Efficiently
    attention_percentage = {level: int(round((count / total_students) * 100, 0)) for level, count in attention_count.items()}
    highest_category = max(attention_percentage, key=attention_percentage.get, default="NO")
    highest_percentage = attention_percentage.get(highest_category, 0)

    category_map = {3: "High", 2: "Medium", 1: "Low"}
    highest_category = category_map.get(highest_category, "NO")

    # ✅ Find Mode for On-Screen Focus
    students_looking_at_screen = sum(1 for states in student_screen_data.values() if Counter(states).most_common(1)[0][0] > 0)
    screen_focus_percentage = int(round((students_looking_at_screen / total_students) * 100, 0)) if total_students > 0 else 0

    # ✅ Find Mode for Active Engagement (`LeET.active`)
    students_active = sum(1 for states in student_active_data.values() if Counter(states).most_common(1)[0][0] > 0)
    active_percentage = int(round((students_active / total_students) * 100, 0)) if total_students > 0 else 0

    # ✅ Count Students Who Closed Their Eyes in at least 4 out of 6 periods
    students_with_frequent_eye_closure = sum(1 for closures in student_eye_closure_data.values() if sum(closures) >= 4)
    eye_closure_percentage = int(round((students_with_frequent_eye_closure / total_students) * 100, 0)) if total_students > 0 else 0

    # ✅ Find Dominant Emotion for Each Student
    student_dominant_emotions = {student_id: Counter(emotions).most_common(1)[0][0] for student_id, emotions in student_emotion_data.items()}

    # ✅ Find the Overall Dominant Emotion for the Class
    all_dominant_emotions = list(student_dominant_emotions.values())
    overall_dominant_emotion = Counter(all_dominant_emotions).most_common(1)[0][0]

    # ✅ Calculate Percentage of Students with the Overall Dominant Emotion
    students_with_dominant_emotion = sum(1 for emotion in all_dominant_emotions if emotion == overall_dominant_emotion)
    dominant_emotion_percentage = int(round((students_with_dominant_emotion / total_students) * 100, 0)) if total_students > 0 else 0

    # ✅ Calculate Absence %
    total_absence = sum(absence.values())
    absence_percentage = int(round((total_absence / total_students) * 100, 0)) if total_students > 0 else 0

    return {
        "attention_level": highest_category,
        "percentage": highest_percentage,
        "absence_percentage": absence_percentage,
        "on_screen_percentage": screen_focus_percentage,
        "active_percentage": active_percentage,
        "eye_closure_percentage": eye_closure_percentage,
        "emotion": overall_dominant_emotion,
        "emotion_percentage": dominant_emotion_percentage,
        "online_students": list(student_ids)  # ✅ Convert set to list once
    }


@app.get('/emotion-distribution/{class_code}')
async def get_emotion_distribution(class_code: str, test_mode: bool = False, threshold=Depends(calculate_time_threshold)):
    """Fetch emotion distribution for the given class in the last 30 seconds."""
    
    # ✅ ดึงข้อมูลจาก MongoDB
    data_cursor = collection.find({'class_code': class_code, 'timestamp': threshold})
    data = await data_cursor.to_list(length=100)

    if not data:
        return {"message": "No recent emotion data found.", "error_code": "e01"}

    # ✅ เก็บข้อมูลอารมณ์ของผู้เรียนในช่วง 30 วินาทีล่าสุด
    student_emotion_data = {}

    for entry in data:
        student_id = entry["student_id"]

        if student_id not in student_emotion_data:
            student_emotion_data[student_id] = []

        # ✅ หาอารมณ์ที่มีค่าสูงสุดใน entry นี้
        dominant_emotion = max(entry["LeEmo"]["emotion"], key=entry["LeEmo"]["emotion"].get)
        student_emotion_data[student_id].append(dominant_emotion)

    # ✅ หาค่า mode ของแต่ละคน
    student_dominant_emotions = {
        student_id: Counter(emotions).most_common(1)[0][0]
        for student_id, emotions in student_emotion_data.items()
    }

    # ✅ สร้าง dict เก็บจำนวนนักเรียนในแต่ละอารมณ์
    emotion_distribution = Counter(student_dominant_emotions.values())

    return {
        "emotion_distribution": emotion_distribution  # ✅ { "Happy": 5, "Neutral": 8, "Sad": 2, ...}
    }


@app.get('/student-status/{class_code}')
async def get_student_status(class_code: str, test_mode: bool = False, threshold=Depends(calculate_time_threshold)):
    """Fetch lists of absent, off-screen, and eye-closure students within the last 30 seconds."""

    # ✅ Fetch data from the last 30 seconds
    data_cursor = collection.find({'class_code': class_code, 'timestamp': threshold})
    print(f'class_code: {class_code}, timestamp: $gte: {threshold}')
    data = await data_cursor.to_list(length=100)

    if not data:
        return {"message": "No recent student data found.", "error_code": "s01"}

    # ✅ Initialize student lists
    absence_students = set()
    off_screen_students = set()
    eye_closure_students = set()

    # ✅ Process Data (Use `set()` to remove duplicates)
    for entry in data:
        student_id = entry["student_id"]

        # ✅ Check Absence (If all values are zero)
        total_models_values = get_total_models_values(entry)
        if total_models_values == 0:
            absence_students.add(student_id)

        # ✅ Check On-Screen State (Look Away)
        if entry["LeET"]["on_screen"] == 0:
            off_screen_students.add(student_id)

        # ✅ Check Eye Closure (If eye close count > 3)
        if entry["LeET"]["eye_close_count"] > 3:
            eye_closure_students.add(student_id)

    return {
        "absence": list(absence_students),
        "off_screen": list(off_screen_students),
        "eye_closure": list(eye_closure_students)
    }