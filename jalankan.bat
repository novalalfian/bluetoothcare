@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   SISTEM PAKAR DIAGNOSIS BLUETOOTH PADA LAPTOP
echo ============================================================
echo   Menjalankan server lokal...
echo   Browser akan terbuka otomatis di http://127.0.0.1:8000
echo   Tekan Ctrl+C di jendela ini untuk menghentikan server.
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [GAGAL] Python tidak ditemukan di PATH.
  echo Instal Python 3.10 atau lebih baru dari https://www.python.org/downloads/
  echo Pastikan opsi "Add Python to PATH" dipilih saat instalasi.
  echo.
  pause
  exit /b 1
)

python app.py %*
set EXIT_CODE=%ERRORLEVEL%

echo.
if not "%EXIT_CODE%"=="0" (
  echo [INFO] Server berhenti dengan kode %EXIT_CODE%.
) else (
  echo [INFO] Server telah dihentikan.
)
pause
exit /b %EXIT_CODE%
