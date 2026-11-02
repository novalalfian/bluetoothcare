# BluetoothCare — Sistem Pakar Diagnosis Konektivitas Bluetooth pada Laptop

Aplikasi web lokal untuk mendiagnosis awal gangguan konektivitas **earphone, speaker, keyboard, dan mouse Bluetooth** pada laptop **Windows 10/11**. Pengguna menjawab 14 pertanyaan Ya/Tidak, mesin **forward chaining** menelusuri 19 aturan JIKA–MAKA, lalu sistem menampilkan diagnosis berurutan prioritas, langkah perbaikan, dan **jejak penalaran per iterasi**.

Proyek ini disusun mengacu pada PRD *Sistem Pakar Diagnosis Gangguan Konektivitas Perangkat Bluetooth (Earphone, Speaker, Keyboard) pada Laptop* versi 2.0 untuk UTS Sistem Pakar (TI22604).

---

## 1. Ringkasan fitur

| Kebutuhan PRD | Status | Keterangan |
| --- | --- | --- |
| FR-01 Halaman pembuka | ✅ | Beranda dengan judul, deskripsi, batasan, dan tombol Mulai Konsultasi |
| FR-02 Form 14 fakta Ya/Tidak, 3 kelompok | ✅ | Kelompok Laptop & sistem, Perangkat Bluetooth, Lingkungan & sinyal |
| FR-03 Validasi masukan | ✅ | Semua pertanyaan wajib dijawab; pesan menyebut kode yang belum dijawab |
| FR-04 Basis pengetahuan JSON terpisah | ✅ | `knowledge_base.json`, dimuat oleh `KnowledgeBase` |
| FR-05 Forward chaining berulang sampai stabil | ✅ | Siklus berhenti saat tidak ada aturan baru aktif |
| FR-06 Operator AND dan OR | ✅ | Termasuk OR bersarang pada R14: `F7 AND (F5 OR F11)` |
| FR-07 Hasil berprioritas + saran | ✅ | 7 diagnosis akhir, kartu saran per diagnosis |
| FR-08 Fasilitas penjelasan | ✅ | Fakta masukan, tabel iterasi, fakta turunan K/H, pohon alasan JIKA–MAKA |
| FR-09 “Belum dapat disimpulkan” | ✅ | Menampilkan gejala terdeteksi dan saran pemeriksaan tambahan |
| FR-10 Konsultasi ulang | ✅ | Mengosongkan sesi dan form |
| FR-11 Halaman aturan dan fakta | ✅ | Tab Fakta, Aturan, Kesimpulan, Skenario Uji, Sumber |
| FR-12 Ekspor hasil | ✅ | Unduh `.txt` + Cetak/PDF melalui dialog cetak browser |
| FR-13 Log konsultasi lokal | ✅ | `logs/konsultasi.jsonl`, hanya gejala dan hasil, tanpa data pribadi |

Kebutuhan non-fungsional:

- **NFR-01** Inferensi jauh di bawah 1 detik (sekitar 0,1–1 ms pada pengujian).
- **NFR-02** Bahasa Indonesia; istilah teknis disertai keterangan singkat pada setiap pertanyaan.
- **NFR-03** Berjalan lokal tanpa koneksi internet dan tanpa dependensi eksternal.
- **NFR-04** Pemisahan basis pengetahuan, mesin inferensi, pengendali HTTP, dan antarmuka.
- **NFR-05** Responsif untuk laptop dan ponsel, termasuk menu navigasi seluler.
- **NFR-06** Tidak meminta data pribadi; log hanya berisi gejala dan hasil inferensi.

Spesifikasi minimum soal UTS:

- 14 fakta (target 10+)
- 7 diagnosis akhir (target 5+)
- 5 kesimpulan antara (target 3+)
- 19 aturan produksi dengan AND/OR (target 15+)
- 7 skenario uji (target 5+)
- Basis pengetahuan JSON terpisah, fasilitas penjelasan, validasi, penanganan “belum dapat disimpulkan”, dan konsultasi ulang

