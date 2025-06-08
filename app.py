from flask import Flask, render_template, request, jsonify
import json
import os
from fuzzywuzzy import fuzz
from textblob import TextBlob

app = Flask(__name__)

threshold = 60
DATA_FILE = "kenny_ai_data.json"
MAX_HISTORY = 5

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
else:
    data = []

conversation_history = []
last_response = ""

synonym_map = {
    "hi": ["hello", "hey", "yo", "sup", "wsg", "wassup"],
    "how are you": ["how's it going", "how are ya", "how you doing", "what's up", "how r u", "how r you", "how are u", "how u doing"],
    "goodbye": ["bye", "goodbye", "later", "cya", "see ya", "gtg", "gotta go"],
    "help": ["can you help me", "i need help", "assist me", "help me out", "can u help me", "need help", "help pls", "help"],
    "you": ["u", "ya"],
    "are": ["r"],
    "okay": ["ok", "k", "alr", "aight", "ight"],
    "nothing": ["nothin", "nun"],
    "yes": ["ye", "yea", "yeah", "yep", "yh", "affirmative", "sure"],
    "no": ["nah", "nope", "nuh uh"],
    "thanks": ["thank you", "thx", "ty", "tysm", "thanx"],
    "what": ["wat", "wut", "wht"],
    "because": ["cuz", "cos", "bc", "cause"]
}

def normalize_input(user_input):
    user_input = user_input.lower()
    words = user_input.split()
    normalized_words = []

    for word in words:
        replaced = False
        for key, synonyms in synonym_map.items():
            if word in synonyms:
                normalized_words.append(key)
                replaced = True
                break
        if not replaced:
            normalized_words.append(word)

    return " ".join(normalized_words)

def get_best_match(user_input):
    max_score = 0
    best_match = None
    for entry in data:
        score = fuzz.ratio(user_input.strip().lower(), entry["prompt"].strip().lower())
        if score > max_score:
            max_score = score
            best_match = entry
    return best_match, max_score

def extract_entities(text):
    blob = TextBlob(text)
    return blob.noun_phrases

def get_contextual_input(history, current_input):
    if history:
        last_user_input = history[-1]["user"]
        return last_user_input + " " + current_input
    return current_input

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global last_response

    user_input = request.json.get("message", "")
    if not user_input.strip():
        return jsonify({"response": "Please say something!"})

    if user_input.strip().lower() == "exit":
        return jsonify({"response": "See ya!"})

    extract_entities(user_input)

    if user_input.lower().strip() in ["no", "nah", "yes", "ok", "maybe", "sure"]:
        contextual_input = get_contextual_input(conversation_history, user_input)
    else:
        contextual_input = user_input

    normalized_input = normalize_input(contextual_input)
    best_match, score = get_best_match(normalized_input)

    if best_match and score >= threshold:
        response = best_match["response"]
        if response == last_response:
            second_best = None
            second_score = 0
            for entry in data:
                entry_score = fuzz.ratio(normalized_input.strip().lower(), entry["prompt"].strip().lower())
                if entry_score > second_score and entry["response"] != last_response:
                    second_best = entry
                    second_score = entry_score
            if second_best and second_score >= threshold - 5:
                response = second_best["response"]
    else:
        response = "I'm still learning, could you teach me how to respond to that?"

    last_response = response
    conversation_history.append({"user": normalized_input, "bot": response})
    if len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)

    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
