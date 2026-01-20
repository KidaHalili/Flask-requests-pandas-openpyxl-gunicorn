import os
import requests
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# ================= CONFIG =================
ORIGIN_COORDS = "40.70858,19.94492"
ORIGIN_LABEL = 'Shkolla "Kristo Isak", PX38+257, Rruga Desaret, Berat'
DEFAULT_CONS = 6.5
DEFAULT_PRICE = 190.0

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# ==========================================

@app.route("/")
def index():
    return render_template(
        "index.html",
        origin=ORIGIN_LABEL,
        defaults={
            "cons": DEFAULT_CONS,
            "price": DEFAULT_PRICE
        },
        google_key=GOOGLE_API_KEY
    )


def directions_distance_km(place_id: str) -> float:
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": ORIGIN_COORDS,
        "destination": f"place_id:{place_id}",
        "mode": "driving",
        "key": GOOGLE_API_KEY
    }

    r = requests.get(url, params=params, timeout=20).json()

    if r.get("status") != "OK":
        raise RuntimeError(r.get("error_message") or r.get("status"))

    meters = r["routes"][0]["legs"][0]["distance"]["value"]
    return meters / 1000


@app.route("/api/calc", methods=["POST"])
def api_calc():
    try:
        data = request.json
        km = directions_distance_km(data["place_id"])

        if data.get("trip") == "round":
            km *= 2

        cons = float(data["cons"])
        price = float(data["price"])

        fuel = km * cons / 100
        cost = fuel * price

        return jsonify({
            "ok": True,
            "km": round(km, 2),
            "fuel_l": round(fuel, 2),
            "cost_lek": round(cost)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/export_excel", methods=["POST"])
def export_excel():
    payload = request.json
    df = pd.DataFrame(payload["rows"])

    out = BytesIO()
    df.to_excel(out, index=False)
    out.seek(0)

    return send_file(
        out,
        as_attachment=True,
        download_name="raport_distanca_karburant.xlsx"
    )


if __name__ == "__main__":
    app.run(debug=True)
