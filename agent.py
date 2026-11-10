import os
import secrets
import urllib.parse
import urllib.request
import json

from flask import Flask, redirect, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "temporary-secret")

META_APP_ID = os.environ.get("META_APP_ID")
META_APP_SECRET = os.environ.get("META_APP_SECRET")
META_CONFIG_ID = os.environ.get("META_CONFIG_ID")

REDIRECT_URI = os.environ.get(
    "REDIRECT_URI",
    "https://instagram-ai-agent-uoee.onrender.com/auth/callback"
)

@app.route("/")
def home():
    return "Instagram AI Agent is running!"

@app.route("/login")
def login():
    if not all([META_APP_ID, META_CONFIG_ID]):
        return "Meta App settings are missing", 500

    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state

    params = {
        "client_id": META_APP_ID,
        "redirect_uri": REDIRECT_URI,
        "config_id": META_CONFIG_ID,
        "response_type": "code",
        "state": state
    }

    url = "https://www.facebook.com/dialog/oauth?" + urllib.parse.urlencode(params)
    return redirect(url)

@app.route("/auth/callback")
def callback():
    if request.args.get("error"):
        return "Instagram login was cancelled or denied."

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or state != session.get("oauth_state"):
        return "Invalid login response", 400

    if not META_APP_SECRET:
        return "Meta App Secret is missing", 500

    params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    url = "https://graph.facebook.com/v25.0/oauth/access_token?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())

        if "access_token" in result:
            session.pop("oauth_state", None)
            return "Instagram login successful! Token received. Secure storage is the next step."

        return "Token exchange failed: " + str(result), 400

    except Exception:
        return "Could not complete Instagram login. Check Render logs.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
