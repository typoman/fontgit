"""fontgit -- a package for loading UFO fonts inside a git repo at a spcific part of git history."""
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version
import tomllib

try:
    __version__ = version("fontGit")
except PackageNotFoundError:
    # The package is not installed, so we fall back to reading the version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    __version__ = pyproject_data["project"]["version"]

from fontGit.objects.font import FontGit

__all__ = ["FontGit"]
