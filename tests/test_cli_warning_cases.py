from pathlib import Path

from src import cli


def test_cli_completes_with_warnings(monkeypatch, tmp_path, capsys):
    """Warnings emitted during orchestration keep the exit code at zero and still write the CSV."""

    stub_input = tmp_path / "input.kt"
    stub_input.write_text("fun main() = Unit\n")
    output = tmp_path / "out.csv"

    def fake_orchestrate(input_file, output_file, config, lang_override=None, logger=None):
        assert Path(input_file) == stub_input
        logger.warning("Skipped ambiguous construct")
        Path(output_file).write_text("Rule ID,Description,Source file,Lines,Endpoint,Endpoint entity,Depends on\n")
        return []

    monkeypatch.setattr(cli, "orchestrate", fake_orchestrate)

    exit_code = cli.main([str(stub_input), "--output", str(output)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Skipped ambiguous construct" in captured.err
    assert output.exists()
