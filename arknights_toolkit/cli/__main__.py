from pathlib import Path

resource_path = Path(__file__).parent.parent / "resource"
(resource_path / "cli_record").touch(exist_ok=True)


def main():
    from arknights_toolkit.cli import arkkit

    arkkit.main()

    (resource_path / "cli_record").unlink(missing_ok=True)
