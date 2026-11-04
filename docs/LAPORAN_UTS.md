# Draf Laporan UTS Sistem Pakar

**Sistem Pakar Diagnosis Gangguan Konektivitas Perangkat Bluetooth pada Laptop (BluetoothCare)**

> Catatan: teks bertanda `[ISI: ...]` dan gambar bertanda `[SISIPKAN GAMBAR: ...]` perlu Anda lengkapi sebelum laporan dikumpulkan.

---

## 1. Halaman Judul dan Identitas Mahasiswa

<div align="center">

**LAPORAN UJIAN TENGAH SEMESTER**

**SISTEM PAKAR (TI22604)**

<br>

**SISTEM PAKAR DIAGNOSIS GANGGUAN KONEKTIVITAS PERANGKAT BLUETOOTH PADA LAPTOP**

**BluetoothCare — Diagnosis awal earphone, speaker, keyboard, dan mouse Bluetooth di Windows 10/11**

<br>

Disusun oleh:

| | |
| --- | --- |
| Nama | [ISI: Nama Lengkap] |
| NIM | [ISI: NIM] |
| Program Studi | [ISI: Program Studi] |
| Kelas | [ISI: Kelas] |
| Dosen Pengampu | [ISI: Nama Dosen] |

<br>

**PROGRAM STUDI [ISI]**

**FAKULTAS [ISI]**

**UNIVERSITAS [ISI]**

**SEMESTER GANJIL 2026/2027**

</div>

---

## 2. Ringkasan Sistem

BluetoothCare adalah sistem pakar berbasis aturan (rule-based expert system) yang membantu pengguna melakukan diagnosis awal gangguan konektivitas perangkat Bluetooth pada laptop Windows 10/11. Perangkat yang dicakup meliputi earphone, speaker, keyboard, dan mouse Bluetooth.

Sistem menerima 20 fakta gejala (jawaban Ya/Tidak), memprosesnya dengan metode **forward chaining** melalui 31 aturan JIKA–MAKA, dan menghasilkan hingga 10 diagnosis akhir berprioritas beserta langkah perbaikan. Sistem juga menyediakan fasilitas penjelasan berupa jejak penalaran per iterasi dan pohon alasan, serta halaman transparansi yang menampilkan seluruh fakta, aturan, kesimpulan, skenario uji, dan sumber pengetahuan.

Basis pengetahuan disimpan terpisah dalam berkas JSON sehingga dapat diubah tanpa menyentuh kode mesin inferensi. Aplikasi berjalan luring di localhost, memakai pustaka standar Python tanpa dependensi eksternal, dan tidak meminta data pribadi.

| Ringkasan angka | Nilai |
| --- | --- |
| Fakta (gejala) | 20 |
| Kelompok fakta | 3 |
| Aturan produksi | 31 |
| Kesimpulan antara (K) | 9 |
| Diagnosis akhir (H) | 10 |
| Skenario uji | 13 |
| Sumber pengetahuan | 9 |
| Metode inferensi | Forward chaining |
| Platform | Windows 10/11, browser modern |

---

## 3. Bab 1 Pendahuluan

### 1.1 Latar Belakang

Gangguan konektivitas Bluetooth pada laptop merupakan masalah umum yang penyebabnya berlapis: bisa dari sisi laptop (driver, layanan, pengaturan daya), sisi perangkat (mode pairing, baterai, data pairing lama), maupun sisi lingkungan (jarak, penghalang, interferensi pita 2,4 GHz). Pengguna awam sering kesulitan menentukan langkah perbaikan yang tepat dan mencoba solusi secara acak, sehingga masalah tidak selesai atau berulang.

Sistem pakar meniru penalaran seorang teknisi: mengumpulkan gejala, mencocokkannya dengan pengetahuan pakar, lalu menyimpulkan penyebab paling mungkin beserta langkah perbaikannya. Dengan pendekatan ini, pengguna dapat memperoleh panduan terstruktur tanpa harus memahami istilah teknis secara mendalam.

### 1.2 Rumusan Masalah

1. Bagaimana mengakuisisi dan merepresentasikan pengetahuan diagnosis gangguan Bluetooth dari sumber yang dapat dipertanggungjawabkan?
2. Bagaimana merancang sistem pakar yang memisahkan basis pengetahuan, mesin inferensi, pengendali, dan antarmuka?
3. Bagaimana mengukur kesesuaian keluaran sistem dengan skenario yang diharapkan?

### 1.3 Tujuan

1. Membangun basis pengetahuan diagnosis Bluetooth yang bersumber dari dokumentasi, standar, dan literatur ilmiah.
2. Membangun mesin inferensi forward chaining yang dapat menjelaskan alasan setiap diagnosis.
3. Menguji sistem terhadap skenario diagnosis dan mengevaluasi tingkat kesesuaiannya.

### 1.4 Calon Pengguna

| Pengguna | Karakteristik | Kebutuhan utama |
| --- | --- | --- |
| Pengguna laptop umum | Awam istilah teknis, memakai earphone/speaker/keyboard Bluetooth | Langkah perbaikan sederhana berurutan |
| Mahasiswa dan pekerja | Sering memakai perangkat audio BT untuk kuliah/rapat daring | Diagnosis cepat untuk masalah suara dan mikrofon |
| Teknisi pemula / laboran | Menangani keluhan pengguna di lab atau toko | Rujukan urutan pemeriksaan dan tingkat keyakinan diagnosis |
| Penyusun laporan / pengajar | Perlu memeriksa keterlacakan keputusan | Halaman transparansi basis pengetahuan |

### 1.5 Ruang Lingkup

