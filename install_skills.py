#!/usr/bin/env python3
"""
install_skills.py — Install open-science-skills into opencode's skill directories.

A CLI installer that copies or symlinks skills from this repo into the directories
opencode scans (native ~/.config/opencode/skills/ by default, or project .opencode/skills/).
The npm `skills` package targets .claude/skills and .agents/skills but not opencode's
native dir; this fills that gap and works offline from a local checkout.

Usage:
    python install_skills.py list                  # show skills available in this repo
    python install_skills.py add all                # install every skill
    python install_skills.py add git-rules          # install one skill
    python install_skills.py add git-rules uv-env   # install several
    python install_skills.py installed              # show what's installed (from lock)
    python install_skills.py update [name ...]      # re-sync installed skills (or named ones)
    python install_skills.py remove all             # remove every installed skill
    python install_skills.py remove git-rules       # remove one

Flags:
    --project        install into ./.opencode/skills instead of global ~/.config/opencode/skills
    --target DIR     custom target directory (overrides --project)
    --copy           copy files instead of symlinking (default is symlink)
    --force          overwrite existing without prompting
    --compatible     also mirror into ~/.claude/skills and ~/.agents/skills (for other tools)

Requires: Python 3.8+ and stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent
DEFAULT_GLOBAL = Path.home() / ".config" / "opencode" / "skills"
COMPAT_DIRS = [
    Path.home() / ".claude" / "skills",
    Path.home() / ".agents" / "skills",
]
LOCK_NAME = ".science-skills.lock.json"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESC_MAX = 1024


# ---------- frontmatter (minimal YAML, no deps) ----------

def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    lines = m.group(1).split("\n")
    fm, i = {}, 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not kv:
            i += 1
            continue
        key, val = kv.group(1), kv.group(2).strip()
        if val in ("", ">", ">-", "|", "|-"):
            collected, i = [], i + 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                if lines[i].strip():
                    collected.append(lines[i].strip())
                i += 1
            fm[key] = " ".join(collected)
        else:
            fm[key] = val.strip().strip('"').strip("'")
            i += 1
    return fm


# ---------- discovery & validation ----------

def discover(repo: Path) -> list[Path]:
    skills = []
    for child in sorted(repo.iterdir()):
        if child.is_dir() and not child.name.startswith(".") and (child / "SKILL.md").is_file():
            skills.append(child)
    return skills


def validate(skill_dir: Path) -> list[str]:
    """Return a list of problems (empty list = valid). opencode rules."""
    probs = []
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    name = fm.get("name")
    desc = fm.get("description", "")
    if not name:
        probs.append("missing frontmatter `name`")
    elif name != skill_dir.name:
        probs.append(f"name `{name}` != dir `{skill_dir.name}` (opencode requires match)")
    if name and not NAME_RE.match(name):
        probs.append(f"name `{name}` fails opencode regex ^[a-z0-9]+(-[a-z0-9]+)*$")
    if not desc:
        probs.append("missing frontmatter `description`")
    elif len(desc) > DESC_MAX:
        probs.append(f"description {len(desc)} > {DESC_MAX} chars")
    return probs


# ---------- lock file ----------

def load_lock(target: Path) -> dict:
    lf = target / LOCK_NAME
    if lf.is_file():
        try:
            return json.loads(lf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"skills": {}}
    return {"skills": {}}


def save_lock(target: Path, lock: dict) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / LOCK_NAME).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


def folder_hash(skill_dir: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(skill_dir.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(skill_dir).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()[:12]


# ---------- install / remove ----------

def _rm_dst(dst: Path) -> None:
    # symlink-to-dir must be unlinked, not rmtree'd (rmtree refuses symlinks)
    if dst.is_symlink():
        dst.unlink()
    elif dst.is_dir():
        shutil.rmtree(dst)
    elif dst.exists():
        dst.unlink()


def _link_or_copy(src: Path, dst: Path, copy: bool) -> None:
    if dst.is_symlink() or dst.exists():
        _rm_dst(dst)
    if copy:
        shutil.copytree(src, dst)
    else:
        dst.symlink_to(src)


def install_one(skill_dir: Path, target: Path, copy: bool, force: bool, lock: dict) -> str:
    name = skill_dir.name
    dst = target / name
    probs = validate(skill_dir)
    if probs:
        return f"  SKIP {name}: " + "; ".join(probs)
    if (dst.is_symlink() or dst.exists()) and not force:
        resp = input(f"  {name} already exists at {dst}. Overwrite? [y/N] ").strip().lower()
        if resp != "y":
            return f"  SKIP {name}: exists (kept)"
    _link_or_copy(skill_dir, dst, copy)
    lock["skills"][name] = {
        "source": str(skill_dir),
        "method": "copy" if copy else "symlink",
        "hash": folder_hash(skill_dir),
        "installedAt": datetime.now(timezone.utc).isoformat(),
    }
    return f"  OK   {name} -> {dst}" + (" (copy)" if copy else " (symlink)")


def remove_one(name: str, target: Path, lock: dict) -> str:
    dst = target / name
    if dst.is_symlink() or dst.exists():
        _rm_dst(dst)
    lock["skills"].pop(name, None)
    return f"  OK   removed {name}"


# ---------- compat mirror (optional, for .claude / .agents) ----------

def mirror_compat(skill_dir: Path, copy: bool, force: bool) -> list[str]:
    msgs = []
    for cdir in COMPAT_DIRS:
        dst = cdir / skill_dir.name
        if dst.is_symlink() or dst.exists():
            if not force:
                continue
            _rm_dst(dst)
        cdir.mkdir(parents=True, exist_ok=True)
        try:
            _link_or_copy(skill_dir, dst, copy)
            msgs.append(f"    + {dst}")
        except OSError as e:
            msgs.append(f"    ! {dst}: {e}")
    return msgs


# ---------- CLI ----------

def cmd_list(args, _lock):
    skills = discover(REPO)
    if not skills:
        return "No skills found in repo."
    out = ["Available skills in this repo:"]
    for s in skills:
        fm = parse_frontmatter(s / "SKILL.md")
        desc = fm.get("description", "")
        out.append(f"  {s.name:<24} {desc[:70]}")
    return "\n".join(out)


def cmd_add(args, lock):
    target = resolve_target(args)
    target.mkdir(parents=True, exist_ok=True)
    available = {s.name: s for s in discover(REPO)}
    wanted = available.keys() if "all" in args.names else args.names
    msgs, lock = [], load_lock(target)
    for name in wanted:
        if name == "all":
            continue
        if name not in available:
            msgs.append(f"  SKIP {name}: not found in repo (try `list`)")
            continue
        msgs.append(install_one(available[name], target, args.copy, args.force, lock))
        if args.compatible:
            msgs.append(f"  mirroring {name} to compatible dirs:")
            msgs.extend(mirror_compat(available[name], args.copy, args.force))
    save_lock(target, lock)
    msgs.append(f"\nTarget: {target}")
    return "\n".join(msgs)


def cmd_installed(args, _lock):
    target = resolve_target(args)
    lock = load_lock(target)
    skills = lock.get("skills", {})
    if not skills:
        return f"No skills installed at {target}"
    out = [f"Installed at {target}:"]
    for name, info in sorted(skills.items()):
        out.append(f"  {name:<24} {info.get('method', '?'):<8} hash={info.get('hash', '?')[:8]}  {info.get('installedAt', '')[:19]}")
    return "\n".join(out)


def cmd_update(args, lock):
    target = resolve_target(args)
    lock = load_lock(target)
    installed = lock.get("skills", {})
    available = {s.name: s for s in discover(REPO)}
    names = installed.keys() if "all" in args.names else args.names
    msgs = []
    for name in names:
        if name not in available:
            msgs.append(f"  SKIP {name}: no longer in repo")
            continue
        if name not in installed:
            msgs.append(install_one(available[name], target, args.copy, True, lock))
            continue
        new_hash = folder_hash(available[name])
        if new_hash != installed[name].get("hash"):
            copy = installed[name].get("method") == "copy"
            msgs.append(install_one(available[name], target, copy, True, lock))
            msgs.append(f"  updated {name}")
        else:
            msgs.append(f"  up-to-date {name}")
    save_lock(target, lock)
    return "\n".join(msgs)


def cmd_remove(args, lock):
    target = resolve_target(args)
    lock = load_lock(target)
    names = lock.get("skills", {}).keys() if "all" in args.names else args.names
    msgs = []
    for name in list(names):
        msgs.append(remove_one(name, target, lock))
    save_lock(target, lock)
    return "\n".join(msgs)


def resolve_target(args) -> Path:
    if args.target:
        return Path(args.target).expanduser().resolve()
    if args.project:
        return Path.cwd() / ".opencode" / "skills"
    return DEFAULT_GLOBAL


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="install_skills.py",
        description="Install open-science-skills into opencode skill directories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="show skills available in this repo").set_defaults(func=cmd_list)
    pi = sub.add_parser("installed", help="show installed skills (from lock)")
    pi.set_defaults(func=cmd_installed)

    pa = sub.add_parser("add", help="install skill(s): `add all` or `add <name> [name ...]`")
    pa.add_argument("names", nargs="+", help="skill name or `all`")
    pa.set_defaults(func=cmd_add)

    pu = sub.add_parser("update", help="re-sync installed skills; pass names or none for all")
    pu.add_argument("names", nargs="*", default=["all"], help="skill name(s) or empty for all installed")
    pu.set_defaults(func=cmd_update)

    pr = sub.add_parser("remove", help="remove skill(s): `remove all` or `remove <name> [name ...]`")
    pr.add_argument("names", nargs="+", help="skill name or `all`")
    pr.set_defaults(func=cmd_remove)

    for sp in (pa, pu, pr, pi):
        sp.add_argument("--project", action="store_true", help="use ./.opencode/skills instead of global")
        sp.add_argument("--target", help="custom target directory")
    pa.add_argument("--copy", action="store_true", help="copy files instead of symlinking")
    pa.add_argument("--force", action="store_true", help="overwrite existing without prompting")
    pa.add_argument("--compatible", action="store_true", help="also mirror into ~/.claude/skills and ~/.agents/skills")
    pu.add_argument("--copy", action="store_true", help="copy files instead of symlinking (for newly-seen skills)")

    args = p.parse_args(argv)
    lock = {}
    print(args.func(args, lock))


if __name__ == "__main__":
    main()
