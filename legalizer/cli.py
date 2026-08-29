from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .config import ConfigError, find_project_root, load_profiles, load_rules, load_sources
from .doctor import run_doctor
from .engine import check_text
from .protection import collect_protected_spans
from .resolver import ResolverError, resolve_profile
from .source_policy import source_applicability, validate_source_registry


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _load():
    root = find_project_root()
    return root, load_rules(root), load_profiles(root), load_sources(root)


def _print_findings(path: Path, findings) -> None:
    for finding in findings:
        if finding.line is None:
            location = str(path)
        else:
            location = f"{path}:{finding.line}:{finding.column or 1}"
        print(f"{location} [{finding.severity}] {finding.rule_id}: {finding.message}")


def cmd_check(args: argparse.Namespace) -> int:
    _, rules, profiles, sources = _load()
    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    resolved, findings = check_text(
        text,
        profile_name=args.profile,
        rules=rules,
        profiles=profiles,
        sources=sources,
        document_date=_date(args.date),
        jurisdiction=args.jurisdiction,
    )
    if args.json:
        print(
            json.dumps(
                {"profile": resolved.to_dict(), "findings": [f.to_dict() for f in findings]},
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
    else:
        _print_findings(path, findings)
        print(f"{len(findings)} finding(s); {len(resolved.active_rules)} active rule(s).")

    if any(f.severity == "HARD_GATE" for f in findings):
        return 2
    if findings:
        return 1
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    _, rules, profiles, sources = _load()
    resolved = resolve_profile(
        args.profile,
        rules,
        profiles,
        sources,
        document_date=_date(args.date),
        jurisdiction=args.jurisdiction,
    )
    payload = resolved.to_dict()
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"Profile: {resolved.name}")
        print("Active rules:", ", ".join(resolved.active_rules))
        if resolved.inactive_rules:
            print("Inactive rules:")
            for rule_id, reason in resolved.inactive_rules.items():
                print(f"  {rule_id}: {reason}")
        if resolved.protected_classes:
            print("Protected classes:", ", ".join(sorted(resolved.protected_classes)))
        if resolved.disabled_for_protected_spans:
            print(
                "Disabled on protected spans:",
                ", ".join(sorted(resolved.disabled_for_protected_spans)),
            )
    return 0


def cmd_protect(args: argparse.Namespace) -> int:
    _, rules, profiles, sources = _load()
    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    resolved = resolve_profile(
        args.profile,
        rules,
        profiles,
        sources,
        document_date=_date(args.date),
        jurisdiction=args.jurisdiction,
    )
    result = collect_protected_spans(text, resolved)
    payload = {
        "profile": args.profile,
        **result.to_dict(),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        for span in result.spans:
            print(
                f"{path}:{span.line}:{span.column} [{span.kind}] {span.text!r} "
                f"({span.start}:{span.end})"
            )
        if result.unresolved_classes:
            print("Protection classes without a runtime locator:", ", ".join(sorted(result.unresolved_classes)))
        if result.disabled_rules_on_spans:
            print("Disable on these spans:", ", ".join(sorted(result.disabled_rules_on_spans)))
    return 0


def cmd_sources(args: argparse.Namespace) -> int:
    _, rules, _, sources = _load()
    document_date = _date(args.date)
    problems = validate_source_registry(rules, sources)
    rows = []
    for source_id, source in sources.items():
        ok, reason = source_applicability(
            source,
            document_date=document_date,
            jurisdiction=args.jurisdiction,
        )
        rows.append(
            {
                "id": source_id,
                "status": source.get("status"),
                "applicable": ok,
                "reason": reason,
            }
        )
    if args.json:
        print(json.dumps({"sources": rows, "registry_problems": problems}, ensure_ascii=False, indent=2, default=str))
    else:
        for row in rows:
            suffix = f" — {row['reason']}" if row["reason"] else ""
            mark = "ACTIVE" if row["applicable"] else "INACTIVE"
            print(f"{row['id']}: {mark} ({row['status']}){suffix}")
        for problem in problems:
            print(f"REGISTRY: {problem}")
    return 1 if problems else 0


def cmd_doctor(args: argparse.Namespace) -> int:
    _, rules, profiles, sources = _load()
    report = run_doctor(rules, profiles, sources)
    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, default=str))
    else:
        for issue in report.issues:
            print(f"[{issue.level}] {issue.code}: {issue.message}")
        print(
            f"{len(report.errors)} error(s), {len(report.warnings)} warning(s); "
            f"{len(report.implemented_rules)} runtime rule(s), {len(report.manual_rules)} contextual/manual rule(s)."
        )
    return 2 if report.errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="legalizer")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--date", help="Document date as YYYY-MM-DD")
    common.add_argument("--jurisdiction", default="RU")
    common.add_argument("--json", action="store_true")

    check = sub.add_parser("check", parents=[common], help="Lint a UTF-8 text/Markdown document")
    check.add_argument("file")
    check.add_argument("--profile", required=True)
    check.set_defaults(func=cmd_check)

    resolve = sub.add_parser("resolve", parents=[common], help="Show the resolved rule set")
    resolve.add_argument("--profile", required=True)
    resolve.set_defaults(func=cmd_resolve)

    protect = sub.add_parser("protect", parents=[common], help="Locate spans protected by the selected profile")
    protect.add_argument("file")
    protect.add_argument("--profile", required=True)
    protect.set_defaults(func=cmd_protect)

    sources = sub.add_parser("sources", parents=[common], help="Show source applicability")
    sources.set_defaults(func=cmd_sources)

    doctor = sub.add_parser("doctor", help="Validate rules, profiles, sources and runtime registry")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ConfigError, ResolverError, ValueError, OSError) as exc:
        print(f"legalizer: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
