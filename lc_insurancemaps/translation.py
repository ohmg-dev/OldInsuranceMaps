from modeltranslation.translator import translator, TranslationOptions
from .models import MapScan, MapCollectionItem


class MapScanTranslationOptions(TranslationOptions):
    fields = ()

class MapCollectionItemTranslationOptions(TranslationOptions):
    fields = ()

translator.register(MapScan, MapScanTranslationOptions)
translator.register(MapCollectionItem, MapCollectionItemTranslationOptions)
