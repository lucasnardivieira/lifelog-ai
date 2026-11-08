"""``lifelog synth`` → fictional events; ``lifelog build`` → dbt build + dashboard JSON."""

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from lifelog.export import build_payload, write_payload
from lifelog.synthetic import generate, to_jsonl

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_EVENTS = Path("data/synthetic/events.jsonl")
PUBLIC_JSON = Path("web/public/data/lifelog.json")
PRIVATE_JSON = Path("web/public/data/lifelog.local.json")  # gitignored


def _synth(args: argparse.Namespace) -> None:
    end = date.fromisoformat(args.end) if args.end else date.today()
    events = generate(end, days=args.days, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(to_jsonl(events), encoding="utf-8")
    print(f"Wrote {len(events):,} synthetic events ({args.days} days until {end}) to {args.out}")


def _build(args: argparse.Namespace) -> None:
    sample = args.events.resolve() == (ROOT / SYNTHETIC_EVENTS).resolve()
    out = args.out or (PUBLIC_JSON if sample else PRIVATE_JSON)
    db = Path("data/lifelog.duckdb" if sample else "data/private/lifelog.duckdb")
    db.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ | {"LIFELOG_EVENTS": str(args.events), "LIFELOG_DUCKDB": str(db)}
    cmd = ["dbt", "build", "--project-dir", "dbt", "--profiles-dir", "dbt", "--quiet"]
    if subprocess.run(cmd, env=env, check=False).returncode != 0:
        sys.exit("dbt build failed")
    goals = yaml.safe_load((ROOT / "dbt/dbt_project.yml").read_text())["vars"]
    write_payload(build_payload(db, sample=sample, goals=goals), out)
    print(f"Wrote dashboard data ({'sample' if sample else 'PRIVATE'}) to {out}")


def main(argv: list[str] | None = None) -> None:
    os.chdir(ROOT)
    parser = argparse.ArgumentParser(prog="lifelog")
    sub = parser.add_subparsers(required=True)

    synth = sub.add_parser("synth", help="generate fictional events for the public demo")
    synth.add_argument("--out", type=Path, default=SYNTHETIC_EVENTS)
    synth.add_argument("--days", type=int, default=183)
    synth.add_argument("--end", help="last day (YYYY-MM-DD), default today")
    synth.add_argument("--seed", type=int, default=42)
    synth.set_defaults(func=_synth)

    build = sub.add_parser("build", help="dbt build + export the dashboard JSON")
    build.add_argument("--events", type=Path, default=SYNTHETIC_EVENTS)
    build.add_argument("--out", type=Path, default=None)
    build.set_defaults(func=_build)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
