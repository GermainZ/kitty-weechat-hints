SEPARATOR = "│"


def extract_url(text, pos, url_prefix):
    """Extracts URL from `text` at `pos`, ignoring WeeChat's chrome."""
    url = ""
    prefix_pos = 0
    start_pos = pos
    while True:
        if pos >= len(text):
            break
        # We're at the end of the message on this line / start of the nicklist.
        # We should keep skipping characters until we reach the start of the
        # wrapped message on the next line.
        if (text[pos] == " " and text[pos + 1] == SEPARATOR) or text[pos] == "\n":
            count = 1 if text[pos] == "\n" else 0
            while True:
                pos += 1
                if pos >= len(text):
                    break
                if text[pos] == SEPARATOR:
                    count += 1
                    if count == 3:
                        pos += 2  # Skip "| " portion.
                        break
        # The URL is over.
        elif text[pos] in [" ", "\0"]:
            break
        if pos >= len(text):
            break
        # If the prefix (e.g. "https://") isn't matched, stop searching.
        if prefix_pos < len(url_prefix) - 1 and text[pos] != url_prefix[prefix_pos]:
            break
        # This is the real start of a potential URL match (i.e. ignoring
        # WeeChat decoration).
        if prefix_pos == 0:
            start_pos = pos
        url += text[pos]
        prefix_pos += 1
        pos += 1
    # Is the text we found actually a URL?
    if not url.startswith(url_prefix):
        url = None
    return start_pos, pos, url


def mark(text, args, Mark, extra_cli_args, *a):
    idx = 0
    start_pos = 0
    while start_pos < len(text):
        # Extract URL, if any.
        start_pos, end_pos, url = extract_url(text, start_pos, "https://")
        if url:
            # Return mark info for kitty.
            yield Mark(idx, start_pos, end_pos, url, {})
            idx += 1
            start_pos = end_pos
        start_pos += 1


def handle_result(args, data, target_window_id, boss, extra_cli_args, *a):
    matches, groupdicts = [], []
    for m, g in zip(data["match"], data["groupdicts"]):
        if m:
            matches.append(m), groupdicts.append(g)
    for match, match_data in zip(matches, groupdicts):
        boss.open_url(match)
