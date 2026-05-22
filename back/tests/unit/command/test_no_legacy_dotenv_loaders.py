from pathlib import Path


def test_command_entrypoints_do_not_use_legacy_dotenv_loading() -> None:
    command_dir = Path(__file__).resolve().parents[3] / "src" / "command"

    offenders = []
    for file_path in sorted(command_dir.rglob("*.py")):
        content = file_path.read_text(encoding="utf-8")
        if "load_dotenv(" in content or "from dotenv import" in content:
            offenders.append(file_path.relative_to(command_dir.parent).as_posix())

    assert offenders == [], f"Legacy dotenv usage found in command entrypoints: {offenders}"
