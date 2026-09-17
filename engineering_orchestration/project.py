"""Active project discovery and Manifest-owned Task paths."""

from pathlib import Path, PureWindowsPath


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from the caller, never from the installed package."""
    start = Path.cwd() if start is None else Path(start)
    candidate = start.resolve()
    for directory in (candidate, *candidate.parents):
        if (directory / ".ai" / "project.yaml").is_file():
            return directory
    raise FileNotFoundError(
        f"No .ai/project.yaml found in '{start}' or any parent directory."
    )


def task_directory(project_root: Path, manifest: dict | None = None) -> Path:
    """Resolve the canonical default or explicit repository-relative Task path.

    Full Manifest validation belongs to structural validation. CLI discovery
    checks the path-bearing fields here so malformed configuration never causes
    a silent fallback to the default.
    """
    import yaml

    if manifest is None:
        manifest = yaml.safe_load(
            (project_root / ".ai/project.yaml").read_text(encoding="utf-8")
        )
    if not isinstance(manifest, dict):
        raise ValueError("Project Manifest must be a mapping")
    tasks = manifest.get("tasks", {})
    if not isinstance(tasks, dict):
        raise ValueError("Manifest tasks must be a mapping")
    directory = tasks.get("directory", ".ai/tasks/")
    if (not isinstance(directory, str) or not directory
            or "\\" in directory or directory.startswith("/")
            or Path(directory).is_absolute()
            or PureWindowsPath(directory).drive):
        raise ValueError("Manifest tasks.directory must be repository-relative")
    return (project_root / directory).resolve()
