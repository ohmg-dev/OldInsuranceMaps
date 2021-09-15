from django.urls import path

from .views import item_detail

urlpatterns = [
    path('volume/<str:docdoi>/', item_detail, {"loc_type": "volume"}, name='volume_detail'),
    path('sheet/<str:docdoi>/', item_detail, {"loc_type": "sheet"}, name='sheet_detail'),
]
