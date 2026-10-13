#!/usr/bin/env python3
"""Keep ~/Downloads and ~/Desktop empty.

Finds items in the two landing folders that are safe to send to the Trash
(an identical copy already lives in a home-directory topic folder, an installer
for an app that is already installed, a temporary file, an archive whose
contents already exist elsewhere, an empty folder) and moves files to their
homes with a log so every change can be undone.

    python3 scripts/tidy_inbox.py scan [--json PATH]   list items and verdicts
    python3 scripts/tidy_inbox.py trash --json PATH    trash the safe ones from a scan
    python3 scripts/tidy_inbox.py move SRC DEST_DIR    move one item, logging it

Nothing is deleted outright: trashing uses /usr/bin/trash, so Finder's
"Put Back" still works until the Trash is emptied. Items changed in the last
24 hours are left alone because they may still be in use.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import zipfile
import zlib

HOME = os.path.expanduser("~")
INBOXES = [os.path.join(HOME, "Downloads"), os.path.join(HOME, "Desktop")]
LOG = os.path.join(HOME, "AI-OS", "private", "tidy-inbox-log.tsv")
# Home folders that are never treated as a topic folder holding the "real" copy.
NOT_TOPIC = {"Downloads", "Desktop", "Library", "Applications", "Public", "node_modules"}
SKIP_DIRS = {"node_modules", ".git", "DerivedData", "Pods", ".venv", "venv", "__pycache__", ".expo"}
RECENT_SECONDS = 24 * 3600

INSTALLER = re.compile(r"\.(dmg|pkg|mpkg)$", re.I)
TEMP = re.compile(r"^~\$|\.(part|crdownload|download|crash|ips)$|^xcode-build-.*\.log$", re.I)
ARCHIVE = re.compile(r"\.zip$", re.I)


def nfc(s):
    return unicodedata.normalize("NFC", s)


def topic_roots():
    for name in sorted(os.listdir(HOME)):
        path = os.path.join(HOME, name)
        if name.startswith(".") or name in NOT_TOPIC or not os.path.isdir(path):
            continue
        yield path


def walk_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.endswith((".photoslibrary", ".imovielibrary", ".app"))
        ]
        for f in filenames:
            if f == ".DS_Store":
                continue
            p = os.path.join(dirpath, f)
            if os.path.islink(p):
                continue
            try:
                yield p, os.path.getsize(p)
            except OSError:
                pass


_sha = {}


def sha1(path):
    if path not in _sha:
        m = hashlib.sha1()
        with open(path, "rb") as fh:
            for block in iter(lambda: fh.read(1 << 22), b""):
                m.update(block)
        _sha[path] = m.hexdigest()
    return _sha[path]


def crc32(path):
    c = 0
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            c = zlib.crc32(block, c)
    return c & 0xFFFFFFFF


def installed_apps():
    names = set()
    for d in ("/Applications", os.path.join(HOME, "Applications")):
        if os.path.isdir(d):
            names.update(n.lower() for n in os.listdir(d))
    return names


def scan():
    now = time.time()
    items = []
    for inbox in INBOXES:
        for name in sorted(os.listdir(inbox)):
            if name in (".DS_Store", ".localized"):
                continue
            path = os.path.join(inbox, name)
            items.append({"path": path, "name": nfc(name), "dir": os.path.isdir(path),
                          "recent": now - os.lstat(path).st_mtime < RECENT_SECONDS})

    # Collect the sizes we need to look up, then index topic folders by size once.
    wanted = set()
    members = {}
    for it in items:
        p = it["path"]
        if it["dir"]:
            it["files"] = list(walk_files(p))
            wanted.update(s for _, s in it["files"] if s)
        elif ARCHIVE.search(p):
            try:
                with zipfile.ZipFile(p) as zf:
                    members[p] = [(i.file_size, i.CRC) for i in zf.infolist()
                                  if not i.is_dir() and i.file_size and "__MACOSX" not in i.filename
                                  and not i.filename.endswith(".DS_Store")]
            except (zipfile.BadZipFile, OSError):
                members[p] = None
            wanted.add(os.path.getsize(p))
            wanted.update(s for s, _ in members[p] or [])
        else:
            wanted.add(os.path.getsize(p))
    by_size = collections.defaultdict(list)
    for root in topic_roots():
        for p, s in walk_files(root):
            if s in wanted:
                by_size[s].append(p)

    def copy_elsewhere(path, size):
        for q in by_size.get(size, []):
            try:
                if sha1(q) == sha1(path):
                    return q
            except OSError:
                pass
        return None

    crcs = {}
    apps = installed_apps()
    for it in items:
        p, name = it["path"], it["name"]
        it["verdict"], it["detail"] = "sort", ""
        if it["recent"]:
            it["verdict"] = "recent"
        elif TEMP.search(name):
            it["verdict"] = "trash:temporary file"
        elif INSTALLER.search(name) or (name.endswith(".app") and name.lower() in apps):
            it["verdict"] = "trash:installer for an installed app"
        elif it["dir"]:
            files = [(f, s) for f, s in it.pop("files") if s]
            if not files:
                it["verdict"] = "trash:empty folder"
            else:
                hits = [copy_elsewhere(f, s) for f, s in files]
                if all(hits):
                    it["verdict"] = "trash:every file already exists elsewhere"
                    it["detail"] = os.path.dirname(hits[0]).replace(HOME, "~")
        else:
            size = os.path.getsize(p)
            hit = copy_elsewhere(p, size) if size else None
            if hit:
                it["verdict"], it["detail"] = "trash:identical copy exists", hit.replace(HOME, "~")
            elif members.get(p):
                for s, _ in members[p]:
                    for q in by_size.get(s, []):
                        if (s, q) not in crcs:
                            crcs[(s, q)] = crc32(q)
                found = {(s, crcs[(s, q)]) for s, _ in members[p] for q in by_size.get(s, [])}
                if all((s, c) in found for s, c in members[p]):
                    it["verdict"] = "trash:archive already extracted elsewhere"
        it.pop("files", None)
    return items


def log(action, src, dest):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as fh:
        fh.write("%s\t%s\t%s\t%s\n" % (time.strftime("%Y-%m-%d %H:%M"), action, src, dest))


def cmd_scan(args):
    items = scan()
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(items, fh, ensure_ascii=False, indent=1)
    for it in items:
        where = os.path.basename(os.path.dirname(it["path"]))
        extra = "  (%s)" % it["detail"] if it["detail"] else ""
        print("%-48s %s/%s%s" % (it["verdict"], where, it["name"], extra))
    counts = collections.Counter(i["verdict"].split(":")[0] for i in items)
    print("\ntrash %d, sort %d, recent %d" % (counts["trash"], counts["sort"], counts["recent"]))


def cmd_trash(args):
    with open(args.json) as fh:
        items = [i for i in json.load(fh) if i["verdict"].startswith("trash:") and os.path.lexists(i["path"])]
    for i in range(0, len(items), 100):
        batch = items[i:i + 100]
        subprocess.run(["/usr/bin/trash"] + [it["path"] for it in batch], check=False)
        for it in batch:
            if os.path.lexists(it["path"]):
                print("could not trash:", it["path"], file=sys.stderr)
            else:
                log("trash", it["path"], it["verdict"][6:])
    print("trashed", sum(not os.path.lexists(it["path"]) for it in items))


def cmd_move(args):
    src, dest = os.path.abspath(args.src), os.path.abspath(os.path.expanduser(args.dest_dir))
    if not os.path.lexists(src):
        sys.exit("missing: " + src)
    os.makedirs(dest, exist_ok=True)
    name = os.path.basename(src)
    stem, ext = (name, "") if os.path.isdir(src) else os.path.splitext(name)
    target, n = os.path.join(dest, name), 2
    while os.path.lexists(target):
        target, n = os.path.join(dest, "%s (%d)%s" % (stem, n, ext)), n + 1
    os.rename(src, target)
    log("move", src, target)
    print(target)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--json")
    s.set_defaults(fn=cmd_scan)
    t = sub.add_parser("trash")
    t.add_argument("--json", required=True)
    t.set_defaults(fn=cmd_trash)
    m = sub.add_parser("move")
    m.add_argument("src")
    m.add_argument("dest_dir")
    m.set_defaults(fn=cmd_move)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