- Platform: **Windows 10 dan Windows 11**.
- Perangkat: **earphone, headset, speaker, keyboard, dan mouse Bluetooth**.
- Gejala yang dicakup: 20 fakta dalam tiga kelompok (laptop & sistem, perangkat Bluetooth, lingkungan & sinyal).
- Keluaran: diagnosis awal berprioritas (maksimal 10) beserta langkah perbaikan, jejak penalaran, dan pohon alasan.
- Mode operasi: aplikasi web lokal (localhost), tanpa autentikasi, tanpa data pribadi.

### 1.6 Batasan

1. Sistem hanya memberikan **diagnosis awal**, bukan pengganti pemeriksaan teknisi.
2. Sistem **tidak mengubah pengaturan** laptop secara otomatis dan tidak memperbaiki perangkat keras.
3. Sistem **tidak mengumpulkan data pribadi**; log konsultasi hanya menyimpan gejala yang dijawab "Ya", daftar diagnosis, aturan yang berjalan, jumlah iterasi, dan waktu inferensi.
4. Diagnosis bergantung pada kejujuran dan ketepatan jawaban pengguna.
5. Sistem tidak menangani sistem operasi selain Windows 10/11.
6. Basis aturan tidak memakai operator `NOT` pada versi ini walaupun mesin mendukungnya.

---

## 4. Bab 2 Akuisisi dan Representasi Pengetahuan

### 2.1 Metode Akuisisi Pengetahuan

Akuisisi pengetahuan dilakukan melalui empat jalur:

1. **Studi literatur ilmiah** — jurnal dan prosiding tentang interferensi dan kinerja Bluetooth.
2. **Standar dan dokumentasi teknis** — spesifikasi Bluetooth SIG, NIST, dan dokumentasi vendor.
3. **Dokumentasi manual perangkat** — perilaku pairing, indikator lampu, dan baterai.
4. **Validasi silang dan konsistensi internal** — sumber yang membahas topik sama dibandingkan (misalnya interferensi pita 2,4 GHz pada S4, S5, dan S9), lalu seluruh basis pengetahuan diperiksa otomatis: kode unik, rujukan premis/kesimpulan valid, dan setiap kesimpulan dihasilkan minimal satu aturan. Wawancara pakar tidak dilakukan, sehingga laporan ini tidak mengklaim validasi oleh pakar.

### 2.2 Sumber Pengetahuan (S1, S2, S4–S10)

| ID | Sumber | Jenis | Status |
| --- | --- | --- | --- |
| S1 | Microsoft Support, *Fix Bluetooth problems in Windows*. https://support.microsoft.com/en-us/windows/hardware/bluetooth/fix-bluetooth-problems-in-windows (diakses 2 Nov 2026) | Dokumentasi vendor | Terverifikasi |
| S2 | Buku manual perangkat Bluetooth (earphone/speaker/keyboard). [ISI: merek dan model] | Manual pabrikan | Perlu dilengkapi |
| S4 | Bluetooth SIG, *Bluetooth Core Specification — operasi pita 2,4 GHz*. https://www.bluetooth.com/specifications/specs/ (diakses 2 Nov 2026) | Standar | Terverifikasi |
| S5 | N. Golmie dkk., "Interference Evaluation of Bluetooth and IEEE 802.11b Systems," *Wireless Networks*, Springer, 2003. https://link.springer.com/article/10.1023/A:1022821110023 | Jurnal | Terverifikasi |
| S6 | Intel Corporation / USB-IF, *USB 3.0 Radio Frequency Interference Impact on 2.4 GHz Wireless Devices*, white paper 327216-001, 2012. https://www.usb.org/sites/default/files/327216.pdf | White paper industri | Terverifikasi |
| S7 | NIST, *Guide to Bluetooth Security (NIST SP 800-121 Rev. 2)*, 2017. https://csrc.nist.gov/pubs/sp/800/121/r2/upd1/final | Standar | Terverifikasi |
| S8 | Bluetooth SIG, *LE Audio*. https://www.bluetooth.com/learn-about-bluetooth/recent-enhancements/le-audio/ | Dokumentasi teknologi | Terverifikasi |
| S9 | C. Cordeiro dkk., "Interference Modeling and Performance of Bluetooth MAC Protocol," *IEEE Transactions on Wireless Communications*, 2003. https://ieeexplore.ieee.org/document/1244801 | Jurnal | Terverifikasi |
| S10 | Microsoft Learn, *Bluetooth power management for modern standby platforms*. https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/bluetooth-power-management-for-modern-standby-platforms | Dokumentasi vendor | Terverifikasi |

Setiap aturan produksi mencantumkan atribut `source` yang menunjuk salah satu sumber di atas, sehingga setiap diagnosis dapat ditelusuri hingga rujukan aslinya. Nomor **S3 sengaja tidak dipakai** karena wawancara pakar tidak dilakukan; nomor sumber lain dipertahankan agar rujukan pada aturan (misalnya S5–S10) tidak berubah.

### 2.3 Fakta (F) — 20 Gejala

