from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import logging

app = Flask(__name__)

# Set up logger for Flask app manually
app.logger.setLevel(logging.INFO)
app.logger = logging.getLogger(__name__)

# Menambahkan logger_name untuk Flask
app.logger_name = "flask_app"  # Menetapkan logger_name agar flask_cors tidak error

# Initialize CORS after setting up logger
CORS(app, resources={r"/compare_faces": {"origins": "*"}})

# Fungsi untuk memproses gambar dan membandingkan wajah
def compare_faces(image1, image2):
    # Ekstrak vektor wajah dari kedua gambar
    face_encoding1 = face_recognition.face_encodings(image1)
    face_encoding2 = face_recognition.face_encodings(image2)

    if len(face_encoding1) == 0 or len(face_encoding2) == 0:
        return False  # Tidak ada wajah yang terdeteksi di salah satu gambar

    # Bandingkan wajah berdasarkan vektor fitur
    match = face_recognition.compare_faces([face_encoding1[0]], face_encoding2[0])
    return match[0]  # Mengembalikan True jika wajah cocok, False jika tidak

# Endpoint untuk menerima dan membandingkan dua gambar wajah
@app.route('/compare_faces', methods=['POST'])
def compare_faces_api():
    try:
        # Memeriksa apakah file di-upload
        if 'image1' not in request.files or 'image2' not in request.files:
            app.logger.error("One or both files are missing.")
            return jsonify({"status": "error", "message": "File tidak ditemukan!"})

        file1 = request.files['image1']
        file2 = request.files['image2']

        # Cek apakah file memiliki nama (bukan kosong)
        if file1.filename == '' or file2.filename == '':
            app.logger.error("One or both files are empty.")
            return jsonify({"status": "error", "message": "Gambar tidak valid!"})

        app.logger.info(f"Received file1: {file1.filename}, file2: {file2.filename}")

        # Membaca gambar menggunakan face_recognition
        image1 = face_recognition.load_image_file(file1)
        image2 = face_recognition.load_image_file(file2)

        app.logger.info(f"Loaded image1 with shape: {image1.shape}, image2 with shape: {image2.shape}")

        # Melakukan perbandingan wajah
        result = compare_faces(image1, image2)

        if result:
            app.logger.info("Faces match.")
            return jsonify({"status": "success", "message": "Wajah cocok!"})
        else:
            app.logger.info("Faces do not match.")
            return jsonify({"status": "error", "message": "Wajah tidak cocok!"})

    except Exception as e:
        app.logger.error(f"Error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)})

# Endpoint untuk menguji server
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "success", "message": "Server is running!"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

