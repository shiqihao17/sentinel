import hashlib
import hmac


def verify_alchemy_webhook_signature(
    payload: bytes,
    signature: str | None,
    secret: str | None,
) -> bool:
    if not signature or not secret:
        return False

    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    normalized_signature = signature.removeprefix("sha256=")
    return hmac.compare_digest(expected, normalized_signature)