---

## 2. Struktur proyek

```text
.
├── app.py                  # Pengendali HTTP (API + berkas statis), tanpa Flask
├── inference_engine.py     # Mesin forward chaining, validasi, jejak, pohon alasan
├── knowledge_base.json     # 14 fakta, 19 aturan, 12 kesimpulan, 4 sumber, 7 skenario
├── jalankan.bat            # Klik dua kali untuk menjalankan di Windows
├── static/
│   ├── index.html          # Beranda, konsultasi, hasil, basis pengetahuan, tentang
│   ├── styles.css          # Desain responsif + gaya cetak/PDF
│   ├── app.js              # Routing, form, render hasil, ekspor, tab
│   └── favicon.svg
├── tests/
│   ├── test_engine.py      # 15 pengujian mesin (termasuk 7 skenario PRD)
│   └── test_api.py         # 13 pengujian integrasi HTTP
├── docs/
│   ├── PEMETAAN_PRD.md     # Keterlacakan kebutuhan PRD ke kode
│   └── HASIL_UJI.md        # Tabel hasil pengujian dan cara memverifikasi
├── logs/                   # Dibuat otomatis saat konsultasi pertama
└── README.md
```

Pengendali HTTP memakai `http.server` dari pustaka standar Python. Perannya sama dengan lapisan Flask pada PRD (menerima permintaan, memanggil mesin inferensi, mengembalikan JSON), tetapi tanpa dependensi eksternal sehingga aplikasi pasti dapat berjalan luring di komputer penguji.

---

## 3. Cara menjalankan

### Cara cepat (Windows)

1. Pastikan **Python 3.10 atau lebih baru** terpasang dan tersedia di `PATH`.
2. Klik dua kali **`jalankan.bat`**.
3. Browser akan terbuka otomatis di `http://127.0.0.1:8000`.

Tidak ada `pip install`, tidak ada `npm install`, dan tidak perlu internet. Seluruh backend memakai pustaka standar Python.

### Cara manual

```powershell
cd "D:\New folder (11)"
python app.py
```

Opsi lain:

```powershell
python app.py --port 8080          # ganti port (otomatis mencari port kosong berikutnya)
python app.py --no-browser         # jangan buka browser
python app.py --no-log             # nonaktifkan log konsultasi
python app.py --verbose            # tampilkan semua log HTTP
```

Hentikan server dengan `Ctrl+C`.

> Jika port 8000 sedang dipakai, aplikasi mencoba port 8001–8019 dan menampilkan URL yang benar di konsol.

---

## 4. Alur demonstrasi (di bawah 5 menit)

1. **Beranda** — jelaskan tujuan, batasan, dan angka basis pengetahuan (14/19/7).
2. **Konsultasi** — tunjukkan tiga kelompok pertanyaan dan validasi saat tombol Proses ditekan tanpa menjawab.
3. Isi skenario **F1 + F14** (Bluetooth laptop tidak bisa diaktifkan dan pairing ulang tetap gagal), jawab pertanyaan lain **Tidak**.
4. **Hasil** — tunjukkan diagnosis **H1** berprioritas 1, langkah perbaikan, waktu inferensi, dan iterasi.
5. Buka **“Mengapa diagnosis ini muncul?”** — tunjukkan R1 → K1 dan R9 → H1 beserta fakta pendukung.
6. Buka **Jejak penalaran** — tunjukkan tabel iterasi 1 dan 2, status “baru”, serta fakta turunan.
7. Klik **Konsultasi ulang** untuk menunjukkan form kembali kosong.
8. Uji **skenario F7 saja** untuk menunjukkan penanganan “belum dapat disimpulkan” beserta saran baterai.
9. Buka **Basis Pengetahuan** — tunjukkan fakta, aturan, pemenuhan spesifikasi minimum, dan sumber.
10. Tunjukkan **Unduh .txt** atau **Cetak / PDF**.

