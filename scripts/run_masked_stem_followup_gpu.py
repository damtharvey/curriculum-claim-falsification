#!/usr/bin/env python3
"""Run second-family and with-stem scoring jobs; write a status partial after each job."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUT_DIR = ROOT / "exports" / "addendum-gpu"
STATUS_PATH = OUT_DIR / "masked-stem-followup-status.json"
PYTHON = ROOT / ".venv" / "bin" / "python"
SCORER = SCRIPTS / "score_choices_only_local_lm.py"

MISTRAL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
MISTRAL_REV = "c170c708c41dac9275d15a8fff4eca08d52bab71"
QWEN7_ID = "Qwen/Qwen2.5-7B-Instruct"
QWEN7_REV = "a09a35458c702b33eeacc393d103063234e8bc28"
QWEN14_ID = "Qwen/Qwen2.5-14B-Instruct"
QWEN14_REV = "cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"


def dump_status(payload: dict[str, object]) -> None:
    STATUS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_job(name: str, argv: list[str], status: dict[str, object]) -> int:
    jobs = status.setdefault("jobs", {})
    if not isinstance(jobs, dict):
        raise RuntimeError("status jobs must be a dict")
    started = time.time()
    jobs[name] = {
        "status": "running",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "argv": argv,
    }
    dump_status(status)
    print(f"=== starting {name} ===", flush=True)
    completed = subprocess.run(argv, cwd=str(ROOT))
    elapsed = time.time() - started
    jobs[name] = {
        "status": "complete" if completed.returncode == 0 else "failed",
        "returnCode": completed.returncode,
        "wallTimeSeconds": elapsed,
        "finishedAt": datetime.now(timezone.utc).isoformat(),
        "argv": argv,
    }
    dump_status(status)
    print(f"=== finished {name} rc={completed.returncode} wall={elapsed:.1f}s ===", flush=True)
    return int(completed.returncode)


def main() -> None:
    if not PYTHON.exists():
        raise RuntimeError(f"expected venv python at {PYTHON}")
    started = time.time()
    status: dict[str, object] = {
        "status": "running",
        "label": "exploratory",
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "python": str(PYTHON),
        "jobs": {},
    }
    dump_status(status)

    id_writer = [
        str(PYTHON),
        str(SCRIPTS / "write_masked_stem_followup_ids.py"),
    ]
    if run_job("write_ids", id_writer, status) != 0:
        status["status"] = "failed"
        dump_status(status)
        raise SystemExit(1)

    jobs = [
        (
            "mistral_options_only",
            [
                str(PYTHON),
                str(SCORER),
                "--model-id",
                MISTRAL_ID,
                "--model-revision",
                MISTRAL_REV,
                "--prompt-mode",
                "choices-only",
                "--item-ids-file",
                str(OUT_DIR / "masked-stem-primary-item-ids.json"),
                "--summary-path",
                str(OUT_DIR / "options-only-mistral-7b.json"),
                "--items-out",
                str(OUT_DIR / "options-only-mistral-7b-items.jsonl"),
                "--skip-with-stem",
                "--no-readme",
                "--batch-size",
                "8",
                "--device-map",
                "to",
                "--allow-download",
            ],
        ),
        (
            "mistral_masked_stem",
            [
                str(PYTHON),
                str(SCORER),
                "--model-id",
                MISTRAL_ID,
                "--model-revision",
                MISTRAL_REV,
                "--prompt-mode",
                "masked-stem",
                "--min-masked-token-count",
                "1",
                "--item-ids-file",
                str(OUT_DIR / "masked-stem-primary-item-ids.json"),
                "--options-only-items",
                str(OUT_DIR / "options-only-mistral-7b-items.jsonl"),
                "--summary-path",
                str(OUT_DIR / "masked-stem-mistral-7b.json"),
                "--items-out",
                str(OUT_DIR / "masked-stem-mistral-7b-items.jsonl"),
                "--audit-out",
                str(OUT_DIR / "masked-stem-mistral-7b-audit.json"),
                "--skip-with-stem",
                "--no-readme",
                "--batch-size",
                "8",
                "--device-map",
                "to",
                "--allow-download",
            ],
        ),
        (
            "qwen7_with_stem_algebra",
            [
                str(PYTHON),
                str(SCORER),
                "--model-id",
                QWEN7_ID,
                "--model-revision",
                QWEN7_REV,
                "--prompt-mode",
                "with-stem",
                "--item-ids-file",
                str(OUT_DIR / "masked-stem-algebra-primary-item-ids.json"),
                "--summary-path",
                str(OUT_DIR / "with-stem-algebra-7b.json"),
                "--items-out",
                str(OUT_DIR / "with-stem-algebra-7b-items.jsonl"),
                "--skip-with-stem",
                "--no-readme",
                "--batch-size",
                "8",
                "--device-map",
                "to",
                "--allow-download",
            ],
        ),
        (
            "qwen14_with_stem_algebra",
            [
                str(PYTHON),
                str(SCORER),
                "--model-id",
                QWEN14_ID,
                "--model-revision",
                QWEN14_REV,
                "--prompt-mode",
                "with-stem",
                "--item-ids-file",
                str(OUT_DIR / "masked-stem-algebra-primary-item-ids.json"),
                "--summary-path",
                str(OUT_DIR / "with-stem-algebra-14b.json"),
                "--items-out",
                str(OUT_DIR / "with-stem-algebra-14b-items.jsonl"),
                "--skip-with-stem",
                "--no-readme",
                "--batch-size",
                "1",
                "--device-map",
                "cuda",
                "--allow-download",
            ],
        ),
    ]
    failed: list[str] = []
    for name, argv in jobs:
        code = run_job(name, argv, status)
        if code != 0:
            failed.append(name)
            break
    status["wallTimeSeconds"] = time.time() - started
    status["finishedAt"] = datetime.now(timezone.utc).isoformat()
    status["failedJobs"] = failed
    status["status"] = "failed" if failed else "complete"
    dump_status(status)
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
