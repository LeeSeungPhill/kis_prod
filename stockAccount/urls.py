from django.urls import path

from . import views

urlpatterns = [
    path('', views.basic),
    path('init/', views.init),

]