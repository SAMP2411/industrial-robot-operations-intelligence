from __future__ import annotations

import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidTag


MAGIC = b"RFII-AESGCM-1\n"


def encrypt_file(source: Path, destination: Path, *, key: bytes, key_id: str) -> None:
    if len(key) not in {16, 24, 32} or not key_id:
        raise ValueError("AES-GCM requires a 128/192/256-bit key and non-empty external key identifier")
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    key_bytes = key_id.encode()
    with source.open("rb") as input_stream, destination.open("xb") as output:
        output.write(MAGIC); output.write(len(key_bytes).to_bytes(2, "big")); output.write(key_bytes); output.write(nonce)
        while chunk := input_stream.read(1024 * 1024): output.write(encryptor.update(chunk))
        output.write(encryptor.finalize()); output.write(encryptor.tag)


def decrypt_file(source: Path, destination: Path, *, key: bytes, expected_key_id: str) -> None:
    with source.open("rb") as input_stream:
        if input_stream.read(len(MAGIC)) != MAGIC: raise ValueError("invalid encrypted evidence header")
        key_id = input_stream.read(int.from_bytes(input_stream.read(2), "big")).decode()
        if key_id != expected_key_id: raise ValueError(f"evidence requires key identifier {key_id}")
        nonce = input_stream.read(12)
        ciphertext_end = source.stat().st_size - 16
        input_stream.seek(ciphertext_end); tag = input_stream.read(16); input_stream.seek(len(MAGIC) + 2 + len(key_id.encode()) + 12)
        decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
        try:
            with destination.open("xb") as output:
                remaining = ciphertext_end - input_stream.tell()
                while remaining:
                    chunk = input_stream.read(min(1024 * 1024, remaining)); remaining -= len(chunk); output.write(decryptor.update(chunk))
                output.write(decryptor.finalize())
        except InvalidTag as exc:
            destination.unlink(missing_ok=True)
            raise ValueError("encrypted evidence integrity verification failed") from exc
