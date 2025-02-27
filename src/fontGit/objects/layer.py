from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    KeysView,
)

from attrs import define, field
from fontTools.ufoLib.glifLib import GlyphSet

from ufoLib2.constants import DEFAULT_LAYER_NAME
from fontGit.objects.glyph import Glyph
from ufoLib2.objects.lib import (
    Lib,
    _get_lib,
    _get_tempLib,
    _set_lib,
    _set_tempLib,
)

_GLYPH_NOT_LOADED = Glyph(name="___GLYPH_NOT_LOADED___")

@define
class Layer:
    """Represents a Layer that holds Glyph objects.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/layerinfo.plist/.

    Note:
        Various methods that work on Glyph objects take a ``layer`` attribute, because
        the UFO data model prescribes that Components within a Glyph object refer to
        glyphs *within the same layer*.

    Behavior: Layer behaves **partly** like a dictionary of type ``Dict[str,
        Glyph]``. The Glyph objects by default are only loaded into memory
        when accessed.

        To get the number of glyphs in the layer::

            glyphCount = len(layer)

        To iterate over all glyphs::

            for glyph in layer:
                ...

        To check if a specific glyph exists::

            exists = "myGlyphName" in layer

        To get a specific glyph::

            layer["myGlyphName"]
    """

    _name: str = field(default=DEFAULT_LAYER_NAME, metadata={"omit_if_default": False})
    _glyphs: Dict[str, Glyph] = field(factory=dict)
    _lib: Lib = field(factory=Lib)
    """The layer's lib for mapping string keys to arbitrary data."""

    _default: bool = False
    """Can set to True to mark a layer as default. If layer name is 'public.default'
    the default attribute is automatically True. Exactly one layer must be marked as
    default in a font."""

    _tempLib: Lib = field(factory=Lib)
    """A temporary map of arbitrary plist values."""

    _glyphSet: Any = field(default=None, init=False, eq=False)


    @classmethod
    def read(cls, name: str, glyphSet: GlyphSet, default: bool = False) -> Layer:
        """Instantiates a Layer object from a
        :class:`fontTools.ufoLib.glifLib.GlyphSet`.

        Args:
            name: The name of the layer.
            glyphSet: The GlyphSet object to read from.
        """
        glyphNames = glyphSet.keys()
        glyphs: dict[str, Glyph]
        glyphs = {gn: _GLYPH_NOT_LOADED for gn in glyphNames}
        self = cls(name, glyphs, default=default)
        self._glyphSet = glyphSet
        glyphSet.readLayerInfo(self)
        return self

    def __contains__(self, name: object) -> bool:
        return name in self._glyphs

    def __getitem__(self, name: str) -> Glyph:
        glyph = self._glyphs[name]
        if glyph is _GLYPH_NOT_LOADED:
            glyph = Glyph(name)
            self._glyphSet.readGlyph(name, glyph, glyph.getPointPen())
            self._glyphs[name] = glyph
        return glyph

    def __iter__(self) -> Iterator[Glyph]:
        for name in self._glyphs:
            yield self[name]

    def __len__(self) -> int:
        return len(self._glyphs)

    def __repr__(self) -> str:
        n = len(self._glyphs)
        return "<{}.{} '{}' ({}{}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            self._name,
            "default, " if self._default else "",
            "empty" if n == 0 else "{} glyph{}".format(n, "s" if n > 1 else ""),
            hex(id(self)),
        )

    def keys(self) -> KeysView[str]:
        """Returns a list of glyph names."""
        return self._glyphs.keys()

    @property
    def name(self) -> str:
        """The name of the layer."""
        return self._name

    lib = property(_get_lib, _set_lib)

    tempLib = property(_get_tempLib, _set_tempLib)

    @property
    def default(self) -> bool:
        """Read-only property. To change the font's default layer use the
        LayerSet.defaultLayer property setter."""
        return self._default
