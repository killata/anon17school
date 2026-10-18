import hashlib
import hmac


def get_author_hash(user_id: int, secret_salt: str) -> str:
    """
    Transforms a telegram_user_id into an irreversible cryptographic HMAC-SHA256 hash.
    
    OpSec Principle:
    Raw telegram user_id, usernames, or first/last names are NEVER persisted
    in the database posts tables. Only this one-way salted hash is recorded.
    Even with a full SQL dump, an adversary cannot deduce student identities without
    brute-forcing the entire keyspace against the high-entropy salt.
    """
    return hmac.new(
        secret_salt.encode(),
        str(user_id).encode(),
        hashlib.sha256
    ).hexdigest()