| Kode | Gejala | Kelompok |
| --- | --- | --- |
| F1 | Pengaturan atau tombol Bluetooth di laptop tidak muncul atau tidak bisa diaktifkan | Laptop & sistem |
| F2 | Perangkat tidak muncul di daftar pencarian laptop | Perangkat |
| F3 | Perangkat pernah terpasang tetapi tidak tersambung otomatis | Perangkat |
| F4 | Pairing gagal atau terus meminta PIN/passkey | Perangkat |
| F5 | Suara putus-putus atau patah-patah | Lingkungan |
| F6 | Jarak lebih dari 10 m, ada penghalang, atau banyak perangkat nirkabel di sekitar | Lingkungan |
| F7 | Baterai perangkat di bawah 20% | Perangkat |
| F8 | Perangkat tersambung tetapi tidak ada suara | Laptop & sistem |
| F9 | Perangkat sedang tersambung ke perangkat lain | Perangkat |
| F10 | Driver Bluetooth bertanda peringatan atau baru diperbarui | Laptop & sistem |
| F11 | Keyboard atau mouse Bluetooth lambat merespons | Perangkat |
| F12 | Mode hemat daya laptop aktif | Laptop & sistem |
| F13 | Lampu indikator perangkat tidak berkedip (belum mode pairing) | Perangkat |
| F14 | Perangkat sudah dihapus dan dipasang ulang, masalah tetap ada | Perangkat |
| F15 | Receiver/adaptor Bluetooth memakai atau dekat port USB 3.0 | Laptop & sistem |
| F16 | Wi-Fi 2,4 GHz aktif dan router dekat laptop | Lingkungan |
| F17 | Banyak perangkat Bluetooth aktif bersamaan | Lingkungan |
| F18 | Audio terlambat, tidak sinkron, atau hanya satu sisi | Perangkat |
| F19 | Tidak tersambung kembali setelah tidur/hibernate/Fast Startup | Laptop & sistem |
| F20 | Driver Bluetooth dari Windows Update, bukan pabrikan | Laptop & sistem |

Setiap fakta memiliki `hint` (keterangan untuk pengguna) dan `solo_advice` (saran bila fakta muncul tanpa diagnosis).

### 2.4 Kesimpulan Antara (K) — 9 Simpulan

| Kode | Kesimpulan antara | Ringkasan |
| --- | --- | --- |
| K1 | Adaptor Bluetooth laptop tidak siap | Indikasi masalah adaptor, driver, atau layanan Bluetooth |
| K2 | Perangkat belum siap dipasangkan | Belum mode pairing, tidak terdeteksi, atau tersambung ke perangkat lain |
| K3 | Sinyal radio terganggu | Jarak, penghalang, atau kepadatan perangkat nirkabel |
| K4 | Pengaturan keluaran audio kemungkinan salah | Windows mengarahkan audio ke keluaran lain |
| K5 | Data pairing lama berpotensi bermasalah | Data pairing tidak lagi cocok |
| K6 | Profil atau codec audio tidak sesuai | Codec tidak cocok sehingga audio terlambat/tidak sinkron |
| K7 | Kanal 2,4 GHz padat | Banyak perangkat berbagi pita 2,4 GHz |
| K8 | Jalur adaptor atau driver belum optimal | Adaptor USB atau driver generik menurunkan kualitas tautan |
| K9 | Adaptor tidak dipulihkan setelah tidur/startup cepat | Pengaturan daya/Fast Startup menahan adaptor |

### 2.5 Diagnosis Akhir (H) dan Prioritas

| Prioritas | Kode | Diagnosis akhir |
| --- | --- | --- |
| 1 | H1 | Driver atau layanan Bluetooth bermasalah |
| 2 | H2 | Perangkat belum mode pairing atau tersambung ke perangkat lain |
| 3 | H6 | Data pairing lama rusak |
| 4 | H7 | Manajemen daya mematikan adaptor |
| 5 | H4 | Baterai perangkat lemah |
| 6 | H3 | Interferensi atau jarak/penghalang |
| 7 | H5 | Output audio default belum diarahkan ke perangkat |
| 8 | H8 | Profil atau codec audio tidak sesuai |
| 9 | H9 | Kanal 2,4 GHz padat |
| 10 | H10 | Adaptor USB atau driver generik tidak kompatibel |

Prioritas mengatur urutan tampil dan pemeriksaan, bukan menghapus diagnosis lain. Bila beberapa diagnosis muncul, semuanya ditampilkan berurutan.

### 2.6 Aturan Produksi (31 Aturan)

Basis aturan dikelompokkan menurut kesimpulan (MAKA). Satu kesimpulan dapat dihasilkan beberapa aturan dengan premis berbeda.

```text
K1  Adaptor Bluetooth laptop tidak siap
    R1  F1                                   -> K1    [S1]
    R2  F10                                  -> K1    [S1]

K2  Perangkat belum siap dipasangkan
    R3  F13 ATAU F9                          -> K2    [S2]
    R4  F2                                   -> K2    [S2]

K3  Sinyal radio terganggu
    R5  F6                                   -> K3    [S4]

K4  Pengaturan keluaran audio kemungkinan salah
    R6  F8                                   -> K4    [S1]

K5  Data pairing lama berpotensi bermasalah
    R7  F3                                   -> K5    [S2]

K6  Profil atau codec audio tidak sesuai
    R24 F18                                  -> K6    [S8]

K7  Kanal 2,4 GHz padat
    R22 F16                                  -> K7    [S5]
    R23 F17                                  -> K7    [S9]

K8  Jalur adaptor atau driver belum optimal
    R20 F15                                  -> K8    [S6]
    R21 F20                                  -> K8    [S1]

K9  Adaptor tidak dipulihkan setelah tidur/startup cepat
    R25 F19                                  -> K9    [S10]

H1  Driver atau layanan Bluetooth bermasalah
    R8  K1 DAN F4                            -> H1    [S1]
    R9  K1 DAN F14                           -> H1    [S1]

H2  Perangkat belum mode pairing atau tersambung ke perangkat lain
    R10 K2 DAN F2                            -> H2    [S2]
    R11 K2 DAN F4                            -> H2    [S2]

H3  Interferensi atau jarak/penghalang
    R12 K3 DAN F5                            -> H3    [S4]
    R13 K3 DAN F11                           -> H3    [S4]

H4  Baterai perangkat lemah
    R14 F7 DAN (F5 ATAU F11)                 -> H4    [S2]

H5  Output audio default belum diarahkan ke perangkat
    R15 K4                                   -> H5    [S1]

H6  Data pairing lama rusak
    R16 K5 DAN F4                            -> H6    [S7]
    R17 K5 DAN F8                            -> H6    [S2]

H7  Manajemen daya mematikan adaptor
    R18 F12 DAN F3                           -> H7    [S1]
    R19 F12 DAN F5                           -> H7    [S1]
    R31 K9                                   -> H7    [S10]

H8  Profil atau codec audio tidak sesuai
    R30 K6                                   -> H8    [S8]

H9  Kanal 2,4 GHz padat
    R28 K7 DAN F5                            -> H9    [S5]
    R29 K7 DAN F11                           -> H9    [S9]

H10 Adaptor USB atau driver generik tidak kompatibel
    R26 K8 DAN F4                            -> H10   [S6]
    R27 K8 DAN F14                           -> H10   [S1]
```

