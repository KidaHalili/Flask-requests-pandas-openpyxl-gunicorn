from flask import Flask, render_template, request, jsonify, send_file
import requests
import pandas as pd
import io
import os

app = Flask(__name__)

# =====================================================
# KONFIGURIME
# =====================================================
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Koordinata fikse – Shkolla Profesionale "Kristo Isak", Berat
ORIGIN_COORDS = "40.70858,19.94492"
ORIGIN_LABEL = 'Shkolla "Kristo Isak", Rruga Desaret, Berat'


# =====================================================
# FUNKSION: DISTANCA NGA GOOGLE DIRECTIONS
# =====================================================
def directions_distance_km(place_id: str) -> float:
    url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": ORIGIN_COORDS,
        "destination": f"place_id:{place_id}",
        "mode": "driving",
        "key": GOOGLE_API_KEY
    }

    r = requests.get(url, params=params, timeout=25).json()

    if r.get("status") != "OK":
        msg = r.get("error_message") or r.get("status") or "Directions error"
        raise RuntimeError(msg)

    meters = r["routes"][0]["legs"][0]["distance"]["value"]
    return meters / 1000.0


# =====================================================
# ROUTE: HOME (INDEX)
# =====================================================
@app.route("/")
def index():
    return render_template(
        "index.html",
        origin=ORIGIN_LABEL,
        defaults={
            "cons": 6.5,     # L / 100km
            "price": 190     # lek / L (Kastrati ref)
        },
        google_key=GOOGLE_API_KEY
    )


# =====================================================
# API: LLOGARITJE PËR NJË RRESHT
# (thirret nga JS sa herë zgjidhet destinacioni)
# =====================================================
@app.route("/api/calc", methods=["POST"])
def api_calc():
    data = request.json or {}

    place_id = data.get("place_id")
    trip = data.get("trip", "oneway")      # oneway | round
    cons = float(data.get("cons", 6.5))    # L/100km
    price = float(data.get("price", 190))  # lek/L

    if not place_id:
        return jsonify(ok=False, error="Place ID mungon"), 400

    try:
        km = directions_distance_km(place_id)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 400

    if trip == "round":
        km *= 2

    fuel_l = (km * cons) / 100
    cost_lek = fuel_l * price

    return jsonify(
        ok=True,
        km=round(km, 3),
        fuel_l=round(fuel_l, 3),
        cost_lek=round(cost_lek, 1)
    )


# =====================================================
# API: EXPORT EXCEL
# =====================================================
@app.route("/export_excel", methods=["POST"])
def export_excel():
    data = request.json or {}
    rows = data.get("rows", [])

    if not rows:
        return jsonify({"error": "Nuk ka të dhëna"}), 400

    df = pd.DataFrame(rows)

    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name="Raport Distanca & Karburant")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="raport_distanca_karburant.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)