### Skenario uji PRD

| No | Fakta masukan | Aturan berjalan | Hasil | Iterasi |
| --- | --- | --- | --- | --- |
| 1 | F1, F14 | R1, R9 | H1 | 2 |
| 2 | F2, F13 | R3, R4, R10 | H2 | 2 |
| 3 | F5, F6 | R5, R12 | H3 | 2 |
| 4 | F8 | R6, R15 | H5 | 2 |
| 5 | F3, F4 | R7, R16 | H6 | 2 |
| 6 | F7, F11 | R14 | H4 | 1 |
| 7 | F7 saja | — | Belum dapat disimpulkan | 0 |

Seluruh skenario sesuai (7/7 = 100%). Rincian bukti ada di [`docs/HASIL_UJI.md`](docs/HASIL_UJI.md).

---

## 5. Basis pengetahuan

### Fakta (F)

14 fakta dibagi ke tiga kelompok:

| Kelompok | Fakta |
| --- | --- |
| Laptop & sistem | F1, F8, F10, F12 |
| Perangkat Bluetooth | F2, F3, F4, F7, F9, F11, F13, F14 |
| Lingkungan & sinyal | F5, F6 |

Setiap fakta memiliki `hint` (keterangan untuk pengguna) dan `solo_advice` (saran bila fakta muncul tanpa diagnosis).

### Kesimpulan antara (K)

K1 adaptor tidak siap · K2 perangkat belum siap dipasangkan · K3 sinyal radio terganggu · K4 keluaran audio salah · K5 data pairing lama bermasalah.

### Diagnosis akhir (H) dan prioritas

| Prioritas | Kode | Diagnosis |
| --- | --- | --- |
| 1 | H1 | Driver atau layanan Bluetooth bermasalah |
| 2 | H2 | Perangkat belum mode pairing atau tersambung ke perangkat lain |
| 3 | H6 | Data pairing lama rusak |
| 4 | H7 | Manajemen daya mematikan adaptor |
| 5 | H4 | Baterai perangkat lemah |
| 6 | H3 | Interferensi atau jarak/penghalang |
| 7 | H5 | Output audio default belum diarahkan ke perangkat |

Prioritas hanya mengatur urutan tampil/pemeriksaan, bukan menghapus diagnosis lain.

### Aturan (19)

```text
R1  F1                         -> K1
R2  F10                        -> K1
R3  F13 OR F9                  -> K2
R4  F2                         -> K2
R5  F6                         -> K3
R6  F8                         -> K4
R7  F3                         -> K5
R8  K1 AND F4                  -> H1
R9  K1 AND F14                 -> H1
R10 K2 AND F2                  -> H2
R11 K2 AND F4                  -> H2
R12 K3 AND F5                  -> H3
R13 K3 AND F11                 -> H3
R14 F7 AND (F5 OR F11)         -> H4
R15 K4                         -> H5
R16 K5 AND F4                  -> H6
R17 K5 AND F8                  -> H6
R18 F12 AND F3                 -> H7
R19 F12 AND F5                 -> H7
```

### Format JSON

```json
{
  "facts": [
    { "id": "F1", "text": "...", "group": "laptop", "hint": "...", "solo_advice": "..." }
  ],
  "rules": [
    { "id": "R14", "if": { "and": ["F7", { "or": ["F5", "F11"] }] }, "then": "H4", "source": "S2" }
  ],
  "conclusions": [
    { "id": "H4", "type": "final", "text": "...", "priority": 5, "advice": ["..."] }
  ]
}
```

Premis mendukung:

- `"F1"` — fakta tunggal
- `{ "and": [...] }`
- `{ "or": [...] }`
- `{ "not": ... }` (didukung mesin, tidak dipakai pada basis aturan saat ini)
- Kombinasi bersarang, misalnya `{"and": ["F7", {"or": ["F5", "F11"]}]}`

Validasi otomatis saat server mulai akan menolak:

