"""fontgit -- a package for loading UFO fonts inside a git repo at a specific part of git history."""
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version
import tomllib

try:
    __version__ = version("fontGit")
except PackageNotFoundError:
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
            __version__ = pyproject_data["project"]["version"]
        except Exception:
            raise

from fontGit.objects.font import FontGit

__all__ = ["FontGit"]
