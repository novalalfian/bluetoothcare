# Hasil Pengujian

**Tanggal pengujian:** 4 November 2026  
**Lingkungan:** Windows, Python 3.15.0, browser modern (Chromium/Edge/Firefox)  
**Perintah:**

```powershell
python -m unittest discover -s tests -v
```

**Hasil:** `Ran 30 tests ... OK` (seluruh pengujian lulus).

---

## 1. Pengujian skenario

Setiap skenario dijalankan dengan seluruh 20 fakta dijawab; hanya fakta pada kolom masukan yang bernilai **Ya**. Pengujian memeriksa:

- status akhir,
- daftar aturan yang benar-benar berjalan (urutan sesuai eksekusi),
- daftar diagnosis,
- tidak ada aturan yang dijalankan dua kali.

| No | Fakta masukan | Aturan berjalan | Iterasi | Hasil | Status | Waktu |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | F1, F14 | R1, R9 | 2 | H1 | diagnosed | ±0,29 ms |
| 2 | F2, F13 | R3, R4, R10 | 2 | H2 | diagnosed | ±0,79 ms |
| 3 | F5, F6 | R5, R12 | 2 | H3 | diagnosed | ±0,19 ms |
| 4 | F8 | R6, R15 | 2 | H5 | diagnosed | ±0,16 ms |
| 5 | F3, F4 | R7, R16 | 2 | H6 | diagnosed | ±0,16 ms |
| 6 | F7, F11 | R14 | 1 | H4 | diagnosed | ±0,10 ms |
| 7 | F7 saja | — | 0 | Belum dapat disimpulkan | inconclusive | ±0,04 ms |
| 8 | F15, F4 | R20, R26 | 2 | H10 | diagnosed | ±0,15 ms |
| 9 | F16, F5 | R22, R28 | 2 | H9 | diagnosed | ±0,15 ms |
| 10 | F18 | R24, R30 | 2 | H8 | diagnosed | ±0,15 ms |
| 11 | F19 | R25, R31 | 2 | H7 | diagnosed | ±0,15 ms |
| 12 | F20, F14 | R21, R27 | 2 | H10 | diagnosed | ±0,15 ms |
| 13 | F17, F11 | R23, R29 | 2 | H9 | diagnosed | ±0,15 ms |

**Tingkat kesesuaian:** (13 skenario sesuai ÷ 13 skenario) × 100% = **100%**.

Catatan skenario 7: sistem menampilkan F7 sebagai gejala terdeteksi, pesan “Belum dapat disimpulkan”, serta saran mengisi ulang baterai dan memeriksa mode pairing. Ini sesuai FR-09.

---

## 2. Rincian jejak dua contoh

### F1 + F14 → H1

| Iterasi | Aturan | Premis | Kesimpulan | Status |
| --- | --- | --- | --- | --- |
| 1 | R1 | F1 | K1 | baru |
| 2 | R9 | K1 DAN F14 | H1 | baru |

Pohon alasan:

```text
H1 (Driver atau layanan Bluetooth bermasalah)
└─ R9: JIKA K1 DAN F14 MAKA H1
   ├─ K1 (Adaptor Bluetooth laptop tidak siap)
   │  └─ R1: JIKA F1 MAKA K1
   │     └─ F1 (Pengaturan/tombol Bluetooth tidak bisa diaktifkan)
   └─ F14 (Sudah dihapus dan dipasang ulang, masalah tetap ada)
```

### F7 → belum dapat disimpulkan

- Aturan berjalan: tidak ada.
- Memori kerja: F7 saja.
- Diagnosis: kosong.
- Saran yang muncul antara lain: isi ulang baterai di atas 20%, periksa mode pairing, dan bandingkan perangkat pada laptop lain.

### F15 + F4 → H10 (contoh jalur berbasis literatur)

| Iterasi | Aturan | Premis | Kesimpulan | Sumber | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | R20 | F15 | K8 | S6 (Intel USB 3.0 RFI) | baru |
| 2 | R26 | K8 DAN F4 | H10 | S6 | baru |

Pohon alasan:

```text
H10 (Adaptor USB atau driver generik tidak kompatibel)
└─ R26: JIKA K8 DAN F4 MAKA H10
   ├─ K8 (Jalur adaptor atau driver belum optimal)
   │  └─ R20: JIKA F15 MAKA K8
   │     └─ F15 (Receiver/adaptor Bluetooth memakai atau dekat port USB 3.0)
   └─ F4 (Pairing gagal atau terus meminta PIN) — didukung S6
```

---

## 3. Pengujian tambahan mesin inferensi

