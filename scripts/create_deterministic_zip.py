"""Create a deterministic ZIP from a staged portable distribution."""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def iter_files(source_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in source_root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not permitted in a portable stage: {path}")
        if path.is_file():
            files.append(path)
    return sorted(
        files,
        key=lambda path: (
            path.relative_to(source_root).as_posix().casefold(),
            path.relative_to(source_root).as_posix(),
        ),
    )


def create_zip(source_root: Path, output_zip: Path) -> None:
    source_root = source_root.resolve()
    output_zip = output_zip.resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"Stage directory does not exist: {source_root}")
    if output_zip == source_root or source_root in output_zip.parents:
        raise ValueError("The output ZIP must not be inside the staged directory.")
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(
        output_zip,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for path in iter_files(source_root):
            relative = path.relative_to(source_root).as_posix()
            archive_name = f"{source_root.name}/{relative}"
            info = zipfile.ZipInfo(archive_name, date_time=FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0x20
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    create_zip(args.source_root, args.output)
    print(f"Created {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
