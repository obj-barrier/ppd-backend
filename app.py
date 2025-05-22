# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel
from typing import List
from scripts.csv_db import ( 
    create_user, get_user_by_id, get_user_by_email,
    update_user_preferences, get_preferences_by_user_id,
    create_shopping_session, get_shopping_session, get_shopping_sessions_by_user_id, add_product_page
)
from scripts.assistant_helpers import create_chat_thread, ChatAgent, ProductDescriptionAgent, ComparisonAgent
import openai
import os

from dotenv import load_dotenv
load_dotenv()

MAIN_ASSIST_ID = os.getenv('MAIN_CHAT_ASSIST_ID')
DESCRIPT_ASSIST_ID = os.getenv('DESCRIPT_ASSIST_ID')
COMPARE_ASSIST_ID = os.getenv('COMPARE_ASSIST_ID')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_PERS", "")

print("Creating OpenAI Client")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
print("Client Created")

# Create the agent objects once on startup.
chat_agent = ChatAgent(openai_client, MAIN_ASSIST_ID)
product_description_agent = ProductDescriptionAgent(openai_client, DESCRIPT_ASSIST_ID)
compare_agent = ComparisonAgent(openai_client, COMPARE_ASSIST_ID)

app = Flask(__name__)
CORS(app)

@app.route('/api/users', methods=['POST'])
def api_create_user():
    print("Received request: POST /api/users")
    data = request.json
    print("Data received:", data)
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    new_user = create_user(name, email, password)
    print("User created:", new_user)
    return jsonify(new_user), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    print("Received request: POST /api/login")
    data = request.json
    print("Data received:", data)
    email = data.get("email")
    password = data.get("password")
    # Use the helper function to retrieve a user by email.
    user = get_user_by_email(email)
    if not user or user.get("password") != password:
        print("Invalid login attempt for email:", email)
        return jsonify({"error": "Invalid email or password"}), 401
    print("Login successful for user:", user)
    return jsonify(user), 200

@app.route('/api/users/<user_id>', methods=['GET'])
def api_get_user(user_id):
    print(f"Received request: GET /api/users/{user_id}")
    user = get_user_by_id(user_id)
    if user is None:
        print("User not found for user_id:", user_id)
        return jsonify({"error": "User not found"}), 404
    print("Returning user:", user)
    return jsonify(user), 200

@app.route('/api/users/<user_id>/preferences', methods=['POST'])
def api_set_preferences(user_id):
    print(f"Received request: POST /api/users/{user_id}/preferences")
    data = request.json
    print("Preferences data received:", data)
    prefs_list = data.get('preferences', [])
    updated = update_user_preferences(user_id, prefs_list)
    print("Updated preferences for user", user_id, ":", updated)
    return jsonify({
        "message": "Preferences updated",
        "updated_preferences": updated
    }), 200

@app.route('/api/users/<user_id>/preferences', methods=['GET'])
def api_get_preferences(user_id):
    print(f"Received request: GET /api/users/{user_id}/preferences")
    prefs = get_preferences_by_user_id(user_id)
    print("Returning preferences for user", user_id, ":", prefs)
    return jsonify({"user_id": user_id, "preferences": prefs}), 200

@app.route('/api/users/<user_id>/shopping_sessions', methods=['POST'])
def api_create_session(user_id):
    print(f"Received request: POST /api/users/{user_id}/shopping_sessions")
    data = request.json
    print("Session creation data:", data)
    intent = data.get("intent", "")
    
    # Retrieve the user from CSV.
    user = get_user_by_id(user_id)
    if not user:
        print("User not found for shopping session, user_id:", user_id)
        return jsonify({"error": "User not found"}), 404

    user_preferences = get_preferences_by_user_id(user_id)
    print("User preferences:", user_preferences)
    
    # Create a new thread using the Assistants API.
    print("Creating chat thread via Assistants API...")
    thread_id, initial_messages = create_chat_thread(openai_client, user_preferences, intent)
    print("Chat thread created with thread_id:", thread_id)
    print("Initial messages:", initial_messages)
    
    # Save the new shopping session (with the thread_id) to CSV.
    new_session = create_shopping_session(user_id, intent, thread_id)
    print("Shopping session created:", new_session)
    
    return jsonify(new_session), 201

@app.route('/api/users/<user_id>/sessions', methods=['GET'])
def api_get_user_sessions(user_id):
    print(f"Received request: GET /api/users/{user_id}/sessions")
    sessions = get_shopping_sessions_by_user_id(user_id)
    if not sessions:
        print("No sessions found for user_id:", user_id)
        return jsonify({"error": "No sessions found for this user"}), 404
    print("Returning sessions for user_id:", user_id, sessions)
    return jsonify(sessions), 200