- kode ganda,
- referensi fakta/kesimpulan yang tidak ada,
- kesimpulan yang tidak pernah dihasilkan aturan,
- diagnosis akhir tanpa prioritas,
- struktur premis yang tidak dikenal.

---

## 6. Mesin inferensi

Implementasi ada di `inference_engine.py`.

```text
memori_kerja <- fakta yang dijawab "Ya"
jejak <- []
iterasi <- 0
ulangi
    snapshot <- salinan memori_kerja
    aturan_aktif <- semua aturan yang belum berjalan dan premisnya terpenuhi snapshot
    jika aturan_aktif kosong: berhenti
    iterasi <- iterasi + 1
    untuk setiap aturan pada aturan_aktif:
        tambahkan kesimpulan ke memori_kerja
        catat (iterasi, aturan, premis, kesimpulan, status baru) ke jejak
        tandai aturan sudah berjalan
hasil <- semua H pada memori_kerja, urut prioritas
jika hasil kosong: tampilkan "belum dapat disimpulkan"
```

Catatan desain:

- Satu iterasi = satu siklus evaluasi terhadap **snapshot** memori kerja. Seluruh aturan yang aktif pada siklus itu dijalankan, lalu fakta baru dipakai pada siklus berikutnya.
- Aturan yang sudah berjalan tidak diulang.
- Batas pengaman 100 iterasi mencegah siklus tak berujung.
- Pohon penjelasan dibangun mundur: H ← aturan yang menghasilkan H ← K/fakta pendukung ← aturan yang menghasilkan K.

Contoh jejak untuk F1 + F14:

| Iterasi | Aturan | Premis | Kesimpulan | Status |
| --- | --- | --- | --- | --- |
| 1 | R1 | F1 | K1 | baru |
| 2 | R9 | K1 DAN F14 | H1 | baru |

---

## 7. API lokal

| Metode | Endpoint | Fungsi |
| --- | --- | --- |
| GET | `/api/knowledge` | Fakta, aturan, kesimpulan, sumber, statistik, pemenuhan spesifikasi |
| GET | `/api/health` | Cek status server |
| POST | `/api/diagnose` | Jalankan inferensi |
| GET | `/` dan aset statis | Antarmuka |

Contoh permintaan:

```bash
curl -X POST http://127.0.0.1:8000/api/diagnose \
  -H "Content-Type: application/json" \
  -d "{\"answers\":{\"F1\":true,\"F2\":false,\"F3\":false,\"F4\":false,\"F5\":false,\"F6\":false,\"F7\":false,\"F8\":false,\"F9\":false,\"F10\":false,\"F11\":false,\"F12\":false,\"F13\":false,\"F14\":true}}"
```

Respons memuat:

- `status`: `diagnosed` atau `inconclusive`
- `diagnoses`: diagnosis berprioritas + `advice` + pohon `derivation`
- `trace`: satu baris per aturan yang berjalan
- `working_memory`: fakta, kesimpulan antara, diagnosis akhir
- `input_facts` / `detected_facts`
- `inconclusive`: pesan, gejala terdeteksi, saran
- `stats`: waktu inferensi, iterasi, aturan aktif, jumlah jawaban

Kesalahan validasi mengembalikan HTTP 400 dengan `error`, `missing`, dan `invalid`. Body maksimum 64 KB.

---

## 8. Pengujian

```powershell
python -m unittest discover -s tests -v
```

Hasil terakhir: **28 pengujian lulus**, mencakup:

- 7 skenario PRD beserta aturan yang berjalan,
- validasi masukan (kosong, hilang, tipe salah, kode asing),
- semantik AND/OR bersarang,
- urutan prioritas saat beberapa diagnosis muncul,
- pohon penjelasan dan jejak iterasi,
- kinerja inferensi < 1 detik,
- API, header keamanan, penyajian aset statis,
- penulisan log tanpa data pribadi.

