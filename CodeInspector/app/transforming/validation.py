import re
from pathlib import Path

JAVADOC_BLOCK_RE = re.compile(r"/\*\*(.*?)\*/", re.DOTALL)
AUTHOR_TAG_RE = re.compile(r"@author\s+([A-Za-z]+\.[A-Za-z]+@enmu\.edu)")
 
def _extract_authors_from_java_file(source: str) -> set:
    """
    returns collection of valid author tags found (john.doe@enmu.edu).
    can be multiple.

    Args:
        source (str): the source file
        
    Returns:
        set: set of author email tags
    """
    authors = set()
    javadocs = JAVADOC_BLOCK_RE.findall(source)

    for block in javadocs:
        for match in AUTHOR_TAG_RE.findall(block):
            authors.add(match)

    return authors

def extract_author_from_submission(source_dir: Path | str) -> str | None:
    """
    function that extracts all valid author tags across a submission.
    if more than one is present, None is returned (invalid submission)

    Args:
        source_dir (str): source dir path

    Returns:
        str | None: author tag (john.doe@enmu.edu)
    """
    source_dir = Path(source_dir)
    
    authors = set()

    for java_file in source_dir.rglob("*.java"):
        
        try:
            with java_file.open("r", encoding="utf-8", errors="ignore") as file:
                source = file.read()
                
        except OSError:
            continue
        
        authors.update(_extract_authors_from_java_file(source))
        
    if len(authors) == 1:
        return next(iter(authors))

    return None