### 2.7 Diagram Pengetahuan (Graf Dependensi)

```text
FAKTA              ATURAN                 KESIMPULAN        ATURAN        DIAGNOSIS

F1 ─────────────────────────────────────────────────────────────────────►
F10 ──R2──┐                                                              
          └─► K1 ─┬─R8 (dengan F4)──┐                                   
F1 ──R1───────────┘                 ├───────────────────────────────► H1 
                  └─R9 (dengan F14)─┘                                   

F13,F9 ──R3──┐                                                           
F2 ──────R4──┴─► K2 ─┬─R10 (dengan F2)──┐                                
                     └─R11 (dengan F4)─┴───────────────────────────► H2 

F6 ──R5──► K3 ─┬─R12 (dengan F5)──┐                                      
               └─R13 (dengan F11)┴────────────────────────────────► H3 

F8 ──R6──► K4 ──R15───────────────────────────────────────────────► H5 

F3 ──R7──► K5 ─┬─R16 (dengan F4)──┐                                      
               └─R17 (dengan F8)──┴───────────────────────────────► H6 

F7 ──R14 (dengan F5 atau F11)─────────────────────────────────────► H4 

F12 ─┬─R18 (dengan F3)──┐                                                
     └─R19 (dengan F5)──┴──────────────────────────────────────────► H7 
F19 ──R25──► K9 ──R31──────────────────────────────────────────────► H7 

F18 ──R24──► K6 ──R30──────────────────────────────────────────────► H8 

F16 ──R22──┐                                                            
F17 ──R23──┴─► K7 ─┬─R28 (dengan F5)──┐                                  
                   └─R29 (dengan F11)┴───────────────────────────► H9 

F15 ──R20──┐                                                            
F20 ──R21──┴─► K8 ─┬─R26 (dengan F4)──┐                                  
                   └─R27 (dengan F14)┴──────────────────────────► H10 
```

Sumber literatur pendukung jalur berbasis literatur: S5 (interferensi Wi-Fi/Bluetooth), S6 (derau USB 3.0), S7 (standar keamanan/pairing NIST), S8 (LE Audio), S9 (kepadatan kanal IEEE), S10 (manajemen daya adaptor).

### 2.8 Validasi Konsistensi Basis Pengetahuan

Saat server dijalankan, `KnowledgeBase` memvalidasi:

- kode fakta, aturan, dan kesimpulan unik;
- setiap premis `if` hanya merujuk fakta/kesimpulan yang terdaftar;
- setiap `then` menunjuk kesimpulan terdaftar;
- setiap kesimpulan dihasilkan minimal satu aturan;
- diagnosis akhir wajib memiliki prioritas berupa bilangan bulat;
- struktur premis hanya `and`, `or`, `not`, atau kode fakta.

---

## 5. Bab 3 Perancangan Sistem

### 3.1 Arsitektur Sistem

Sistem memakai pemisahan tanggung jawab berlapis: basis pengetahuan, mesin inferensi, pengendali HTTP, dan antarmuka.

```text
┌──────────────────────────────────────────────┐
│                 BROWSER (UI)                 │
│  index.html + styles.css + app.js            │
│  Hash routing: #beranda #konsultasi #hasil   │
│  #pengetahuan #tentang                       │
└───────────────┬──────────────────────────────┘
                │  fetch JSON (HTTP)
                ▼
┌──────────────────────────────────────────────┐
│           PENGENDALI HTTP (app.py)           │
│  http.server.ThreadingHTTPServer             │
│  GET  /api/health                            │
│  GET  /api/knowledge                         │
│  POST /api/diagnose                          │
│  GET  / , /styles.css , /app.js , ...        │
│  (opsional) tulis logs/konsultasi.jsonl      │
└───────────────┬──────────────────────────────┘
                │  panggil fungsi
                ▼
┌──────────────────────────────────────────────┐
│        MESIN INFERENSI (inference_engine.py) │
│  KnowledgeBase.load() / public_data()        │
│  validate_answers()                          │
│  run_inference()  (forward chaining)         │
│  trace[], working_memory, derivation         │
└───────────────┬──────────────────────────────┘
                │  baca
                ▼
┌──────────────────────────────────────────────┐
│        BASIS PENGETAHUAN (knowledge_base.json)│
│  meta, facts[20], conclusions[19], rules[31], │
│  sources[10]                                  │
└──────────────────────────────────────────────┘
```

### 3.2 Alur Proses (Forward Chaining)

```text
memori_kerja <- fakta yang dijawab "Ya"
jejak <- []
iterasi <- 0
ulangi
    snapshot <- salinan memori_kerja
    aturan_aktif <- semua aturan yang belum berjalan
                    dan premisnya terpenuhi pada snapshot
    jika aturan_aktif kosong: berhenti
    iterasi <- iterasi + 1
    untuk setiap aturan pada aturan_aktif:
        tambahkan kesimpulan ke memori_kerja
        catat (iterasi, aturan, premis, kesimpulan, status baru) ke jejak
        tandai aturan sudah berjalan
selesai
susun diagnosis akhir berurutan berdasarkan prioritas
```