Verifikasi browser juga dilakukan selama pengembangan: **21 pemeriksaan lulus** (alur H1, unduhan TXT, mode cetak, muat ulang hasil, alur F7, tabel pengetahuan, dan menu seluler), tanpa error runtime JavaScript. Tampilan desktop dan ponsel diperiksa melalui tangkapan layar.

Rincian: [`docs/HASIL_UJI.md`](docs/HASIL_UJI.md).

---

## 9. Mengubah basis pengetahuan

1. Buka `knowledge_base.json`.
2. Tambahkan fakta pada `facts` (pastikan `group` valid).
3. Tambahkan aturan pada `rules`; `then` harus menunjuk kesimpulan yang sudah ada.
4. Tambahkan kesimpulan akhir pada `conclusions` dengan `type: "final"` dan `priority`.
5. Muat ulang halaman. Server memvalidasi konsistensi saat start; pesan kesalahan ditampilkan di konsol.

Kode inferensi tidak perlu diubah (FR-04). Jika menambah fakta, form, progres, dan tabel basis pengetahuan otomatis menyesuaikan karena dirender dari JSON.

### Sebelum pengumpulan tugas

- Isi `meta.author` pada `knowledge_base.json` dan halaman Tentang dengan **NIM + nama**.
- Lengkapi sumber **S2** (merek/model manual perangkat) dan **S3** (nama, tanggal, ringkasan wawancara). Status “Perlu dilengkapi” terlihat pada tab Sumber.
- Ganti placeholder `(isi NIM dan nama)` pada `static/index.html` bila diperlukan.
- Simpan versi awal dan akhir basis aturan sebagai bukti proses.
- Cantumkan pernyataan penggunaan AI pada laporan akhir.

---

## 10. Keamanan dan privasi

- Server hanya bind ke `127.0.0.1` secara default.
- Tidak ada data pribadi yang diminta.
- Log konsultasi (`logs/konsultasi.jsonl`) hanya menyimpan waktu, fakta “Ya”, diagnosis, aturan, iterasi, dan waktu inferensi.
- Header respons mencakup CSP, `X-Content-Type-Options`, dan `Referrer-Policy`.
- Semua teks dari basis pengetahuan di-escape sebelum dirender di DOM.
- Tidak ada CDN, font eksternal, atau telemetri; aplikasi dapat berjalan tanpa internet.

---

## 11. Troubleshooting

| Masalah | Solusi |
| --- | --- |
| `python` tidak dikenali | Instal Python 3.10+ dan centang “Add Python to PATH”, atau jalankan `py app.py` |
| Port 8000 dipakai | Server otomatis mencoba 8001–8019; lihat URL di konsol atau gunakan `--port 8080` |
| Halaman kosong / pertanyaan tidak muncul | Pastikan server berjalan; buka `http://127.0.0.1:8000`; cek konsol browser |
| “Basis pengetahuan gagal dimuat” | Jalankan dari folder proyek agar `knowledge_base.json` ditemukan; cek pesan validasi di konsol |
| Perubahan JSON tidak terlihat | Muat ulang halaman (Ctrl+F5); server membaca JSON saat start |
| Browser tidak terbuka otomatis | Buka URL di konsol secara manual, atau jalankan tanpa `--no-browser` |
| Log tidak dibuat | Log dibuat saat konsultasi pertama; pastikan folder proyek dapat ditulis dan `--no-log` tidak dipakai |

---

## 12. Pernyataan penggunaan AI

Struktur dokumen, kode, dan sebagian teks dibantu oleh AI. Penulis bertanggung jawab memvalidasi seluruh fakta, aturan, sumber, dan kode, serta mencantumkan pernyataan penggunaan AI pada laporan akhir sesuai ketentuan mata kuliah.

---

**Mata kuliah:** Sistem Pakar (TI22604) · UTS Semester Ganjil 2026/2027  
**Metode:** Forward Chaining · **Platform:** Windows 10/11 · localhost  
**Versi aplikasi:** 2.0
