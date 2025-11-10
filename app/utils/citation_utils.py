import re


def clean_citations(text: str) -> str:
    """
    Normalize and fix citation markdown formats.
    Handles single, multiple, and malformed citations from AI output.

    Supported transformations:
    - [1]                   -> [1](#citation-1)
    - [1, 3]                -> [1](#citation-1)[3](#citation-3)
    - (#citation-1]         -> (#citation-1)
    - [1] (#citation-1)     -> [1](#citation-1)
    """

    # Expand multiple citations: [1, 3] → [1](#citation-1)[3](#citation-3)
    text = re.sub(
        r"\[(\d+(?:,\s*\d+)*)\](?!\()",
        lambda m: "".join(
            [
                f"[{num.strip()}](#citation-{num.strip()})"
                for num in m.group(1).split(",")
            ]
        ),
        text,
    )

    # Fix single citations: [1] → [1](#citation-1)
    text = re.sub(r"\[(\d+)\](?!\()", r"[\1](#citation-\1)", text)

    # Fix mixed brackets: (#citation-1], [#citation-1), [#citation-1] → (#citation-1)
    text = re.sub(r"[\[\(]#citation-(\d+)[\]\)]", r"(#citation-\1)", text)

    # Remove unnecessary spaces: [1] (#citation-1) → [1](#citation-1)
    text = re.sub(r"\[(\d+)\]\s+\(#citation-", r"[\1](#citation-", text)

    return text
