"""Pengendali HTTP untuk Sistem Pakar Diagnosis Bluetooth.

Aplikasi ini hanya memakai pustaka standar Python sehingga dapat berjalan
luring (localhost) tanpa Flask, npm, atau koneksi internet.

Struktur:
    static/            antarmuka (HTML, CSS, JavaScript)
    knowledge_base.json  basis pengetahuan
    inference_engine.py  mesin forward chaining
    app.py             pengendali HTTP + penyajian berkas statis
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import traceback
import webbrowser
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from inference_engine import (
    InputError,
    KnowledgeBase,
    KnowledgeBaseError,
    run_inference,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
KNOWLEDGE_PATH = BASE_DIR / "knowledge_base.json"
DEFAULT_LOG = BASE_DIR / "logs" / "konsultasi.jsonl"
MAX_BODY_BYTES = 64 * 1024
CSP = (
    "default-src 'self'; "
    "img-src 'self' data:; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self'; "
    "connect-src 'self'; "
    "base-uri 'none'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


class AppHandler(SimpleHTTPRequestHandler):
    """Handler API + berkas statis. Parameter kb/log diisi oleh factory."""

    server_version = "SistemPakarBluetooth/2.0"
    protocol_version = "HTTP/1.1"

    def __init__(
        self,
        *args: Any,
        kb: KnowledgeBase,
        log_file: Path | None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> None:
        self.kb = kb
        self.log_file = log_file
        self.verbose = verbose
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    # -- Utilitas respons ---------------------------------------------------

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CSP)
        super().end_headers()

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=None).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _api_not_found(self) -> None:
        self._send_json(
            {"error": "Endpoint API tidak ditemukan."}, HTTPStatus.NOT_FOUND
        )

    # -- GET ----------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 (nama metode bawaan http.server)
        path = urlparse(self.path).path

        if path == "/api/knowledge":
            self._send_json(self.kb.public_data())
            return
        if path == "/api/health":
            self._send_json(
                {
                    "status": "ok",
                    "facts": len(self.kb.facts),
                    "rules": len(self.kb.rules),
                    "conclusions": len(self.kb.conclusions),
                }
            )
            return
        if path.startswith("/api/"):
            self._api_not_found()
            return

        # Dukungan tautan langsung (hash routing tetap dipakai di sisi klien).
        if path in {"/", "/index.html", "/konsultasi", "/hasil", "/pengetahuan", "/tentang"}:
            self.path = "/index.html"

        super().do_GET()

    # -- POST ---------------------------------------------------------------

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/diagnose":
            self._api_not_found()
            return

        try:
            raw_length = self.headers.get("Content-Length", "0")
            length = int(raw_length)
        except ValueError:
            self._send_json(
                {"error": "Header Content-Length tidak valid."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        if length <= 0:
            self._send_json(
                {"error": "Badan permintaan kosong. Kirim objek 'answers'."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        if length > MAX_BODY_BYTES:
            self._send_json(
                {"error": "Badan permintaan terlalu besar."},
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            return

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                {"error": "Badan permintaan bukan JSON yang valid."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            result = run_inference(self.kb, payload)
        except InputError as exc:
            self._send_json(
                {
                    "error": exc.message,
                    "missing": exc.missing,
                    "invalid": exc.invalid,
                },
                HTTPStatus.BAD_REQUEST,
            )
            return
        except KnowledgeBaseError as exc:
            self._send_json(
                {"error": f"Basis pengetahuan bermasalah: {exc}"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return
        except Exception:  # pragma: no cover - pengaman agar server tetap hidup
            traceback.print_exc()
            self._send_json(
                {"error": "Terjadi kesalahan tak terduga saat menjalankan inferensi."},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self._write_log(result)
        self._send_json(result, HTTPStatus.OK)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    # -- Log konsultasi (FR-13, tanpa data pribadi) -------------------------

    def _write_log(self, result: dict[str, Any]) -> None:
        if self.log_file is None:
            return
        record = {
            "timestamp": result.get("generated_at") or datetime.now().isoformat(timespec="seconds"),
            "status": result["status"],
            "yes_facts": result["working_memory"]["facts"],
            "diagnoses": [item["id"] for item in result["diagnoses"]],
            "rules_fired": [item["rule_id"] for item in result["trace"]],
            "iterations": result["stats"]["iterations"],
            "elapsed_ms": result["stats"]["elapsed_ms"],
        }
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:  # log tidak boleh menggagalkan konsultasi
            print(f"[peringatan] Gagal menulis log konsultasi: {exc}", file=sys.stderr)

    # -- Konsol -------------------------------------------------------------

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        status = str(args[1]) if len(args) > 1 else ""
        if self.verbose or status.startswith(("4", "5")):
            super().log_message(format, *args)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    kb: KnowledgeBase | None = None,
    log_file: Path | None = DEFAULT_LOG,
    verbose: bool = False,
) -> ThreadingHTTPServer:
    """Buat server HTTP. ``port=0`` memilih port acak (dipakai pengujian)."""
    knowledge = kb or KnowledgeBase.load(KNOWLEDGE_PATH)

    def handler_factory(*args: Any, **kwargs: Any) -> AppHandler:
        return AppHandler(
            *args,
            kb=knowledge,
            log_file=log_file,
            verbose=verbose,
            **kwargs,
        )

    server = ThreadingHTTPServer((host, port), handler_factory)
    server.daemon_threads = True
    server.verbose = verbose  # type: ignore[attr-defined]
    return server


def _open_browser(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    parser = argparse.ArgumentParser(
        description="Sistem Pakar Diagnosis Gangguan Konektivitas Bluetooth pada Laptop"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Alamat bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port server (default 8000)")
    parser.add_argument(
        "--no-browser", action="store_true", help="Jangan membuka browser otomatis"
    )
    parser.add_argument(
        "--no-log", action="store_true", help="Nonaktifkan log konsultasi lokal"
    )
    parser.add_argument("--verbose", action="store_true", help="Tampilkan log setiap request")
    args = parser.parse_args()

    try:
        kb = KnowledgeBase.load(KNOWLEDGE_PATH)
    except KnowledgeBaseError as exc:
        print("\n[GAGAL] Basis pengetahuan tidak dapat dimuat.\n", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    log_file = None if args.no_log else DEFAULT_LOG
    server: ThreadingHTTPServer | None = None
    last_error: OSError | None = None

    for candidate in range(args.port, args.port + 20):
        try:
            server = create_server(
                args.host,
                candidate,
                kb=kb,
                log_file=log_file,
                verbose=args.verbose,
            )
            break
        except OSError as exc:
            last_error = exc
            continue

    if server is None:
        print(
            f"\n[GAGAL] Tidak dapat membuka port {args.port}-{args.port + 19}: {last_error}",
            file=sys.stderr,
        )
        return 1

    actual_port = server.server_address[1]
    url = f"http://{args.host}:{actual_port}"
    intermediate = sum(
        1 for item in kb.conclusions.values() if item["type"] == "intermediate"
    )
    final = len(kb.final_conclusions)

    print()
    print("=" * 64)
    print("  SISTEM PAKAR DIAGNOSIS BLUETOOTH PADA LAPTOP")
    print("  Forward Chaining · Windows 10/11")
    print("=" * 64)
    print(f"  Basis pengetahuan : {len(kb.facts)} fakta, {len(kb.rules)} aturan")
    print(f"                      {intermediate} kesimpulan antara, {final} diagnosis")
    print(f"  Server berjalan   : {url}")
    print(f"  Log konsultasi    : {'nonaktif' if log_file is None else log_file}")
    print("  Hentikan          : Ctrl+C")
    print("=" * 64)
    print()

    if not args.no_browser:
        threading.Timer(0.8, _open_browser, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
