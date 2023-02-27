from django.urls import path

from . import views

urlpatterns = [
    path('list/', views.list),
    path('info/', views.info),
    path('subTotal/', views.subTotal),
    path('chart/', views.chart),
    path('send/', views.send),
    path('update/', views.update),
    path('cancel/', views.cancel),
    path('<str:company>/', views.detail),
]