import re


def compile_truth(existing_truth: str, new_summary: str, max_chars: int = 1200) -> str:
    sentences = []
    seen = set()
    for text in [existing_truth, new_summary]:
        for sentence in split_sentences(text):
            key = re.sub(r"\s+", " ", sentence).strip().lower()
            if key and key not in seen:
                seen.add(key)
                sentences.append(sentence)
    compiled = " ".join(sentences).strip()
    if len(compiled) <= max_chars:
        return compiled
    return compiled[:max_chars].rsplit(" ", 1)[0].rstrip() + "..."


def split_sentences(text: str) -> list[str]:
    clean = " ".join((text or "").split())
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?。！？])\s+", clean)
    return [part.strip() for part in parts if part.strip()]

