from weechat_hints import get_urls


def test_hint_urls(input_text, expected_urls):
    results = [result[2] for result in get_urls(input_text)]
    assert results == expected_urls

def test_hint_positions(input_text, expected_urls):
    hints = [input_text[result[0]:result[1]] for result in get_urls(input_text)]
    for hint, url in zip(hints, expected_urls):
        assert hint[0] == url[0] and hint[-1] == url[-1], f'{hint=} {url=}'
