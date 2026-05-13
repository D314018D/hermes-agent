from pathlib import Path


def find_raw_content_sections(vault_path: str = "./obsidian-vault") -> list[str]:
    vault = Path(vault_path)
    matches = []
    for note in vault.rglob("*.md"):
        if "## Raw Content" in note.read_text(encoding="utf-8"):
            matches.append(str(note))
    return matches


if __name__ == "__main__":
    for path in find_raw_content_sections():
        print(path)

