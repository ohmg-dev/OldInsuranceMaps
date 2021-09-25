from django.urls import path

from .views import item_detail, SimpleAPI, VolumeDetail

urlpatterns = [
    path('volume/<str:docdoi>/', item_detail, {"loc_type": "volume"}, name='volume_detail'),
    path('sheet/<str:docdoi>/', item_detail, {"loc_type": "sheet"}, name='sheet_detail'),
    path('api/', SimpleAPI.as_view() , name='lc_api'),
    path('<str:volumeid>/', VolumeDetail.as_view(), name="volume_summary"),
]
