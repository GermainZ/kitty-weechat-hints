from weechat_hints import get_urls


def test_hints(input_text, expected_urls):
    results = [result[2] for result in get_urls(input_text)]
    assert results == list(expected_urls)
