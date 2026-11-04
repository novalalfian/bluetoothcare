# Panduan Export dan Deploy

Aplikasi ini adalah **server Python** yang menyajikan halaman statis dan API inferensi. Karena itu, aplikasi tidak dapat dijalankan apa adanya di hosting statis seperti GitHub Pages, Netlify, atau Vercel.

Ada dua jalur:

1. **Export** — untuk dikumpulkan, dicadangkan, atau dijalankan di komputer lain.
2. **Online** — untuk demo melalui URL publik.

---

## 1. Export proyek

### Opsi A — ZIP

Dari PowerShell:

```powershell
$source = "D:\New folder (11)"
$items = Get-ChildItem $source -Force | Where-Object {
  $_.Name -notin @(".git", "__pycache__", "logs")
}
Compress-Archive -Path $items.FullName -DestinationPath "D:\BluetoothCare.zip" -Force
```

Berkas hasil: `D:\BluetoothCare.zip`.

Yang tidak perlu dimasukkan:

- `.git/` — riwayat Git, bukan bagian aplikasi,
- `__pycache__/` — cache Python,
- `logs/` — log konsultasi lokal.

### Opsi B — GitHub

Repo proyek: <https://github.com/novalalfian/bluetoothcare>

```powershell
cd "D:\New folder (11)"
git add .
git commit -m "Tambahkan konfigurasi deploy"
git push
```

---

## 2. Deploy ke Render (disarankan)

Render dapat membangun image Docker langsung dari repo. Docker tidak perlu dipasang di komputer lokal.

### Cara A — Blueprint (paling cepat)

1. Buka <https://dashboard.render.com>.
2. Pilih **New +** → **Blueprint**.
3. Hubungkan repo `novalalfian/bluetoothcare`.
4. Render membaca `render.yaml` dan menampilkan service `bluetoothcare`.
5. Klik **Apply** / **Deploy**.
6. Tunggu build selesai, lalu buka URL yang diberikan Render.

Konfigurasi yang dipakai:

- Runtime: Docker
- Health check: `/api/health`
- Auto deploy: aktif setiap push ke branch utama
- Start command: sudah ada di `Dockerfile`

### Cara B — Web Service manual

1. **New +** → **Web Service**.
2. Pilih repo GitHub.
3. Runtime: **Docker**.
4. Health check path: `/api/health`.
5. Deploy.

### Cara C — Native Python

Jika tidak ingin memakai Docker:

- Runtime: **Python 3**
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
python app.py --host 0.0.0.0 --port $PORT --no-browser --no-log
```

- Health check path:

```text
/api/health
```

`requirements.txt` sengaja tidak berisi dependensi karena aplikasi hanya memakai pustaka standar Python.

### Catatan paket gratis Render

- Service akan **tidur** setelah tidak dipakai; permintaan pertama bisa lambat.
- Filesystem bersifat sementara, sehingga log lokal tidak disimpan permanen.
- Karena itu start command memakai `--no-log`.
- URL Render bersifat publik dan **tidak memiliki login**.

---

## 3. Deploy ke Railway

1. Buka <https://railway.app>.
2. **New Project** → **Deploy from GitHub repo**.
3. Pilih repo proyek.
4. Railway mendeteksi `Dockerfile`; variabel `PORT` diberikan otomatis.
5. Setelah deploy, buka **Settings** → **Networking** → **Generate Domain**.

`Procfile` juga disediakan untuk platform yang memakai model Procfile:

```text
web: python app.py --host 0.0.0.0 --port $PORT --no-browser --no-log
```

---

## 4. Deploy ke VPS

Contoh untuk Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y python3 git
sudo git clone https://github.com/novalalfian/bluetoothcare.git /opt/bluetoothcare
cd /opt/bluetoothcare
python3 app.py --host 127.0.0.1 --port 8000 --no-browser --no-log
```

Agar berjalan terus, buat service systemd:

```ini
[Unit]
Description=BluetoothCare
After=network.target

[Service]
WorkingDirectory=/opt/bluetoothcare
ExecStart=/usr/bin/python3 app.py --host 127.0.0.1 --port 8000 --no-browser --no-log
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

Simpan sebagai `/etc/systemd/system/bluetoothcare.service`, lalu:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bluetoothcare
```

Pasang reverse proxy Caddy untuk HTTPS:

```text
bluetoothcare.domainanda.com {
    reverse_proxy 127.0.0.1:8000
}
```

---

## 5. Demo sementara tanpa deploy

Cocok untuk presentasi singkat. Komputer harus tetap menyala.

```powershell
python app.py --no-browser
cloudflared tunnel --url http://127.0.0.1:8000
```

atau dengan ngrok:

```powershell
ngrok http 8000
```

Hentikan tunnel setelah demo selesai. URL sementara dapat diakses siapa pun yang memilikinya.

---

## 6. Hosting yang tidak cocok

| Layanan | Alasan |
| --- | --- |
| GitHub Pages | Hanya berkas statis; tidak menjalankan Python |
| Netlify | Tidak menjalankan proses Python `app.py` |
| Vercel | Tidak menjalankan server Python ini apa adanya |
| PythonAnywhere | Model WSGI berbeda; perlu adaptasi khusus |

Jika ingin benar-benar statis, mesin inferensi harus ditulis ulang dalam JavaScript agar berjalan di browser. Itu perubahan besar dan menduplikasi logika, jadi tidak disarankan untuk versi ini.

---

## 7. Keamanan untuk versi online

Aplikasi ini tidak meminta data pribadi, tetapi **belum memiliki autentikasi**. Siapa pun yang memiliki URL dapat membuka halaman dan memanggil API.

- Gunakan `--no-log` pada deployment publik.
- Jangan mengaktifkan log berisi data sensitif.
- Hentikan tunnel setelah demo.
- Untuk penggunaan nyata, tambahkan basic auth, rate limiting, dan pemantauan.
- Jangan gunakan wildcard `safe.directory` pada Git.
- Batasi ukuran request bila memakai reverse proxy.

---

## 8. Pemeriksaan setelah deploy

Buka:

```text
https://URL-ANDA/api/health
```

Respons yang diharapkan:

```json
{"status":"ok","facts":20,"rules":31,"conclusions":19}
```

Lalu uji:

1. Halaman beranda terbuka.
2. Form menampilkan 20 pertanyaan (mode semua perangkat); pilih jenis perangkat untuk menyembunyikan pertanyaan yang tidak relevan.
3. Skenario F1 + F14 menghasilkan H1.
4. Unduh TXT berfungsi.
5. Halaman basis pengetahuan menampilkan 20 fakta dan 31 aturan.

---

## 9. Troubleshooting

| Masalah | Penyebab dan solusi |
| --- | --- |
| Build Render gagal | Pastikan `Dockerfile` ada di root repo dan push sudah masuk |
| Service hidup tetapi 502 | Cek log Render; pastikan aplikasi bind ke `0.0.0.0` dan memakai `$PORT` |
| Health check gagal | Pastikan path `/api/health` dapat diakses tanpa login |
| Halaman terbuka tetapi data kosong | Pastikan `knowledge_base.json` ikut ter-copy ke image |
| Log tidak muncul | Normal jika memakai `--no-log` atau filesystem sementara |
| URL lambat pertama kali | Service gratis Render sedang bangun dari kondisi tidur |
