"""Mesin inferensi forward chaining untuk Sistem Pakar Diagnosis Bluetooth.

Modul ini sengaja dipisahkan dari ``app.py`` (pengendali HTTP) dan dari
``knowledge_base.json`` (basis pengetahuan) agar aturan dapat diubah tanpa
menyentuh kode inferensi.

Alur utama:
1. ``KnowledgeBase`` memuat dan memvalidasi fakta, aturan, serta kesimpulan.
2. ``validate_answers`` memastikan seluruh 14 fakta dijawab Ya/Tidak.
3. ``run_inference`` menjalankan siklus forward chaining sampai stabil:
   kumpulkan aturan yang aktif -> jalankan -> tambahkan fakta baru -> ulangi.
4. Setiap aturan yang berjalan dicatat pada ``trace`` (fasilitas penjelasan).
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Iterator

MAX_ITERATIONS = 100  # pengaman agar tidak terjadi perulangan tanpa akhir


class KnowledgeBaseError(ValueError):
    """Basis pengetahuan tidak valid atau tidak konsisten."""


class InputError(ValueError):
    """Jawaban pengguna tidak lengkap atau tidak valid."""

    def __init__(
        self,
        message: str,
        *,
        missing: list[str] | None = None,
        invalid: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.missing = missing or []
        self.invalid = invalid or []


def id_sort_key(item_id: str) -> tuple[int, str]:
    """Urutkan kode seperti F1, F2, F10 secara numerik (bukan alfabetis)."""
    match = re.search(r"\d+", item_id)
    return (int(match.group()) if match else 0, item_id)


# ---------------------------------------------------------------------------
# Evaluasi premis (mendukung AND, OR, dan NOT bersarang)
# ---------------------------------------------------------------------------


def _eval_node(node: Any, working_memory: set[str] | frozenset[str], used: list[str]) -> bool:
    if isinstance(node, str):
        if node in working_memory:
            used.append(node)
            return True
        return False

    if not isinstance(node, dict) or len(node) != 1:
        raise KnowledgeBaseError(f"Bentuk premis tidak dikenal: {node!r}")

    operator, value = next(iter(node.items()))

    if operator == "and":
        results = [_eval_node(child, working_memory, used) for child in value]
        return all(results)

    if operator == "or":
        results = [_eval_node(child, working_memory, used) for child in value]
        return any(results)

    if operator == "not":
        ignored: list[str] = []
        return not _eval_node(value, working_memory, ignored)

    raise KnowledgeBaseError(f"Operator premis tidak dikenal: {operator!r}")


def eval_premise(
    node: Any, working_memory: set[str] | frozenset[str]
) -> tuple[bool, list[str]]:
    """Nilai premis terhadap memori kerja.

    Mengembalikan ``(terpenuhi, fakta_yang_dipakai)``. Untuk OR, seluruh cabang
    yang bernilai benar ikut dicatat agar penjelasan tetap informatif.
    """
    used: list[str] = []
    return _eval_node(node, working_memory, used), used


def premise_label(node: Any) -> str:
    """Bentuk ringkas premis, misalnya ``F7 DAN (F5 ATAU F11)``."""
    if isinstance(node, str):
        return node

    if not isinstance(node, dict) or len(node) != 1:
        raise KnowledgeBaseError(f"Bentuk premis tidak dikenal: {node!r}")

    operator, value = next(iter(node.items()))
    if operator == "not":
        label = premise_label(value)
        return f"TIDAK ({label})" if isinstance(value, dict) else f"TIDAK {label}"
    if operator not in {"and", "or"}:
        raise KnowledgeBaseError(f"Operator premis tidak dikenal: {operator!r}")

    joiner = " DAN " if operator == "and" else " ATAU "
    parts = []
    for child in value:
        label = premise_label(child)
        parts.append(f"({label})" if isinstance(child, dict) else label)
    return joiner.join(parts)


def premise_sentence(node: Any, names: dict[str, str]) -> str:
    """Kalimat JIKA dengan teks fakta, misalnya ``F7 (Baterai ...)``."""
    if isinstance(node, str):
        return f"{node} ({names.get(node, node)})"

    if not isinstance(node, dict) or len(node) != 1:
        raise KnowledgeBaseError(f"Bentuk premis tidak dikenal: {node!r}")

    operator, value = next(iter(node.items()))
    if operator == "not":
        inner = premise_sentence(value, names)
        return f"TIDAK ({inner})"
    if operator not in {"and", "or"}:
        raise KnowledgeBaseError(f"Operator premis tidak dikenal: {operator!r}")

    joiner = " DAN " if operator == "and" else " ATAU "
    parts = []
    for child in value:
        sentence = premise_sentence(child, names)
        parts.append(f"({sentence})" if isinstance(child, dict) else sentence)
    return joiner.join(parts)


def _iter_refs(node: Any) -> Iterator[str]:
    if isinstance(node, str):
        yield node
        return
    if not isinstance(node, dict) or len(node) != 1:
        raise KnowledgeBaseError(f"Bentuk premis tidak dikenal: {node!r}")
    operator, value = next(iter(node.items()))
    if operator in {"and", "or"}:
        for child in value:
            yield from _iter_refs(child)
    elif operator == "not":
        yield from _iter_refs(value)
    else:
        raise KnowledgeBaseError(f"Operator premis tidak dikenal: {operator!r}")


# ---------------------------------------------------------------------------
# Basis pengetahuan
# ---------------------------------------------------------------------------


class KnowledgeBase:
    """Representasi basis pengetahuan JSON yang sudah divalidasi."""

    def __init__(self, data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise KnowledgeBaseError("Isi basis pengetahuan harus berupa objek JSON.")

        self.data = data
        self.meta: dict[str, Any] = data.get("meta", {})
        self.groups: list[dict[str, Any]] = self.meta.get("groups", [])
        self.raw_facts: list[dict[str, Any]] = data.get("facts", [])
        self.raw_conclusions: list[dict[str, Any]] = data.get("conclusions", [])
        self.raw_rules: list[dict[str, Any]] = data.get("rules", [])
        self.sources: list[dict[str, Any]] = data.get("sources", [])

        self._validate_structure()

        self.facts = {fact["id"]: fact for fact in self.raw_facts}
        self.conclusions = {item["id"]: item for item in self.raw_conclusions}
        self.rules = {rule["id"]: rule for rule in self.raw_rules}

        self.fact_order = sorted(self.facts, key=id_sort_key)
        self.conclusion_order = sorted(self.conclusions, key=id_sort_key)
        self.ordered_rules = sorted(self.raw_rules, key=lambda rule: id_sort_key(rule["id"]))
        self.names = {
            **{fid: fact["text"] for fid, fact in self.facts.items()},
            **{cid: item["text"] for cid, item in self.conclusions.items()},
        }
        self.final_conclusions = [
            cid
            for cid in self.conclusion_order
            if self.conclusions[cid]["type"] == "final"
        ]

        self._validate_references()

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        file_path = Path(path)
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError as exc:
            raise KnowledgeBaseError(f"Berkas basis pengetahuan tidak ditemukan: {file_path}") from exc
        except json.JSONDecodeError as exc:
            raise KnowledgeBaseError(
                f"JSON pada {file_path.name} tidak valid (baris {exc.lineno}): {exc.msg}"
            ) from exc
        return cls(data)

    def _validate_structure(self) -> None:
        errors: list[str] = []

        if not isinstance(self.meta, dict):
            errors.append("Bagian 'meta' harus berupa objek.")

        if not isinstance(self.raw_facts, list) or not self.raw_facts:
            errors.append("Bagian 'facts' harus berupa daftar dan tidak boleh kosong.")
            self.raw_facts = []
        if not isinstance(self.raw_conclusions, list) or not self.raw_conclusions:
            errors.append("Bagian 'conclusions' harus berupa daftar dan tidak boleh kosong.")
            self.raw_conclusions = []
        if not isinstance(self.raw_rules, list) or not self.raw_rules:
            errors.append("Bagian 'rules' harus berupa daftar dan tidak boleh kosong.")
            self.raw_rules = []
        if not isinstance(self.sources, list):
            errors.append("Bagian 'sources' harus berupa daftar.")
            self.sources = []

        group_ids = {
            group.get("id") for group in self.groups if isinstance(group, dict)
        }

        seen_facts: set[str] = set()
        for index, fact in enumerate(self.raw_facts, start=1):
            if not isinstance(fact, dict):
                errors.append(f"Fakta ke-{index} harus berupa objek.")
                continue
            fid = fact.get("id")
            if not isinstance(fid, str) or not fid.strip():
                errors.append(f"Fakta ke-{index} tidak memiliki 'id' yang valid.")
                continue
            if fid in seen_facts:
                errors.append(f"Kode fakta ganda: {fid}.")
            seen_facts.add(fid)
            if not isinstance(fact.get("text"), str) or not fact["text"].strip():
                errors.append(f"{fid} tidak memiliki 'text'.")
            if fact.get("group") not in group_ids:
                errors.append(f"{fid} memiliki grup tidak dikenal: {fact.get('group')!r}.")
            if "hint" in fact and not isinstance(fact["hint"], str):
                errors.append(f"'hint' pada {fid} harus berupa teks.")

        seen_conclusions: set[str] = set()
        for index, item in enumerate(self.raw_conclusions, start=1):
            if not isinstance(item, dict):
                errors.append(f"Kesimpulan ke-{index} harus berupa objek.")
                continue
            cid = item.get("id")
            if not isinstance(cid, str) or not cid.strip():
                errors.append(f"Kesimpulan ke-{index} tidak memiliki 'id' yang valid.")
                continue
            if cid in seen_conclusions:
                errors.append(f"Kode kesimpulan ganda: {cid}.")
            seen_conclusions.add(cid)
            if item.get("type") not in {"intermediate", "final"}:
                errors.append(f"{cid} harus memiliki type 'intermediate' atau 'final'.")
            if not isinstance(item.get("text"), str) or not item["text"].strip():
                errors.append(f"{cid} tidak memiliki 'text'.")
            if item.get("type") == "final":
                priority = item.get("priority")
                if not isinstance(priority, int) or isinstance(priority, bool):
                    errors.append(f"{cid} adalah diagnosis akhir dan wajib punya 'priority' bilangan bulat.")
                if not isinstance(item.get("advice", []), list):
                    errors.append(f"'advice' pada {cid} harus berupa daftar.")
            if "priority" in item and item["priority"] is not None and not isinstance(item["priority"], int):
                errors.append(f"'priority' pada {cid} harus bilangan bulat atau null.")

        seen_rules: set[str] = set()
        for index, rule in enumerate(self.raw_rules, start=1):
            if not isinstance(rule, dict):
                errors.append(f"Aturan ke-{index} harus berupa objek.")
                continue
            rid = rule.get("id")
            if not isinstance(rid, str) or not rid.strip():
                errors.append(f"Aturan ke-{index} tidak memiliki 'id' yang valid.")
                continue
            if rid in seen_rules:
                errors.append(f"Kode aturan ganda: {rid}.")
            seen_rules.add(rid)
            if "if" not in rule:
                errors.append(f"{rid} tidak memiliki premis 'if'.")
            else:
                try:
                    for _ in _iter_refs(rule["if"]):
                        pass
                except KnowledgeBaseError as exc:
                    errors.append(f"Premis {rid} tidak valid: {exc}")
            if not isinstance(rule.get("then"), str) or not rule["then"].strip():
                errors.append(f"{rid} tidak memiliki kesimpulan 'then'.")

        if errors:
            raise KnowledgeBaseError(
                "Basis pengetahuan tidak valid:\n- " + "\n- ".join(errors)
            )

    def _validate_references(self) -> None:
        errors: list[str] = []
        known_ids = set(self.facts) | set(self.conclusions)

        for rule in self.raw_rules:
            rid = rule["id"]
            if rule["then"] not in self.conclusions:
                errors.append(
                    f"{rid} menyimpulkan '{rule['then']}' yang bukan kesimpulan terdaftar."
                )
            for ref in _iter_refs(rule["if"]):
                if ref not in known_ids:
                    errors.append(f"{rid} memakai '{ref}' yang tidak ada pada fakta/kesimpulan.")

        produced = {rule["then"] for rule in self.raw_rules}
        for cid in self.conclusions:
            if cid not in produced:
                errors.append(f"Kesimpulan {cid} tidak pernah dihasilkan oleh aturan mana pun.")

        if not self.final_conclusions:
            errors.append("Tidak ada diagnosis akhir (type 'final') pada basis pengetahuan.")

        if errors:
            raise KnowledgeBaseError(
                "Referensi basis pengetahuan bermasalah:\n- " + "\n- ".join(errors)
            )

    def compliance(self) -> list[dict[str, Any]]:
        """Ringkasan pemenuhan spesifikasi minimum soal UTS."""
        intermediate_count = sum(
            1 for item in self.conclusions.values() if item["type"] == "intermediate"
        )
        final_count = len(self.final_conclusions)
        scenarios = self.meta.get("test_scenarios", [])
        supports_and_or = any(
            isinstance(rule["if"], dict)
            and any(key in rule["if"] for key in ("and", "or"))
            for rule in self.raw_rules
        )

        def check(label: str, minimum: int, actual: int, unit: str = "") -> dict[str, Any]:
            return {
                "label": label,
                "minimum": minimum,
                "actual": actual,
                "unit": unit,
                "met": actual >= minimum,
            }

        return [
            check("Fakta", 10, len(self.facts)),
            check("Kesimpulan akhir", 5, final_count),
            check("Kesimpulan antara", 3, intermediate_count),
            check("Aturan produksi", 15, len(self.rules)),
            check("Skenario uji", 5, len(scenarios)),
            {
                "label": "Operator AND/OR",
                "minimum": 1,
                "actual": 1 if supports_and_or else 0,
                "unit": "",
                "met": supports_and_or,
            },
        ]

    def public_data(self) -> dict[str, Any]:
        """Data basis pengetahuan untuk halaman transparansi (FR-11)."""
        return {
            "meta": self.meta,
            "facts": [self.facts[fid] for fid in self.fact_order],
            "conclusions": [
                {
                    **self.conclusions[cid],
                    "advice_count": len(self.conclusions[cid].get("advice", [])),
                }
                for cid in self.conclusion_order
            ],
            "rules": [
                {
                    **rule,
                    "premise_label": premise_label(rule["if"]),
                    "premise_sentence": premise_sentence(rule["if"], self.names),
                }
                for rule in self.ordered_rules
            ],
            "sources": self.sources,
            "stats": {
                "facts": len(self.facts),
                "intermediate": sum(
                    1 for item in self.conclusions.values() if item["type"] == "intermediate"
                ),
                "final": len(self.final_conclusions),
                "rules": len(self.rules),
                "scenarios": len(self.meta.get("test_scenarios", [])),
                "sources": len(self.sources),
            },
            "compliance": self.compliance(),
        }


# ---------------------------------------------------------------------------
# Validasi masukan
# ---------------------------------------------------------------------------


def validate_answers(kb: KnowledgeBase, payload: Any) -> dict[str, bool]:
    """Pastikan semua fakta dijawab dengan boolean Ya/Tidak."""
    if not isinstance(payload, dict):
        raise InputError("Format permintaan tidak valid: badan permintaan harus berupa objek JSON.")

    answers = payload.get("answers")
    if not isinstance(answers, dict):
        raise InputError("Objek 'answers' tidak ditemukan pada permintaan.")

    missing = [fid for fid in kb.fact_order if fid not in answers]
    invalid = [
        str(fid)
        for fid, value in answers.items()
        if fid not in kb.facts or type(value) is not bool
    ]

    if missing or invalid:
        parts = ["Semua pertanyaan wajib dijawab Ya atau Tidak."]
        if missing:
            parts.append(f"Belum dijawab: {', '.join(missing)}.")
        if invalid:
            parts.append(f"Jawaban tidak valid: {', '.join(invalid)}.")
        raise InputError(" ".join(parts), missing=missing, invalid=invalid)

    return {fid: answers[fid] for fid in kb.fact_order}


# ---------------------------------------------------------------------------
# Inferensi
# ---------------------------------------------------------------------------


def _fact_payload(kb: KnowledgeBase, fid: str) -> dict[str, Any]:
    fact = kb.facts[fid]
    return {
        "id": fid,
        "text": fact["text"],
        "group": fact.get("group"),
        "hint": fact.get("hint", ""),
    }


def _conclusion_payload(kb: KnowledgeBase, cid: str) -> dict[str, Any]:
    item = kb.conclusions[cid]
    return {
        "id": cid,
        "type": item["type"],
        "text": item["text"],
        "summary": item.get("summary", ""),
        "priority": item.get("priority"),
    }


def _build_derivation(
    kb: KnowledgeBase,
    node_id: str,
    fired_by_conclusion: dict[str, list[dict[str, Any]]],
    path: frozenset[str],
) -> dict[str, Any]:
    """Bangun pohon alasan: H <- K + fakta <- aturan sebelumnya."""
    if node_id in kb.facts:
        return {"kind": "fact", **_fact_payload(kb, node_id)}

    item = kb.conclusions[node_id]
    causes = []
    for record in fired_by_conclusion.get(node_id, []):
        antecedents = []
        for antecedent in record["antecedents"]:
            if antecedent in path:
                antecedents.append(
                    {
                        "kind": "cycle",
                        "id": antecedent,
                        "text": "Rantai sudah ditampilkan sebelumnya.",
                    }
                )
            else:
                antecedents.append(
                    _build_derivation(
                        kb,
                        antecedent,
                        fired_by_conclusion,
                        path | {node_id},
                    )
                )
        causes.append(
            {
                "rule_id": record["rule_id"],
                "iteration": record["iteration"],
                "premise_label": record["premise_label"],
                "premise_sentence": record["premise_sentence"],
                "source": record["source"],
                "antecedents": antecedents,
            }
        )

    return {
        "kind": "conclusion",
        "id": node_id,
        "type": item["type"],
        "text": item["text"],
        "summary": item.get("summary", ""),
        "causes": causes,
    }


def run_inference(kb: KnowledgeBase, payload: Any) -> dict[str, Any]:
    """Jalankan forward chaining sampai tidak ada aturan baru yang aktif.

    Satu iterasi = satu siklus evaluasi terhadap snapshot memori kerja.
    Seluruh aturan yang aktif pada siklus tersebut dijalankan, lalu fakta baru
    dipakai pada siklus berikutnya. Aturan yang sudah berjalan tidak diulang.
    """
    started = perf_counter()
    answers = validate_answers(kb, payload)
    working_memory: set[str] = {fid for fid, value in answers.items() if value}

    fired: set[str] = set()
    trace: list[dict[str, Any]] = []
    iteration = 0

    while True:
        snapshot = frozenset(working_memory)
        conflict_set: list[tuple[dict[str, Any], list[str]]] = []

        for rule in kb.ordered_rules:
            if rule["id"] in fired:
                continue
            satisfied, used = eval_premise(rule["if"], snapshot)
            if satisfied:
                conflict_set.append((rule, used))

        if not conflict_set:
            break

        iteration += 1
        if iteration > MAX_ITERATIONS:
            raise KnowledgeBaseError(
                "Inferensi melebihi batas iterasi. Periksa kemungkinan siklus aturan."
            )

        for rule, used in conflict_set:
            conclusion_id = rule["then"]
            is_new = conclusion_id not in working_memory
            working_memory.add(conclusion_id)
            fired.add(rule["id"])

            trace.append(
                {
                    "iteration": iteration,
                    "rule_id": rule["id"],
                    "premise_label": premise_label(rule["if"]),
                    "premise_sentence": premise_sentence(rule["if"], kb.names),
                    "conclusion": conclusion_id,
                    "conclusion_text": kb.names[conclusion_id],
                    "conclusion_type": kb.conclusions[conclusion_id]["type"],
                    "is_new": is_new,
                    "antecedents": used,
                    "source": rule.get("source", ""),
                }
            )

    fired_by_conclusion: dict[str, list[dict[str, Any]]] = {}
    for record in trace:
        fired_by_conclusion.setdefault(record["conclusion"], []).append(record)

    input_facts = [_fact_payload(kb, fid) for fid in kb.fact_order if fid in working_memory]
    derived_conclusions = [
        _conclusion_payload(kb, cid)
        for cid in kb.conclusion_order
        if cid in working_memory
    ]

    final_ids = [
        cid
        for cid in working_memory
        if cid in kb.conclusions and kb.conclusions[cid]["type"] == "final"
    ]
    final_ids.sort(
        key=lambda cid: (
            kb.conclusions[cid].get("priority") or 99,
            id_sort_key(cid),
        )
    )

    diagnoses: list[dict[str, Any]] = []
    for cid in final_ids:
        item = kb.conclusions[cid]
        diagnoses.append(
            {
                "id": cid,
                "text": item["text"],
                "summary": item.get("summary", ""),
                "priority": item.get("priority"),
                "advice": item.get("advice", []),
                "derivation": _build_derivation(
                    kb, cid, fired_by_conclusion, frozenset()
                ),
                "rule_ids": [record["rule_id"] for record in fired_by_conclusion.get(cid, [])],
            }
        )

    detected = [_fact_payload(kb, fid) for fid in kb.fact_order if fid in working_memory]
    suggestions: list[str] = []
    seen_suggestions: set[str] = set()
    for fact in detected:
        advice = kb.facts[fact["id"]].get("solo_advice")
        if advice and advice not in seen_suggestions:
            suggestions.append(advice)
            seen_suggestions.add(advice)

    if not suggestions:
        suggestions.append(
            "Amati ulang gejala yang paling mengganggu, lalu jawab pertanyaan terkait dengan lebih pasti."
        )
    suggestions.append(
        "Coba sambungkan perangkat ke laptop atau ponsel lain untuk membandingkan apakah masalah ada pada perangkat."
    )
    suggestions.append(
        "Periksa manual perangkat untuk memastikan mode pairing, arti lampu indikator, dan kebutuhan baterai."
    )

    status = "diagnosed" if diagnoses else "inconclusive"
    if status == "diagnosed":
        inconclusive = None
    elif detected:
        inconclusive = {
            "message": (
                f"Belum dapat disimpulkan. Sistem mendeteksi {len(detected)} gejala, "
                "tetapi kombinasinya belum memenuhi aturan diagnosis mana pun."
            ),
            "detected_facts": detected,
            "suggestions": suggestions,
        }
    else:
        inconclusive = {
            "message": (
                "Belum dapat disimpulkan. Tidak ada gejala yang dijawab 'Ya', "
                "sehingga tidak ada aturan yang dapat dijalankan."
            ),
            "detected_facts": [],
            "suggestions": suggestions,
        }

    elapsed_ms = round((perf_counter() - started) * 1000, 3)
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    return {
        "status": status,
        "generated_at": generated_at,
        "answers": answers,
        "input_facts": input_facts,
        "detected_facts": detected,
        "diagnoses": diagnoses,
        "inconclusive": inconclusive,
        "trace": trace,
        "working_memory": {
            "facts": [fact["id"] for fact in input_facts],
            "conclusions": derived_conclusions,
            "intermediate": [
                item for item in derived_conclusions if item["type"] == "intermediate"
            ],
            "final": [item for item in derived_conclusions if item["type"] == "final"],
        },
        "stats": {
            "elapsed_ms": elapsed_ms,
            "iterations": iteration,
            "rules_fired": len(trace),
            "answered": len(answers),
            "yes": sum(1 for value in answers.values() if value),
            "facts_total": len(kb.facts),
            "rules_total": len(kb.rules),
            "diagnoses": len(diagnoses),
        },
    }
