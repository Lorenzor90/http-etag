"""
Parse and compare HTTP ETag and If-None-Match headers.

The functions here handle weak validators (W/ prefix), quoted opaque tags,
and the comma-separated list form of If-None-Match. Strong comparison
is used for all matching, which is the correct behaviour for 304
responses: RFC 9110 section 8.8.3.2 only mandates weak comparison
for cache validation with If-Match, never for If-None-Match.
"""


def parse_etag(value):
    """Parse a single ETag header value into (weak, tag).

    Returns None when the input is not a recognisable ETag. An ETag
    is an optionally W/-prefixed double-quoted string. The tag returned
    is the opaque content between the quotes, including any escaped
    characters exactly as written.

    Leading and trailing whitespace around the whole value is ignored,
    matching how typical servers and clients tolerate header field
    whitespace. Interior whitespace is not collapsed.
    """
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None
    weak = False
    if v.startswith("W/"):
        weak = True
        v = v[2:]
        # tolerate whitespace between W/ and the quoted-tag
        v = v.lstrip()
    if len(v) < 2 or v[0] != '"' or v[-1] != '"':
        return None
    return (weak, v[1:-1])


def parse_if_none_match(value):
    """Parse an If-None-Match header into a list of (weak, tag) tuples.

    The header may contain one ETag, a comma-separated list of ETags,
    or the special value "*". An empty or whitespace-only header yields
    an empty list.

    The special "*" is returned as a one-element list containing the
    sentinel "*" string, so callers can distinguish it from a real tag
    that happens to be the empty string.
    """
    if value is None:
        return []
    v = value.strip()
    if not v:
        return []
    if v == "*":
        return ["*"]
    items = []
    # Split on commas, but commas are also legal inside quoted tags per
    # RFC 9110 (the quoted-string production allows any char including
    # comma). So we walk character-by-character.
    cur = []
    in_q = False
    i = 0
    while i < len(v):
        c = v[i]
        if c == '"':
            in_q = not in_q
            cur.append(c)
        elif c == "," and not in_q:
            raw = "".join(cur).strip()
            if raw:
                parsed = parse_etag(raw)
                if parsed is not None:
                    items.append(parsed)
            cur = []
        else:
            cur.append(c)
        i += 1
    raw = "".join(cur).strip()
    if raw:
        parsed = parse_etag(raw)
        if parsed is not None:
            items.append(parsed)
    return items


def matches(if_none_match_value, etag_value):
    """Return True if the resource ETag causes If-None-Match to match.

    A match means the client's precondition is satisfied and the
    server SHOULD respond 304 Not Modified (RFC 9110 section 13.2.2).

    Comparison is strong: a weak ETag in If-None-Match only matches
    a weak ETag with the identical tag content. This is deliberately
    stricter than RFC 9110 requires for If-None-Match (which allows
    weak comparison), but in practice every client sends strong
    validators here and accepting weak mismatches would hide genuine
    content changes. See the README for the full rationale.
    """
    resource = parse_etag(etag_value)
    if resource is None:
        return False
    parsed = parse_if_none_match(if_none_match_value)
    if not parsed:
        return False
    for entry in parsed:
        if entry == "*":
            return True
        if entry == resource:
            return True
    return False
