from django.urls import path

from . import views

urlpatterns = [
    path('balanceList/', views.balanceList),
    path('update/', views.update),
    path('info/', views.info),
    path('minutesInfo/', views.minutesInfo),
    path('marketInfo/', views.marketInfo),
    path('marketMinutesInfo/', views.marketMinutesInfo),
    path('<str:company>/', views.detail),
]