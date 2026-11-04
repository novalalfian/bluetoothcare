# Draf Bab 5 — Pengujian dan Pembahasan

**Sistem Pakar Diagnosis Gangguan Konektivitas Perangkat Bluetooth pada Laptop (BluetoothCare)**

> Bab ini membatasi pembahasan pada empat aspek: skenario pengujian, hasil pengujian, tingkat kesesuaian, dan evaluasi. Basis pengetahuan yang diuji adalah versi 2.2: 20 fakta, 31 aturan, 9 kesimpulan antara, 10 diagnosis akhir, dan 13 skenario.

---

## 5.1 Skenario Pengujian

Pengujian dilakukan dengan 13 skenario diagnosis. Setiap skenario dijalankan dengan seluruh 20 fakta dijawab; hanya fakta yang tercantum pada kolom **Fakta masukan** yang bernilai **Ya**, sedangkan sisanya **Tidak**.

| No | Fakta masukan | Hasil yang diharapkan |
| --- | --- | --- |
| 1 | F1, F14 | H1 — Driver atau layanan Bluetooth bermasalah |
| 2 | F2, F13 | H2 — Perangkat belum mode pairing atau tersambung ke perangkat lain |
| 3 | F5, F6 | H3 — Interferensi atau jarak/penghalang |
| 4 | F8 | H5 — Output audio default belum diarahkan ke perangkat |
| 5 | F3, F4 | H6 — Data pairing lama rusak |
| 6 | F7, F11 | H4 — Baterai perangkat lemah |
| 7 | F7 saja | Belum dapat disimpulkan (inconclusive) |
| 8 | F15, F4 | H10 — Adaptor USB atau driver generik tidak kompatibel |
| 9 | F16, F5 | H9 — Kanal 2,4 GHz padat |
| 10 | F18 | H8 — Profil atau codec audio tidak sesuai |
| 11 | F19 | H7 — Manajemen daya mematikan adaptor |
| 12 | F20, F14 | H10 — Adaptor USB atau driver generik tidak kompatibel |
| 13 | F17, F11 | H9 — Kanal 2,4 GHz padat |

Skenario 7 sengaja dirancang sebagai kasus **tidak lengkap**: F7 saja tidak memenuhi premis aturan mana pun secara utuh, sehingga sistem harus berhenti tanpa memaksakan diagnosis.

---

## 5.2 Hasil Pengujian

Seluruh skenario dijalankan pada 4 November 2026. Untuk setiap skenario, pengujian memeriksa status akhir, aturan yang berjalan, urutan iterasi, dan diagnosis yang dihasilkan.

| No | Fakta masukan | Aturan berjalan | Iterasi | Hasil | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | F1, F14 | R1, R9 | 2 | H1 | diagnosed |
| 2 | F2, F13 | R3, R4, R10 | 2 | H2 | diagnosed |
| 3 | F5, F6 | R5, R12 | 2 | H3 | diagnosed |
| 4 | F8 | R6, R15 | 2 | H5 | diagnosed |
| 5 | F3, F4 | R7, R16 | 2 | H6 | diagnosed |
| 6 | F7, F11 | R14 | 1 | H4 | diagnosed |
| 7 | F7 saja | — | 0 | Belum dapat disimpulkan | inconclusive |
| 8 | F15, F4 | R20, R26 | 2 | H10 | diagnosed |
| 9 | F16, F5 | R22, R28 | 2 | H9 | diagnosed |
| 10 | F18 | R24, R30 | 2 | H8 | diagnosed |
| 11 | F19 | R25, R31 | 2 | H7 | diagnosed |
| 12 | F20, F14 | R21, R27 | 2 | H10 | diagnosed |
| 13 | F17, F11 | R23, R29 | 2 | H9 | diagnosed |

### Catatan hasil

