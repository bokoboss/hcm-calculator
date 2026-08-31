"""Remove package test helpers from the internal portable application payload."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from pathlib import PurePosixPath


TEST_DIRECTORY_NAMES = {"test", "tests"}
UNWANTED_APP_DIRECTORY_NAMES = {".agents", ".git", ".github", ".pytest_cache"}
UNWANTED_APP_TOP_LEVEL_DIRECTORIES = {"bin"}
TEST_FILE_NAMES = {
    "pytest_plugin.py",
    "testclient.py",
    "testing.py",
    "test_cases.py",
}
RUNTIME_NON_PAYLOAD_DIRECTORIES = {
    "lib/ensurepip",
    "lib/idlelib",
    "lib/turtledemo",
    "lib/venv",
}
RUNTIME_NON_PAYLOAD_FILES = {
    "lib/doctest.py",
    "tcl/tcl8/8.5/tcltest-2.5.3.tm",
}


def is_test_payload(path: Path, app_root: Path) -> bool:
    relative = path.relative_to(app_root)
    parts = [part.casefold() for part in relative.parts]
    name = relative.name.casefold()
    if parts and parts[0] in UNWANTED_APP_TOP_LEVEL_DIRECTORIES:
        return True
    if any(part in UNWANTED_APP_DIRECTORY_NAMES for part in parts[:-1]):
        return True
    if any(part in TEST_DIRECTORY_NAMES for part in parts[:-1]):
        return True
    if name in TEST_FILE_NAMES:
        return True
    return name.startswith("test_") or name.endswith("_test.py")


def prune(app_root: Path) -> list[str]:
    app_root = app_root.resolve()
    if not app_root.is_dir():
        raise FileNotFoundError(f"Application stage does not exist: {app_root}")

    removed: list[str] = []
    for path in sorted(app_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if not is_test_payload(path, app_root):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not permitted in the application stage: {path}")
        if path.is_dir():
            path.rmdir()
        elif path.is_file():
            path.unlink()
        else:
            raise ValueError(f"Unsupported application-stage entry: {path}")
        removed.append(path.relative_to(app_root).as_posix())
    return sorted(removed)


def prune_stale_record_entries(app_root: Path) -> list[str]:
    """Remove RECORD rows for files intentionally absent from the stage."""

    app_root = app_root.resolve()
    changed: list[str] = []
    for record in sorted(app_root.rglob("RECORD")):
        if not record.parent.name.endswith(".dist-info"):
            continue
        rows = list(csv.reader(record.read_text(encoding="utf-8").splitlines()))
        kept: list[list[str]] = []
        removed = False
        for row in rows:
            if not row or not row[0]:
                kept.append(row)
                continue
            relative = PurePosixPath(row[0])
            candidate = (record.parent / Path(*relative.parts)).resolve()
            try:
                candidate.relative_to(app_root)
            except ValueError:
                exists_in_stage = False
            else:
                exists_in_stage = candidate.is_file()
            if exists_in_stage:
                kept.append(row)
            else:
                removed = True
        if not removed:
            continue
        with record.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerows(kept)
        changed.append(record.relative_to(app_root).as_posix())
    return changed


def prune_runtime(runtime_root: Path) -> list[str]:
    runtime_root = runtime_root.resolve()
    if not runtime_root.is_dir():
        raise FileNotFoundError(f"Runtime stage does not exist: {runtime_root}")

    removed: list[str] = []
    for path in sorted(runtime_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        relative = path.relative_to(runtime_root)
        normalized = "/".join(part.casefold() for part in relative.parts)
        remove = path.is_file() and path.suffix.casefold() == ".pdb"
        remove = remove or (
            path.is_file()
            and path.name.casefold().startswith("_test")
            and path.suffix.casefold() in {".dll", ".lib", ".pyd"}
        )
        remove = remove or normalized in RUNTIME_NON_PAYLOAD_FILES
        remove = remove or any(
            normalized == directory or normalized.startswith(directory + "/")
            for directory in RUNTIME_NON_PAYLOAD_DIRECTORIES
        )
        if not remove:
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not permitted in the runtime stage: {path}")
        if path.is_dir():
            path.rmdir()
        elif path.is_file():
            path.unlink()
        else:
            raise ValueError(f"Unsupported runtime-stage entry: {path}")
        removed.append(relative.as_posix())
    return sorted(removed)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path)
    args = parser.parse_args()
    removed = prune(args.app_root)
    print(f"Pruned {len(removed)} package test payload entries from {args.app_root.resolve()}")
    for relative in removed:
        print(f"  removed {relative}")
    record_files = prune_stale_record_entries(args.app_root)
    print(f"Pruned stale RECORD entries from {len(record_files)} distribution metadata files")
    for relative in record_files:
        print(f"  updated {relative}")
    if args.runtime_root:
        runtime_removed = prune_runtime(args.runtime_root)
        print(
            f"Pruned {len(runtime_removed)} non-runtime standalone payload entries "
            f"from {args.runtime_root.resolve()}"
        )
        for relative in runtime_removed:
            print(f"  removed runtime/{relative}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
