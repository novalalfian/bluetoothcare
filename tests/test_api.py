"""Pengujian integrasi HTTP: API, penyajian berkas statis, dan validasi."""

from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_server  # noqa: E402
from inference_engine import KnowledgeBase  # noqa: E402


class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.kb = KnowledgeBase.load(ROOT / "knowledge_base.json")
        cls.server = create_server("127.0.0.1", 0, kb=cls.kb, log_file=None)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(
        self,
        method: str,
        path: str,
        body: bytes | str | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        request_headers = {"Connection": "close"}
        if headers:
            request_headers.update(headers)
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        payload = response.read()
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        status = response.status
        connection.close()
        return status, response_headers, payload

    def answers(self, yes: list[str]) -> dict[str, bool]:
        return {fid: fid in yes for fid in self.kb.fact_order}

    # -- GET ---------------------------------------------------------------

    def test_knowledge_endpoint(self) -> None:
        status, headers, payload = self.request("GET", "/api/knowledge")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers["content-type"])
        self.assertIn("content-security-policy", headers)
        data = json.loads(payload.decode("utf-8"))
        self.assertEqual(len(data["facts"]), 14)
        self.assertEqual(len(data["rules"]), 19)
        self.assertEqual(data["stats"]["final"], 7)
        self.assertTrue(all(item["met"] for item in data["compliance"]))

    def test_health_endpoint(self) -> None:
        status, _, payload = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        data = json.loads(payload)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["rules"], 19)

    def test_index_page(self) -> None:
        status, headers, payload = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["content-type"])
        self.assertIn("BluetoothCare", payload.decode("utf-8"))

    def test_static_assets(self) -> None:
        for path, content_type in [
            ("/styles.css", "text/css"),
            ("/app.js", "javascript"),
            ("/favicon.svg", "svg"),
        ]:
            with self.subTest(path=path):
                status, headers, _ = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(content_type, headers["content-type"])

    def test_unknown_api_get(self) -> None:
        status, headers, payload = self.request("GET", "/api/tidak-ada")
        self.assertEqual(status, 404)
        self.assertIn("application/json", headers["content-type"])
        self.assertIn("error", json.loads(payload))

    # -- POST --------------------------------------------------------------

    def test_diagnose_valid(self) -> None:
        body = json.dumps({"answers": self.answers(["F1", "F14"])}).encode("utf-8")
        status, _, payload = self.request(
            "POST", "/api/diagnose", body, {"Content-Type": "application/json"}
        )
        self.assertEqual(status, 200)
        data = json.loads(payload)
        self.assertEqual(data["status"], "diagnosed")
        self.assertEqual([item["id"] for item in data["diagnoses"]], ["H1"])
        self.assertEqual([item["rule_id"] for item in data["trace"]], ["R1", "R9"])
        self.assertEqual(data["stats"]["answered"], 14)

    def test_diagnose_inconclusive(self) -> None:
        body = json.dumps({"answers": self.answers(["F7"])}).encode("utf-8")
        status, _, payload = self.request("POST", "/api/diagnose", body)
        self.assertEqual(status, 200)
        data = json.loads(payload)
        self.assertEqual(data["status"], "inconclusive")
        self.assertEqual(data["diagnoses"], [])

    def test_diagnose_missing_answers(self) -> None:
        answers = self.answers([])
        del answers["F5"]
        body = json.dumps({"answers": answers}).encode("utf-8")
        status, _, payload = self.request("POST", "/api/diagnose", body)
        self.assertEqual(status, 400)
        data = json.loads(payload)
        self.assertIn("F5", data["missing"])
        self.assertIn("wajib", data["error"].lower())

    def test_diagnose_invalid_json(self) -> None:
        status, _, payload = self.request(
            "POST", "/api/diagnose", b"{bukan json", {"Content-Type": "application/json"}
        )
        self.assertEqual(status, 400)
        self.assertIn("JSON", json.loads(payload)["error"])

    def test_diagnose_empty_body(self) -> None:
        status, _, payload = self.request("POST", "/api/diagnose", b"")
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(payload))

    def test_unknown_post_route(self) -> None:
        status, _, _ = self.request("POST", "/api/lain", b"{}")
        self.assertEqual(status, 404)

    def test_options(self) -> None:
        status, headers, _ = self.request("OPTIONS", "/api/diagnose")
        self.assertEqual(status, 204)
        self.assertIn("POST", headers["allow"])

    def test_consultation_log_written_without_answers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_file = Path(directory) / "logs" / "konsultasi.jsonl"
            server = create_server("127.0.0.1", 0, kb=self.kb, log_file=log_file)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection(
                    "127.0.0.1", server.server_address[1], timeout=5
                )
                body = json.dumps({"answers": self.answers(["F8"])}).encode("utf-8")
                connection.request(
                    "POST",
                    "/api/diagnose",
                    body=body,
                    headers={"Content-Type": "application/json", "Connection": "close"},
                )
                response = connection.getresponse()
                response.read()
                self.assertEqual(response.status, 200)
                connection.close()
                self.assertTrue(log_file.exists())
                record = json.loads(log_file.read_text(encoding="utf-8").strip())
                self.assertEqual(record["diagnoses"], ["H5"])
                self.assertNotIn("answers", record)
                self.assertNotIn("name", record)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