| Pengujian | Skenario | Hasil |
| --- | --- | --- |
| Semua jawaban “Tidak” | 20 fakta false | Inconclusive, 0 aturan, pesan tanpa gejala — lulus |
| OR salah satu cukup | F7 + F5 | H4 — lulus |
| OR salah satu cukup | F7 + F11 | H4 — lulus |
| AND belum lengkap | F7 saja | Tidak ada H4 — lulus |
| K tanpa H | F13 saja | K2 terbentuk, H2 belum — lulus |
| K + fakta melengkapi | F2 + F13 | H2 — lulus |
| Banyak diagnosis | F1, F4, F7, F11 | H1 (prioritas 1) lalu H4 (prioritas 5) — lulus |
| Dua aturan untuk satu H | F1, F4, F14 | H1 didukung R8 dan R9 — lulus |
| Validasi jawaban hilang | Hanya F1 dijawab | `InputError`, 19 kode hilang — lulus |
| Validasi tipe salah | F1 = `"ya"` | `InputError`, F1 invalid — lulus |
| Validasi kode asing | F99 | `InputError` — lulus |
| Kinerja | Seluruh fakta “Ya” | < 1 detik (aktual < 1 ms) — lulus |
| Label premis | R14 | `F7 DAN (F5 ATAU F11)` — lulus |
| Rujukan sumber aturan | Semua R1–R31 | Setiap `source` ada di daftar sumber — lulus |
| Kelengkapan literatur | S5–S10 | Judul, penerbit, URL https, status terverifikasi, kontribusi terisi — lulus |
| Integritas minimum | — | 20 fakta, 31 aturan, 10 H, 9 K — lulus |

---

## 4. Pengujian API dan berkas statis

| Pengujian | Hasil |
| --- | --- |
| `GET /api/knowledge` | 200, JSON, 20 fakta, 31 aturan, 9 sumber, seluruh pemeriksaan spesifikasi `met` |
| `GET /api/health` | 200, `status: ok`, `rules: 31` |
| `GET /` | 200, HTML memuat “BluetoothCare” |
| `GET /styles.css`, `/app.js`, `/favicon.svg` | 200 dengan MIME type sesuai |
| `POST /api/diagnose` valid | 200, H1, aturan R1/R9, 20 jawaban |
| `POST /api/diagnose` F7 | 200, inconclusive |
| Jawaban hilang | 400, `missing: ["F5"]` |
| JSON rusak | 400, pesan JSON tidak valid |
| Body kosong | 400 |
| Endpoint tidak dikenal | 404 JSON |
| `OPTIONS /api/diagnose` | 204, header `Allow` |
| Header keamanan | CSP dan `X-Content-Type-Options` ada |
| Log konsultasi | File JSONL dibuat; hanya diagnosis/gejala/aturan; tanpa `answers`, nama, atau IP |

---

## 5. Pengujian antarmuka (browser)

Checklist berikut telah diverifikasi pada Chromium headless (Playwright) dengan server lokal aktif:

- [x] Beranda tampil di desktop dan ponsel; tombol Mulai membuka form.
- [x] Form menampilkan 20 pertanyaan dalam 3 kelompok; progres berubah saat menjawab.
- [x] Pemilih jenis perangkat menyembunyikan pertanyaan tidak relevan: mode audio → 19 pertanyaan (F11 tersembunyi); mode keyboard/mouse → 17 pertanyaan (F5, F8, F18 tersembunyi); pertanyaan tersembunyi dikirim sebagai “Tidak”.
- [x] Submit kosong menampilkan pesan dan menandai pertanyaan belum dijawab.
- [x] Skenario F1 + F14 menghasilkan H1, saran, dan jejak 2 iterasi.
- [x] Detail “Mengapa diagnosis ini muncul?” menampilkan R1 → K1 dan R9 → H1.
- [x] Skenario F7 saja menampilkan “Belum dapat disimpulkan” + saran baterai.
- [x] Konsultasi ulang mengosongkan form dan hasil.
- [x] Tab basis pengetahuan menampilkan 20 fakta, 31 aturan, 19 kesimpulan, 13 skenario, 9 sumber.
- [x] Tombol Unduh .txt menghasilkan berkas; Cetak/PDF menampilkan halaman bersih tanpa navigasi.
- [x] Menu seluler dapat dibuka/ditutup, dan navigasi hash berfungsi.
- [x] Muat ulang halaman saat berada di `#hasil` mempertahankan hasil dari `sessionStorage`.

**Hasil verifikasi browser:** 35 pemeriksaan lulus, tanpa error runtime JavaScript. Pemeriksaan mencakup tombol submit aktif setelah basis pengetahuan dimuat, alur H1, pemilih jenis perangkat (audio dan keyboard/mouse), unduhan TXT (nama berkas dan isi), mode cetak, konsultasi ulang, alur F7, tabel pengetahuan, dan menu seluler. Tampilan desktop 1440×1000 serta ponsel 390×844 juga diperiksa melalui tangkapan layar.

Pengujian DOM terpisah (jsdom) juga dijalankan: 50 pemeriksaan lulus, mencakup 20 pertanyaan, filter jenis perangkat, validasi kosong, alur H1, konsultasi ulang, alur F7, tab pengetahuan, dan menu seluler — tanpa error runtime JavaScript.

---

## 6. Kesimpulan

- Seluruh kebutuhan **Wajib** (FR-01–FR-10) terpenuhi.
- Seluruh kebutuhan opsional (FR-11–FR-13) juga diimplementasikan.
- Seluruh 13 skenario sesuai (100%).
- Seluruh 30 pengujian otomatis lulus.
- Seluruh 35 pemeriksaan browser lulus tanpa error runtime JavaScript.
- Seluruh 50 pemeriksaan DOM (jsdom) lulus, termasuk filter jenis perangkat.
- Waktu inferensi jauh di bawah batas 1 detik.

**Siap untuk demonstrasi lokal dan verifikasi kode.**
