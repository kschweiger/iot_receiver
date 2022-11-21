from secrets import token_hex
from typing import Tuple

from passlib.context import CryptContext


def generate_token(nbytes: int) -> Tuple[str, str]:
    token = token_hex(nbytes)
    hashed_token = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(token)

    return token, hashed_token
