from urllib.parse import urlsplit, urlunsplit


def fix_plus_in_url(url: str) -> str:
    """
    Replace raw '+' by '%2B' in URL paths only.
    Avoid touching query params or already-encoded values.
    """
    parts = urlsplit(url)

    # Replace '+' only in the path
    fixed_path = parts.path.replace("+", "%2B")

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            fixed_path,
            parts.query,
            parts.fragment,
        )
    )
