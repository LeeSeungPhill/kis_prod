from rest_framework import viewsets  # viewset import
from .serializer import StockOrderCompleteSerializer  # 생성한 serializer import
from .models import stock_order_complete  # stock_order import

class StockOrderCompleteViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = stock_order_complete.objects.all()
    serializer_class = StockOrderCompleteSerializer