1. **Skenario 2** menghasilkan K2 melalui dua aturan, yaitu R3 (F13 ATAU F9) dan R4 (F2). K2 hanya ditambahkan sekali ke memori kerja karena memori kerja berupa himpunan. Kedua aturan tetap tercatat pada jejak; R3 mencatat `is_new = true`, sedangkan R4 mencatat `is_new = false`. Ini bukan duplikasi yang salah, melainkan dua jalur premis yang sah menuju kesimpulan yang sama.
2. **Skenario 7** tidak menjalankan aturan apa pun. F7 tetap ditampilkan sebagai gejala terdeteksi, sistem menampilkan pesan “Belum dapat disimpulkan”, dan pengguna diberi saran mengisi ulang baterai serta memeriksa mode pairing.
3. **Semua diagnosis yang muncul** sesuai dengan prioritas yang ditetapkan. Bila beberapa diagnosis muncul bersamaan, semuanya ditampilkan berurutan tanpa saling menghapus.

---

## 5.3 Tingkat Kesesuaian

Tingkat kesesuaian dihitung dari jumlah skenario yang keluarannya sama dengan harapan:

```text
(13 skenario sesuai ÷ 13 skenario) × 100% = 100%
```

| Kategori | Jumlah |
| --- | --- |
| Skenario diuji | 13 |
| Skenario sesuai harapan | 13 |
| Skenario tidak sesuai | 0 |
| Diagnosis akhir yang dihasilkan | 12 skenario |
| Kasus inconclusive yang diharapkan | 1 skenario |
| **Tingkat kesesuaian** | **100%** |

Angka **100%** menunjukkan konsistensi internal antara basis aturan, mesin inferensi, dan skenario yang dirancang. Angka ini bukan ukuran akurasi diagnosis di dunia nyata, karena skenario disusun oleh penyusun sistem dan jawaban fakta diberikan secara terkontrol.

---

## 5.4 Evaluasi

### 5.4.1 Kelebihan

1. **Penalaran dapat ditelusuri** — setiap diagnosis disertai aturan, fakta, dan urutan iterasi yang membentuknya.
2. **Forward chaining berjalan sesuai rancangan** — fakta memicu kesimpulan antara, lalu kesimpulan antara bersama fakta lain memicu diagnosis akhir.
3. **Beberapa aturan dapat mendukung kesimpulan yang sama** — cakupan kombinasi gejala lebih luas tanpa menggandakan kesimpulan di memori kerja.
4. **Prioritas tidak menghapus diagnosis lain** — semua diagnosis yang relevan tetap ditampilkan berurutan.
5. **Kondisi tidak lengkap ditangani jujur** — sistem memilih `inconclusive` daripada memaksakan diagnosis yang tidak didukung premis lengkap.
6. **Setiap aturan memiliki sumber** — keputusan dapat ditelusuri hingga dokumentasi vendor, standar, atau literatur ilmiah.

### 5.4.2 Keterbatasan

1. **Skenario disusun bersama aturan** — keberhasilan 13/13 berpotensi menunjukkan konsistensi internal, bukan validitas eksternal.
2. **Tidak ada validasi pakar** — aturan divalidasi melalui sumber dan konsistensi basis pengetahuan, bukan penilaian teknisi.
3. **Tidak ada pengujian lapangan** — sistem belum diuji pada perangkat Bluetooth nyata dalam jumlah kasus yang memadai.
4. **Jawaban pengguna bersifat mandiri** — jawaban yang keliru akan menghasilkan diagnosis yang keliru.
5. **Cakupan terbatas** — hanya Windows 10/11 dan perangkat audio/input Bluetooth.
6. **Belum ada uji usability formal** - kemudahan penggunaan baru dinilai secara kualitatif.
7. **Filter jenis perangkat belum diuji terpisah** - pemilih perangkat adalah fitur antarmuka; pengujian otomatis memastikan pertanyaan tersembunyi dikirim sebagai `Tidak`, tetapi pemetaan audio/keyboard-mouse belum dinilai oleh pengguna nyata atau pakar.

### 5.4.3 Implikasi

Hasil pengujian menunjukkan bahwa sistem layak digunakan sebagai **alat bantu diagnosis awal yang dapat dijelaskan**, bukan pengganti pemeriksaan teknisi. Kekuatan utama sistem terletak pada keterlacakan aturan dan kejelasan alasan, bukan pada klaim akurasi statistik.

Pengembangan berikutnya sebaiknya menambah variasi skenario, melakukan pengujian lapangan, dan menilai kejelasan pertanyaan bersama calon pengguna. Validasi tambahan juga dapat dilakukan dengan memperluas rujukan literatur dan standar, tanpa perlu mengubah arsitektur sistem.
