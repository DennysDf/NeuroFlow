from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def normalize_cpf(value: str | None) -> str:
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isdigit())


def format_cpf(cpf: str) -> str:
    cpf = normalize_cpf(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[0:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"


def validate_cpf(value: str | None) -> bool:
    cpf = normalize_cpf(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def _digit(prefix: str, weights: range) -> int:
        total = sum(int(d) * w for d, w in zip(prefix, weights))
        rem = total % 11
        return 0 if rem < 2 else 11 - rem

    d1 = _digit(cpf[:9], range(10, 1, -1))
    d2 = _digit(cpf[:9] + str(d1), range(11, 1, -1))
    return cpf[-2:] == f"{d1}{d2}"
