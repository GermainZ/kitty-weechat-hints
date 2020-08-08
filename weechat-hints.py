# Must be equal to the values of `weechat.look.separator_vertical` and
# `weechat.look.prefix_suffix`.
SEPARATOR = "│"
# How many separators to skip. For very narrow terminals or if you don't use a
# bufflist, you should probably set this to 2.
SEPARATOR_SKIP_COUNT = 3
# How many characters to skip when the last separator (before the continuation
# of a message) is reached. For very narrow terminals, you should probably set
# this to 0 as WeeChat doesn't insert spaces after the separator in that case.
SEPARATOR_SUFFIX_SKIP_COUNT = 1


def extract_url(text, pos, url_prefix):
    """Extracts URL from `text` at `pos`, ignoring WeeChat's chrome."""
    url = ""
    prefix_pos = 0
    start_pos = pos
    reached_next_message = False
    while True:
        if pos >= len(text):
            break
        # We're at the end of the message on this line / start of the nicklist.
        # We should keep skipping characters until we reach the start of the
        # wrapped message on the next line.
        if (text[pos] == " " and text[pos + 1] == SEPARATOR) or text[pos] == "\n":
            count = 1 if text[pos] == "\n" else 0
            old_pos = pos
            while True:
                pos += 1
                if pos >= len(text):
                    break
                if text[pos] == SEPARATOR:
                    # When a line is wrapped, the nick/nick prefix is not
                    # shown. If it is (i.e. if we don't find a space before the
                    # separator), then we've reached a new message and it's
                    # time to stop looking.
                    if count == SEPARATOR_SKIP_COUNT - 1 and text[pos - 2] != " ":
                        pos = old_pos
                        reached_next_message = True
                        break
                    count += 1
                    if count == SEPARATOR_SKIP_COUNT:
                        pos += 1 + SEPARATOR_SUFFIX_SKIP_COUNT  # Skip "| " portion.
                        break
        # The URL is over.
        elif text[pos] in [" ", "\0"]:
            break
        if pos >= len(text):
            break
        if reached_next_message:
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
        if not url:
            start_pos, end_pos, url = extract_url(text, start_pos, "http://")
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
