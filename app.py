import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Template

# Load .env variables
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")

# Basic sanity check
if not SENDGRID_API_KEY or not SENDER_EMAIL:
    # Log and keep going — the app will return meaningful errors on requests
    logging.warning("SENDGRID_API_KEY or SENDER_EMAIL not set. Add them to your .env file.")

app = Flask(__name__)

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Server is running!"}), 200


# Basic send email route
@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.get_json(silent=True) or {}

    recipient = data.get("email")
    name = data.get("name")

    if not recipient or not name:
        return jsonify({"error": "Missing email or name"}), 400

    # Load template
    try:
        with open("templates/email_template.html", "r", encoding="utf-8") as f:
            template = Template(f.read())
    except FileNotFoundError:
        logging.exception("Email template not found")
        return jsonify({"error": "Email template missing on server"}), 500

    html_content = template.render(name=name)

    try:
        if not SENDGRID_API_KEY:
            return jsonify({"error": "SendGrid API key not configured"}), 500

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=recipient,
            subject="Personalized Email",
            html_content=html_content,
        )
        response = sg.send(message)

        # Prefer 202 for accepted sends; include provider message id for tracking
        msg_id = None
        try:
            msg_id = response.headers.get("X-Message-Id") or response.headers.get("x-message-id")
        except Exception:
            msg_id = None

        return jsonify({
            "message": "Email accepted",
            "status": response.status_code,
            "provider_message_id": msg_id
        }), 202

    except Exception as e:
        # Log full exception server-side but return friendly message to client
        logging.exception("SendGrid error while sending email")
        return jsonify({"error": "Failed to send email (server error)"}), 500


if __name__ == "__main__":
    # debug=True is OK locally; set False before deploying
    app.run(debug=True)
