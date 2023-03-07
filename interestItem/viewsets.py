from rest_framework import viewsets  # viewset import
from .serializer import InterestItemSerializer  # 생성한 serializer import
from .models import interest_item  # interest_item import

class InterestItemViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = interest_item.objects.all()
    serializer_class = InterestItemSerializer