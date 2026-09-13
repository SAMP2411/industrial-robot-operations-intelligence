from scripts.anonymize_dataset import anonymize_text, pseudonym


def test_pseudonyms_are_stable_and_preserve_relationships():
    secret = b"test-secret-long-enough"
    text = "ops@example.com connected robot-alpha to 10.1.2.3 via AA:BB:CC:DD:EE:FF; site Blue Warehouse"
    first, mapping = anonymize_text(text, secret, ["Blue Warehouse"])
    second, _ = anonymize_text(text, secret, ["Blue Warehouse"])
    assert first == second
    assert all(value not in first for value in ("ops@example.com", "10.1.2.3", "AA:BB:CC:DD:EE:FF", "Blue Warehouse"))
    assert mapping["ops@example.com"] == pseudonym("EMAIL", "ops@example.com", secret)
    repeated, _ = anonymize_text("ops@example.com ops@example.com", secret)
    assert repeated.split()[0] == repeated.split()[1]
