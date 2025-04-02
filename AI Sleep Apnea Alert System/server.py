from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import webbrowser
import threading
import time

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# State to track conversation
user_data = {"step": 0, "symptoms": {}, "demographics": {}}

@app.route("/")
def home():
    return render_template("index.html")  # Serve index.html from the templates folder

@app.route("/chat", methods=["POST"])
def chat():
    global user_data
    user_message = request.json["message"].lower().strip()

    # Initial greeting or reset
    if user_data["step"] == 0 or "start" in user_message:
        user_data = {"step": 1, "symptoms": {}, "demographics": {}}
        return jsonify({"reply": "Let’s assess your sleep apnea risk. Do you snore loudly most nights? (Yes/No)"})

    # Step 1: Snoring
    if user_data["step"] == 1:
        user_data["symptoms"]["snoring"] = "yes" in user_message
        user_data["step"] = 2
        return jsonify({"reply": "Do you often feel tired or sleepy during the day? (Yes/No)"})

    # Step 2: Tiredness
    elif user_data["step"] == 2:
        user_data["symptoms"]["tiredness"] = "yes" in user_message
        user_data["step"] = 3
        return jsonify({"reply": "Have you ever been told you stop breathing during sleep? (Yes/No)"})

    # Step 3: Breathing pauses
    elif user_data["step"] == 3:
        user_data["symptoms"]["breathing_pauses"] = "yes" in user_message
        user_data["step"] = 4
        return jsonify({"reply": "How old are you? (Please enter your age in years, e.g., 35)"})

    # Step 4: Age
    elif user_data["step"] == 4:
        try:
            age = int(user_message)
            user_data["demographics"]["age"] = age
            user_data["step"] = 5
            return jsonify({"reply": "What’s your weight in kilograms? (e.g., 70)"})
        except ValueError:
            return jsonify({"reply": "Please enter a valid number for your age (e.g., 35)."})

    # Step 5: Weight
    elif user_data["step"] == 5:
        try:
            weight = float(user_message)
            user_data["demographics"]["weight"] = weight
            user_data["step"] = 6
            return jsonify({"reply": "What’s your height in centimeters? (e.g., 170)"})
        except ValueError:
            return jsonify({"reply": "Please enter a valid number for your weight (e.g., 70)."})

    # Step 6: Height (for BMI calculation)
    elif user_data["step"] == 6:
        try:
            height = float(user_message)
            user_data["demographics"]["height"] = height
            user_data["step"] = 7
            return jsonify({"reply": "What’s your neck circumference in centimeters? (e.g., 40, or type 'unknown' if you don’t know)"})
        except ValueError:
            return jsonify({"reply": "Please enter a valid number for your height (e.g., 170)."})

    # Step 7: Neck circumference
    elif user_data["step"] == 7:
        if "unknown" in user_message:
            user_data["demographics"]["neck"] = None
        else:
            try:
                neck = float(user_message)
                user_data["demographics"]["neck"] = neck
            except ValueError:
                return jsonify({"reply": "Please enter a valid number for your neck circumference (e.g., 40) or type 'unknown'."})
        
        user_data["step"] = 8

        # Calculate BMI
        height_m = user_data["demographics"]["height"] / 100
        bmi = user_data["demographics"]["weight"] / (height_m * height_m)

        # Risk assessment
        risk_score = 0
        if user_data["symptoms"]["snoring"]: risk_score += 1
        if user_data["symptoms"]["tiredness"]: risk_score += 1
        if user_data["symptoms"]["breathing_pauses"]: risk_score += 2
        if user_data["demographics"]["age"] > 50: risk_score += 1
        if bmi > 30: risk_score += 2
        if user_data["demographics"]["neck"] and user_data["demographics"]["neck"] > 43: risk_score += 1

        # Determine risk level
        if risk_score >= 5:
            reply = f"Your risk score is {risk_score}. You may be at HIGH risk for sleep apnea. Please consult a doctor soon."
        elif risk_score >= 3:
            reply = f"Your risk score is {risk_score}. You may be at MODERATE risk for sleep apnea. Consider monitoring your symptoms and consulting a doctor."
        else:
            reply = f"Your risk score is {risk_score}. Your risk for sleep apnea seems LOW. Keep an eye on your sleep health."

        user_data["step"] = 0  # Reset for next session
        return jsonify({"reply": reply})

    return jsonify({"reply": "I didn’t understand that. Type 'start' to begin the sleep apnea check."})

def open_browser():
    time.sleep(1)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Start the browser in a separate thread
    threading.Thread(target=open_browser).start()
    app.run(debug=True)