# Draf Bab 5 — Pengujian dan Pembahasan

**Sistem Pakar Diagnosis Gangguan Konektivitas Perangkat Bluetooth pada Laptop (BluetoothCare)**

> Bab ini disusun sebagai bagian mandiri untuk laporan UTS. Seluruh angka dan hasil diambil dari basis pengetahuan versi 2.2: 20 fakta, 31 aturan, 9 kesimpulan antara, 10 diagnosis akhir, 13 skenario, dan 9 sumber.

---

## 5.1 Tujuan dan Ruang Lingkup Pengujian

Pengujian dilakukan untuk memastikan bahwa sistem memenuhi tiga hal:

1. **Kebenaran fungsional** — keluaran sistem sesuai dengan aturan dan skenario yang telah ditetapkan.
2. **Keterlacakan penalaran** — setiap diagnosis dapat dijelaskan melalui aturan, fakta, dan sumber yang mendukungnya.
3. **Kelayakan operasional** — aplikasi berjalan stabil di localhost, antarmuka dapat digunakan, dan waktu inferensi berada di bawah batas yang ditetapkan.

Ruang lingkup pengujian mencakup:

- mesin inferensi forward chaining;
- validasi masukan dan penanganan kesalahan;
- API HTTP dan penyajian berkas statis;
- antarmuka pengguna pada desktop dan ponsel;
- kinerja inferensi;
- konsistensi basis pengetahuan.

Pengujian **tidak** mencakup:

- pengujian lapangan pada perangkat Bluetooth nyata;
- pengujian usability dengan pengguna umum dalam jumlah besar;
- pengujian keamanan siber secara menyeluruh;
- pengujian pada sistem operasi selain Windows 10/11.

---

## 5.2 Lingkungan dan Perangkat Uji

| Komponen | Keterangan |
| --- | --- |
| Sistem operasi | Windows |
| Bahasa | Python 3.15.0 |
| Kerangka uji | `unittest` (bawaan Python) |
| Browser uji | Microsoft Edge (Playwright, mode headless) |
| Pengujian DOM | jsdom |
| Server | `python app.py --port 8765 --no-browser --no-log` |
| Basis pengetahuan | `knowledge_base.json` versi 2.2 |
| Tanggal pengujian | 4 November 2026 |

Aplikasi tidak memakai dependensi eksternal pada saat berjalan. Perangkat pengujian browser (Playwright/jsdom) hanya dipakai untuk verifikasi dan tidak menjadi bagian dari aplikasi yang dikumpulkan.

---

## 5.3 Strategi dan Tingkat Pengujian

| Tingkat | Metode | Cakupan | Jumlah |
| --- | --- | --- | --- |
| Skenario | Uji otomatis berbasis `meta.test_scenarios` | 13 alur diagnosis | 13 skenario |
| Unit mesin | `unittest` | Aturan, validasi, trace, prioritas, sumber | 17 pengujian |
| Integrasi API | HTTP request langsung | Endpoint, status code, header, log | 13 pengujian |
| Antarmuka DOM | jsdom | Form, hasil, tab, menu | 33 pemeriksaan |
| Antarmuka browser | Playwright + Edge | Alur nyata, unduh, cetak, responsif | 21 pemeriksaan |
| Kinerja | Pengukuran waktu inferensi | Seluruh fakta bernilai “Ya” | 1 pengujian |

Total pengujian otomatis Python: **30** (17 mesin + 13 API), seluruhnya lulus.

---

## 5.4 Pengujian Skenario Diagnosis

### 5.4.1 Prosedur

Setiap skenario dijalankan dengan seluruh 20 fakta dijawab. Hanya fakta yang tercantum pada kolom **Fakta masukan** yang bernilai **Ya**; sisanya **Tidak**. Untuk setiap skenario, pengujian memeriksa:

- status akhir (`diagnosed` atau `inconclusive`);
- daftar aturan yang benar-benar berjalan;
- urutan iterasi;
- daftar diagnosis yang dihasilkan;
- tidak ada aturan yang dijalankan dua kali.

### 5.4.2 Hasil

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

**Tingkat kesesuaian:**

```text
(13 skenario sesuai ÷ 13 skenario) × 100% = 100%
```

### 5.4.3 Catatan Skenario 7

