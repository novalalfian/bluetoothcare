# Pemetaan PRD ke Implementasi

Dokumen ini menghubungkan setiap kebutuhan pada PRD versi 2.0 dengan berkas, fungsi, dan bukti di aplikasi.

## 1. Kebutuhan fungsional

| ID | Kebutuhan | Implementasi | Bukti / cara memeriksa |
| --- | --- | --- | --- |
| FR-01 | Halaman pembuka: judul, deskripsi, batasan, tombol Mulai | `static/index.html` bagian `#view-beranda`; hero, bagian ruang lingkup, CTA | Buka `#beranda`; tombol “Mulai konsultasi” menuju `#konsultasi` |
| FR-02 | 14 fakta Ya/Tidak, 3 kelompok | `knowledge_base.json` → `facts` + `meta.groups`; dirender `renderQuestionGroups()` di `static/app.js` | Form menampilkan 14 pertanyaan dalam 3 fieldset |
| FR-03 | Validasi: semua wajib dijawab | `validate_answers()` (`inference_engine.py`); validasi klien `onSubmit()` + `markInvalid()` | Tekan Proses tanpa menjawab → pesan menyebut kode, pertanyaan ditandai merah |
| FR-04 | Basis pengetahuan JSON terpisah | `knowledge_base.json`; `KnowledgeBase.load()`; tidak ada aturan di kode inferensi | Ubah JSON → restart/muat ulang → perilaku berubah tanpa menyentuh Python/JS |
| FR-05 | Forward chaining berulang sampai stabil | `run_inference()`: loop `snapshot` → `conflict_set` → *fire* → ulangi | Jejak F1+F14 menunjukkan iterasi 1 (R1→K1) dan 2 (R9→H1) |
| FR-06 | Operator AND/OR pada premis | `eval_premise()` / `_eval_node()`; R3, R14, R15 | Uji `F7` saja (gagal R14) vs `F7+F5`/`F7+F11` (R14 aktif) |
| FR-07 | Diagnosis berprioritas + saran | Prioritas di `conclusions[].priority`; pengurutan di `run_inference()`; kartu di `renderDiagnosis()` | Hasil F1+F14 → H1 prioritas 1; beberapa diagnosis diurutkan 1→7 |
| FR-08 | Fasilitas penjelasan | `trace[]`, `working_memory`, `_build_derivation()`; `renderTrace()`, `renderCause()` | Tabel iterasi, fakta masukan, K/H, pohon alasan JIKA–MAKA |
| FR-09 | “Belum dapat disimpulkan” | Cabang `inconclusive` di `run_inference()`; panel di `renderResult()` | Skenario F7 saja menampilkan pesan, F7, dan saran baterai |
| FR-10 | Konsultasi ulang | `reconsult()` di `static/app.js`; tombol atas & bawah | Form kosong, progres 0/14, `sessionStorage` dihapus |
| FR-11 | Daftar aturan/fakta | `GET /api/knowledge`; tab `#view-pengetahuan`; `renderFactsTable()`, `renderRulesTable()`, `renderConclusions()`, `renderScenarios()`, `renderSources()` | Tab menampilkan 14 fakta, 19 aturan, 12 kesimpulan, 7 skenario, 4 sumber |
| FR-12 | Ekspor PDF/teks | `buildTextReport()` + `downloadResult()`; `@media print` + `printResult()` | Tombol Unduh `.txt` dan Cetak/PDF |
| FR-13 | Log konsultasi lokal | `AppHandler._write_log()`; `logs/konsultasi.jsonl`; opsi `--no-log` | Setelah konsultasi, file JSONL bertambah; hanya gejala/hasil, tanpa nama/IP |

## 2. Kebutuhan non-fungsional

| ID | Kebutuhan | Implementasi / bukti |
| --- | --- | --- |
| NFR-01 | Inferensi < 1 detik | Pengujian `test_inference_is_fast`; hasil aktual 0,04–0,8 ms untuk 7 skenario |
| NFR-02 | Bahasa Indonesia sederhana | Seluruh antarmuka Indonesia; `hint` pada setiap fakta; `advice` berupa langkah konkret |
| NFR-03 | Lokal tanpa internet | Python stdlib (`http.server`), tanpa CDN/font eksternal; hanya bind `127.0.0.1` |
| NFR-04 | Pemisahan komponen | `knowledge_base.json` (KB) ↔ `inference_engine.py` (mesin) ↔ `app.py` (pengendali) ↔ `static/` (UI) |
| NFR-05 | Responsif | Breakpoint 1080/920/760/520 px; menu seluler; tabel dapat digulir; `tests` UI memeriksa toggle menu |
| NFR-06 | Tanpa data pribadi | Form hanya 14 gejala; log tidak memuat nama/IP/jawaban lengkap; tidak ada analitik |

## 3. Basis pengetahuan dan konsistensi

