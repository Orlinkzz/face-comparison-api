# Face Comparison API
API sederhana berbasis Flask untuk membandingkan dua gambar wajah menggunakan library `face_recognition`.

## Fitur

- Membandingkan dua gambar wajah dan menentukan apakah wajahnya cocok atau tidak.
- Mendukung CORS agar dapat diakses dari aplikasi front-end lintas domain.
- Logging untuk debugging dan pelacakan aktivitas API.
- Siap dijalankan dalam container Docker.

---

## Instalasi Manual (Opsional)
1. Clone repositori:
   ```bash
   git clone https://github.com/orlinkzz/face-comparison-api.git
   cd face-comparison-api
   ```

2. Buat virtual environment (opsional):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Jalankan server:
   ```bash
   python app.py
   ```

---

## Menjalankan dengan Docker

### 1. **Dockerfile**

```Dockerfile
# Gunakan image dasar Python
FROM python:3.8-slim

# Instal CMake dan dependensi lainnya yang diperlukan untuk membangun dlib
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory di dalam container
WORKDIR /app

# Salin file requirements.txt ke dalam container
COPY requirements.txt /app/

# Install dependensi yang diperlukan
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh file aplikasi ke dalam container
COPY . /app/

# Expose port 5000 agar dapat mengakses aplikasi Flask
EXPOSE 5000

# Tentukan perintah untuk menjalankan aplikasi Flask
CMD ["python", "app.py"]
```

### 2. **docker-compose.yml**

```yaml
services:
  face-recognition-app:
    build: .
    ports:
      - "5000:5000"
    networks:
      - web
    container_name: face_recognition_app

networks:
  web:
    external: true
```

### 3. **Menjalankan dengan Docker Compose**

```bash
docker-compose up --build
```

---

## Endpoint

### `GET /test`

- Mengecek apakah server berjalan.
- **Response:**
  ```json
  {
    "status": "success",
    "message": "Server is running!"
  }
  ```

### `POST /compare_faces`

- Menerima dua gambar (`image1`, `image2`) via form-data.
- **Response sukses:**
  ```json
  {
    "status": "success",
    "message": "Wajah cocok!"
  }
  ```

- **Response gagal atau error:**
  ```json
  {
    "status": "error",
    "message": "Wajah tidak cocok!"
  }
  ```

---

## Contoh Curl
```bash
curl -X POST http://localhost:5000/compare_faces \
  -F "image1=@path/to/image1.jpg" \
  -F "image2=@path/to/image2.jpg"
```

---

## Catatan
- Pastikan hanya satu wajah yang terlihat jelas di setiap gambar.
- `face_recognition` menggunakan `dlib`, yang membutuhkan compiler C++ (`cmake`, `g++`) saat build.
