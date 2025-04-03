from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import webbrowser
import threading
import time

import google.generativeai as genai
genai.configure(api_key='AIzaSyB5IZ-7Vi_5ImjwaHmflrSHi__rN6S5G5U')

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# State to track conversation
user_data = {"step": 0, "symptoms": {}, "demographics": {}, "conversation_history": [], "risk_score": 0, "risk_level": "", "bmi": 0}

# Select the Gemini model
model = genai.GenerativeModel('gemini-1.5-pro')

@app.route("/")
def home():
    return render_template("index.html")  # Serve index.html from the templates folder

@app.route("/chat", methods=["POST"])
def chat():
    global user_data
    user_message = request.json["message"].strip()

    # Add user message to conversation history
    user_data["conversation_history"].append({"role": "user", "message": user_message})

    # Initial greeting or reset
    if user_data["step"] == 0 or "start" in user_message.lower():
        user_data = {"step": 1, "symptoms": {}, "demographics": {}, "conversation_history": [], "risk_score": 0, "risk_level": "", "bmi": 0}
        user_data["conversation_history"].append({"role": "bot", "message": "Let’s assess your sleep apnea risk. Do you snore loudly most nights? (Yes/No)"})
        return jsonify({"reply": "Let’s assess your sleep apnea risk. Do you snore loudly most nights? (Yes/No)"})

    # Step 1: Snoring
    if user_data["step"] == 1:
        if "yes" in user_message.lower() or "no" in user_message.lower():
            user_data["symptoms"]["snoring"] = "yes" in user_message.lower()
            user_data["step"] = 2
            user_data["conversation_history"].append({"role": "bot", "message": "Do you often feel tired or sleepy during the day? (Yes/No)"})
            return jsonify({"reply": "Do you often feel tired or sleepy during the day? (Yes/No)"})
        else:
            user_data["conversation_history"].append({"role": "bot", "message": "Please answer with 'Yes' or 'No' to proceed with the assessment."})
            return jsonify({"reply": "Please answer with 'Yes' or 'No' to proceed with the assessment."})

    # Step 2: Tiredness
    elif user_data["step"] == 2:
        if "yes" in user_message.lower() or "no" in user_message.lower():
            user_data["symptoms"]["tiredness"] = "yes" in user_message.lower()
            user_data["step"] = 3
            user_data["conversation_history"].append({"role": "bot", "message": "Have you ever been told you stop breathing during sleep? (Yes/No)"})
            return jsonify({"reply": "Have you ever been told you stop breathing during sleep? (Yes/No)"})
        else:
            user_data["conversation_history"].append({"role": "bot", "message": "Please answer with 'Yes' or 'No' to proceed with the assessment."})
            return jsonify({"reply": "Please answer with 'Yes' or 'No' to proceed with the assessment."})

    # Step 3: Breathing pauses
    elif user_data["step"] == 3:
        if "yes" in user_message.lower() or "no" in user_message.lower():
            user_data["symptoms"]["breathing_pauses"] = "yes" in user_message.lower()
            user_data["step"] = 4
            user_data["conversation_history"].append({"role": "bot", "message": "How old are you? (Please enter your age in years, e.g., 35)"})
            return jsonify({"reply": "How old are you? (Please enter your age in years, e.g., 35)"})
        else:
            user_data["conversation_history"].append({"role": "bot", "message": "Please answer with 'Yes' or 'No' to proceed with the assessment."})
            return jsonify({"reply": "Please answer with 'Yes' or 'No' to proceed with the assessment."})

    # Step 4: Age
    elif user_data["step"] == 4:
        try:
            age = int(user_message)
            user_data["demographics"]["age"] = age
            user_data["step"] = 5
            user_data["conversation_history"].append({"role": "bot", "message": "What’s your weight in kilograms? (e.g., 70)"})
            return jsonify({"reply": "What’s your weight in kilograms? (e.g., 70)"})
        except ValueError:
            user_data["conversation_history"].append({"role": "bot", "message": "Please enter a valid number for your age (e.g., 35)."})
            return jsonify({"reply": "Please enter a valid number for your age (e.g., 35)."})

    # Step 5: Weight
    elif user_data["step"] == 5:
        try:
            weight = float(user_message)
            user_data["demographics"]["weight"] = weight
            user_data["step"] = 6
            user_data["conversation_history"].append({"role": "bot", "message": "What’s your height in centimeters? (e.g., 170)"})
            return jsonify({"reply": "What’s your height in centimeters? (e.g., 170)"})
        except ValueError:
            user_data["conversation_history"].append({"role": "bot", "message": "Please enter a valid number for your weight (e.g., 70)."})
            return jsonify({"reply": "Please enter a valid number for your weight (e.g., 70)."})

    # Step 6: Height (for BMI calculation)
    elif user_data["step"] == 6:
        try:
            height = float(user_message)
            user_data["demographics"]["height"] = height
            user_data["step"] = 7
            user_data["conversation_history"].append({"role": "bot", "message": "What’s your neck circumference in centimeters? (e.g., 40, or type 'unknown' if you don’t know)"})
            return jsonify({"reply": "What’s your neck circumference in centimeters? (e.g., 40, or type 'unknown' if you don’t know)"})
        except ValueError:
            user_data["conversation_history"].append({"role": "bot", "message": "Please enter a valid number for your height (e.g., 170)."})
            return jsonify({"reply": "Please enter a valid number for your height (e.g., 170)."})

    # Step 7: Neck circumference
    elif user_data["step"] == 7:
        if "unknown" in user_message.lower():
            user_data["demographics"]["neck"] = None
        else:
            try:
                neck = float(user_message)
                user_data["demographics"]["neck"] = neck
            except ValueError:
                user_data["conversation_history"].append({"role": "bot", "message": "Please enter a valid number for your neck circumference (e.g., 40) or type 'unknown'."})
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
            risk_level = "HIGH"
            reply = f"Your risk score is {risk_score}. You may be at HIGH risk for sleep apnea. Please consult a doctor soon."
        elif risk_score >= 3:
            risk_level = "MODERATE"
            reply = f"Your risk score is {risk_score}. You may be at MODERATE risk for sleep apnea. Consider monitoring your symptoms and consulting a doctor."
        else:
            risk_level = "LOW"
            reply = f"Your risk score is {risk_score}. Your risk for sleep apnea seems LOW. Keep an eye on your sleep health."

        # Store risk data for use in follow-up questions
        user_data["risk_score"] = risk_score
        user_data["risk_level"] = risk_level
        user_data["bmi"] = bmi
        user_data["conversation_history"].append({"role": "bot", "message": reply})

        return jsonify({"reply": reply})

    # Step 8 and beyond: Use Gemini API for all user prompts
    elif user_data["step"] >= 8:
        try:
            # Construct a detailed prompt for Gemini API
            prompt = (
                f"The user has the following sleep apnea risk profile: "
                f"Age: {user_data['demographics']['age']} years, "
                f"Weight: {user_data['demographics']['weight']} kg, "
                f"Height: {user_data['demographics']['height']} cm, "
                f"BMI: {user_data['bmi']:.1f}, "
                f"Neck Circumference: {user_data['demographics']['neck'] if user_data['demographics']['neck'] else 'unknown'} cm, "
                f"Snoring: {'yes' if user_data['symptoms']['snoring'] else 'no'}, "
                f"Tiredness: {'yes' if user_data['symptoms']['tiredness'] else 'no'}, "
                f"Breathing Pauses: {'yes' if user_data['symptoms']['breathing_pauses'] else 'no'}, "
                f"Risk Score: {user_data['risk_score']}, "
                f"Risk Level: {user_data['risk_level']}. "
                f"Conversation history: {user_data['conversation_history']}. "
                f"The user asked: '{user_message}'. Provide a relevant and helpful response."
            )

            # Generate a response using Gemini API
            response = model.generate_content(prompt, generation_config={"temperature": 0.2})
            reply = response.text

            # Add bot response to conversation history
            user_data["conversation_history"].append({"role": "bot", "message": reply})
        except Exception as e:
            reply = f"Sorry, I encountered an error: {str(e)}. Please try again or type 'start' to begin a new assessment."
            user_data["conversation_history"].append({"role": "bot", "message": reply})

        return jsonify({"reply": reply})

    return jsonify({"reply": "I didn’t understand that. Type 'start' to begin the sleep apnea check."})

def open_browser():
    time.sleep(1)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    # Start the browser in a separate thread
    threading.Thread(target=open_browser).start()
    app.run(debug=True)