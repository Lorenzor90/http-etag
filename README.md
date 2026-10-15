# http-etag

Parses and compares HTTP `ETag` and `If-None-Match` headers, handling weak validators (`W/` prefix), quoted opaque tags, and comma-separated lists.

## Usage

```python
from http_etag import parse_etag, parse_if_none_match, matches

resource_etag = '"v3"'
inm = 'W/"v1", "v3"'

if matches(inm, resource_etag):
    # precondition met → respond 304 Not Modified
    ...
else:
    # send the full representation with its ETag header
    ...

# inspect individual validators
parse_etag('W/"v1"')         # (True, "v1")
parse_if_none_match('*')     # ['*']
parse_if_none_match('"a", "b"')  # [(False, 'a'), (False, 'b')]
```

Exported names: `parse_etag`, `parse_if_none_match`, `matches`.

## Why this exists

A 304 Not Modified response is only correct when the server genuinely knows the client\'s cached representation is still current. The check is a two-step dance: parse the client\'s `If-None-Match` list and compare each entry against the resource\'s current `ETag`. Doing this by hand misses edge cases — commas inside quoted tags, the `*` wildcard, weak prefixes, and whitespace tolerated by real clients.

This library does exactly that parse-and-compare and nothing else. It does not generate ETags, compute hashes, or set headers.

## The comparison rule (a deliberate choice)

`matches` uses **strong comparison only**. A weak validator in `If-None-Match` only matches a weak `ETag` with the identical tag content; a strong `ETag` never matches a weak entry in the list, and vice versa.

RFC 9110 permits weak comparison for `If-None-Match`, which would let `W/"v1"` in the list match a strong `"v1"` resource. This library does not do that. The rationale: in practice clients send strong validators in `If-None-Match`, and accepting weak-to-strong matches would mask genuine content changes (a weak validator signals the representation may differ semantically even if the bytes are "close enough"). If you need RFC-liberal weak comparison, this is the wrong library and that is by design.

## Edge cases worth knowing

- `parse_if_none_match("*")` returns `["*"]` — the literal string sentinel, not a tuple. Callers should check for it before treating entries as `(weak, tag)` pairs. `matches` handles this internally.
- Commas inside quoted tags (`"a,b"`) are preserved; the list splitter is quote-aware.
- Invalid items in a comma-separated list are silently skipped rather than raising, because real-world headers are messy and a single malformed entry should not prevent a valid one from matching.
- An empty or missing `If-None-Match` never matches — the precondition is simply absent.
