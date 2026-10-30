# Face Comparison API

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/flask-2.0-lightgrey)

REST API sederhana berbasis **Flask** untuk membandingkan dua foto wajah (**verifikasi wajah / face verification**), misalnya foto profil dan selfie, menggunakan library [`face_recognition`](https://github.com/ageitgey/face_recognition) (dlib). Cocok untuk absensi selfie, e-KYC sederhana, dan validasi foto akun.

> **English:** Open-source, self-hosted face comparison / face verification REST API built with Python, Flask and face_recognition (dlib). Compare a profile photo with a selfie and get a match, pending or no-match result with the face distance. Docker-ready, MIT licensed.

🔗 **Demo/tester:** [orlinkzz.github.io/face-comparison-api](https://orlinkzz.github.io/face-comparison-api/)

## Fitur

- Membandingkan dua wajah dengan tiga hasil: **cocok**, **perlu verifikasi**, atau **tidak cocok**.
- Cache encoding foto profil di memori (LRU, maksimal 1000 entri), sehingga foto profil yang sama tidak diproses ulang.
- Header `Server-Timing` di setiap response untuk memantau durasi tiap tahap.
- CORS aktif untuk `/compare_faces`, sehingga bisa dipanggil dari front-end lintas domain.
- Siap produksi dengan Docker + Gunicorn.
- Halaman tester (`index.html`) dan skrip load test k6.
- Berjalan di Docker dengan **gunicorn** (2 worker).

## Struktur repo

```
.
├── app.py                      # Aplikasi Flask
├── requirements.txt
├── Dockerfile                  # Image produksi (Gunicorn, 4 worker)
├── docker-compose.yml
├── index.html                  # Halaman tester (GitHub Pages)
├── samples/
│   ├── profile.jpg             # Gambar contoh untuk image1
│   └── selfie.jpg              # Gambar contoh untuk image2
└── k6/
    └── face-recognition-test.js  # Load test
```

## Menjalankan

### Dengan Docker (disarankan)

```bash
git clone https://github.com/orlinkzz/face-comparison-api.git
cd face-comparison-api

# docker-compose memakai network eksternal "web"; buat sekali saja
docker network create web

docker compose up -d --build
```

API tersedia di `http://localhost:5000`. Container berjalan dengan Gunicorn (4 worker, timeout 120 detik).

> Build pertama cukup lama (sekitar 5–15 menit) karena `dlib` dikompilasi dari source.

### Manual (development)

Butuh Python 3.11 dan compiler C++ beserta CMake untuk membangun `dlib`:

- **Ubuntu/Debian:** `sudo apt install build-essential cmake libopenblas-dev liblapack-dev`
- **macOS:** `brew install cmake`
- **Windows:** install *Visual Studio Build Tools* (workload "Desktop development with C++") dan CMake

```bash
cd face-recognition
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
pip install -r requirements.txt
python app.py                 # http://localhost:5000
```

`python app.py` memakai server development bawaan Flask. Untuk produksi, gunakan Gunicorn seperti di `Dockerfile`.

## Endpoint

### `GET /test`

Health check.

```json
{ "status": "success", "message": "Server is running!" }
```

### `POST /compare_faces`

Request `multipart/form-data`:

| Field    | Keterangan                                 |
|----------|--------------------------------------------|
| `image1` | Foto profil/referensi (encoding di-cache)  |
| `image2` | Foto selfie yang akan diverifikasi         |

**Response** — hasil perbandingan selalu dikembalikan dengan HTTP `200`, jadi baca field `status`:

| Kondisi                         | `status`  | `message`                            |
|---------------------------------|-----------|--------------------------------------|
| `distance < 0.45`               | `success` | Wajah cocok!                         |
| `0.45 ≤ distance < 0.6`         | `pending` | Wajah cocok, tapi perlu verifikasi.  |
| `distance ≥ 0.6`                | `error`   | Wajah tidak cocok!                   |
| Wajah tidak terdeteksi          | `error`   | Wajah tidak ditemukan! (`distance: null`) |

Contoh:

```json
{
  "status": "success",
  "message": "Wajah cocok!",
  "distance": 0.3412
}
```

**Error lain:**

| HTTP | `message`                 | Penyebab                              |
|------|---------------------------|---------------------------------------|
| 400  | File tidak ditemukan!     | `image1` atau `image2` tidak dikirim  |
| 400  | Gambar tidak valid!       | Nama file kosong                      |
| 400  | File gambar kosong!       | File berukuran 0 byte                 |
| 500  | Gagal memproses gambar.   | Gambar rusak/format tidak didukung    |

**Header `Server-Timing`** (dalam milidetik):

```
Server-Timing: profile_encoding;dur=412.10, selfie_encoding;dur=398.55, face_compare;dur=0.12, total;dur=815.30
```

## Mencoba API

### curl

```bash
curl -X POST http://localhost:5000/compare_faces \
  -F "image1=@samples/profile.jpg" \
  -F "image2=@samples/selfie.jpg"
```

## Konfigurasi (environment)

| Variabel | Default | Keterangan |
|---|---|---|
| `FACE_API_KEY` | _(kosong)_ | Jika diisi, `POST /compare_faces` wajib membawa header `X-Api-Key` yang sama; tanpa itu dijawab `401 Unauthorized`. Harus sama dengan `FACE_RECOGNITION_KEY` di `.env` HR. `GET /test` tetap terbuka. |
| `FACE_MAX_IMAGE_SIDE` | `800` | Sisi terpanjang gambar (px) sebelum deteksi wajah. Gambar juga diputar sesuai EXIF. |
| `FACE_MAX_UPLOAD_MB` | `10` | Batas total upload; di atasnya response `413` `Ukuran gambar terlalu besar!`. |
| `FACE_SLOW_REQUEST_MS` | `5000` | Request lebih lama dari ini dicatat di log (`Slow request ...`) beserta rincian timing. |

`FACE_API_KEY` diisi di `face-recognition/.env` (tidak di-commit dan tidak ikut ke image, lihat `.dockerignore`), lalu diteruskan oleh `docker-compose.yml`:

```bash
cp .env.example .env
sed -i "s/^FACE_API_KEY=.*/FACE_API_KEY=$(openssl rand -hex 32)/" .env
chmod 600 .env
docker compose up -d --build
```

Gunicorn dijalankan dengan `--preload` supaya model dlib dimuat sekali sebelum worker dibuat.

---

### Halaman tester (`index.html`)

`index.html` adalah halaman statis untuk mengunggah dua gambar dan melihat hasilnya: status, distance, dan waktu respons. Gambar dari `samples/` dimuat otomatis.

- **Online:** buka halaman GitHub Pages repo ini, lalu isi URL endpoint dengan alamat API Anda.
- **Lokal:** sajikan lewat server agar gambar contoh bisa dimuat:
  ```bash
  python -m http.server 8080
  # buka http://localhost:8080
  ```

**Mengaktifkan GitHub Pages:** *Settings → Pages → Build and deployment → Source: Deploy from a branch*, pilih branch `main` dan folder `/ (root)`.

> Halaman di GitHub Pages berjalan di HTTPS. Browser mengizinkannya memanggil `http://localhost`, tetapi API di alamat lain harus diakses lewat HTTPS agar tidak diblokir sebagai *mixed content*.

### Load test (k6)

```bash
k6 run -e BASE_URL=https://domain-anda k6/face-recognition-test.js
```

Skrip ini mengirim request ke `${BASE_URL}/face-recognition/compare_faces`, yaitu path di belakang reverse proxy. Skenarionya naik bertahap: 5 → 10 → 20 → 40 → 120 VU, dengan target p95 < 10 detik per tahap.

| Variabel          | Default                   |
|-------------------|---------------------------|
| `BASE_URL`        | `http://10.xxx.xx.xx`     |
| `PROFILE_PHOTO`   | `./profile.jpg`  |
| `SELFIE_PHOTO`    | `./selfie.jpg`   |
| `REQUEST_TIMEOUT` | `60s`                     |
| `VERBOSE`         | `0` (isi `1` untuk log per request) |

## Tips & batasan

- Pastikan hanya **satu wajah** yang terlihat jelas di setiap gambar. Jika ada lebih dari satu, yang dipakai adalah wajah pertama yang terdeteksi.
- Gunakan foto yang cukup terang dan menghadap depan. Ukuran ideal sekitar 500–1000 px; gambar yang lebih besar memperlambat proses.
- Cache encoding disimpan per worker Gunicorn dan hilang saat container di-restart.
- Ambang 0.45 dan 0.6 diatur di `app.py`. Sesuaikan dengan kebutuhan false-positive/false-negative sistem Anda.
- Data wajah adalah data pribadi. Pastikan ada persetujuan pemilik foto dan patuhi regulasi yang berlaku (misalnya UU PDP).

## Gambar contoh

`samples/profile.jpg` dan `samples/selfie.jpg` diambil dari folder [`examples/`](https://github.com/ageitgey/face_recognition/tree/master/examples) proyek `face_recognition` (MIT License). Keduanya adalah foto berbeda dari orang yang sama, sehingga hasil yang diharapkan adalah **cocok**. Gambar ini hanya untuk pengujian.

## Catatan

- Pastikan hanya **satu wajah** yang terlihat jelas di setiap gambar. Jika ada lebih dari satu, yang dipakai adalah wajah pertama yang terdeteksi.
- Cache ada di memori **per worker gunicorn** dan hilang saat container restart.
- Ambang batas (`0.45` dan `0.6`) diatur langsung di `app.py`.
- CORS mengizinkan semua origin (`*`) untuk `/compare_faces`. Batasi di reverse proxy jika perlu.


## Kontribusi

Kontribusi sangat diterima! Baca [CONTRIBUTING.md](CONTRIBUTING.md) untuk alur pull request dan panduan kode.

## Lisensi

Dirilis di bawah [MIT License](LICENSE).
