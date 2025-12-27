from pathlib import Path

def count_loc_in_dir(source_dir: Path | str) -> int:
    """
    function to count lines of code of all Java files in a given dir. Ignores whitespace lines and comments

    Args:
        source_dir (str | Path): dir location

    Returns:
        int: the number of loc in the dir
    """
    source_dir = Path(source_dir)
    total = 0
    for java_file in source_dir.rglob("*.java"):
        total += _count_loc_in_file(java_file)
    return total

def _count_loc_in_file(path: Path | str) -> int:
    """
    function to count the lines of java code within a single file

    Args:
        path (str | Path): the file location

    Returns:
        int: the number of loc in the file
    """
    path = Path(path)
    in_block_comment = False
    loc = 0

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            code, in_block_comment = _strip_java_comments(line, in_block_comment)
            if code.strip():  # if line not empty after removing comments
                loc += 1

    return loc

def _strip_java_comments(line: str, in_block_comment: bool) -> tuple[str, bool]:
    """
    removes Java comments from a single line while tracking whether we are
    currently inside a block comment across lines. Also avoids treating // or /* 
    inside string/char literals as comments.

    Args:
        line (str): the line to remove comments from
        in_block_comment (bool): if we are in a block comment

    Returns:
        tuple[str, bool]: the stripped line, and whether we are inside a block comment
    """
    i = 0
    n = len(line)
    out_chars: list[str] = []

    in_string = False   # inside "..."
    in_char = False     # inside '...'
    escape = False      # escape sequence

    while i < n:
        ch = line[i]
        nxt = line[i + 1] if i + 1 < n else ""

        if in_block_comment:
            # check for end of block comment
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        # not in block comment:
        # handle string/char literal
        if escape:
            out_chars.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\" and (in_string or in_char):
            out_chars.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"' and not in_char:
            in_string = not in_string
            out_chars.append(ch)
            i += 1
            continue

        if ch == "'" and not in_string:
            in_char = not in_char
            out_chars.append(ch)
            i += 1
            continue

        # if inside a literal, add char to list
        if in_string or in_char:
            out_chars.append(ch)
            i += 1
            continue

        # detect comment starts
        if ch == "/" and nxt == "/":
            # rest of line is a comment. Continue to next line
            break

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        # normal code char
        out_chars.append(ch)
        i += 1

    return "".join(out_chars), in_block_comment