Skenario 7 hanya memasukkan **F7** (baterai di bawah 20%). Mesin tidak menemukan aturan yang premisnya terpenuhi secara lengkap, sehingga:

- status akhir `inconclusive`;
- tidak ada aturan yang berjalan;
- F7 tetap ditampilkan sebagai gejala terdeteksi;
- sistem menampilkan pesan “Belum dapat disimpulkan”;
- sistem menampilkan saran baterai dan pemeriksaan mode pairing.

Perilaku ini sesuai dengan rancangan: fakta tunggal yang belum cukup membentuk diagnosis tidak dipaksa menghasilkan kesimpulan.

---

## 5.5 Jejak Penalaran

### 5.5.1 Skenario 1: F1 + F14 → H1

| Iterasi | Aturan | Premis | Kesimpulan | Status baru |
| --- | --- | --- | --- | --- |
| 1 | R1 | F1 | K1 | Ya |
| 2 | R9 | K1 DAN F14 | H1 | Ya |

Pohon alasan:

```text
H1 (Driver atau layanan Bluetooth bermasalah)
└─ R9: JIKA K1 DAN F14 MAKA H1
   ├─ K1 (Adaptor Bluetooth laptop tidak siap)
   │  └─ R1: JIKA F1 MAKA K1
   │     └─ F1 (Pengaturan/tombol Bluetooth tidak bisa diaktifkan)
   └─ F14 (Sudah dihapus dan dipasang ulang, masalah tetap ada)
```

### 5.5.2 Skenario 8: F15 + F4 → H10

| Iterasi | Aturan | Premis | Kesimpulan | Sumber | Status baru |
| --- | --- | --- | --- | --- | --- |
| 1 | R20 | F15 | K8 | S6 (Intel USB 3.0 RFI) | Ya |
| 2 | R26 | K8 DAN F4 | H10 | S6 | Ya |

Pohon alasan:

```text
H10 (Adaptor USB atau driver generik tidak kompatibel)
└─ R26: JIKA K8 DAN F4 MAKA H10
   ├─ K8 (Jalur adaptor atau driver belum optimal)
   │  └─ R20: JIKA F15 MAKA K8
   │     └─ F15 (Receiver/adaptor Bluetooth memakai atau dekat port USB 3.0)
   └─ F4 (Pairing gagal atau terus meminta PIN/passkey)
```

### 5.5.3 Skenario 2: F2 + F13 → H2

| Iterasi | Aturan | Premis | Kesimpulan | Status baru |
| --- | --- | --- | --- | --- |
| 1 | R3 | F13 ATAU F9 | K2 | Ya |
| 1 | R4 | F2 | K2 | Tidak (sudah ada) |
| 2 | R10 | K2 DAN F2 | H2 | Ya |

Skenario ini menunjukkan dua hal:

1. **R3 dan R4 sama-sama menghasilkan K2.** Keduanya sah karena premisnya berbeda (R3: perangkat belum mode pairing atau tersambung ke perangkat lain; R4: perangkat tidak terdeteksi).
2. **K2 hanya ditambahkan sekali ke memori kerja** karena memori kerja berupa himpunan. R3 mencatat `is_new = true`, sedangkan R4 mencatat `is_new = false`. Keduanya tetap muncul di jejak sebagai bukti penalaran.

Perilaku ini **bukan duplikasi kesimpulan yang salah**, melainkan konsekuensi wajar dari beberapa aturan yang menuju kesimpulan sama.

---

## 5.6 Pengujian Mesin Inferensi

### 5.6.1 Daftar Pengujian

