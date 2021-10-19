from modeltranslation.translator import translator, TranslationOptions
from .models import Volume, Sheet


class VolumeTranslationOptions(TranslationOptions):
    fields = ()

class SheetTranslationOptions(TranslationOptions):
    fields = ()

translator.register(Volume, VolumeTranslationOptions)
translator.register(Sheet, SheetTranslationOptions)