@app.route('/api/shopping_sessions/<session_id>', methods=['GET'])
def api_get_session(session_id):
    print(f"Received request: GET /api/shopping_sessions/{session_id}")
    session = get_shopping_session(session_id)
    if not session:
        print("Session not found for session_id:", session_id)
        return jsonify({"error": "Session not found"}), 404
    print("Returning shopping session:", session)
    return jsonify(session), 200

@app.route('/api/shopping_sessions/<session_id>/messages', methods=['POST'])
def api_add_message(session_id):
    data = request.json
    user_message = data.get("message", "")
    
    session = get_shopping_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    thread_id = session.get("thread_id")
    updated_messages = chat_agent.add_message(thread_id, user_message)
    return jsonify(updated_messages), 200

@app.route('/api/shopping_sessions/<session_id>/product_description', methods=['POST'])
def api_generate_product_description(session_id):
    data = request.json
    product_page = data.get("product_page", "")
    if not product_page:
        return jsonify({"error": "Missing product_page string"}), 400
    
    
    result = product_description_agent.generate_description(session_id, product_page)

    # Save the product page description to the product pages CSV
    add_product_page(session_id, result[0]['content'])
    return jsonify(result), 200

@app.route('/api/shopping_sessions/<session_id>/product_comparison', methods=['POST'])
def api_generate_product_comparison(session_id):
    
    result = compare_agent.generate_comparison(session_id)
    return jsonify(result), 200


# Define our structured response model for extracting user preferences.
class Preference(BaseModel):
    key: str
    value: str

class PreferenceExtraction(BaseModel):
    preferences: List[Preference]

@app.route('/api/shopping_sessions/<session_id>/end', methods=['POST'])
def api_end_shopping_session(session_id):
    """
    Ends a shopping session by analyzing the user's conversation and extracting
    user preferences/insights to update the preferences table for future use.
    
    This endpoint performs the following steps:
      1. Retrieve the shopping session using the session_id.
      2. Get the conversation (chat thread) associated with that session.
      3. Use the Chat Completions API with structured response extraction (using a Pydantic model)
         to extract key user preferences from the conversation.
      4. Call update_user_preferences to update the user's preferences.
      5. Return the updated preferences.
    """
    
    # Retrieve the session and get its thread id.
    session = get_shopping_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    thread_id = session.get("thread_id")
    if not thread_id:
        return jsonify({"error": "No thread associated with this session"}), 400
    
    # Fetch the conversation text from the thread.
    conversation_response = openai_client.beta.threads.messages.list(thread_id=thread_id)
    conversation_text = ""
    for msg in conversation_response.data[::-1]:
        for item in msg.content:
            if item.type == "text":
                conversation_text += item.text.value + "\n"

    # Prepare the system prompt instructing extraction of user preferences.
    system_prompt = (
        "You are an expert at extracting structured user preferences from conversation text.\n "
        "Given the conversation below, extract any key user preferences or insights.\n"
        "Return your result following the provided structure.\n"
        "Some examples of user information you might extract from a conversation:\n"
        "{\n"
        '  "preferences": [\n'
        '    {"key": "Marital Status", "value": "Married"},\n'
        '    {"key": "Career", "value": "Graphic Designer"},\n'
        '    {"key": "Interests", "value": "Digital Design, Travel Documentaries, Baking"},\n'
        '    {"key": "Tech Savviness", "value": "High"}\n'
        "  ]\n"
        "}\n\n"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": conversation_text}
    ]
    
    # Use the structured data extraction feature with the Pydantic model.
    extraction = openai_client.beta.chat.completions.parse(
        model="gpt-4o",  # or another appropriate model version
        messages=messages,
        response_format=PreferenceExtraction
    )
    
    # Extract the structured preferences from the parsed output.
    extracted_prefs = extraction.choices[0].message.parsed
    # Convert extracted preferences to the expected format for update_user_preferences
    pref_list = [{"key": pref.key, "value": pref.value} for pref in extracted_prefs.preferences]
    
    user_id = session.get("user_id")
    updated_preferences = update_user_preferences(user_id, pref_list)
    
    return jsonify({
        "message": "Session ended. Preferences updated.",
        "updated_preferences": pref_list
    }), 200


if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, host='127.0.0.1', port=5000)
