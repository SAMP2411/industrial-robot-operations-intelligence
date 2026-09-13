from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def test_backup_restore_scripts_are_strict_checksum_and_encryption_aware():
    for name in ("backup.sh", "restore.sh"):
        path = ROOT / "deployment/on_prem" / name
        subprocess.run(["bash", "-n", str(path)], check=True)
        text = path.read_text()
        assert "set -euo pipefail" in text
        assert "SHA256SUMS" in text
        assert "age" in text
    assert "sha256sum --check" in (ROOT / "deployment/on_prem/restore.sh").read_text()


def test_backup_manifest_uses_paths_valid_from_inside_backup_directory():
    text = (ROOT / "deployment/on_prem/backup.sh").read_text()
    assert '(cd "$destination" && sha256sum database.sql evidence.tar.gz >SHA256SUMS)' in text
    assert '(cd "$destination" && sha256sum database.sql.age evidence.tar.gz.age >SHA256SUMS)' in text
    assert 'sha256sum "$destination/database.sql"' not in text
