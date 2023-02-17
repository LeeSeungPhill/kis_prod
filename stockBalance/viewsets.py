from rest_framework import viewsets  # viewset import
from .serializer import StockBalanceSerializer  # 생성한 serializer import
from .models import stock_balance  # stock_balance import

class StockBalanceViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = stock_balance.objects.all()
    serializer_class = StockBalanceSerializer