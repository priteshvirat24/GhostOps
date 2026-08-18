import re

# Regular expressions for common secret patterns
AWS_KEY_REGEX = re.compile(r'(?i)(?:aws_access_key_id|aws_secret_access_key|secret_key|access_key|secret)\s*[:=]\s*["\']?([A-Za-z0-9/+=]{16,40})["\']?')
AKIA_REGEX = re.compile(r'AKIA[0-9A-Z]{16}')
BEARER_TOKEN_REGEX = re.compile(r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*')
PRIVATE_KEY_REGEX = re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----')
PASSWORD_PARAM_REGEX = re.compile(r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s&]+)["\']?')

def redact_secrets(text: str) -> str:
    """
    Redacts sensitive credentials, tokens, and private keys from string text
    before passing to embedding generation or external systems.
    Authoritative raw evidence remains untouched in raw storage.
    """
    if not text:
        return ""

    redacted = text
    redacted = PRIVATE_KEY_REGEX.sub("[REDACTED_PRIVATE_KEY]", redacted)
    redacted = AKIA_REGEX.sub("[REDACTED_AWS_KEY_ID]", redacted)
    redacted = AWS_KEY_REGEX.sub("secret=[REDACTED_SECRET]", redacted)
    redacted = BEARER_TOKEN_REGEX.sub("Bearer [REDACTED_TOKEN]", redacted)
    redacted = PASSWORD_PARAM_REGEX.sub("password=[REDACTED_PASSWORD]", redacted)
    return redacted
