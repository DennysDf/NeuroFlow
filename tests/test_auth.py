from app.auth.services import hash_password, normalize_cpf, validate_cpf, verify_password


def test_validate_cpf_accepts_well_formed_cpf():
    assert validate_cpf("111.444.777-35") is True
    assert validate_cpf("11144477735") is True


def test_validate_cpf_rejects_repeated_digits():
    assert validate_cpf("00000000000") is False
    assert validate_cpf("12345678900") is False


def test_normalize_cpf():
    assert normalize_cpf("111.444.777-35") == "11144477735"
    assert normalize_cpf(None) == ""


def test_password_hash_roundtrip():
    h = hash_password("hunter2")
    assert verify_password(h, "hunter2") is True
    assert verify_password(h, "wrong") is False


def test_login_with_valid_cpf_and_password(client, world):
    res = client.post(
        "/login",
        data={"cpf": "111.444.777-35", "password": "Senha123!"},
        follow_redirects=False,
    )
    assert res.status_code in (302, 303)


def test_login_with_invalid_password(client, world):
    res = client.post(
        "/login",
        data={"cpf": "111.444.777-35", "password": "wrong"},
        follow_redirects=False,
    )
    assert res.status_code == 200
    assert b"incorretos" in res.data
