from pathlib import Path


def delete_file_if_exists(file_path: str | None) -> bool:
    if not file_path:
        return False
    path = Path(file_path)
    if not path.exists():
        return False
    path.unlink()
    return True
