from flask import Flask, request, jsonify, g
from flask_cors import CORS
from collections import OrderedDict
from threading import Lock
from io import BytesIO
import time
import face_recognition
import numpy as np
import hashlib
import logging
import os

app = Flask(__name__)

@app.before_request
def start_request_timing():
    g.face_timings = {}
    g.face_request_start = time.perf_counter()


@app.after_request
def add_server_timing(response):
    timings = getattr(g, "face_timings", {})

    total_ms = (
        time.perf_counter() - g.face_request_start
    ) * 1000

    timings["total"] = total_ms

    response.headers["Server-Timing"] = ", ".join(
        f"{name};dur={duration:.2f}"
        for name, duration in timings.items()
    )

    return response

# Set up logger for Flask app manually
app.logger.setLevel(logging.INFO)
app.logger = logging.getLogger(__name__)

# Menambahkan logger_name untuk Flask
app.logger_name = "flask_app"  # Menetapkan logger_name agar flask_cors tidak error

# Initialize CORS after setting up logger
CORS(app, resources={r"/compare_faces": {"origins": "*"}})

# Cache encoding foto profil dalam memori.
# Maksimum 1000 encoding, bukan menyimpan seluruh foto.
PROFILE_CACHE_MAX = 1000
profile_cache = OrderedDict()
cache_lock = Lock()

def get_profile_encoding(image_bytes):
    key = hashlib.sha256(image_bytes).hexdigest()

    with cache_lock:
        cached = profile_cache.get(key)
        if cached is not None:
            profile_cache.move_to_end(key)
            return cached

    # Proses mahal dilakukan di luar lock agar request lain
    # tetap bisa memproses encoding.
    image = face_recognition.load_image_file(BytesIO(image_bytes))
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        return None

    encoding = encodings[0]

    with cache_lock:
        # Periksa kembali untuk menangani cache miss bersamaan.
        cached = profile_cache.get(key)
        if cached is not None:
            profile_cache.move_to_end(key)
            return cached

        profile_cache[key] = encoding
        profile_cache.move_to_end(key)

        while len(profile_cache) > PROFILE_CACHE_MAX:
            profile_cache.popitem(last=False)

    return encoding


def get_selfie_encoding(image_bytes):
    image = face_recognition.load_image_file(BytesIO(image_bytes))
    encodings = face_recognition.face_encodings(image)

    return encodings[0] if encodings else None


@app.route("/compare_faces", methods=["POST"])
def compare_faces_api():
    try:
        if "image1" not in request.files or "image2" not in request.files:
            app.logger.error("One or both files are missing.")
            return jsonify({
                "status": "error",
                "message": "File tidak ditemukan!"
            }), 400

        file1 = request.files["image1"]
        file2 = request.files["image2"]

        if not file1.filename or not file2.filename:
            app.logger.error("One or both files are empty.")
            return jsonify({
                "status": "error",
                "message": "Gambar tidak valid!"
            }), 400

        image1_bytes = file1.read()
        image2_bytes = file2.read()

        if not image1_bytes or not image2_bytes:
            return jsonify({
                "status": "error",
                "message": "File gambar kosong!"
            }), 400

        # Encoding profil digunakan kembali jika sudah di-cache.
        start = time.perf_counter()
        encoding1 = get_profile_encoding(image1_bytes)
        g.face_timings["profile_encoding"] = (
            time.perf_counter() - start
        ) * 1000

        start = time.perf_counter()
        encoding2 = get_selfie_encoding(image2_bytes)
        g.face_timings["selfie_encoding"] = (
            time.perf_counter() - start
        ) * 1000

        if encoding1 is None or encoding2 is None:
            app.logger.info("One or both faces not found.")
            return jsonify({
                "status": "error",
                "message": "Wajah tidak ditemukan!",
                "distance": None
            }), 200

        start = time.perf_counter()
        distance = float(
            face_recognition.face_distance(
                [encoding1], encoding2
            )[0]
        )

        g.face_timings["face_compare"] = (
            time.perf_counter() - start
        ) * 1000

        if distance >= 0.6:
            app.logger.info("Faces do not match.")
            return jsonify({
                "status": "error",
                "message": "Wajah tidak cocok!",
                "distance": distance
            }), 200

        if distance < 0.45:
            app.logger.info("Faces match.")
            return jsonify({
                "status": "success",
                "message": "Wajah cocok!",
                "distance": distance
            }), 200

        app.logger.info("Faces match but needs verification")
        return jsonify({
            "status": "pending",
            "message": "Wajah cocok, tapi perlu verifikasi.",
            "distance": distance
        }), 200

    except Exception:
        app.logger.exception("Face recognition failed")
        return jsonify({
            "status": "error",
            "message": "Gagal memproses gambar."
        }), 500


@app.route("/test", methods=["GET"])
def test():
    return jsonify({
        "status": "success",
        "message": "Server is running!"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