Satu iterasi = satu siklus evaluasi terhadap **snapshot** memori kerja. Seluruh aturan yang aktif pada siklus itu dijalankan, lalu fakta baru dipakai pada siklus berikutnya. Aturan yang sudah berjalan tidak diulang.

### 3.3 Rancangan Antarmuka

Aplikasi berupa Single Page Application dengan hash routing (tanpa server render). Lima tampilan utama:

| Hash | Tampilan | Isi |
| --- | --- | --- |
| `#beranda` | Beranda | Judul, ruang lingkup, statistik basis pengetahuan, tombol Mulai |
| `#konsultasi` | Konsultasi | Form 20 pertanyaan Ya/Tidak dalam 3 kelompok + progres |
| `#hasil` | Hasil | Diagnosis berprioritas, langkah perbaikan, jejak iterasi, pohon alasan, unduh/cetak |
| `#pengetahuan` | Basis Pengetahuan | Pemenuhan spesifikasi, tab Fakta, Aturan, Kesimpulan, Skenario, Sumber |
| `#tentang` | Tentang | Metode, ruang lingkup, batasan, sumber, pernyataan penggunaan AI |

Prinsip desain: bahasa Indonesia sederhana, tiap pertanyaan punya `hint`, tombol besar, desain responsif (laptop dan ponsel), dan gaya cetak khusus untuk ekspor PDF.

### 3.4 Rancangan Data (Struktur JSON)

```json
{
  "meta": {
    "title": "...",
    "version": "2.2",
    "groups": [
      { "id": "laptop", "label": "Laptop & sistem" },
      { "id": "perangkat", "label": "Perangkat Bluetooth" },
      { "id": "lingkungan", "label": "Lingkungan & sinyal" }
    ],
    "test_scenarios": [ { "no": 1, "facts": ["F1","F14"], "rules": ["R1","R9"], "result": "H1" } ]
  },
  "facts": [
    { "id": "F1", "text": "...", "group": "laptop", "hint": "...", "solo_advice": "..." }
  ],
  "conclusions": [
    { "id": "K1", "type": "intermediate", "text": "...", "summary": "..." },
    { "id": "H1", "type": "final", "text": "...", "priority": 1, "advice": ["..."] }
  ],
  "rules": [
    { "id": "R14", "if": { "and": ["F7", { "or": ["F5","F11"] }] }, "then": "H4", "source": "S2" }
  ],
  "sources": [
    { "id": "S5", "title": "...", "publisher": "...", "url": "...", "status": "terverifikasi" }
  ]
}
```

Premis mendukung: fakta tunggal (`"F1"`), `and`, `or`, `not`, dan kombinasi bersarang seperti `{"and": ["F7", {"or": ["F5","F11"]}]}`.

### 3.5 Rancangan API

| Metode | Rute | Fungsi | Keluaran |
| --- | --- | --- | --- |
| GET | `/api/health` | Status server | `{status, facts, rules, conclusions}` |
| GET | `/api/knowledge` | Data transparansi | Fakta, aturan, kesimpulan, sumber, statistik, pemenuhan spesifikasi |
| POST | `/api/diagnose` | Jalankan inferensi | Diagnosis, trace, working_memory, stats |
| GET | `/`, `/styles.css`, `/app.js`, `/favicon.svg` | Berkas antarmuka | HTML/CSS/JS/SVG |

---

## 6. Bab 4 Implementasi

### 6.1 Teknologi

| Komponen | Teknologi | Alasan |
| --- | --- | --- |
| Bahasa | Python 3.10+ | Tersedia luas, pustaka standar lengkap |
| Pengendali HTTP | `http.server.ThreadingHTTPServer` | Tanpa dependensi eksternal, pasti jalan luring |
| Antarmuka | HTML, CSS, JavaScript (vanilla) | Ringan, tanpa build tool, tanpa CDN |
| Basis pengetahuan | JSON | Terpisah dari kode, mudah diaudit |
| Pengujian | `unittest` | Bawaan Python |
| Deployment (opsional) | Docker/Render | Menjalankan proses Python, bukan hosting statis |

Aplikasi **tidak memakai dependensi eksternal**; `requirements.txt` sengaja kosong.

### 6.2 Struktur Program

```text
.
├── app.py                  # Pengendali HTTP (API + berkas statis)
├── inference_engine.py     # Mesin forward chaining, validasi, jejak, pohon alasan
├── knowledge_base.json     # 20 fakta, 31 aturan, 19 kesimpulan, 9 sumber, 13 skenario
├── jalankan.bat            # Peluncur Windows
├── static/
│   ├── index.html          # Lima tampilan (beranda, konsultasi, hasil, pengetahuan, tentang)
│   ├── styles.css          # Desain responsif + gaya cetak/PDF
│   ├── app.js              # Routing, form, render hasil, ekspor, tab
│   └── favicon.svg
├── tests/
│   ├── test_engine.py      # 17 pengujian mesin (termasuk 13 skenario)
│   └── test_api.py         # 13 pengujian integrasi HTTP
├── docs/
│   ├── PEMETAAN_PRD.md     # Keterlacakan kebutuhan ke kode
│   ├── HASIL_UJI.md        # Tabel hasil pengujian
│   └── LAPORAN_UTS.md      # Dokumen ini
├── requirements.txt        # Kosong: hanya pustaka standar
├── Dockerfile, render.yaml, Procfile, DEPLOY.md, README.md
```

### 6.3 Basis Pengetahuan

Basis pengetahuan berisi 20 fakta, 9 kesimpulan antara, 10 diagnosis akhir, 31 aturan, dan 9 sumber. Semua dimuat oleh `KnowledgeBase.load()` yang sekaligus memvalidasi konsistensi. Penambahan fakta atau aturan baru tidak memerlukan perubahan kode mesin inferensi maupun antarmuka, karena form, progres, dan tabel dirender dari JSON.

