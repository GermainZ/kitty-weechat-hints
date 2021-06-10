#!/usr/bin/env python3
# vim:fileencoding=utf-8
# License: GPL v3 Copyright: 2021, Germain Z. <germanosz at gmail.com>
#                            2018, Kovid Goyal <kovid at kovidgoyal.net>
# pylint: disable=line-too-long

import collections
from dataclasses import dataclass, field
import itertools
import math
import re


# Must be equal to the values of `weechat.look.separator_vertical` and
# `weechat.look.prefix_suffix`.
WEECHAT_SEPARATOR = "│"

CONTEXT_CHARS = 5

# From <https://github.com/kovidgoyal/kitty/blob/2e7b68bf74f94622875679398365282f991cb1eb/kittens/hints/url_regex.py#L1>
# and <https://github.com/kovidgoyal/kitty/blob/8f491e7dbbe04abe913b45983c48e50c07ff00fa/kitty/options/types.py#L800>.
URL_DELIMITERS = "\x00-\x09\x0b-\x20\x7f-\xa0\xad\u0600-\u0605\u061c\u06dd\u070f\u08e2\u1680\u180e\u2000-\u200f\u2028-\u202f\u205f-\u2064\u2066-\u206f\u3000\ud800-\uf8ff\ufeff\ufff9-\ufffb\U000110bd\U000110cd\U00013430-\U00013438\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0001\U000e0020-\U000e007f\U000f0000-\U000ffffd\U00100000-\U0010fffd"
URL_PREFIXES = (
    "http",
    "https",
    "file",
    "ftp",
    "gemini",
    "irc",
    "gopher",
    "mailto",
    "news",
    "git",
)
REGEX = re.compile(rf"(?:{'|'.join(URL_PREFIXES)}):\/\/[^{URL_DELIMITERS}]{{3,}}")

CLOSING_BRACKET_MAP = {
    "(": ")",
    "[": "]",
    "{": "}",
    "<": ">",
    "*": "*",
    '"': '"',
    "'": "'",
}
OPENING_BRACKETS = "".join(CLOSING_BRACKET_MAP)


@dataclass
class TextAreaLine:
    text: str


@dataclass(frozen=True)
class TextAreaKey:
    start_col: int
    end_col: int


@dataclass
class TextArea:
    lines: list[TextAreaLine] = field(default_factory=list)
    len_line: int = 0


# postprocess_url() code from <https://github.com/kovidgoyal/kitty/blob/2e7b68bf74f94622875679398365282f991cb1eb/kittens/hints/main.py#L231>
def postprocess_url(text: str, s: int, e: int) -> tuple[int, int]:
    if s > 4 and text[s - 5 : s] == "link:":  # asciidoc URLs.
        url = text[s:e]
        idx = url.rfind("[")
        if idx > -1:
            e -= len(url) - idx
    while text[e - 1] in ".,?!" and e > 1:  # Remove trailing punctuation.
        e -= 1
    # Truncate url at closing bracket/quote.
    if s > 0 and e <= len(text) and text[s - 1] in OPENING_BRACKETS:
        q = CLOSING_BRACKET_MAP[text[s - 1]]
        idx = text.find(q, s)
        if idx > s:
            e = idx
    # Restructured Text URLs.
    if e > 3 and text[e - 2 : e] == "`_":
        e -= 2
    return s, e