| No | Nama pengujian | Aspek yang diperiksa | Hasil |
| --- | --- | --- | --- |
| 1 | `test_minimum_specification` | 20 fakta, 31 aturan, 10 H, 9 K | Lulus |
| 2 | `test_premise_labels_include_nested_or` | Label R14: `F7 DAN (F5 ATAU F11)` | Lulus |
| 3 | `test_public_data_has_rule_explanations` | Penjelasan aturan untuk halaman transparansi | Lulus |
| 4 | `test_every_rule_cites_a_known_source` | Semua `source` aturan valid | Lulus |
| 5 | `test_literature_sources_are_complete` | S5–S10 lengkap dan terverifikasi | Lulus |
| 6 | `test_all_prd_scenarios` | 13 skenario sesuai | Lulus |
| 7 | `test_scenario_7_reports_detected_single_fact` | F7 terdeteksi tanpa diagnosis | Lulus |
| 8 | `test_rule_iteration_trace` | Urutan iterasi dan aturan | Lulus |
| 9 | `test_derivation_tree_contains_intermediate_rule` | Pohon alasan memuat aturan antara | Lulus |
| 10 | `test_all_no_is_inconclusive` | Semua “Tidak” → inconclusive | Lulus |
| 11 | `test_and_or_semantics` | OR cukup salah satu; AND harus lengkap | Lulus |
| 12 | `test_multiple_diagnoses_sorted_by_priority` | Urutan diagnosis sesuai prioritas | Lulus |
| 13 | `test_multiple_rules_can_support_same_diagnosis` | Dua aturan mendukung satu H | Lulus |
| 14 | `test_validation_rejects_missing_answers` | Jawaban hilang ditolak | Lulus |
| 15 | `test_validation_rejects_invalid_values` | Nilai selain boolean ditolak | Lulus |
| 16 | `test_validation_rejects_unknown_and_missing_payload` | Kode asing dan payload kosong ditolak | Lulus |
| 17 | `test_inference_is_fast` | Inferensi < 1 detik | Lulus |

### 5.6.2 Temuan Penting

| Kasus | Perilaku yang diharapkan | Hasil |
| --- | --- | --- |
| Semua jawaban “Tidak” | Tidak ada aturan berjalan, status inconclusive | Sesuai |
| F7 + F5 | H4 melalui OR | Sesuai |
| F7 + F11 | H4 melalui OR | Sesuai |
| F7 saja | H4 tidak muncul karena AND belum lengkap | Sesuai |
| F13 saja | K2 terbentuk, H2 belum | Sesuai |
| F2 + F13 | K2 + F2 → H2 | Sesuai |
| F1, F4, F7, F11 | H1 (prioritas 1) dan H4 (prioritas 5) | Sesuai |
| F1, F4, F14 | H1 didukung R8 dan R9 | Sesuai |
| F1 saja dijawab | `InputError`, 19 kode hilang | Sesuai |
| F1 = `"ya"` | `InputError`, tipe tidak valid | Sesuai |
| F99 | `InputError`, kode tidak dikenal | Sesuai |
| Seluruh fakta “Ya” | Selesai < 1 detik | Sesuai |

---

## 5.7 Pengujian API dan Berkas Statis

### 5.7.1 Daftar Pengujian

| No | Nama pengujian | Skenario | Hasil |
| --- | --- | --- | --- |
| 1 | `test_knowledge_endpoint` | `GET /api/knowledge` | 200, 20 fakta, 31 aturan, 9 sumber |
| 2 | `test_health_endpoint` | `GET /api/health` | 200, `status: ok`, `rules: 31` |
| 3 | `test_index_page` | `GET /` | 200, HTML “BluetoothCare” |
| 4 | `test_static_assets` | CSS, JS, favicon | 200, MIME sesuai |
| 5 | `test_unknown_api_get` | GET endpoint tidak dikenal | 404 JSON |
| 6 | `test_diagnose_valid` | F1 + F14 | 200, H1, R1/R9 |
| 7 | `test_diagnose_inconclusive` | F7 | 200, inconclusive |
| 8 | `test_diagnose_missing_answers` | Jawaban tidak lengkap | 400, `missing` |
| 9 | `test_diagnose_invalid_json` | JSON rusak | 400 |
| 10 | `test_diagnose_empty_body` | Body kosong | 400 |
| 11 | `test_unknown_post_route` | POST endpoint tidak dikenal | 404 JSON |
| 12 | `test_options` | `OPTIONS /api/diagnose` | 204, header `Allow` |
| 13 | `test_consultation_log_written_without_answers` | Log konsultasi | JSONL dibuat, tanpa data pribadi |

### 5.7.2 Catatan Keamanan dan Privasi

- Respons API memakai header `Content-Security-Policy` dan `X-Content-Type-Options`.
- Log konsultasi hanya menyimpan gejala yang dijawab “Ya”, diagnosis, aturan yang berjalan, jumlah iterasi, dan waktu inferensi.
- Log **tidak** menyimpan nama, alamat IP, atau seluruh payload jawaban.
- Tidak ada autentikasi karena aplikasi dirancang untuk localhost; hal ini dicatat sebagai keterbatasan untuk versi online.

---

