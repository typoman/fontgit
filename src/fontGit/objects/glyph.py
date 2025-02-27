from __future__ import annotations

from typing import Iterator, List, Optional, cast

from attrs import define, field
from fontTools.pens.basePen import AbstractPen
from fontTools.pens.pointPen import (
    AbstractPointPen,
    PointToSegmentPen,
    SegmentToPointPen,
)

from ufoLib2.objects.anchor import Anchor
from ufoLib2.objects.component import Component
from ufoLib2.objects.contour import Contour
from ufoLib2.objects.guideline import Guideline
from ufoLib2.objects.image import Image
from ufoLib2.objects.lib import (
    Lib,
    _get_lib,
    _get_tempLib,
)
from ufoLib2.pointPens.glyphPointPen import GlyphPointPen


@define
class Glyph:
    """Represents a glyph, containing contours, components, anchors and various
    other bits of data concerning it.

    See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/.

    Behavior:
        The Glyph object has list-like behavior. This behavior allows you to interact
        with contour data directly. For example, to get a particular contour::

            contour = glyph[0]

        To iterate over all contours::

            for contour in glyph:
                ...

        To get the number of contours::

            contourCount = len(glyph)

        To check if a :class:`Contour` object is in glyph::

            exists = contour in glyph

        To interact with components or anchors in a similar way, use the
        :attr:`Glyph.components` and :attr:`Glyph.anchors` attributes.
    """

    _name: Optional[str] = None

    width: float = 0
    """The width of the glyph."""

    height: float = 0
    """The height of the glyph."""

    unicodes: List[int] = field(factory=list)
    """The Unicode code points assigned to the glyph. Note that a glyph can have
    multiple."""

    _image: Image = field(factory=Image)

    _lib: Lib = field(factory=Lib)
    """The glyph's mapping of string keys to arbitrary data."""

    note: Optional[str] = None
    """A free form text note about the glyph."""

    _anchors: List[Anchor] = field(factory=list)
    components: List[Component] = field(factory=list)
    """The list of components the glyph contains."""

    contours: List[Contour] = field(factory=list)
    """The list of contours the glyph contains."""

    _guidelines: List[Guideline] = field(factory=list)

    _tempLib: Lib = field(factory=Lib)
    """A temporary map of arbitrary plist values."""

    def __len__(self) -> int:
        return len(self.contours)

    def __getitem__(self, index: int) -> Contour:
        return self.contours[index]

    def __contains__(self, contour: Contour) -> bool:
        return contour in self.contours

    def __iter__(self) -> Iterator[Contour]:
        return iter(self.contours)

    def __repr__(self) -> str:
        return "<{}.{} {}at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            f"'{self._name}' " if self._name is not None else "",
            hex(id(self)),
        )

    @property
    def lib(self) -> Lib:
        return _get_lib(self)

    @property
    def tempLib(self) -> Lib:
        return _get_tempLib(self)

    @property
    def anchors(self) -> list[Anchor]:
        """The list of anchors the glyph contains.

        Getter:
            Returns a list of anchors the glyph contains.
        """
        return self._anchors

    @property
    def guidelines(self) -> list[Guideline]:
        """The list of guidelines the glyph contains.

        Getter:
            Returns a list of guidelines the glyph contains.
        """
        return self._guidelines

    @property
    def name(self) -> str | None:
        """The name of the glyph."""
        return self._name

    @property
    def unicode(self) -> int | None:
        """The first assigned Unicode code point or None.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#unicode.
        """
        if self.unicodes:
            return self.unicodes[0]
        return None

    @property
    def image(self) -> Image:
        """The background image reference associated with the glyph.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#image.
        """
        return self._image


    def draw(self, pen: AbstractPen, outputImpliedClosingLine: bool = False) -> None:
        """Draws glyph into given pen."""
        pointPen = PointToSegmentPen(
            pen, outputImpliedClosingLine=outputImpliedClosingLine
        )
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen: AbstractPointPen) -> None:
        """Draws points of glyph into given point pen."""
        for contour in self.contours:
            contour.drawPoints(pointPen)
        for component in self.components:
            component.drawPoints(pointPen)

    def getPen(self) -> AbstractPen:
        """Returns a pen for others to draw into self."""
        pen = SegmentToPointPen(self.getPointPen())
        return pen

    def getPointPen(self) -> AbstractPointPen:
        """Returns a point pen for others to draw points into self."""
        pointPen = GlyphPointPen(self)
        return pointPen

    @property
    def markColor(self) -> str | None:
        """The color assigned to the glyph.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#publicmarkcolor.

        Getter:
            Returns the mark color or None.
        """
        return cast(Optional[str], self.lib.get("public.markColor"))

    @property
    def verticalOrigin(self) -> float | None:
        """The vertical origin of the glyph.

        See http://unifiedfontobject.org/versions/ufo3/glyphs/glif/#publicverticalorigin.

        Getter:
            Returns the vertical origin or None.
        """
        return cast(Optional[float], self.lib.get("public.verticalOrigin"))
