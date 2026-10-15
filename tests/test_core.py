import unittest

from http_etag.core import parse_etag, parse_if_none_match, matches


class TestParseEtag(unittest.TestCase):
    def test_strong_quoted(self):
        self.assertEqual(parse_etag('"abc123"'), (False, "abc123"))

    def test_weak_prefix(self):
        self.assertEqual(parse_etag('W/"abc123"'), (True, "abc123"))

    def test_empty_tag_string(self):
        self.assertEqual(parse_etag('""'), (False, ""))

    def test_unquoted_value_returns_none(self):
        self.assertIsNone(parse_etag("abc123"))

    def test_none_input_returns_none(self):
        self.assertIsNone(parse_etag(None))

    def test_whitespace_around_value(self):
        self.assertEqual(parse_etag('  "xyz"  '), (False, "xyz"))

    def test_weak_with_space_after_slash(self):
        self.assertEqual(parse_etag('W/ "tag"'), (True, "tag"))

    def test_weak_prefix_without_closing_quote(self):
        self.assertIsNone(parse_etag('W/"tag'))

    def test_only_opening_quote(self):
        self.assertIsNone(parse_etag('"'))

    def test_preserves_escaped_quote_inside(self):
        self.assertEqual(parse_etag(r'"a\"b"'), (False, r'a\"b'))


class TestParseIfNoneMatch(unittest.TestCase):
    def test_none_input(self):
        self.assertEqual(parse_if_none_match(None), [])

    def test_empty_string(self):
        self.assertEqual(parse_if_none_match(""), [])

    def test_whitespace_only(self):
        self.assertEqual(parse_if_none_match("   "), [])

    def test_single_strong(self):
        self.assertEqual(parse_if_none_match('"v1"'), [(False, "v1")])

    def test_single_weak(self):
        self.assertEqual(parse_if_none_match('W/"v1"'), [(True, "v1")])

    def test_list_of_two(self):
        self.assertEqual(
            parse_if_none_match('"a", W/"b"'),
            [(False, "a"), (True, "b")],
        )

    def test_list_with_extra_whitespace(self):
        self.assertEqual(
            parse_if_none_match(' "a" ,  W/"b" '),
            [(False, "a"), (True, "b")],
        )

    def test_star(self):
        self.assertEqual(parse_if_none_match("*"), ["*"])

    def test_comma_inside_quotes_is_not_split(self):
        self.assertEqual(
            parse_if_none_match('"a,b"'),
            [(False, "a,b")],
        )

    def test_empty_item_in_list_is_skipped(self):
        self.assertEqual(
            parse_if_none_match('"a", , "b"'),
            [(False, "a"), (False, "b")],
        )

    def test_invalid_items_skipped_valid_kept(self):
        self.assertEqual(
            parse_if_none_match('broken, "ok", also-broken'),
            [(False, "ok")],
        )


class TestMatches(unittest.TestCase):
    def test_star_matches_anything(self):
        self.assertTrue(matches("*", '"anything"'))

    def test_exact_strong_match(self):
        self.assertTrue(matches('"v1"', '"v1"'))

    def test_strong_does_not_match_weak_same_tag(self):
        # Strong comparison: a strong validator never equals a weak one.
        self.assertFalse(matches('"v1"', 'W/"v1"'))

    def test_weak_matches_weak_same_tag(self):
        self.assertTrue(matches('W/"v1"', 'W/"v1"'))

    def test_weak_in_list_does_not_match_strong_resource(self):
        self.assertFalse(matches('W/"v1"', '"v1"'))

    def test_list_first_match_wins(self):
        self.assertTrue(matches('"v1", "v2"', '"v1"'))

    def test_list_second_match(self):
        self.assertTrue(matches('"v1", "v2"', '"v2"'))

    def test_no_match(self):
        self.assertFalse(matches('"v1"', '"v2"'))

    def test_empty_if_none_match_never_matches(self):
        self.assertFalse(matches("", '"v1"'))

    def test_none_if_none_match_never_matches(self):
        self.assertFalse(matches(None, '"v1"'))

    def test_invalid_resource_etag_never_matches(self):
        self.assertFalse(matches('"v1"', 'not-an-etag'))

    def test_star_does_not_match_invalid_resource(self):
        self.assertFalse(matches("*", "not-an-etag"))

    def test_list_with_weak_and_strong_strong_resource(self):
        # Resource is strong v1; list has weak v1 (no match) and strong v2 (no match).
        self.assertFalse(matches('W/"v1", "v2"', '"v1"'))


if __name__ == "__main__":
    unittest.main()