## 5.8 Pengujian Antarmuka

### 5.8.1 Pengujian DOM (jsdom)

Pengujian DOM memeriksa perilaku antarmuka tanpa browser penuh. Sebanyak **33 pemeriksaan** dilakukan dan seluruhnya lulus, meliputi:

- 20 pertanyaan tampil dalam 3 kelompok;
- progres berubah saat jawaban diisi;
- submit kosong ditolak dan menandai pertanyaan;
- alur F1 + F14 menghasilkan H1;
- pohon alasan menampilkan R1 → K1 dan R9 → H1;
- alur F7 menampilkan “Belum dapat disimpulkan”;
- konsultasi ulang mengosongkan form dan hasil;
- tab fakta, aturan, kesimpulan, skenario, dan sumber;
- tabel aturan terkelompok menurut kesimpulan;
- menu seluler dapat dibuka dan ditutup;
- tidak ada error runtime JavaScript.

### 5.8.2 Pengujian Browser (Playwright + Edge)

Sebanyak **21 pemeriksaan browser** dilakukan dan seluruhnya lulus, meliputi:

| No | Pemeriksaan | Hasil |
| --- | --- | --- |
| 1 | Beranda tampil di desktop | Lulus |
| 2 | Beranda tampil di ponsel | Lulus |
| 3 | Tombol Mulai membuka form konsultasi | Lulus |
| 4 | Form menampilkan 20 pertanyaan | Lulus |
| 5 | Form terbagi dalam 3 kelompok | Lulus |
| 6 | Progres berubah saat menjawab | Lulus |
| 7 | Submit kosong ditolak | Lulus |
| 8 | Alur F1 + F14 menghasilkan H1 | Lulus |
| 9 | Jejak 2 iterasi tampil | Lulus |
| 10 | Detail alasan menampilkan R1 → K1 → R9 → H1 | Lulus |
| 11 | Alur F7 menampilkan inconclusive | Lulus |
| 12 | Saran baterai tampil pada F7 | Lulus |
| 13 | Konsultasi ulang mengosongkan hasil | Lulus |
| 14 | Unduh `.txt` menghasilkan berkas | Lulus |
| 15 | Cetak/PDF menampilkan halaman bersih | Lulus |
| 16 | Tabel fakta memuat 20 fakta | Lulus |
| 17 | Tabel aturan memuat 31 aturan | Lulus |
| 18 | Tabel skenario memuat 13 skenario | Lulus |
| 19 | Sembilan kartu sumber tampil | Lulus |
| 20 | Menu seluler dapat dibuka/ditutup | Lulus |
| 21 | Tidak ada error runtime JavaScript | Lulus |

Catatan lingkungan: Chromium bawaan Playwright tidak tersedia pada mesin pengujian, sehingga pengujian browser memakai **Microsoft Edge** melalui kanal `msedge`. Perbedaan ini tidak memengaruhi fungsionalitas yang diuji.

---

## 5.9 Pengujian Kinerja

| Pengujian | Kondisi | Hasil |
| --- | --- | --- |
| Waktu inferensi | Seluruh 20 fakta bernilai “Ya” | < 1 ms |
| Waktu inferensi per skenario | 13 skenario uji | 0,04–0,79 ms |
| Batas yang ditetapkan | Pengujian otomatis | < 1 detik |

Angka waktu di atas adalah indikasi pada satu mesin pengujian, bukan benchmark formal. Waktu respons HTTP dan waktu muat halaman tidak diukur secara terpisah dalam bab ini. Yang penting, seluruh proses inferensi berada jauh di bawah batas **1 detik** yang ditetapkan pada pengujian otomatis.

Faktor yang membuat inferensi cepat:

- hanya 31 aturan dan 20 fakta;
- setiap aturan hanya dijalankan sekali;
- evaluasi dilakukan terhadap snapshot memori kerja;
- tidak ada pemanggilan jaringan atau basis data saat inferensi.

---

## 5.10 Pemenuhan Spesifikasi Minimum

| Aspek | Target | Capaian | Status |
| --- | --- | --- | --- |
| Fakta | 10+ | 20 | Terpenuhi |
| Diagnosis akhir | 5+ | 10 | Terpenuhi |
| Kesimpulan antara | 3+ | 9 | Terpenuhi |
| Aturan produksi | 15+ | 31 | Terpenuhi |
| Skenario uji | 5+ | 13 | Terpenuhi |
| Operator AND/OR | Wajib | Banyak aturan | Terpenuhi |
| Sumber pengetahuan | 2+ | 9 | Terpenuhi |
| Fasilitas penjelasan | Wajib | Trace + pohon alasan | Terpenuhi |

