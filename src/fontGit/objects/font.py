from __future__ import annotations
from typing import (
    Any,
    Dict,
    Iterator,
    KeysView,
    List,
    Sequence,
    cast,
)
from attrs import define, field
from fontGit.utils import GitCommitFS
from fontTools.ufoLib import UFOReader
from ufoLib2.objects.dataSet import DataSet
from ufoLib2.objects.features import Features
from fontGit.objects.glyph import Glyph
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.imageSet import ImageSet
from ufoLib2.objects.info import Info
from ufoLib2.objects.kerning import Kerning
from ufoLib2.objects.layerSet import LayerSet
from ufoLib2.objects.lib import (
    Lib,
    _get_lib,
    _get_tempLib,
)

from ufoLib2.typing import PathLike, T


@define(kw_only=True)
class Font:
    """A data class representing a single Unified Font Object (UFO).
    This data class is only meant for reading and viewing the
    contents of the UFO.
    """

    layers: LayerSet = field(
        factory=LayerSet.default,
        metadata={"omit_if_default": False},
    )
    """LayerSet: A mapping of layer names to Layer objects."""

    info: Info = field(factory=Info)
    """Info: The font Info object."""

    features: Features = field(factory=Features)
    """Features: The font Features object."""

    groups: Dict[str, List[str]] = field(factory=dict)
    """Dict[str, List[str]]: A mapping of group names to a list of glyph names."""

    kerning: Kerning = field(factory=Kerning, alias="_kerning", kw_only=True)
    """Dict[Tuple[str, str], float]: A mapping of a tuple of first and second kerning
    pair to a kerning value."""

    _lib: Lib = field(factory=Lib)
    """Dict[str, PlistEncodable]: A mapping of keys to arbitrary plist values."""

    data: DataSet = field(factory=DataSet)
    """DataSet: A mapping of data file paths to arbitrary data."""

    images: ImageSet = field(factory=ImageSet)
    """ImageSet: A mapping of image file paths to arbitrary image data."""

    _tempLib: Lib = field(factory=Lib)
    """Dict[str, PlistEncodable]: A temporary map of arbitrary plist values."""

    @classmethod
    def open(cls, path: PathLike, validate: bool = True) -> Font:
        """Instantiates a new Font object from a path to a UFO.

        Args:
            path: The path to the UFO to load.
            validate: If True, enable UFO data model validation during loading. If
                False, load whatever is deserializable.
        """
        reader = UFOReader(path, validate=validate)
        self = cls.read(reader)
        self._path = path
        reader.close()
        return self

    @classmethod
    def read(cls, reader: UFOReader) -> Font:
        """Instantiates a Font object from a :class:`fontTools.ufoLib.UFOReader`.

        Args:
            path: The path to the UFO to load.
        """
        self = cls(
            layers=LayerSet.read(reader),
            data=DataSet.read(reader),
            images=ImageSet.read(reader),
            info=Info.read(reader),
            features=Features(reader.readFeatures()),
            groups=reader.readGroups(),
            kerning=Kerning(reader.readKerning()),
            lib=Lib(reader.readLib()),
        )
        self._fileStructure = reader.fileStructure
        self._reader = reader
        return self

    def __contains__(self, name: object) -> bool:
        return name in self.layers._defaultLayer

    def __getitem__(self, name: str) -> Glyph:
        return self.layers._defaultLayer[name]

    def __iter__(self) -> Iterator[Glyph]:
        return iter(self.layers._defaultLayer)

    def __len__(self) -> int:
        return len(self.layers._defaultLayer)

    def get(self, name: str, default: T | None = None) -> T | Glyph | None:
        """Return the :class:`.Glyph` object for name if it is present in the
        default layer, otherwise return ``default``."""
        return self.layers._defaultLayer.get(name, default)

    def keys(self) -> KeysView[str]:
        """Return a list of glyph names in the default layer."""
        return self.layers._defaultLayer.keys()

    def _get_kerning(self) -> Kerning:
        return self._kerning

    kerning = property(_get_kerning)
    lib = property(_get_lib)
    tempLib = property(_get_tempLib)

    @property
    def reader(self) -> UFOReader | None:
        """Returns the underlying :class:`fontTools.ufoLib.UFOReader`."""
        return self._reader

    @property
    def glyphOrder(self) -> list[str]:
        """The font's glyph order."""
        return list(cast(Sequence[str], self.lib.get("public.glyphOrder", [])))

    @property
    def guidelines(self) -> list[Guideline]:
        """The font's global guidelines."""
        if self.info.guidelines is None:
            return []
        return self.info.guidelines

    @property
    def path(self) -> PathLike | None:
        """Return the path of the UFO, if it was set, or None."""
        return self._path

    def close(self) -> None:
        """Closes the UFOReader if it still exists to finalize any outstanding
        file operations."""
        if self._reader is not None:
            self._reader.close()

    def __enter__(self) -> Font:
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        names = list(filter(None, [self.info.familyName, self.info.styleName]))
        fontName = " '{}'".format(" ".join(names)) if names else ""
        return "<{}.{}{} at {}>".format(
            self.__class__.__module__, self.__class__.__name__, fontName, hex(id(self))
        )

class FontGit(Font):

    @classmethod
    def open_at_commit(cls, path: str, commit_sha: str = None, validate: bool = False) -> "FontGit":
        """
        Commit_sha is optional. If no commit hash is given, then the last commit will be used.
        """
        git_fs = GitCommitFS(path, commit_sha)
        reader = UFOReader(git_fs, validate=validate)
        font = cls.read(reader)
        font._commit_sha = git_fs.commitsha
        return font

    @property
    def commitHash(self):
        return self._commit_sha

    def diff(self):
        # TODO: return a new font objc that only contains the changed parts
        pass
