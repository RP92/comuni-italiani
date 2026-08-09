# src/comuni_italiani/cli.py
import csv
import json
import sys
import tomllib
import zipfile
from pathlib import Path

from comuni_italiani.changelog import diff_datasets
from comuni_italiani.download import fetch
from comuni_italiani.parse.anagrafica import parse_anagrafica
from comuni_italiani.parse.popolazione import parse_popolazione
from comuni_italiani.parse.superficie import parse_superficie
from comuni_italiani.parse.coordinate import parse_coordinate
from comuni_italiani.parse.cap import parse_cap
from comuni_italiani.merge import merge
from comuni_italiani.emit import emit
from comuni_italiani.validate import validate

SCHEMA_PATH = Path("data/schema.json")

def _read_rows(spec: dict, cache_dir: Path, offline: bool) -> list[dict]:
    if "path" in spec:
        path = Path(spec["path"])
    else:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = fetch(spec["url"], cache_dir / spec["cache"], force=False) if not offline else cache_dir / spec["cache"]
    encoding = spec.get("encoding", "utf-8")
    is_zip = "member" in spec or (path.exists() and path.read_bytes()[:4] == b"PK\x03\x04")
    if is_zip:
        with zipfile.ZipFile(path) as zf:
            if "member" in spec:
                available = zf.namelist()
                if spec["member"] not in available:
                    raise ValueError(
                        f"ZIP {path.name} has no member {spec['member']!r}; "
                        f"available: {available}"
                    )
                member_name = spec["member"]
            else:
                names = [n for n in zf.namelist() if n.endswith(".csv") or n.endswith(".txt")]
                if len(names) == 0:
                    raise ValueError(
                        f"ZIP {path.name} has no CSV/TXT member; specify 'member' in the source spec"
                    )
                if len(names) > 1:
                    raise ValueError(
                        f"ZIP {path.name} has multiple CSV/TXT members {names}; specify 'member' in the source spec"
                    )
                member_name = names[0]
            text = zf.read(member_name).decode(encoding)
    else:
        text = path.read_text(encoding=encoding)
    reader = csv.DictReader(text.splitlines(), delimiter=spec.get("delimiter", ";"))
    rows = list(reader)
    remap = spec.get("columns")
    if remap:
        fieldnames = reader.fieldnames or []
        for new, old in remap.items():
            if old not in fieldnames:
                raise ValueError(
                    f"source column {old!r} not found in header {fieldnames}"
                )
        rows = [r | {new: r.get(old, "") for new, old in remap.items()} for r in rows]
    return rows

def build(config: dict, cache_dir: Path, out_dir: Path, *, offline: bool = False,
          changelog_path=None) -> dict:
    cache_dir, out_dir = Path(cache_dir), Path(out_dir)
    anagrafica = parse_anagrafica(_read_rows(config["anagrafica"], cache_dir, offline))
    popolazione = parse_popolazione(_read_rows(config["popolazione"], cache_dir, offline))
    superficie = parse_superficie(_read_rows(config["superficie"], cache_dir, offline))
    coordinate = parse_coordinate(_read_rows(config["coordinate"], cache_dir, offline))
    cap = parse_cap(_read_rows(config["cap"], cache_dir, offline))

    comuni = merge(anagrafica, popolazione, superficie, coordinate, cap)

    # Read the previous dataset BEFORE emit() overwrites it
    prev_file = out_dir / "comuni.json"
    old = json.loads(prev_file.read_text(encoding="utf-8")) if prev_file.exists() else []

    emit(comuni, out_dir)
    report = validate(comuni, SCHEMA_PATH, min_count=len(comuni), max_count=len(comuni)) \
        if offline else validate(comuni, SCHEMA_PATH)
    (out_dir / "quality-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Update changelog if a path was provided
    if changelog_path is not None:
        changelog_path = Path(changelog_path)
        changes = diff_datasets(old, comuni)
        n_added = len(changes["added"])
        n_removed = len(changes["removed"])
        n_modified = len(changes["modified"])
        if n_added or n_removed or n_modified:
            section_lines = [
                "## [generated]\n",
                f"- Added: {n_added}\n",
                f"- Removed: {n_removed}\n",
                f"- Modified: {n_modified}\n",
            ]
            # Append short lists of codici if there are few entries
            if n_added and n_added <= 10:
                section_lines.append(f"  - added: {', '.join(changes['added'])}\n")
            if n_removed and n_removed <= 10:
                section_lines.append(f"  - removed: {', '.join(changes['removed'])}\n")
            if n_modified and n_modified <= 10:
                section_lines.append(f"  - modified: {', '.join(changes['modified'])}\n")
            section_lines.append("\n")
            new_section = "".join(section_lines)
            existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
            changelog_path.write_text(new_section + existing, encoding="utf-8")

    return report

def main(argv=None):
    argv = argv or sys.argv[1:]
    config_path = Path(argv[0]) if argv else Path("sources.toml")
    config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    report = build(config, cache_dir=Path(".cache"), out_dir=Path("data"),
                   changelog_path=Path("CHANGELOG.md"))
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