---

## 5.11 Pembahasan

### 5.11.1 Makna Tingkat Kesesuaian 100%

Tingkat kesesuaian **100%** berarti seluruh 13 skenario yang dirancang menghasilkan keluaran yang diharapkan. Angka ini **bukan** ukuran akurasi diagnosis di dunia nyata, karena:

- skenario disusun oleh penyusun sistem, bukan sampel acak pengguna;
- jawaban fakta diberikan secara terkontrol, bukan berasal dari pengguna nyata;
- diagnosis yang diuji terbatas pada 10 kelas diagnosis yang tersedia;
- tidak ada pembandingan dengan diagnosis teknisi atau data lapangan.

Dengan demikian, 100% menunjukkan **konsistensi internal** antara basis aturan, mesin inferensi, dan harapan pengujian, bukan validitas klinis atau akurasi statistik.

### 5.11.2 Analisis Hasil

**a. Forward chaining bekerja sesuai rancangan.**

Pada skenario 1, F1 memicu R1 sehingga K1 masuk ke memori kerja. Pada iterasi berikutnya, K1 bersama F14 memicu R9 sehingga H1 dihasilkan. Ini menunjukkan rantai dua tingkat (fakta → kesimpulan antara → diagnosis akhir) berjalan benar.

**b. Beberapa aturan dapat menuju kesimpulan yang sama.**

Skenario 2 menunjukkan R3 dan R4 sama-sama menghasilkan K2. Mesin menyimpan K2 sekali, tetapi mencatat kedua aturan pada jejak. Ini penting untuk keterlacakan: pengguna dapat melihat bahwa K2 didukung oleh dua jalur premis yang berbeda.

**c. Prioritas tidak menghapus diagnosis lain.**

Pada kasus F1, F4, F7, dan F11, sistem menampilkan H1 (prioritas 1) dan H4 (prioritas 5). Keduanya muncul berurutan. Prioritas berfungsi untuk urutan tampil dan pemeriksaan, bukan sebagai filter tunggal.

**d. Kondisi tidak lengkap ditangani secara eksplisit.**

F7 saja tidak dipaksa menghasilkan H4 karena R14 membutuhkan F7 **dan** salah satu dari F5/F11. Sistem menampilkan status inconclusive beserta saran. Ini lebih jujur daripada menghasilkan diagnosis yang tidak didukung premis lengkap.

**e. Basis pengetahuan dapat diaudit.**

Setiap aturan memiliki `source`. Pengujian memastikan seluruh rujukan valid dan sumber literatur S5–S10 lengkap. Dengan demikian, setiap diagnosis dapat ditelusuri hingga dokumentasi atau literatur asalnya.

### 5.11.3 Kelebihan

1. **Terpisah dan modular** — basis pengetahuan, mesin inferensi, pengendali HTTP, dan antarmuka dipisahkan.
2. **Dapat dijelaskan** — hasil disertai jejak iterasi dan pohon alasan.
3. **Tervalidasi otomatis** — kesalahan kode, rujukan, dan prioritas ditolak saat basis pengetahuan dimuat.
4. **Tanpa dependensi eksternal** — aplikasi dapat berjalan luring dengan pustaka standar Python.
5. **Cakupan gejala cukup luas** — 20 fakta dan 31 aturan mencakup laptop, perangkat, dan lingkungan.
6. **Sumber dapat dipertanggungjawabkan** — 9 sumber terdiri atas dokumentasi vendor, standar, dan literatur ilmiah.

### 5.11.4 Keterbatasan dan Ancaman Validitas

