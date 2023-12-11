from django.urls import path

from . import views

urlpatterns = [
    path('runStockSearch/', views.runStockSearch),
    path('stockSearch/', views.stockSearch),
    path('orderList/', views.orderList),
    path('info/', views.info),
    path('subTotal/', views.subTotal),
    path('chart/', views.chart),
    path('send/', views.send),
    path('update/', views.update),
    path('cancel/', views.cancel),
    path('minutesInfo/', views.minutesInfo),
    path('<str:company>/', views.detail),
]