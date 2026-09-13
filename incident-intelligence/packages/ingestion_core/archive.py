from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

from .service import ALLOWED_EXTENSIONS, sha256_file


@dataclass(frozen=True)
class ExtractedEvidence:
    relative_path: str
    size_bytes: int
    sha256: str


def extract_safe_zip(
    archive_path: Path,
    destination: Path,
    *,
    max_files: int = 200,
    max_uncompressed_bytes: int = 500 * 1024 * 1024,
    max_compression_ratio: float = 100.0,
) -> dict:
    """Extract a ZIP without permitting traversal, links, bombs, or nested archives."""
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[ExtractedEvidence] = []
    total = 0
    with zipfile.ZipFile(archive_path) as archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) > max_files:
            raise ValueError("archive file-count limit exceeded")
        for member in members:
            path = PurePosixPath(member.filename)
            mode = member.external_attr >> 16
            if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(mode):
                raise ValueError(f"unsafe archive member: {member.filename}")
            if member.flag_bits & 0x1:
                raise ValueError("encrypted ZIP archives are not supported")
            suffix = path.suffix.lower()
            if suffix in {".zip", ".tar", ".gz", ".bz2", ".7z"}:
                raise ValueError("nested archives are not supported")
            if suffix not in ALLOWED_EXTENSIONS:
                raise ValueError(f"unsupported evidence file: {member.filename}")
            total += member.file_size
            if total > max_uncompressed_bytes:
                raise ValueError("archive uncompressed-size limit exceeded")
            ratio = member.file_size / max(member.compress_size, 1)
            if ratio > max_compression_ratio:
                raise ValueError("archive compression-ratio limit exceeded")
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with archive.open(member) as source, target.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    output.write(chunk)
            extracted.append(ExtractedEvidence(str(path), member.file_size, digest.hexdigest()))
    return {
        "archive_sha256": sha256_file(archive_path),
        "total_uncompressed_bytes": total,
        "files": [item.__dict__ for item in extracted],
    }
