import re
import unicodedata

_FEAT = re.compile(r"\s*[\(\[](feat\.?|ft\.?|with|con)\s[^\)\]]*[\)\]]", re.I)
_SUFFIX = re.compile(r"\s+-\s+(remaster(ed)?(\s+\d{4})?|\d{4}\s+remaster(ed)?|single version|radio edit|live)\s*$", re.I)


def normalize(s: str) -> str:
    """Titolo/artista in forma confrontabile: minuscolo, senza accenti, senza 'feat.' e suffissi tipo Remastered."""
    s = _FEAT.sub("", s or "")
    s = _SUFFIX.sub("", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()