### 6.4 Mesin Inferensi

Fungsi utama pada `inference_engine.py`:

| Fungsi | Tanggung jawab |
| --- | --- |
| `KnowledgeBase.load()` | Memuat JSON dan memvalidasi struktur serta referensi |
| `validate_answers()` | Memastikan semua fakta dijawab Ya/Tidak |
| `eval_premise()` / `_eval_node()` | Mengevaluasi premis AND/OR/NOT bersarang |
| `run_inference()` | Siklus forward chaining sampai stabil |
| `_build_derivation()` | Menyusun pohon alasan tiap diagnosis |
| `public_data()` / `compliance()` | Data halaman transparansi dan pemenuhan spesifikasi |

Cuplikan inti (ringkas):

```python
def _eval_node(node, working_memory, used):
    if isinstance(node, str):
        if node in working_memory:
            used.append(node)
            return True
        return False
    operator, value = next(iter(node.items()))
    if operator == "and":
        return all(_eval_node(child, working_memory, used) for child in value)
    if operator == "or":
        return any(_eval_node(child, working_memory, used) for child in value)
    if operator == "not":
        return not _eval_node(value, working_memory, [])
    raise KnowledgeBaseError(f"Operator premis tidak dikenal: {operator!r}")
```

```python
# run_inference: siklus sampai tidak ada aturan baru aktif
while True:
    snapshot = frozenset(working_memory)
    conflict_set = []
    for rule in kb.ordered_rules:
        if rule["id"] in fired:
            continue
        satisfied, used = eval_premise(rule["if"], snapshot)
        if satisfied:
            conflict_set.append((rule, used))
    if not conflict_set:
        break
    iteration += 1
    for rule, used in conflict_set:
        working_memory.add(rule["then"])
        fired.add(rule["id"])
        trace.append({ "iteration": iteration, "rule_id": rule["id"], ... })
```

Catatan penting: kesimpulan disimpan di memori kerja sebagai **himpunan**, jadi bila dua aturan menghasilkan kesimpulan sama (misalnya R3 dan R4 sama-sama menghasilkan K2), kesimpulan hanya ditambahkan sekali. Setiap aturan tetap dicatat pada `trace` sebagai bukti asal-usul.

---

## 7. Bab 5 Pengujian dan Pembahasan

**Tanggal pengujian:** 4 November 2026
**Lingkungan:** Windows, Python 3.15.0, PyTest tidak dipakai (memakai `unittest`), browser Chromium/Edge.
**Perintah:**

```powershell
python -m unittest discover -s tests -v
```

**Hasil:** `Ran 30 tests ... OK`.

### 5.1 Pengujian Skenario

Setiap skenario dijalankan dengan seluruh 20 fakta dijawab; hanya fakta pada kolom masukan yang bernilai **Ya**.

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

**Tingkat kesesuaian:** (13 skenario sesuai ÷ 13 skenario) × 100% = **100%**.

Catatan skenario 7: sistem menampilkan F7 sebagai gejala terdeteksi, pesan "Belum dapat disimpulkan", serta saran mengisi ulang baterai dan memeriksa mode pairing.

### 5.2 Contoh Jejak Penalaran

**Skenario 1: F1 + F14 → H1**

| Iterasi | Aturan | Premis | Kesimpulan | Status |
| --- | --- | --- | --- | --- |
| 1 | R1 | F1 | K1 | baru |
| 2 | R9 | K1 DAN F14 | H1 | baru |

```text
H1 (Driver atau layanan Bluetooth bermasalah)
└─ R9: JIKA K1 DAN F14 MAKA H1
   ├─ K1 (Adaptor Bluetooth laptop tidak siap)
   │  └─ R1: JIKA F1 MAKA K1
   │     └─ F1 (Pengaturan/tombol Bluetooth tidak bisa diaktifkan)
   └─ F14 (Sudah dihapus dan dipasang ulang, masalah tetap ada)
```

**Skenario 8: F15 + F4 → H10 (jalur berbasis literatur)**

| Iterasi | Aturan | Premis | Kesimpulan | Sumber |
| --- | --- | --- | --- | --- |
| 1 | R20 | F15 | K8 | S6 (Intel USB 3.0 RFI) |
| 2 | R26 | K8 DAN F4 | H10 | S6 |

### 5.3 Pengujian Mesin Inferensi

| Pengujian | Skenario | Hasil |
| --- | --- | --- |
| Semua jawaban "Tidak" | 20 fakta false | Inconclusive, 0 aturan — lulus |
| OR salah satu cukup | F7 + F5 atau F7 + F11 | H4 — lulus |
| AND belum lengkap | F7 saja | Tidak ada H4 — lulus |
| K tanpa H | F13 saja | K2 terbentuk, H2 belum — lulus |
| K + fakta melengkapi | F2 + F13 | H2 — lulus |
| Banyak diagnosis | F1, F4, F7, F11 | H1 (prioritas 1) lalu H4 (prioritas 5) — lulus |
| Dua aturan satu H | F1, F4, F14 | H1 didukung R8 dan R9 — lulus |
| Validasi jawaban hilang | Hanya F1 dijawab | `InputError`, 19 kode hilang — lulus |
| Validasi tipe salah | F1 = "ya" | `InputError`, F1 invalid — lulus |
| Rujukan sumber aturan | R1–R31 | Setiap `source` valid — lulus |
| Kelengkapan literatur | S5–S10 | Lengkap dan terverifikasi — lulus |
| Kinerja | Seluruh fakta "Ya" | < 1 detik (aktual < 1 ms) — lulus |

### 5.4 Pengujian API dan Berkas Statis

