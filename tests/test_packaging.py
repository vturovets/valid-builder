import tomllib
from pathlib import Path


def _load_pyproject():
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must be present for packaging"
    return tomllib.loads(pyproject_path.read_text())


def test_pyproject_has_minimum_metadata():
    """Ensure the project declares basic metadata and build-system settings."""
    data = _load_pyproject()

    build_system = data.get("build-system", {})
    assert build_system.get("build-backend") == "setuptools.build_meta"
    assert any("setuptools" in requirement for requirement in build_system.get("requires", []))

    project = data.get("project", {})
    assert project.get("name") == "valid-builder"
    assert project.get("version")
    assert project.get("description")
    assert project.get("readme") == "readme.md"
    assert project.get("requires-python")
    assert Path(project["readme"]).exists()


def test_pyproject_dependencies_include_required_runtime_packages():
    """Verify runtime dependencies include the YAML and dotenv libraries mandated by the SDD."""
    project = _load_pyproject().get("project", {})
    dependencies = [dependency.lower() for dependency in project.get("dependencies", [])]

    assert any(dep.startswith("ruamel.yaml") for dep in dependencies)
    assert any(dep.startswith("python-dotenv") for dep in dependencies)


def test_console_script_entrypoint_exposes_cli():
    """Confirm the CLI is exposed as a console script for installation convenience."""
    project = _load_pyproject().get("project", {})
    scripts = project.get("scripts", {})

    assert scripts.get("valid-builder") == "src.cli:main"
