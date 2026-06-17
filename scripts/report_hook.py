#!/usr/bin/env python3
"""min-spec 轻量上报 hook 入口。

轻量实现：保留 emit 子命令、JSONL 写入、
key=value 解析和"吞异常"模式；不含任何企业级字段。

非阻塞铁律：写 JSONL 失败一律被吞掉，绝不阻塞调用方。
事件落点：docs/meta/sessions/{run_id}.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SINK_TEMPLATE = "docs/meta/sessions/{run_id}.jsonl"
SCHEMA = "min-spec-report-hook-event-v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sanitize_run_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "min-spec"


def parse_json(raw: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
    return value if isinstance(value, dict) else {"value": value}


def parse_tags(raw: str) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_key_value(items: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in items:
        key, sep, value = item.partition("=")
        key = key.strip()
        if not key:
            continue
        if not sep:
            parsed[key] = True
            continue
        value = value.strip()
        if value.lower() in {"true", "false"}:
            parsed[key] = value.lower() == "true"
            continue
        try:
            parsed[key] = int(value)
            continue
        except ValueError:
            pass
        try:
            parsed[key] = float(value)
            continue
        except ValueError:
            pass
        parsed[key] = value
    return parsed


def resolve_repo_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    env_root = os.environ.get("MINSPEC_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return REPO_ROOT


def resolve_run_id(args: argparse.Namespace) -> str:
    explicit = args.run_id or os.environ.get("MINSPEC_RUN_ID") or ""
    if explicit:
        return sanitize_run_id(explicit)
    return "min-spec"


def resolve_sink_path(root: Path, run_id: str, raw_path: str | None) -> Path:
    rel = raw_path or DEFAULT_SINK_TEMPLATE
    path = Path(rel.format(run_id=run_id))
    if not path.is_absolute():
        path = root / path
    return path


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    # 非阻塞：写入失败一律吞掉，绝不影响调用方。
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        return


def build_event(args: argparse.Namespace, root: Path, run_id: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "event_id": str(uuid.uuid4()),
        "ts": utc_now_iso(),
        "hook_id": args.hook_id,
        "category": args.category,
        "event": args.event,
        "source": args.source,
        "status": args.status,
        "run_id": run_id,
        "phase": args.phase,
        "project_root": str(root),
        "tags": parse_tags(args.tags),
        "evidence": list(args.evidence),
        "metadata": parse_key_value(args.metadata),
        "payload": parse_json(args.payload_json),
    }


def cmd_emit(args: argparse.Namespace) -> int:
    root = resolve_repo_root(args.project_root)
    run_id = resolve_run_id(args)
    event = build_event(args, root, run_id)
    sink_path = resolve_sink_path(root, run_id, args.local_jsonl)

    if not args.dry_run:
        append_jsonl(sink_path, event)

    if not args.quiet:
        print(json.dumps({
            "ok": True,
            "event_id": event["event_id"],
            "hook_id": event["hook_id"],
            "sink": str(sink_path),
            "dry_run": bool(args.dry_run),
        }, ensure_ascii=False))
    return 0


def add_emit_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("emit", help="写入一条 hook 上报事件")
    p.add_argument("--hook-id", required=True, help="注册表中的 hook id，例如 git.pre_commit")
    p.add_argument("--category", required=True, help="hook 分类，例如 git_lifecycle / pipeline_stage / quality_gate")
    p.add_argument("--event", required=True, help="事件名，例如 pre_commit / stage_enter / gate_run")
    p.add_argument("--source", default="manual", help="来源")
    p.add_argument("--status", default="completed", help="状态，例如 pass/fail/completed")
    p.add_argument("--run-id", default="", help="运行 ID，缺省取 $MINSPEC_RUN_ID 或 min-spec")
    p.add_argument("--phase", default="", help="阶段名 clarify/plan/build/verify/retrospect")
    p.add_argument("--tags", default="", help="逗号分隔标签")
    p.add_argument("--evidence", action="append", default=[], help="证据路径或摘要，可重复")
    p.add_argument("--metadata", action="append", default=[], help="元数据 key=value，可重复")
    p.add_argument("--payload-json", default="", help="额外 JSON payload")
    p.add_argument("--project-root", default="", help="项目根目录，默认自动解析")
    p.add_argument("--local-jsonl", default="", help="覆盖本地 JSONL 落点")
    p.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    p.add_argument("--quiet", action="store_true", help="静默模式")
    p.set_defaults(func=cmd_emit)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="report_hook", description="min-spec 轻量上报 hook 入口")
    sub = parser.add_subparsers(dest="command", required=True)
    add_emit_parser(sub)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except SystemExit:
        raise
    except Exception as exc:
        # 非阻塞：自身异常也返回 0，不连累调用方。
        if not getattr(args, "quiet", False):
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
