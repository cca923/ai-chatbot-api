import re


CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\](?!\()")
MIXED_RE = re.compile(r"[\[\(]#citation-(\d+)[\]\)]")
DEDUP_RE = re.compile(r"\[(\d+)\]\(#citation-\1\)\s*\(#citation-\1\)")


def normalize_citations(text: str) -> str:
    text = CITATION_RE.sub(
        lambda m: "".join(
            f"[{num.strip()}](#citation-{num.strip()})" for num in m.group(1).split(",")
        ),
        text,
    )
    text = MIXED_RE.sub(r"(#citation-\1)", text)
    text = DEDUP_RE.sub(r"[\1](#citation-\1)", text)
    return text