| Aspek | Target | Aktual | Pemeriksaan |
| --- | --- | --- | --- |
| Fakta | 10+ | 14 | `KnowledgeBase._validate_structure` + `test_minimum_specification` |
| Diagnosis akhir | 5+ | 7 | `final_conclusions` |
| Kesimpulan antara | 3+ | 5 | `type: "intermediate"` |
| Aturan | 15+ | 19 | `len(kb.rules)` |
| AND/OR | Wajib | R3, R14, R15 dan lainnya | `eval_premise`, label `R14 = F7 DAN (F5 ATAU F11)` |
| Skenario uji | 5+ | 7 | `meta.test_scenarios` + `test_all_prd_scenarios` |
| Sumber | 2+ | 4 (S1–S4) | Tab Sumber; S2/S3 masih perlu identitas lengkap |

Pemeriksaan konsistensi otomatis:

- kode fakta/aturan/kesimpulan unik;
- semua `if` hanya merujuk fakta atau kesimpulan yang terdaftar;
- semua `then` menunjuk kesimpulan terdaftar;
- setiap kesimpulan dihasilkan minimal satu aturan;
- diagnosis akhir wajib memiliki prioritas bilangan bulat;
- struktur premis hanya `and`, `or`, `not`, atau kode fakta;
- deteksi kesimpulan ganda pada memori kerja ditandai “sudah ada”;
- batas 100 iterasi mencegah siklus.

## 4. Representasi pengetahuan (graf dependensi)

```text
F1 ──R1──┐
F10 ─R2──┴──> K1 ──R8 (dengan F4)──> H1
                    └─R9 (dengan F14)─> H1

F13 ─┐
F9 ──┴─R3──┐
F2 ──R4────┴──> K2 ──R10 (dengan F2)──> H2
                     └─R11 (dengan F4)─> H2

F6 ──R5──> K3 ──R12 (dengan F5)──> H3
                  └─R13 (dengan F11)─> H3

F8 ──R6──> K4 ──R15──> H5

F3 ──R7──> K5 ──R16 (dengan F4)──> H6
                  └─R17 (dengan F8)─> H6

F7 ──R14 (dengan F5 atau F11)──> H4
F12 ─R18 (dengan F3)──> H7
F12 ─R19 (dengan F5)──> H7
```

Graf ini juga dapat diperiksa pada data `rules` dan pohon `derivation` di halaman hasil.

## 5. Pemetaan ke rubrik UTS

| Komponen rubrik (bobot) | Bukti |
| --- | --- |
| Analisis kasus (8) | Bab 1–3 PRD; bagian “Latar belakang” dan “Batasan” di aplikasi |
| Akuisisi pengetahuan (12) | 4 sumber di `knowledge_base.json`; status verifikasi pada tab Sumber; placeholder S2/S3 untuk dilengkapi |
| Basis pengetahuan (17) | 14 fakta, 5 K, 7 H, 19 aturan; validasi konsistensi otomatis; uji minimum |
| Representasi pengetahuan (8) | Graf dependensi di atas; premis bersarang JSON; label aturan |
| Mesin inferensi (20) | `inference_engine.py`; pseudocode di README; tabel iterasi di halaman hasil |
| Implementasi (15) | FR-01–FR-10 terpenuhi; UI responsif; API lokal |
| Fasilitas penjelasan (5) | `trace`, `working_memory`, pohon alasan per diagnosis, kalimat JIKA–MAKA |
| Pengujian (10) | 28 pengujian otomatis; 7/7 skenario sesuai; `docs/HASIL_UJI.md` |
| Dokumentasi (5) | README, dokumen ini, hasil uji, komentar kode, video demo (perlu direkam) |

## 6. Risiko dan mitigasi pada implementasi

| Risiko PRD | Mitigasi yang sudah ada |
| --- | --- |
| Judul terlalu umum | Judul membatasi platform Windows 10/11 dan perangkat audio/input |
| Sumber tidak terdokumentasi | Setiap aturan memiliki `source` (S1–S4); tab sumber menampilkan status |
| Beberapa diagnosis muncul bersamaan | Pengurutan prioritas + penjelasan per diagnosis + catatan bahwa prioritas tidak menghapus diagnosis lain |
| Tidak memahami kode sendiri | Komentar modul/fungsi, pemisahan tanggung jawab, README berisi alur dan pseudocode |
| Penggunaan AI tidak dinyatakan | Pernyataan AI di README, halaman Tentang, dan template laporan |

## 7. Deliverables yang perlu dilengkapi mahasiswa

- [x] Aplikasi berjalan lokal
- [x] Basis aturan JSON versi 2.0
- [x] 7 skenario uji otomatis
- [x] Dokumentasi teknis
- [ ] NIM/nama pada `meta.author` dan halaman Tentang
- [ ] Identitas lengkap sumber S2 (merek/model manual) dan S3 (nama/tanggal wawancara)
- [ ] Laporan PDF `NIM_NamaLengkap_UTS_SistemPakar.pdf`
- [ ] Video demonstrasi maksimal 5 menit
- [ ] Bukti versi awal dan akhir basis aturan
- [ ] Pernyataan penggunaan AI di laporan akhir
