import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

import chatbot_config as cfg

load_dotenv()

MODEL_NAME = "gemini-3.1-flash-lite"

app = Flask(__name__)


def get_client():
    api_key = os.getenv("API_KEY")
    if not api_key or api_key == "YOUR_API_KEY":
        return None
    return genai.Client(api_key=api_key)


@app.route("/")
def index():
    return render_template(
        "index.html",
        name=cfg.CHATBOT_NAME,
        domain=cfg.DOMAIN,
        emoji=cfg.EMOJI,
        tagline=cfg.TAGLINE,
        welcome=cfg.WELCOME_MESSAGE,
        topics=cfg.TOPICS,
        suggestions=cfg.SUGGESTIONS,
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "Please type a message."}), 400

    client = get_client()
    if client is None:
        return jsonify({"error": "Gemini API key is missing. Add it to the .env file."}), 500

    contents = []
    for item in history[-20:]:
        role = "user" if item.get("role") == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=str(item.get("text", "")))])
        )
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=cfg.SYSTEM_PROMPT,
                temperature=0.6,
            ),
        )
        return jsonify({"reply": response.text or "Sorry, I could not generate a reply."})
    except Exception:
        return jsonify({"error": "Could not get a reply from Gemini. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
