# Panduan Kontribusi

Terima kasih sudah tertarik berkontribusi ke **Face Comparison API**! Laporan bug, usulan fitur, perbaikan dokumentasi, dan pull request semuanya diterima.

## Melaporkan bug

Buka [issue baru](https://github.com/orlinkzz/face-comparison-api/issues) dan sertakan:

- Langkah untuk mereproduksi masalah (sertakan perintah `curl` jika bisa).
- Response yang diterima (JSON dan kode HTTP) serta response yang diharapkan.
- Cara menjalankan API: Docker atau manual, versi Python, dan sistem operasi.
- Potongan log yang relevan.

> **Jangan unggah foto wajah orang lain ke issue publik.** Gunakan gambar di folder `samples/` atau foto Anda sendiri.

## Mengusulkan fitur

Buka issue dengan label `enhancement` dan jelaskan masalah yang ingin diselesaikan, bukan hanya solusinya. Untuk perubahan besar, diskusikan dulu di issue sebelum membuat PR.

## Alur pull request

1. Fork repo, lalu buat branch dari `main`:
   ```bash
   git checkout -b fix/nama-perbaikan
   ```
2. Siapkan environment lokal:
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
3. Buat perubahan, lalu uji minimal:
   ```bash
   curl http://localhost:5000/test
   curl -X POST http://localhost:5000/compare_faces \
     -F "image1=@samples/profile.jpg" \
     -F "image2=@samples/selfie.jpg"
   ```
   Kalau perubahan menyangkut performa, jalankan juga load test di `k6/` (lihat README).
4. Commit dengan pesan yang jelas. Disarankan memakai format [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: tambah endpoint batch compare
   fix: tangani gambar PNG dengan channel alpha
   docs: perbarui contoh curl di README
   ```
5. Push ke fork Anda, lalu buka pull request ke `main`. Jelaskan **apa** yang berubah dan **mengapa**.

## Panduan kode

- Ikuti [PEP 8](https://peps.python.org/pep-0008/).
- Format response JSON harus tetap konsisten: `status` (`success` / `pending` / `error`), `message`, dan `distance` jika ada. Perubahan format adalah *breaking change* bagi client.
- Pesan untuk pengguna akhir ditulis dalam Bahasa Indonesia; log boleh berbahasa Inggris.
- Jangan commit file `.env`, kredensial, atau foto wajah yang bukan milik Anda.
- Jika menambah dependency, perbarui `requirements.txt` dengan versi yang dipin.

## Lisensi

Dengan berkontribusi, Anda setuju bahwa kontribusi Anda dilisensikan di bawah [MIT License](LICENSE) yang sama dengan proyek ini.
