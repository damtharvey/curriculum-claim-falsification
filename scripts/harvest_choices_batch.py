#!/usr/bin/env python3
"""Audit a choices-only subagent transcript and, if tool-free, write predictions."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from score_choices_only import extract_json_object

TRANSCRIPT_ROOTS = [
    Path(
        "/home/harvey/.cursor/projects/home-harvey-repos-whats-new/"
        "agent-transcripts/48539ff1-3f2f-48f8-8a8d-b74ef6443552/subagents"
    ),
    Path(
        "/home/harvey/.cursor/projects/home-harvey-repos-whats-new/"
        "agent-transcripts/50743b63-59bd-4474-b278-7abe638d7381/subagents"
    ),
]
ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "exports" / "choices-only" / "predictions"
AUDIT_PATH = ROOT / "exports" / "channel-audit.json"
BATCH_DIR = ROOT / "exports" / "choices-only" / "batches"


def find_transcript(agent_id: str) -> Path | None:
    for root in TRANSCRIPT_ROOTS:
        path = root / f"{agent_id}.jsonl"
        if path.exists():
            return path
    return None


def tool_use_count(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("role") != "assistant":
            continue
        content = rec.get("message", {}).get("content") or rec.get("content") or []
        if isinstance(content, str):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                count += 1
    return count


def last_assistant_text(path: Path) -> str:
    text = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("role") != "assistant":
            continue
        content = rec.get("message", {}).get("content") or rec.get("content") or []
        if isinstance(content, str):
            text = content
            continue
        chunks: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                chunks.append(str(block.get("text") or ""))
        if chunks:
            text = "\n".join(chunks)
    return text


def upsert_audit(entry: dict[str, Any], kept: bool) -> None:
    audit: dict[str, Any]
    if AUDIT_PATH.exists():
        audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    else:
        audit = {"batches": [], "discarded": []}
    key = "batches" if kept else "discarded"
    others = [row for row in audit.get(key, []) if row.get("batch") != entry["batch"] or row.get("agentId") != entry["agentId"]]
    others.append(entry)
    audit[key] = others
    AUDIT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: harvest_choices_batch.py <batch> <agent_id>")
    batch = sys.argv[1]
    agent_id = sys.argv[2]
    transcript = find_transcript(agent_id)
    if transcript is None:
        print(json.dumps({"batch": batch, "agentId": agent_id, "status": "no_transcript"}))
        return
    tools = tool_use_count(transcript)
    text = last_assistant_text(transcript)
    preds = extract_json_object(text)
    map_path = BATCH_DIR / f"batch-{batch}.map.json"
    item_ids = [row["itemId"] for row in json.loads(map_path.read_text(encoding="utf-8"))] if map_path.exists() else []
    map_n = len(item_ids)
    kept = tools == 0 and (len(preds) >= 40 or (map_n > 0 and len(preds) >= map_n))
    entry = {
        "batch": batch,
        "agentId": agent_id,
        "model": "composer-2.5-fast",
        "toolUseCount": tools,
        "itemIds": item_ids,
        "nPredictions": len(preds),
        "kept": kept,
        "transcript": str(transcript),
        "wave": "n2405",
    }
    if kept:
        PRED_DIR.mkdir(parents=True, exist_ok=True)
        (PRED_DIR / f"batch-{batch}.json").write_text(
            json.dumps({"predictions": preds}, indent=2) + "\n", encoding="utf-8"
        )
    upsert_audit(entry, kept)
    print(json.dumps({"batch": batch, "tools": tools, "npred": len(preds), "kept": kept}, indent=2))


if __name__ == "__main__":
    main()
