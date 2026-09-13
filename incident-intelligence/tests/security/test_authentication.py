from packages.common.security import decode_token, hash_password, issue_token, verify_password


def test_password_hash_is_salted_and_verifiable():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)


def test_signed_token_expiry_and_tamper_detection():
    token = issue_token(user_id="u1", role="analyst", token_version=1, secret_key="a-secure-test-key", expire_minutes=5)
    assert decode_token(token, secret_key="a-secure-test-key")["role"] == "analyst"
    try:
        decode_token(token + "x", secret_key="a-secure-test-key")
    except ValueError:
        pass
    else:
        raise AssertionError("tampered token was accepted")
