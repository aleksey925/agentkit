#!/usr/bin/env python3
"""
Install agent-brainpack skills into Claude Code and Codex without plugins.

Which skills go to which agent is taken from the repo's own manifests,
so the plugin setup and this script never disagree:

  .claude-plugin/marketplace.json   -> Claude Code  (~/.claude/skills)
  .agents/plugins/marketplace.json  -> Codex        (~/.agents/skills)

Every plugin listed in a manifest contributes its <plugin>/skills/<name>/
folders (a folder counts as a skill if it contains SKILL.md). If a manifest
is missing, all plugins under ./plugins are used for that agent.

Safety: nothing is overwritten or deleted unless it is provably safe.
A skill is a whole folder, so it is compared by a hash of its entire tree
(file paths, contents, executable bits, symlinks, sub-folders). When a skill
is copied, that hash is stored next to it. Before replacing or removing an
existing skill folder the script checks:

  * identical to the repo version               -> safe, nothing is lost
  * unchanged since this script installed it    -> safe to update/remove
  * anything else (edited by hand, someone
    else's skill with the same name, ...)       -> CONFLICT, skipped

All conflicts are listed at the end with a diff command, so you can resolve
them by hand. --force replaces conflicting skills anyway.

Usage:
  python3 install_skills.py                  # install to both agents (symlinks)
  python3 install_skills.py --agent claude   # only Claude Code
  python3 install_skills.py --copy           # copy instead of symlink
  python3 install_skills.py --relative       # relative symlinks
  python3 install_skills.py --list           # show what would go where
  python3 install_skills.py --dry-run        # print actions, change nothing
  python3 install_skills.py --uninstall      # remove what this script installed
  python3 install_skills.py --force          # also replace conflicting skills
  python3 install_skills.py --home /home/box # install into another home dir

Exit code is 1 if any skill was skipped because of a conflict.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

def find_repo_root():
    """Walk up from the script's folder to the repo root, so the script
    works both from the root and from a subfolder like scripts/."""
    start = Path(__file__).resolve().parent
    for folder in (start, *start.parents):
        if ((folder / ".claude-plugin").is_dir() or (folder / ".agents" / "plugins").is_dir()
                or (folder / "plugins").is_dir()):
            return folder
    sys.exit(f"Repo root not found: no .claude-plugin/, .agents/plugins/ or plugins/ above {start}")


REPO = find_repo_root()
MARKER = ".brainpack"  # JSON stored inside copied skills: source + hash
IGNORED = {MARKER, ".DS_Store", "__pycache__"}  # never compared, never copied

AGENTS = {
    "claude": {
        "manifest": ".claude-plugin/marketplace.json",
        "target": ".claude/skills",
    },
    "codex": {
        "manifest": ".agents/plugins/marketplace.json",
        "target": ".agents/skills",
    },
}

conflicts = []  # (agent, name, installed_path, repo_path_or_None, reason)


def warn(msg):
    print(f"  ! {msg}", file=sys.stderr)


def is_inside_repo(path):
    try:
        path.resolve().relative_to(REPO)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- discovery

def plugin_dirs_for(agent):
    """Return plugin folders an agent should get, according to its manifest."""
    manifest = REPO / AGENTS[agent]["manifest"]
    if not manifest.is_file():
        warn(f"{agent}: {manifest.relative_to(REPO)} not found, using every plugin in ./plugins")
        plugins_root = REPO / "plugins"
        if not plugins_root.is_dir():
            return []
        return sorted(p for p in plugins_root.iterdir() if (p / "skills").is_dir())

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in {manifest}: {e}")

    plugin_root = (data.get("metadata") or {}).get("pluginRoot")
    dirs = []
    for entry in data.get("plugins", []):
        name = entry.get("name", "?")
        source = entry.get("source")
        if isinstance(source, dict):
            if source.get("source") != "local":
                warn(f"{agent}: plugin '{name}' is not local, skipped")
                continue
            path = source.get("path")
        else:
            path = source
        if not path:
            warn(f"{agent}: plugin '{name}' has no source path, skipped")
            continue
        if plugin_root and not path.startswith(("./", "../", "/")):
            path = os.path.join(plugin_root, path)
        plugin_dir = (REPO / path).resolve()
        if not plugin_dir.is_dir():
            warn(f"{agent}: plugin '{name}' points to missing folder {path}, skipped")
            continue
        dirs.append(plugin_dir)
    return dirs


def skills_for(agent):
    """Return {skill_name: skill_dir} for an agent."""
    skills = {}
    for plugin_dir in plugin_dirs_for(agent):
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if not (skill_dir / "SKILL.md").is_file():
                continue
            name = skill_dir.name
            if name in skills:
                warn(f"{agent}: skill '{name}' exists in several plugins, "
                     f"keeping {skills[name].relative_to(REPO)}")
                continue
            skills[name] = skill_dir
    return skills


# ----------------------------------------------------------- tree hashing

def tree_hash(root):
    """Hash a whole skill folder: relative paths, file contents,
    executable bits, symlink targets and folder structure.
    Two folders have the same hash only if they are identical."""
    h = hashlib.sha256()

    def walk(directory, rel):
        for entry in sorted(os.scandir(directory), key=lambda e: e.name):
            if entry.name in IGNORED:
                continue
            path = rel + entry.name
            if entry.is_symlink():
                h.update(f"L\0{path}\0{os.readlink(entry.path)}\0".encode())
            elif entry.is_dir():
                h.update(f"D\0{path}\0".encode())
                walk(entry.path, path + "/")
            else:
                st = entry.stat()
                executable = "x" if st.st_mode & 0o111 else "-"
                h.update(f"F\0{path}\0{executable}\0{st.st_size}\0".encode())
                with open(entry.path, "rb") as f:
                    for chunk in iter(lambda: f.read(1 << 16), b""):
                        h.update(chunk)

    walk(root, "")
    return h.hexdigest()


def read_marker(path):
    try:
        data = json.loads((path / MARKER).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}  # missing or old plain-text marker: no recorded hash
    return data if isinstance(data, dict) else {}


# ------------------------------------------------------------ install logic

def link_target(src, dst, relative):
    return os.path.relpath(src, dst.parent) if relative else str(src)


def is_managed(path):
    """True if the entry was created by this script."""
    if path.is_symlink():
        target = Path(os.readlink(path))
        if not target.is_absolute():
            target = path.parent / target
        return is_inside_repo(target)
    return path.is_dir() and (path / MARKER).is_file()


def unchanged_since_install(path):
    recorded = read_marker(path).get("hash")
    return recorded is not None and recorded == tree_hash(path)


def check_existing(dst, src, args):
    """Decide what to do with an existing entry at dst.
    Returns ("up-to-date" | "update" | "conflict", reason)."""
    mode = "copy" if args.copy else "link"
    if dst.is_symlink():
        if not is_managed(dst):
            return "conflict", f"a symlink to {os.readlink(dst)} not created by this script is in the way"
        if not args.copy:
            if os.readlink(dst) == link_target(src, dst, args.relative):
                return "up-to-date", ""
            if os.path.isabs(os.readlink(dst)) != os.path.isabs(link_target(src, dst, args.relative)):
                return "update", "absolute → relative link" if args.relative else "relative → absolute link"
            return "update", "link pointed to an old location"
        return "update", "link → copy"  # content lives in the repo, nothing to lose

    if not dst.is_dir():
        return "conflict", "a file with this name is in the way"

    current = tree_hash(dst)
    if current == tree_hash(src):
        if not is_managed(dst):
            return "update", f"existing folder was identical, replaced with {mode}"
        if args.copy:
            if read_marker(dst).get("hash") == current:
                return "up-to-date", ""
            return "update", "copy was identical, hash record refreshed"
        return "update", "copy → link"
    if is_managed(dst):
        if unchanged_since_install(dst):
            return "update", "repo changed" if args.copy else "repo changed, copy → link"
        return "conflict", "installed copy was edited after installation"
    return "conflict", "a different skill with the same name already exists"


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def copy_skill(src, dst):
    """Copy via a temp folder so a failed copy never leaves a half-skill behind."""
    tmp = dst.with_name(dst.name + ".brainpack-tmp")
    if tmp.exists() or tmp.is_symlink():
        remove(tmp)
    shutil.copytree(src, tmp, symlinks=True, ignore=shutil.ignore_patterns(*IGNORED))
    marker = {"source": str(src), "hash": tree_hash(tmp)}
    (tmp / MARKER).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    if dst.exists() or dst.is_symlink():
        remove(dst)
    tmp.rename(dst)


def place(src, dst, args):
    """Create the link or copy. Returns "link" or "copy" (what was actually made)."""
    if args.copy:
        copy_skill(src, dst)
        return "copy"
    if dst.exists() or dst.is_symlink():
        remove(dst)
    try:
        os.symlink(link_target(src, dst, args.relative), dst, target_is_directory=True)
        return "link"
    except OSError as e:  # e.g. Windows without symlink rights
        warn(f"symlink failed ({e}), copying instead")
        copy_skill(src, dst)
        return "copy"


def say(args, done, planned):
    return planned if args.dry_run else done


def install_skill(agent, name, src, dst, args):
    """Install one skill. Returns (summary_key, status text)."""
    mode = "copy" if args.copy else "link"
    if not (dst.exists() or dst.is_symlink()):
        made = mode if args.dry_run else place(src, dst, args)
        return "installed", say(args, f"installed ({made})", f"will install ({mode})")

    action, reason = check_existing(dst, src, args)
    if action == "up-to-date":
        return "up to date", "up to date"
    if action == "conflict":
        if not args.force:
            conflicts.append((agent, name, dst, src, reason))
            return "skipped", f"SKIPPED: {reason}"
        if not args.dry_run:
            place(src, dst, args)
        return "overwritten", say(args, f"OVERWRITTEN (--force): {reason}",
                                  f"will OVERWRITE (--force): {reason}")
    if not args.dry_run:
        place(src, dst, args)
    return "updated", say(args, f"updated: {reason}", f"will update: {reason}")


def prune(agent, target, keep, args, counts):
    """Remove entries this script installed that are no longer wanted."""
    if not target.is_dir():
        return
    why = "uninstall" if args.uninstall else "no longer in repo"
    for entry in sorted(target.iterdir()):
        if entry.name in keep or entry.name.endswith(".brainpack-tmp") or not is_managed(entry):
            continue
        if not entry.is_symlink() and not unchanged_since_install(entry):
            reason = f"{why}, but the installed copy was edited"
            if not args.force:
                conflicts.append((agent, entry.name, entry, None, reason))
                counts["skipped"] = counts.get("skipped", 0) + 1
                print(f"  {entry.name:<30} SKIPPED: {reason}")
                continue
            why = f"{why} (--force, copy was edited)"
        if not args.dry_run:
            remove(entry)
        counts["removed"] = counts.get("removed", 0) + 1
        print(f"  {entry.name:<30} {say(args, 'removed', 'will remove')}: {why}")


def sync_agent(agent, args, counts):
    target = Path(args.home).expanduser() / AGENTS[agent]["target"]
    skills = {} if args.uninstall else skills_for(agent)
    if args.list or args.uninstall:
        how = ""
    elif args.copy:
        how = " (copies)"
    else:
        how = f" ({'relative' if args.relative else 'absolute'} symlinks to repo)"
    print(f"\n[{agent}] {target}{how}")

    if args.list:
        for name, src in skills.items():
            print(f"  {name:<30} {src.relative_to(REPO)}")
        if not skills:
            print("  (no skills)")
        return

    if not args.dry_run:
        target.mkdir(parents=True, exist_ok=True)

    for name, src in skills.items():
        key, status = install_skill(agent, name, src, target / name, args)
        counts[key] = counts.get(key, 0) + 1
        print(f"  {name:<30} {status}")

    prune(agent, target, set(skills), args, counts)


def report_summary(counts, args):
    order = ["installed", "updated", "up to date", "overwritten", "removed", "skipped"]
    parts = [f"{counts[k]} {k}" for k in order if counts.get(k)]
    if parts:
        prefix = "Plan: " if args.dry_run else "Done: "
        print(prefix + ", ".join(parts))
    if args.dry_run:
        print("DRY RUN: nothing was changed.")


def report_conflicts():
    if not conflicts:
        return
    print("\n" + "=" * 70)
    print(f"{len(conflicts)} skill(s) skipped, resolve by hand:\n")
    for agent, name, installed, repo, reason in conflicts:
        print(f"[{agent}] {name}: {reason}")
        print(f"    installed: {installed}")
        if repo:
            print(f"    repo:      {repo}")
            print(f"    compare:   diff -r '{repo}' '{installed}'")
        print()
    print("After resolving, re-run the script, or use --force to overwrite.")


def main():
    parser = argparse.ArgumentParser(
        description="Install agent-brainpack skills into Claude Code and Codex.")
    parser.add_argument("--agent", choices=sorted(AGENTS), action="append",
                        help="agent to install for (repeatable, default: all)")
    parser.add_argument("--copy", action="store_true",
                        help="copy skills instead of symlinking")
    parser.add_argument("--relative", action="store_true",
                        help="use relative symlinks (handy when home and repo are mounted together)")
    parser.add_argument("--force", action="store_true",
                        help="replace or remove conflicting skills anyway")
    parser.add_argument("--uninstall", action="store_true",
                        help="remove skills installed by this script")
    parser.add_argument("--list", action="store_true",
                        help="show which skills each agent gets, change nothing")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would happen, change nothing")
    parser.add_argument("--home", default=str(Path.home()),
                        help="home directory to install into (default: current user's)")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN: showing what would happen, nothing will be changed.")
    counts = {}
    for agent in args.agent or sorted(AGENTS):
        sync_agent(agent, args, counts)
    print()
    if not args.list:
        report_summary(counts, args)
    report_conflicts()
    sys.exit(1 if conflicts else 0)


if __name__ == "__main__":
    main()
