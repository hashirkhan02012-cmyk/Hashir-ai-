from flask import Flask, render_template, request, jsonify
import ollama
import re

app = Flask(__name__)

chats = {}
chat_counter = 0
user_name = None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/new_chat", methods=["POST"])
def new_chat():
    global chat_counter

    chat_counter += 1
    chat_id = str(chat_counter)

    chats[chat_id] = {
        "title": "New Chat",
        "messages": []
    }

    return jsonify({
        "chat_id": chat_id,
        "title": "New Chat"
    })


@app.route("/chats", methods=["GET"])
def get_chats():
    result = []

    for chat_id, chat in chats.items():
        result.append({
            "id": chat_id,
            "title": chat["title"]
        })

    return jsonify(result)


@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    data = request.get_json()
    chat_id = data.get("chat_id")

    if chat_id in chats:
        del chats[chat_id]

    return jsonify({
        "success": True
    })


@app.route("/chat", methods=["POST"])
def chat():
    global user_name, chat_counter

    data = request.get_json()

    chat_id = data.get("chat_id")
    user_message = data.get("message", "").strip()

    print("MESSAGE RECEIVED:", repr(user_message))

    if not user_message:
        return jsonify({
            "reply": "Please type a message."
        })

    if chat_id not in chats:
        chat_counter += 1
        chat_id = str(chat_counter)

        chats[chat_id] = {
            "title": "New Chat",
            "messages": []
        }

    current_chat = chats[chat_id]

    # Remember name
    match = re.search(
        r"\bmy name is\s+([a-zA-Z]+)",
        user_message,
        re.IGNORECASE
    )

    if match:
        user_name = match.group(1)

        reply = f"Nice to meet you, {user_name}! 😊 I will remember your name."

        current_chat["messages"].append({
            "role": "user",
            "content": user_message
        })

        current_chat["messages"].append({
            "role": "assistant",
            "content": reply
        })

        return jsonify({
            "reply": reply,
            "chat_id": chat_id,
            "title": current_chat["title"]
        })

    # Check name
    lower_message = user_message.lower()

    if (
        "what is my name" in lower_message
        or "whats my name" in lower_message
        or "do you know my name" in lower_message
        or "tell me my name" in lower_message
    ):
        if user_name:
            reply = f"Your name is {user_name}. 😊"
        else:
            reply = "You haven't told me your name yet."

        return jsonify({
            "reply": reply,
            "chat_id": chat_id
        })

    # Save user message
    current_chat["messages"].append({
        "role": "user",
        "content": user_message
    })

    # Chat title
    if current_chat["title"] == "New Chat":
        title = user_message[:30]

        if len(user_message) > 30:
            title += "..."

        current_chat["title"] = title

    # AI instructions
    messages = [
        {
            "role": "system",
            "content": """
You are Hashir AI.

You are a helpful personal AI assistant.

Always use the conversation history.

Remember information the user tells you.

If the user says their favorite game is GTA V
and later asks what their favorite game is,
answer directly:

Your favorite game is GTA V. 🎮

Do not say you cannot have personal preferences
when the user is asking about information they
previously told you.

Be friendly and concise.
"""
        }
    ]

    if user_name:
        messages.append({
            "role": "system",
            "content": f"The user's name is {user_name}."
        })

    messages.extend(current_chat["messages"])

    # Ollama
    try:
        response = ollama.chat(
            model="gemma3:1b",
            messages=messages
        )

        ai_message = response["message"]["content"]

        current_chat["messages"].append({
            "role": "assistant",
            "content": ai_message
        })

        return jsonify({
            "reply": ai_message,
            "chat_id": chat_id,
            "title": current_chat["title"]
        })

    except Exception as e:
        print("ERROR:", e)

        return jsonify({
            "reply": "Sorry, an error occurred.",
            "chat_id": chat_id
        })


@app.route("/get_chat/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    if chat_id not in chats:
        return jsonify({
            "messages": []
        })

    return jsonify({
        "messages": chats[chat_id]["messages"]
    })


if __name__ == "__main__":
    app.run(debug=True)