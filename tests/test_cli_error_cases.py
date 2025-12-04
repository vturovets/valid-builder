from src import cli


def test_cli_reports_missing_input_file(tmp_path):
    """A missing input file results in exit code 1 and no CSV output."""

    output = tmp_path / "out.csv"

    exit_code = cli.main([str(tmp_path / "missing.kt"), "--output", str(output)])

    assert exit_code == 1
    assert not output.exists()


def test_cli_rejects_unsupported_extension(tmp_path):
    """Unsupported file types map to exit code 2 and do not create outputs."""

    unknown = tmp_path / "data.txt"
    unknown.write_text("just some content with no hints")
    output = tmp_path / "out.csv"

    exit_code = cli.main([str(unknown), "--output", str(output)])

    assert exit_code == 2
    assert not output.exists()


def test_cli_handles_corrupted_yaml(tmp_path):
    """Invalid YAML input triggers an error exit without creating the CSV."""

    corrupted = tmp_path / "broken.yml"
    corrupted.write_text("openapi: 3.0.0\npaths: [")
    output = tmp_path / "out.csv"

    exit_code = cli.main([str(corrupted), "--output", str(output)])

    assert exit_code == 1
    assert not output.exists()
