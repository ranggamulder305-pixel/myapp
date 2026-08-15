"""
Minimal pure-Python SRT parser, dropin replacement for the `srt` package's
`srt.parse()` function. Only implements what's needed here: parsing an .srt
string into objects with .index, .start, .end (as datetime.timedelta), and
.content attributes.

No external dependency -> avoids python-for-android wheel resolution issues.
"""
import re
from datetime import timedelta


class Subtitle:
    __slots__ = ("index", "start", "end", "content")

    def __init__(self, index, start, end, content):
        self.index = index
        self.start = start
        self.end = end
        self.content = content

    def __repr__(self):
        return f"Subtitle(index={self.index}, start={self.start}, end={self.end}, content={self.content!r})"


_TIME_RE = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{3})")


def _parse_timestamp(ts):
    m = _TIME_RE.match(ts.strip())
    if not m:
        raise ValueError(f"Invalid SRT timestamp: {ts!r}")
    hours, minutes, seconds, millis = (int(x) for x in m.groups())
    return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=millis)


# Splits blocks separated by one or more blank lines. Handles \r\n and \n.
_BLOCK_SPLIT_RE = re.compile(r"\r?\n\r?\n+")
_ARROW_RE = re.compile(r"\s*-->\s*")


def parse(text):
    """
    Parse SRT-formatted `text` and yield Subtitle objects, mirroring
    srt.parse() from the `srt` PyPI package closely enough for this project.
    """
    if text is None:
        return

    text = text.replace("\ufeff", "")  # strip BOM if present
    blocks = _BLOCK_SPLIT_RE.split(text.strip())

    for block in blocks:
        lines = [l for l in block.splitlines() if l.strip() != "" or True]
        # Remove trailing empty lines
        while lines and lines[-1].strip() == "":
            lines.pop()
        if not lines:
            continue

        # First line should be the index (may sometimes be missing/malformed)
        idx_line = lines[0].strip()
        line_offset = 1
        try:
            index = int(idx_line)
        except ValueError:
            # Some malformed SRTs skip the index line; try to recover
            index = None
            line_offset = 0

        if len(lines) <= line_offset:
            continue

        time_line = lines[line_offset].strip()
        if "-->" not in time_line:
            # Not a valid subtitle block, skip
            continue

        start_str, end_str = _ARROW_RE.split(time_line, maxsplit=1)
        try:
            start = _parse_timestamp(start_str)
            end = _parse_timestamp(end_str.split()[0])  # drop any trailing position info
        except ValueError:
            continue

        content_lines = lines[line_offset + 1:]
        content = "\n".join(content_lines).strip()

        if index is None:
            index = 0

        yield Subtitle(index, start, end, content)


def compose(subtitles):
    """
    Compose Subtitle objects back into an SRT-formatted string.
    Mirrors srt.compose() closely enough for this project's needs.
    """
    def fmt_ts(td):
        total_ms = int(td.total_seconds() * 1000)
        hours, rem = divmod(total_ms, 3600000)
        minutes, rem = divmod(rem, 60000)
        seconds, millis = divmod(rem, 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    parts = []
    for sub in subtitles:
        parts.append(
            f"{sub.index}\n{fmt_ts(sub.start)} --> {fmt_ts(sub.end)}\n{sub.content}\n"
        )
    return "\n".join(parts)
