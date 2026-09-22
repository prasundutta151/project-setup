"""Create and inspect an external data workspace for an existing project."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Iterable, Optional

VERSION = "1.1.0"
DEFAULT_ROOT = Path("/Volumes/Work/Data")
CONFIG_NAME = "data-path.json"
DEFAULT_SUBFOLDERS = ("raw", "processed", "outputs", "cache")


def project_path(value: Optional[str], parent: Optional[Path] = None) -> Path:
    if value is None:
        path = Path.cwd()
    elif "/" not in value and "\\" not in value and value not in (".", "..", "~"):
        path = (parent or Path.home() / "Documents") / value
    else:
        path = Path(value).expanduser()
    path = path.resolve()
    if not path.is_dir() or not path.name:
        raise ValueError(f"Project directory does not exist: {path}")
    return path


def valid_subfolder(value: str) -> str:
    if not value or value in (".", "..") or "/" in value or "\\" in value or "\x00" in value:
        raise argparse.ArgumentTypeError("subfolder names must be single directory names")
    return value


def valid_tree_path(value: str) -> str:
    parts = value.split("/")
    if not value or any(part in (".", "..", "") or "\\" in part or "\x00" in part for part in parts):
        raise ValueError("setup-tree entries must be relative directory paths")
    for part in parts:
        valid_subfolder(part)
    return value


def _tree_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _tree_values(item)
    elif isinstance(value, dict):
        for key, child in value.items():
            if key in ("name", "description", "version"):
                continue
            if key == "subfolders":
                yield from _tree_values(child)
            else:
                yield key
                yield from _tree_values(child)


def read_tree(path: Path) -> list[str]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Setup-tree file not found or is a symlink: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Cannot read setup-tree file: {exc}")
    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        decoded = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if isinstance(decoded, dict) and "subfolders" not in decoded and "tree" in decoded:
        decoded = decoded["tree"]
    folders = list(dict.fromkeys(valid_tree_path(name) for name in _tree_values(decoded)))
    if not folders:
        raise ValueError(f"Setup-tree file contains no subfolders: {path}")
    return folders


def config_file(project: Path, requested: Optional[Path], for_show: bool = False) -> Path:
    if requested:
        path = requested.expanduser()
        if path.is_dir():
            path = path / CONFIG_NAME
        return path.resolve()
    preferred = project / CONFIG_NAME
    if preferred.is_file():
        return preferred
    candidates = sorted(project.glob("*.json")) if for_show else []
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValueError("More than one JSON file is present; supply --json FILE or DIRECTORY")
    return preferred


def read_config(project: Path, requested: Optional[Path] = None) -> Optional[dict[str, Any]]:
    path = config_file(project, requested, for_show=True)
    if path.is_symlink():
        raise ValueError(f"Refusing a symbolic-link configuration: {path}")
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON configuration {path}: {exc}")
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported or invalid data-path.json schema")
    for key in ("project_path", "data_root", "data_path"):
        if not isinstance(data.get(key), str) or not Path(data[key]).is_absolute():
            raise ValueError("Invalid configuration field: " + key)
    folders = data.get("subfolders")
    if not isinstance(folders, list) or any(not isinstance(f, str) for f in folders):
        raise ValueError("Invalid subfolders in configuration")
    for folder in folders:
        valid_tree_path(folder)
    if data["project_path"] != str(project):
        raise ValueError("Project location differs from its recorded path; review the JSON before continuing")
    if data["data_path"] != str(Path(data["data_root"]) / project.name):
        raise ValueError("Recorded data path does not match data root and project name")
    return data


def setup(project: Path, destination: Optional[str] = None, subfolders: Optional[list[str]] = None,
          tree_file: Optional[Path] = None, json_path: Optional[Path] = None,
          dry_run: bool = False) -> dict[str, Any]:
    old = read_config(project, json_path)
    root = Path(destination).expanduser().absolute() if destination else Path(old["data_root"]) if old else DEFAULT_ROOT
    if len(root.parts) >= 3 and root.parts[1] == "Volumes" and not os.path.ismount(Path(*root.parts[:3])):
        raise ValueError(f"Volume is not mounted: {Path(*root.parts[:3])}. Mount it or pass --destination.")
    root = root.resolve()
    data_path = root / project.name
    if old and str(data_path) != old["data_path"]:
        raise ValueError(f"Project is already configured at {old['data_path']}; relocation is not performed")
    if data_path == project or project in data_path.parents or data_path in project.parents:
        raise ValueError("Data directory and project directory must be separate, not nested")
    if tree_file:
        selected = read_tree(tree_file)
    elif subfolders:
        selected = list(subfolders)
    elif old:
        selected = list(old["subfolders"])
    else:
        selected = list(DEFAULT_SUBFOLDERS)
    folders = list(dict.fromkeys(selected))
    if old:
        folders = list(dict.fromkeys(old["subfolders"] + folders))
    for folder in folders:
        valid_tree_path(folder)
    for path in [data_path] + [data_path / folder for folder in folders]:
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"Expected an ordinary directory, found a file or symlink: {path}")
    config = {"schema_version": 1, "project_data_version": VERSION, "project_name": project.name,
              "project_path": str(project), "data_root": str(root), "data_path": str(data_path),
              "subfolders": folders,
              "created_at": old["created_at"] if old and "created_at" in old else dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    if not dry_run:
        target = config_file(project, json_path)
        if project != target.parent and project not in target.parent.parents:
            raise ValueError("--json must name a file or directory inside the project")
        fd, staging = tempfile.mkstemp(prefix=".data-path-", suffix=".tmp", dir=project)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            data_path.mkdir(parents=True, exist_ok=True)
            for folder in folders:
                (data_path / folder).mkdir(parents=True, exist_ok=True)
            os.replace(staging, target)
        finally:
            Path(staging).unlink(missing_ok=True)
    return config


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", help="legacy positional project name or explicit project path")
    parser.add_argument("--project", help="project name or explicit project path")
    parser.add_argument("--proj-dir", default=".", help="parent directory for --project; default current directory")
    parser.add_argument("--destination", metavar="PATH", help="external data root; project name is appended")
    parser.add_argument("--subfolders", nargs="+", type=valid_subfolder, metavar="NAME")
    parser.add_argument("--proj-dir-like", type=Path, metavar="FILE", help="JSON or text setup-tree file defining subfolders")
    parser.add_argument("--json", type=Path, metavar="FILE_OR_DIR", help="configuration JSON file or directory containing data-path.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show", action="store_true", help="show settings; --json selects the file, otherwise one JSON in the project is used")
    parser.add_argument("--version", action="version", version="project-data " + VERSION)
    args = parser.parse_args(argv)
    if args.name and args.project:
        parser.error("use either the positional project name or --project")
    name = args.project or args.name
    try:
        project = project_path(name, Path(args.proj_dir).expanduser().resolve() if name else None)
        if args.show:
            if args.destination or args.subfolders or args.proj_dir_like or args.dry_run:
                parser.error("--show cannot be combined with setup options")
            config = read_config(project, args.json)
            if config is None:
                raise ValueError("No JSON configuration found; supply --json FILE or create one first")
            print(json.dumps(config, indent=2) if args.json and args.json.suffix.lower() == ".json" else config["data_path"])
            return 0
        config = setup(project, args.destination, args.subfolders, args.proj_dir_like, args.json, args.dry_run)
        if args.json and args.json.suffix.lower() == ".json":
            print(json.dumps(config, indent=2))
        else:
            print("Preview only" if args.dry_run else "Data workspace ready")
            print("Project: " + config["project_path"])
            print("Data: " + config["data_path"])
            print("Subfolders: " + ", ".join(config["subfolders"]))
            print("Configuration: " + str(config_file(project, args.json)))
        return 0
    except (OSError, ValueError, argparse.ArgumentTypeError) as exc:
        print("project-data: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