| Pengujian | Hasil |
| --- | --- |
| `GET /api/knowledge` | 200, 20 fakta, 31 aturan, 9 sumber, spesifikasi `met` |
| `GET /api/health` | 200, `status: ok`, `rules: 31` |
| `GET /` | 200, HTML "BluetoothCare" |
| Aset statis | `/styles.css`, `/app.js`, `/favicon.svg` → 200 |
| `POST /api/diagnose` valid | 200, H1, R1/R9, 20 jawaban |
| `POST /api/diagnose` F7 | 200, inconclusive |
| Jawaban hilang | 400, `missing` menyebut kode |
| JSON rusak / body kosong | 400 |
| Endpoint tidak dikenal | 404 JSON |
| `OPTIONS /api/diagnose` | 204, header `Allow` |
| Log konsultasi | Dibuat; hanya gejala/hasil/aturan; tanpa data pribadi |

### 5.5 Pengujian Antarmuka (Browser)

- [x] Beranda tampil di desktop dan ponsel; tombol Mulai membuka form.
- [x] Form menampilkan 20 pertanyaan dalam 3 kelompok; progres berubah.
- [x] Submit kosong ditolak dan menandai pertanyaan.
- [x] Skenario F1 + F14 menghasilkan H1, saran, dan jejak 2 iterasi.
- [x] Fasilitas penjelasan menampilkan R1 → K1 dan R9 → H1.
- [x] Skenario F7 menampilkan "Belum dapat disimpulkan" + saran baterai.
- [x] Konsultasi ulang mengosongkan form dan hasil.
- [x] Tab basis pengetahuan menampilkan 20 fakta, 31 aturan, 19 kesimpulan, 13 skenario, 9 sumber.
- [x] Tabel aturan terkelompok menurut kesimpulan.
- [x] Unduh `.txt` dan Cetak/PDF berfungsi.
- [x] Menu seluler buka/tutup dan navigasi hash berfungsi.
- [x] Muat ulang di `#hasil` mempertahankan hasil.

**Hasil:** 21 pemeriksaan browser lulus, tanpa error runtime JavaScript. Pengujian DOM (jsdom) terpisah juga lulus.

### 5.6 Pemenuhan Spesifikasi Minimum

| Aspek | Target | Capaian | Status |
| --- | --- | --- | --- |
| Fakta | 10+ | 20 | Terpenuhi |
| Diagnosis akhir | 5+ | 10 | Terpenuhi |
| Kesimpulan antara | 3+ | 9 | Terpenuhi |
| Aturan produksi | 15+ | 31 | Terpenuhi |
| Skenario uji | 5+ | 13 | Terpenuhi |
| Operator AND/OR | Wajib | Banyak aturan | Terpenuhi |

### 5.7 Evaluasi dan Pembahasan

**Kelebihan:**

1. Basis pengetahuan terpisah dan tervalidasi otomatis, sehingga mudah diperluas.
2. Setiap aturan menunjuk sumber, sehingga keputusan dapat dipertanggungjawabkan.
3. Fasilitas penjelasan menunjukkan alasan dan urutan iterasi, bukan sekadar hasil.
4. Satu kesimpulan dapat didukung beberapa aturan, sehingga cakupan kombinasi gejala lebih luas.
5. Kesimpulan duplikat ditangani sebagai himpunan, sehingga tidak terjadi pengulangan yang salah.

**Keterbatasan:**

1. Sistem tidak belajar dari pengguna (belum ada basis pengetahuan dinamis).
2. Diagnosis bergantung pada ketepatan jawaban pengguna.
3. Cakupan terbatas pada Windows 10/11 dan gangguan konektivitas Bluetooth.
4. Sumber S2 (manual perangkat) belum diisi identitas lengkap.
5. Tidak ada wawancara pakar; validasi aturan bersandar pada sumber literatur/standar dan pemeriksaan konsistensi internal.
6. Belum ada autentikasi untuk versi online.

**Rencana pengembangan:**

1. Menambah bobot keyakinan (certainty factor) pada tiap aturan.
2. Menambah basis kasus (case-based reasoning) untuk pengalaman perbaikan nyata.
3. Menambah dukungan sistem operasi lain.
4. Menyediakan antarmuka pengelolaan basis pengetahuan.

---

## 8. Daftar Pustaka

1. Microsoft Support. (2026). *Fix Bluetooth problems in Windows*. Diakses 2 November 2026 dari https://support.microsoft.com/en-us/windows/hardware/bluetooth/fix-bluetooth-problems-in-windows
2. Bluetooth SIG. (2026). *Bluetooth Core Specification — operasi pita 2,4 GHz*. Diakses 2 November 2026 dari https://www.bluetooth.com/specifications/specs/
3. Golmie, N., Van Dyck, R. E., & Soltanian, A. (2003). Interference Evaluation of Bluetooth and IEEE 802.11b Systems. *Wireless Networks*, Springer. https://link.springer.com/article/10.1023/A:1022821110023
4. Intel Corporation / USB-IF. (2012). *USB 3.0 Radio Frequency Interference Impact on 2.4 GHz Wireless Devices* (white paper 327216-001). https://www.usb.org/sites/default/files/327216.pdf
5. National Institute of Standards and Technology. (2017). *Guide to Bluetooth Security* (NIST SP 800-121 Rev. 2). https://csrc.nist.gov/pubs/sp/800/121/r2/upd1/final
6. Bluetooth SIG. (2026). *LE Audio*. Diakses 3 November 2026 dari https://www.bluetooth.com/learn-about-bluetooth/recent-enhancements/le-audio/
7. Cordeiro, C. M., Abhyankar, S., Toshiwal, R., & Agrawal, D. P. (2003). Interference Modeling and Performance of Bluetooth MAC Protocol. *IEEE Transactions on Wireless Communications*. https://ieeexplore.ieee.org/document/1244801
8. Microsoft Learn. (2021). *Bluetooth power management for modern standby platforms*. Diakses 3 November 2026 dari https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/bluetooth-power-management-for-modern-standby-platforms
9. [ISI: manual perangkat S2 — merek/model]