def get_urls(text: str) -> list[tuple[int, int, str]]:
    results: list[tuple[int, int, str]] = []
    paddings: dict[int, dict[int, int]] = collections.defaultdict(dict)
    lines = text.splitlines()
    num_cols = len(lines[0])
    # Get the positions of the separators. We also take the start and end of
    # lines as separators.
    separators_positions_tmp: dict[int, set[int]] = collections.defaultdict(
        lambda: {0, num_cols}
    )
    for line_num, line in enumerate(lines):
        for col_num, char in enumerate(line):
            if char == WEECHAT_SEPARATOR:
                separators_positions_tmp[line_num].add(col_num)
    separators_positions: dict[int, list[int]] = {
        line_num: sorted(list(col_nums))
        for line_num, col_nums in separators_positions_tmp.items()
    }
    # An area exists between separators that seem consistent, for
    # example: the topic bar, the chat area, the nicklist, etc.
    # areas: dict[tuple[int, int], list[tuple[int, str]]] = collections.defaultdict(list)
    areas: dict[TextAreaKey, TextArea] = collections.defaultdict(TextArea)
    pos_separators: list[list[tuple[int, int]]] = [
        list(zip(pos, pos[1:])) for pos in separators_positions.values()
    ]
    all_areas_boundaries = list(set(itertools.chain(*pos_separators)))
    for line_num, col_nums in separators_positions.items():
        area_boundaries = list(zip(col_nums, col_nums[1:]))
        for area_start, area_end in all_areas_boundaries:
            padding_start = 0
            padding_end = 0
            if (area_start, area_end) in area_boundaries:
                line_paddings = paddings.get(line_num, {})
                for padding_col_num, col_padding in line_paddings.items():
                    if area_start > padding_col_num:
                        padding_start += col_padding
                    if area_end > padding_col_num:
                        padding_end += col_padding
            padding_start -= 1
            if lines[line_num][area_start + 1] == " ":
                padding_start -= 1
            if lines[line_num][area_end - 1] == " ":
                padding_end += 1
            # Add the line of text of the area.
            # If our area does not match the current area boundaries we are
            # checking, append an empty line instead.
            if (area_start, area_end) in area_boundaries:
                line = lines[line_num][
                    area_start - padding_start : area_end - padding_end
                ]
                area = areas[TextAreaKey(area_start, area_end)]
                area.lines.append(TextAreaLine(line))
                if len(line) > area.len_line:
                    area.len_line = len(line)
            else:
                # The empty string will be replaced with spaces later.
                areas[TextAreaKey(area_start, area_end)].lines.append(TextAreaLine(""))
    # For empty lines, replace '' with an appropriate number of spaces.
    # For lines that came up short (usually due to symbol withlen != wcwidth), pad them.
    for area in areas.values():
        for area_line in area.lines:
            if not area_line.text:
                area_line.text = " " * area.len_line
            if len(area_line.text) < area.len_line:
                area_line.text = f"{area_line.text:{area.len_line}}"
    # Check each area for URLs.
    # for (area_start, area_end), area in areas.items():
    for area_key, area in areas.items():
        area_start = area_key.start_col
        area_end = area_key.end_col
        len_line = area.len_line
        area_text = "".join([line.text for line in area.lines])
        # Match the concatenated text of the area for URLs.
        for match in REGEX.finditer(area_text):
            # For each match, we get its original starting/ending character positions.
            start_line_num = int(match.start() / len_line) + 1
            start_num_prev_lines = max(0, start_line_num - 1)
            start_char = match.start() - start_num_prev_lines * len_line
            end_line_num = int(match.end() / len_line) + 1
            end_num_prev_lines = max(0, end_line_num - 1)
            if match.end() % len_line == 0:
                end_num_prev_lines -= 1
            end_char = match.end() - end_num_prev_lines * len_line

            # If the URL is sent in message A and is just long enough to fill the full
            # line, then message B will be taken as the continuation since there are no
            # spaces between the two messages.  To handle that, we check if the weechat
            # prefix (nick) is empty or not. If not (meaning a new message has begun),
            # we decrease the end position accordingly and stop.
            url = match.group(0)
            for line_num in range(start_line_num + 1, end_line_num + 1):
                weechat_prefix = lines[line_num - 1][area_start - 2 : area_start]
                if weechat_prefix.strip():
                    end_line_num = line_num - 1
                    end_num_prev_lines = max(0, end_line_num - 1)
                    if end_char < len(url):
                        url = url[:-end_char]
                    end_char = len(area.lines[start_line_num - 1].text)
                    break

            padding_start = 1 if lines[start_line_num - 1][area_start + 1] == " " else 0
            padding_end = 1 if lines[start_line_num - 1][area_start + 1] == " " else 0

            global_start_char = (
                start_num_prev_lines * (num_cols + 1)  # Chars in previous lines
                + area_start  # Chars before the separator
                + 1  # Separator char
                + padding_start  # Padding
                + start_char  # Chars before the URL we matched
            )
            global_end_char = (
                end_num_prev_lines * (num_cols + 1)
                + area_start
                + 1
                + padding_end
                + end_char
            )
            start = global_start_char
            end = global_end_char
            # Postprocessing to handle things like trailing commas.
            context = area_text[match.start() - CONTEXT_CHARS : match.start()]
            url = f"{context: <{CONTEXT_CHARS}}{url}"
            _, end_diff = postprocess_url(url, CONTEXT_CHARS, len(url))
            end -= len(url) - end_diff

            results.append((start, end, url[CONTEXT_CHARS:end_diff]))

    return list(sorted(results))


def mark(text, args, Mark, extra_cli_args, *a):
    results = get_urls(text)
    for idx, (start_pos, end_pos, url) in enumerate(results):
        yield Mark(idx, start_pos, end_pos, url, {})


def handle_result(args, data, target_window_id, boss, extra_cli_args, *a):
    matches, groupdicts = [], []
    for match, group in zip(data["match"], data["groupdicts"]):
        if match:
            matches.append(match), groupdicts.append(group)
    for match, match_data in zip(matches, groupdicts):
        boss.open_url(match)
