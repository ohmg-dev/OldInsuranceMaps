from django.urls import path

from .views import item_detail, get_volume_sheets

urlpatterns = [
    path('volume/<str:docdoi>/', item_detail, {"loc_type": "volume"}, name='volume_detail'),
    path('volume/<str:docdoi>/get-sheets', get_volume_sheets, {"loc_type": "volume"}, name='get_volume_sheets'),
    path('sheet/<str:docdoi>/', item_detail, {"loc_type": "sheet"}, name='sheet_detail'),
]