| Jenis | Keterbatasan | Dampak |
| --- | --- | --- |
| Validitas internal | Skenario disusun bersama aturan, sehingga berpotensi “menguji dirinya sendiri” | Kesesuaian 100% tidak menjamin kebenaran di luar skenario |
| Validitas eksternal | Hanya Windows 10/11 dan perangkat audio/input Bluetooth | Hasil belum tentu berlaku untuk OS atau perangkat lain |
| Validitas konstruk | Fakta berasal dari jawaban mandiri pengguna | Jawaban yang keliru menghasilkan diagnosis yang keliru |
| Reliabilitas | Mesin deterministik, tetapi hasil bergantung pada masukan | Pengujian ulang dengan masukan sama menghasilkan keluaran sama |
| Validasi pakar | Tidak ada wawancara pakar | Aturan divalidasi melalui sumber dan konsistensi internal, bukan penilaian ahli |
| Uji pengguna | Belum ada uji usability formal | Kemudahan penggunaan baru dinilai secara kualitatif |
| Keamanan | Belum ada autentikasi | Aplikasi hanya cocok untuk localhost |

Keterbatasan ini tidak membatalkan hasil pengujian, tetapi membatasi klaim yang boleh dibuat. Sistem layak disebut **diagnosis awal berbasis aturan yang dapat dijelaskan**, bukan pengganti teknisi atau sistem diagnosis medis.

### 5.11.5 Perbandingan Singkat dengan Pendekatan Lain

| Pendekatan | Kelebihan | Kekurangan | Posisi sistem ini |
| --- | --- | --- | --- |
| Sistem pakar berbasis aturan | Dapat dijelaskan, deterministik, mudah diaudit | Aturan harus disusun manual | Dipakai |
| Machine learning | Dapat belajar dari data | Memerlukan data besar, sulit dijelaskan | Tidak dipakai |
| Case-based reasoning | Belajar dari kasus nyata | Memerlukan basis kasus | Direncanakan |
| Sistem pakar fuzzy | Menangani ketidakpastian | Lebih kompleks, perlu fungsi keanggotaan | Direncanakan |

Pemilihan rule-based forward chaining tepat untuk konteks UTS karena tujuan utamanya adalah **keterlacakan penalaran**, bukan akurasi statistik pada data besar.

---

## 5.12 Rencana Perbaikan Pengujian

1. Menambah skenario negatif dan kombinasi fakta yang lebih beragam.
2. Menguji dengan pengguna nyata untuk menilai kejelasan pertanyaan dan saran.
3. Menambah pengujian lintas browser (Firefox, Chrome, Edge).
4. Menambah pengujian regresi otomatis untuk antarmuka di dalam repositori.
5. Membandingkan hasil sistem dengan diagnosis teknisi pada sejumlah kasus nyata.
6. Menambah pengujian beban ringan jika aplikasi dipublikasikan online.
7. Menambah pengujian aksesibilitas (kontras, navigasi keyboard, pembaca layar).

---

## 5.13 Kesimpulan Bab

1. Seluruh **13 skenario** menghasilkan keluaran yang diharapkan (**100%** untuk skenario yang dirancang).
2. Seluruh **30 pengujian otomatis** (17 mesin + 13 API) lulus.
3. Seluruh **21 pemeriksaan browser** dan **33 pemeriksaan DOM** lulus tanpa error runtime JavaScript.
4. Waktu inferensi jauh di bawah batas 1 detik.
5. Sistem memenuhi seluruh spesifikasi minimum: 20 fakta, 31 aturan, 9 K, 10 H, 13 skenario, dan 9 sumber.
6. Keterbatasan utama adalah tidak adanya validasi pakar dan pengujian lapangan; klaim akurasi karena itu dibatasi pada konsistensi internal dan keterlacakan aturan.

---

## Lampiran 5A — Perintah Pengujian

```powershell
# Dari direktori proyek
python -m unittest discover -s tests -v
```

Contoh keluaran:

```text
Ran 30 tests in 1.132s

OK
```

Untuk menjalankan aplikasi sebelum pengujian manual:

```powershell
python app.py --port 8765 --no-browser --no-log
```

Lalu buka `http://127.0.0.1:8765`.

---

## Lampiran 5B — Rekap Bukti

| Bukti | Lokasi |
| --- | --- |
| Hasil pengujian lengkap | `docs/HASIL_UJI.md` |
| Pengujian mesin | `tests/test_engine.py` |
| Pengujian API | `tests/test_api.py` |
| Basis pengetahuan | `knowledge_base.json` |
| Tabel hasil di aplikasi | `#pengetahuan` → tab Skenario |
| Tangkapan layar | Lampiran C laporan utama |

---

*Draf bab ini dapat langsung digabungkan ke laporan utama setelah placeholder identitas mahasiswa dan tangkapan layar dilengkapi.*
