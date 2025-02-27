from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    Iterable,
    Iterator,
    Optional,
    Sized,
)

from attrs import define, field
from fontTools.ufoLib import UFOReader

from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.errors import Error
from ufoLib2.objects.layer import Layer
from ufoLib2.objects.misc import (
    _setstate_attrs,
)
from ufoLib2.typing import T

if TYPE_CHECKING:
    from typing import Type

    from cattrs import Converter

_LAYER_NOT_LOADED = Layer(name="____LAYER_NOT_LOADED____")


@define
class LayerSet:
    """Represents a mapping of layer names to Layer objects.

    See http://unifiedfontobject.org/versions/ufo3/layercontents.plist/ for layer
    semantics.

    Behavior:
        LayerSet behaves **partly** like a dictionary of type ``Dict[str, Layer]``,
        creating and loading layers is done through their own methods. The layer objects and their
        glyphs are by default only loaded into memory when accessed.

        To get the number of layers in the font::

            layerCount = len(font.layers)

        To iterate over all layers::

            for layer in font.layers:
                ...

        To check if a specific layer exists::

            exists = "myLayerName" in font.layers

        To get a specific layer::

            font.layers["myLayerName"]
    """

    _layers: Dict[str, Layer] = field()
    _defaultLayer: Layer = field(default=_LAYER_NOT_LOADED, eq=False)
    _reader: Optional[UFOReader] = field(default=None, init=False, eq=False)

    @classmethod
    def default(cls) -> LayerSet:
        """Return a new LayerSet with an empty default Layer."""
        return cls.from_iterable([Layer()])

    @classmethod
    def from_iterable(
        cls, value: Iterable[Layer], defaultLayerName: str = DEFAULT_LAYER_NAME
    ) -> LayerSet:
        """Instantiates a LayerSet from an iterable of :class:`.Layer` objects.

        Args:
            value: an iterable of :class:`.Layer` objects.
            defaultLayerName: the name of the default layer of the ones in ``value``.
        """
        layers: dict[str, Layer] = {}
        defaultLayer = None
        for layer in value:
            if layer.name == defaultLayerName or layer._default:
                if not layer._default:
                    layer._default = True
                defaultLayer = layer
            layers[layer.name] = layer

        if defaultLayer is None:
            raise ValueError("no layer marked as default")
        return cls(layers=layers, defaultLayer=defaultLayer)

    @classmethod
    def read(cls, reader: UFOReader) -> LayerSet:
        """Instantiates a LayerSet object from a :class:`fontTools.ufoLib.UFOReader`.

        Args:
            path: The path to the UFO to load.
        """
        layers: dict[str, Layer] = {}
        defaultLayer = None

        defaultLayerName = reader.getDefaultLayerName()

        for layerName in reader.getLayerNames():
            isDefault = layerName == defaultLayerName
            if isDefault:
                layer = LayerSet._loadLayer(reader, layerName, isDefault)
                if isDefault:
                    defaultLayer = layer
                layers[layerName] = layer
            else:
                layers[layerName] = _LAYER_NOT_LOADED

        assert defaultLayer is not None

        self = cls(layers=layers, defaultLayer=defaultLayer)
        self._reader = reader
        return self

    def __contains__(self, name: str) -> bool:
        return name in self._layers

    def __getitem__(self, name: str) -> Layer:
        if name is None:
            name = self._defaultLayer.name
        layer_object = self._layers[name]
        if layer_object is _LAYER_NOT_LOADED:
            layer_object = LayerSet._loadLayer(self._reader, layer_name)
            self._layers = layer_object
        return layer_object

    def __iter__(self) -> Iterator[Layer]:
        for layer_name, layer_object in self._layers.items():
            yield self[layer_name]

    def __len__(self) -> int:
        return len(self._layers)

    def __repr__(self) -> str:
        n = len(self._layers)
        return "<{}.{} ({} layer{}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            n,
            "s" if n > 1 else "",
            hex(id(self)),
        )

    @property
    def layerOrder(self) -> list[str]:
        """The font's layer order.

        Getter:
            Returns the font's layer order.
        """
        return list(self._layers)

    @staticmethod
    def _loadLayer(
        reader: UFOReader, layerName: str, default: bool = False
    ) -> Layer:
        glyphSet = reader.getGlyphSet(layerName)
        layer = Layer.read(layerName, glyphSet, default=default)
        return layer

    @property
    def defaultLayer(self) -> Layer:
        return self._defaultLayer
