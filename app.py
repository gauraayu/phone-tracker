from flask import Flask, request, jsonify, render_template, url_for, session, redirect
import requests

app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret"  # Needed for session storage

# ===== CONFIG =====
OWNER_KEY = "Aayu@123"  # Keep this secret
FAST2SMS_API_KEY = "VGhWdnRCx6l7YUkZurKjsvN941LSMHezoE5Pfgy3JQFaBwp8mALdp24931xmji7Z6bPBcyYXSJWVrMnk"
GOOGLE_MAPS_API_KEY = "AIzaSyAANsKxn6vtnwv6W6zpjIQRKk2FcpmKA4M"  # Replace with your actual key

# ===== DATA STORAGE =====
shared_locations = {}     # { phone: {"lat":..., "lng":...} }
active_tracking = {}      # { phone: bool }

# ===== FUNCTIONS =====
def send_sms_via_fast2sms(phone, message):
    """Send SMS using Fast2SMS API."""
    url = "https://www.fast2sms.com/dev/bulk"
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    # Remove + sign and ensure string
    phone_number = phone.replace("+", "").strip()
    payload = {
        "sender_id": "FSTSMS",
        "message": message,
        "language": "english",
        "route": "t",       # transactional
        "numbers": phone_number
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Fast2SMS API Response:", response.text)
    return response.json()


# ===== ROUTES =====

# LOGIN PAGE
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        entered_key = request.form.get("owner_key")
        if entered_key == OWNER_KEY:
            session['owner_key'] = entered_key
            return redirect("/")
        else:
            return render_template("login.html", error="Incorrect Owner Key!")
    return render_template("login.html", error=None)

# DASHBOARD
@app.route("/")
def admin_dashboard():
    if 'owner_key' not in session:
        return redirect("/login")  # Ask for key first

    locations = []
    for phone, loc in shared_locations.items():
        locations.append({
            "phone": phone,
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "active": bool(active_tracking.get(phone, False))
        })
    return render_template(
        "index.html",
        locations=locations,
        admin_key=session['owner_key'],   # Use session key
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )

# SEND LOCATION LINK
@app.route("/send_link", methods=["POST"])
def send_link():
    if 'owner_key' not in session:
        return "Unauthorized", 403

    phone_input = request.form.get("phone")
    if not phone_input:
        return "Missing phone number", 400

    # Split by comma and clean spaces
    phones = [p.strip() for p in phone_input.split(",") if p.strip()]
    sent_links = []

    for phone in phones:
        link = url_for("share_location", phone=phone, _external=True)
        message_body = f"Hi! Please share your current location here: {link}"

        try:
            result = send_sms_via_fast2sms(phone, message_body)
            print(f"Fast2SMS response for {phone}:", result)
        except Exception as e:
            print(f"Error sending SMS to {phone}: {str(e)}")
            continue

        active_tracking[phone] = True
        sent_links.append({"phone": phone, "link": link})

    return render_template("result.html", sent_links=sent_links)

# LOCATION SHARING PAGE
@app.route("/share.html")
def share_location():
    phone = request.args.get("phone")
    if not phone:
        return "Missing phone number.", 400
    if not active_tracking.get(phone, False):
        return "Location sharing disabled for this number.", 403
    return render_template("share.html", phone=phone)

# SUBMIT LOCATION
@app.route("/submit_location", methods=["POST"])
def submit_location():
    phone = request.form.get("phone")
    lat = request.form.get("lat")
    lng = request.form.get("lng")

    if not (phone and lat and lng):
        return "Missing data.", 400
    if not active_tracking.get(phone, False):
        return "Location sharing disabled.", 403

    shared_locations[phone] = {"lat": lat, "lng": lng}
    return render_template("view_shared.html", lat=lat, lng=lng)

# STOP TRACKING
@app.route("/stop_tracking", methods=["POST"])
def stop_tracking():
    if 'owner_key' not in session:
        return "Unauthorized", 403

    phone = request.form.get("phone")
    if not phone:
        return "Missing phone", 400

    active_tracking[phone] = False
    return f"Tracking stopped for {phone}.", 200

# JSON LOCATIONS
@app.route("/locations.json")
def locations_json():
    key = request.args.get("key", "")
    if key != OWNER_KEY:
        return "Unauthorized", 403
    payload = [
        {
            "phone": phone,
            "lat": loc.get("lat"),
            "lng": loc.get("lng"),
            "active": active_tracking.get(phone, False)
        }
        for phone, loc in shared_locations.items()
    ]
    return jsonify(payload)

if __name__ == "__main__":
    app.run(debug=True)
