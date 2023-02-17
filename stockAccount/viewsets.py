from rest_framework import viewsets  # viewset import
from .serializer import StockAccountSerializer  # 생성한 serializer import
from .models import stock_account  # stock_account import

class StockAccountViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = stock_account.objects.all()
    serializer_class = StockAccountSerializer



