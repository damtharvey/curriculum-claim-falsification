#!/usr/bin/env python3
"""GPU jobs for the non-Qwen scorer-capability check. Writes a status partial after each job."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUT_DIR = ROOT / "exports" / "addendum-gpu"
STATUS_PATH = OUT_DIR / "scorer-capability-status.json"
PYTHON = ROOT / ".venv" / "bin" / "python"
SCORER = SCRIPTS / "score_choices_only_local_lm.py"
PRIMARY_IDS = OUT_DIR / "masked-stem-primary-item-ids.json"
ALGEBRA_IDS = OUT_DIR / "masked-stem-algebra-primary-item-ids.json"
DEADLINE_UTC = datetime(2026, 9, 16, 22, 28, tzinfo=timezone.utc)

PHI4_ID = "microsoft/phi-4"
PHI4_REV = "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"
MISTRAL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
MISTRAL_REV = "c170c708c41dac9275d15a8fff4eca08d52bab71"
GEMMA_ID = "google/gemma-2-9b-it"
GEMMA_REV = "11c9b309abf73637e4b6f9a3fa1e92e615547819"
GEMMA_SNAPSHOT = (
    Path.home()
    / ".cache"
    / "huggingface"
    / "hub"
    / "models--google--gemma-2-9b-it"
    / "snapshots"
    / GEMMA_REV
)


def dump_status(payload: dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seconds_until_deadline() -> float:
    return (DEADLINE_UTC - utc_now()).total_seconds()


def run_summarizer() -> None:
    completed = subprocess.run(
        [str(PYTHON), str(SCRIPTS / "summarize_masked_stem_scorer_capability.py")],
        cwd=str(ROOT),
    )
    print(f"=== summarizer rc={completed.returncode} ===", flush=True)


def run_job(name: str, argv: list[str], status: dict[str, Any]) -> int:
    jobs = status.setdefault("jobs", {})
    if not isinstance(jobs, dict):
        raise RuntimeError("status jobs must be a dict")
    started = time.time()
    jobs[name] = {
        "status": "running",
        "startedAt": utc_now().isoformat(),
        "argv": argv,
        "secondsUntilDeadlineAtStart": seconds_until_deadline(),
    }
    dump_status(status)
    print(f"=== starting {name} remaining_s={seconds_until_deadline():.0f} ===", flush=True)
    completed = subprocess.run(argv, cwd=str(ROOT))
    elapsed = time.time() - started
    jobs[name] = {
        "status": "complete" if completed.returncode == 0 else "failed",
        "returnCode": completed.returncode,
        "wallTimeSeconds": elapsed,
        "finishedAt": utc_now().isoformat(),
        "argv": argv,
        "secondsUntilDeadlineAtFinish": seconds_until_deadline(),
    }
    dump_status(status)
    print(
        f"=== finished {name} rc={completed.returncode} wall={elapsed:.1f}s "
        f"remaining_s={seconds_until_deadline():.0f} ===",
        flush=True,
    )
    run_summarizer()
    return int(completed.returncode)


def scorer_argv(
    *,
    name_tag: str,
    model_id: str,
    model_revision: str | None,
    prompt_mode: str,
    ids_file: Path,
    summary_path: Path,
    items_out: Path,
    batch_size: int,
    device_map: str,
    allow_download: bool,
    min_masked_token_count: int | None = None,
    options_only_items: Path | None = None,
    audit_out: Path | None = None,
) -> list[str]:
    argv = [
        str(PYTHON),
        str(SCORER),
        "--model-id",
        model_id,
        "--prompt-mode",
        prompt_mode,
        "--item-ids-file",
        str(ids_file),
        "--summary-path",
        str(summary_path),
        "--items-out",
        str(items_out),
        "--skip-with-stem",
        "--no-readme",
        "--batch-size",
        str(batch_size),
        "--device-map",
        device_map,
    ]
    if model_revision:
        argv.extend(["--model-revision", model_revision])
    if allow_download:
        argv.append("--allow-download")
    if min_masked_token_count is not None:
        argv.extend(["--min-masked-token-count", str(min_masked_token_count)])
    if options_only_items is not None:
        argv.extend(["--options-only-items", str(options_only_items)])
    if audit_out is not None:
        argv.extend(["--audit-out", str(audit_out)])
    _ = name_tag
    return argv


def main() -> None:
    if not PYTHON.exists():
        raise RuntimeError(f"expected venv python at {PYTHON}")
    started = time.time()
    status: dict[str, Any] = {
        "status": "running",
        "label": "exploratory",
        "startedAt": utc_now().isoformat(),
        "deadlineUtc": DEADLINE_UTC.isoformat(),
        "python": str(PYTHON),
        "gpuRequired": True,
        "jobs": {},
        "cut": [],
        "hypothesis": (
            "The masked-stem plus options Algebra I / II effect needs a capable "
            "scorer, not a Qwen scorer."
        ),
    }
    dump_status(status)

    jobs: list[tuple[str, list[str], float]] = [
        (
            "phi4_options_only",
            scorer_argv(
                name_tag="phi4_options_only",
                model_id=PHI4_ID,
                model_revision=PHI4_REV,
                prompt_mode="choices-only",
                ids_file=PRIMARY_IDS,
                summary_path=OUT_DIR / "options-only-phi4.json",
                items_out=OUT_DIR / "options-only-phi4-items.jsonl",
                batch_size=1,
                device_map="cuda",
                allow_download=True,
            ),
            900.0,
        ),
        (
            "phi4_masked_stem",
            scorer_argv(
                name_tag="phi4_masked_stem",
                model_id=PHI4_ID,
                model_revision=PHI4_REV,
                prompt_mode="masked-stem",
                ids_file=PRIMARY_IDS,
                summary_path=OUT_DIR / "masked-stem-phi4.json",
                items_out=OUT_DIR / "masked-stem-phi4-items.jsonl",
                batch_size=1,
                device_map="cuda",
                allow_download=True,
                min_masked_token_count=1,
                options_only_items=OUT_DIR / "options-only-phi4-items.jsonl",
                audit_out=OUT_DIR / "masked-stem-phi4-audit.json",
            ),
            900.0,
        ),
        (
            "phi4_with_stem_algebra",
            scorer_argv(
                name_tag="phi4_with_stem_algebra",
                model_id=PHI4_ID,
                model_revision=PHI4_REV,
                prompt_mode="with-stem",
                ids_file=ALGEBRA_IDS,
                summary_path=OUT_DIR / "with-stem-algebra-phi4.json",
                items_out=OUT_DIR / "with-stem-algebra-phi4-items.jsonl",
                batch_size=1,
                device_map="cuda",
                allow_download=True,
            ),
            480.0,
        ),
        (
            "mistral_with_stem_algebra",
            scorer_argv(
                name_tag="mistral_with_stem_algebra",
                model_id=MISTRAL_ID,
                model_revision=MISTRAL_REV,
                prompt_mode="with-stem",
                ids_file=ALGEBRA_IDS,
                summary_path=OUT_DIR / "with-stem-algebra-mistral.json",
                items_out=OUT_DIR / "with-stem-algebra-mistral-items.jsonl",
                batch_size=8,
                device_map="to",
                allow_download=False,
            ),
            180.0,
        ),
    ]
    gemma_cached = GEMMA_SNAPSHOT.exists() and (GEMMA_SNAPSHOT / "config.json").exists()
    status["gemmaCached"] = gemma_cached
    status["gemmaSnapshot"] = str(GEMMA_SNAPSHOT)
    dump_status(status)
    if gemma_cached:
        jobs.extend(
            [
                (
                    "gemma_options_only",
                    scorer_argv(
                        name_tag="gemma_options_only",
                        model_id=GEMMA_ID,
                        model_revision=GEMMA_REV,
                        prompt_mode="choices-only",
                        ids_file=PRIMARY_IDS,
                        summary_path=OUT_DIR / "options-only-gemma-2-9b.json",
                        items_out=OUT_DIR / "options-only-gemma-2-9b-items.jsonl",
                        batch_size=4,
                        device_map="cuda",
                        allow_download=False,
                    ),
                    420.0,
                ),
                (
                    "gemma_masked_stem",
                    scorer_argv(
                        name_tag="gemma_masked_stem",
                        model_id=GEMMA_ID,
                        model_revision=GEMMA_REV,
                        prompt_mode="masked-stem",
                        ids_file=PRIMARY_IDS,
                        summary_path=OUT_DIR / "masked-stem-gemma-2-9b.json",
                        items_out=OUT_DIR / "masked-stem-gemma-2-9b-items.jsonl",
                        batch_size=4,
                        device_map="cuda",
                        allow_download=False,
                        min_masked_token_count=1,
                        options_only_items=OUT_DIR / "options-only-gemma-2-9b-items.jsonl",
                        audit_out=OUT_DIR / "masked-stem-gemma-2-9b-audit.json",
                    ),
                    420.0,
                ),
                (
                    "gemma_with_stem_algebra",
                    scorer_argv(
                        name_tag="gemma_with_stem_algebra",
                        model_id=GEMMA_ID,
                        model_revision=GEMMA_REV,
                        prompt_mode="with-stem",
                        ids_file=ALGEBRA_IDS,
                        summary_path=OUT_DIR / "with-stem-algebra-gemma-2-9b.json",
                        items_out=OUT_DIR / "with-stem-algebra-gemma-2-9b-items.jsonl",
                        batch_size=4,
                        device_map="cuda",
                        allow_download=False,
                    ),
                    240.0,
                ),
            ]
        )
    else:
        status["cut"].append(
            {
                "job": "gemma-2-9b-it",
                "reason": "snapshot missing; would need a gated Hugging Face download",
            }
        )
        dump_status(status)

    failed: list[str] = []
    for name, argv, estimated_seconds in jobs:
        remaining = seconds_until_deadline()
        if remaining < estimated_seconds:
            status["cut"].append(
                {
                    "job": name,
                    "reason": (
                        f"deadline 2026-09-16T22:28:00Z; remaining {remaining:.0f}s "
                        f"below estimate {estimated_seconds:.0f}s"
                    ),
                }
            )
            dump_status(status)
            print(f"=== cutting {name} remaining_s={remaining:.0f} ===", flush=True)
            continue
        code = run_job(name, argv, status)
        if code != 0:
            if name.startswith("gemma"):
                status["cut"].append(
                    {
                        "job": name,
                        "reason": (
                            "scorer exited "
                            f"{code}; Gemma-2 chat template rejects the shared system "
                            "message (System role not supported). Remaining Gemma jobs skipped."
                        ),
                    }
                )
                dump_status(status)
                break
            failed.append(name)
            status["cut"].append(
                {
                    "job": name,
                    "reason": f"scorer exited {code}; later jobs not started",
                }
            )
            break

    status["wallTimeSeconds"] = time.time() - started
    status["finishedAt"] = utc_now().isoformat()
    status["failedJobs"] = failed
    if failed:
        status["status"] = "failed"
    elif status["cut"]:
        status["status"] = "partial"
    else:
        status["status"] = "complete"
    dump_status(status)
    run_summarizer()
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
