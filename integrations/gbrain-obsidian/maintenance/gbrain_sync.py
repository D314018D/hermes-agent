from pathlib import Path

from .gbrain_cli import run_gbrain_command


def sync(vault_path: str = "./obsidian-vault") -> dict:
    return run_gbrain_command(["import", str(Path(vault_path)), "--no-embed"], command_timeout_seconds=300)


if __name__ == "__main__":
    print(sync())
