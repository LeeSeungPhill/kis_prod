from django.urls import path

from . import views

urlpatterns = [
    path('list/', views.list),
    path('update/', views.update),
    path('info/', views.info),
    path('<str:company>/', views.detail),
]