---

## 9. Lampiran

### Lampiran A — Dokumentasi Akuisisi Pengetahuan

**A.1 Pemetaan fakta ke sumber**

| Fakta | Sumber utama |
| --- | --- |
| F1, F10, F12 | S1 (Microsoft Support), S10 |
| F2, F3, F4, F7, F9, F11, F13, F14 | S2 (manual perangkat), S7 (NIST) |
| F5, F6 | S4 (Bluetooth SIG) |
| F8 | S1 |
| F15 | S6 (Intel USB 3.0) |
| F16 | S5 (Golmie, Springer) |
| F17 | S9 (Cordeiro, IEEE) |
| F18 | S8 (LE Audio) |
| F19 | S10 (Microsoft power management) |
| F20 | S1 |

**A.2 Pemetaan aturan ke sumber**

Seluruh 31 aturan mencantumkan `source`. Contoh jalur berbasis literatur: R20/R26 → S6, R22/R28 → S5, R23/R29 → S9, R24/R30 → S8, R25/R31 → S10, R16 → S7.

**A.3 Catatan manual perangkat (S2)** — [ISI: merek/model]

| Aspek | Keterangan |
| --- | --- |
| Mode pairing | Tekan/tahan tombol 3–5 detik sampai lampu berkedip cepat (F13) |
| Arti indikator | Kedip cepat = siap pairing; menyala tetap = tersambung |
| Baterai | [ISI: ambang baterai perangkat] |

### Lampiran B — Source Code Penting

**B.1 Contoh aturan JSON (termasuk OR bersarang dan rujukan sumber)**

```json
{ "id": "R3",  "if": { "or": ["F13", "F9"] },                 "then": "K2",  "source": "S2" }
{ "id": "R14", "if": { "and": ["F7", { "or": ["F5", "F11"] }] }, "then": "H4", "source": "S2" }
{ "id": "R20", "if": "F15",                                   "then": "K8",  "source": "S6" }
{ "id": "R26", "if": { "and": ["K8", "F4"] },                 "then": "H10", "source": "S6" }
{ "id": "R31", "if": "K9",                                    "then": "H7",  "source": "S10" }
```

**B.2 Evaluasi premis bersarang**

```python
def _eval_node(node, working_memory, used):
    if isinstance(node, str):
        if node in working_memory:
            used.append(node)
            return True
        return False
    if not isinstance(node, dict) or len(node) != 1:
        raise KnowledgeBaseError(f"Bentuk premis tidak dikenal: {node!r}")
    operator, value = next(iter(node.items()))
    if operator == "and":
        return all(_eval_node(child, working_memory, used) for child in value)
    if operator == "or":
        return any(_eval_node(child, working_memory, used) for child in value)
    if operator == "not":
        return not _eval_node(value, working_memory, [])
    raise KnowledgeBaseError(f"Operator premis tidak dikenal: {operator!r}")
```

**B.3 Siklus forward chaining**

```python
while True:
    snapshot = frozenset(working_memory)
    conflict_set = []
    for rule in kb.ordered_rules:
        if rule["id"] in fired:
            continue
        satisfied, used = eval_premise(rule["if"], snapshot)
        if satisfied:
            conflict_set.append((rule, used))
    if not conflict_set:
        break
    iteration += 1
    for rule, used in conflict_set:
        conclusion_id = rule["then"]
        is_new = conclusion_id not in working_memory
        working_memory.add(conclusion_id)
        fired.add(rule["id"])
        trace.append({ "iteration": iteration, "rule_id": rule["id"],
                       "conclusion": conclusion_id, "is_new": is_new, ... })
```

**B.4 Validasi basis pengetahuan (ringkas)**

```python
produced = {rule["then"] for rule in self.raw_rules}
for cid in self.conclusions:
    if cid not in produced:
        errors.append(f"Kesimpulan {cid} tidak pernah dihasilkan oleh aturan mana pun.")
```

### Lampiran C — Tangkapan Layar

[SISIPKAN GAMBAR]

1. **Br-01 Beranda** — judul, statistik basis pengetahuan (20/31/10), tombol Mulai.
2. **Br-02 Konsultasi** — form 20 pertanyaan, 3 kelompok, progres.
3. **Br-03 Hasil H1** — kartu diagnosis prioritas 1, langkah perbaikan, jejak 2 iterasi.
4. **Br-04 Pohon alasan** — R9 → K1 → R1 → F1 dan F14.
5. **Br-05 Belum dapat disimpulkan** — skenario F7 dan saran baterai.
6. **Br-06 Basis pengetahuan (Fakta)** — 20 fakta.
7. **Br-07 Basis pengetahuan (Aturan)** — 31 aturan terkelompok per kesimpulan.
8. **Br-08 Basis pengetahuan (Sumber)** — 9 sumber, status verifikasi.
9. **Br-09 Halaman Tentang** — metode, batasan, pernyataan AI.
10. **Br-10 Tampilan ponsel** — beranda dan konsultasi.

> Cara mendapatkannya: jalankan `python app.py`, buka `http://127.0.0.1:8000`, lalu gunakan fitur Cetak/PDF atau tangkapan layar. Skrip otomatis pengambilan tangkapan layar tersedia pada berkas pengujian browser.

---

*Dokumen ini adalah draf. Lengkapi placeholder `[ISI: ...]` dan sisipkan tangkapan layar sebelum dikumpulkan. Cantumkan pernyataan penggunaan AI pada laporan akhir sesuai ketentuan mata kuliah.*
