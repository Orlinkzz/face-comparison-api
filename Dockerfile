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
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
