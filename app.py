from flask import Flask, render_template, request, jsonify
import folium

app = Flask(__name__)

# Store received location in memory (you can use DB instead)
shared_locations = []

@app.route("/")
def index():
    return render_template("index.html")  # Your existing tracker form

@app.route("/share")
def share():
    return render_template("share.html")  # Page for location sharing

@app.route("/receive_location", methods=["POST"])
def receive_location():
    data = request.json
    name = data.get("name", "Unknown")
    lat = data.get("lat")
    lng = data.get("lng")

    shared_locations.append({"name": name, "lat": lat, "lng": lng})
    print(f"📍 Received from {name}: {lat}, {lng}")

    return jsonify({"status": "success", "message": "Location received"})

@app.route("/view_shared")
def view_shared():
    if not shared_locations:
        return "No shared locations yet."

    # Show map with all shared locations
    map_obj = folium.Map(location=[shared_locations[0]["lat"], shared_locations[0]["lng"]], zoom_start=10)
    for loc in shared_locations:
        folium.Marker([loc["lat"], loc["lng"]], popup=loc["name"]).add_to(map_obj)
    return map_obj._repr_html_()

if __name__ == "__main__":
    app.run(debug=True)
