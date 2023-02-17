from rest_framework import viewsets  # viewset import
from .serializer import StockMarketMngSerializer  # 생성한 serializer import
from .models import stock_market_mng  # stock_order import

class StockMarketMngViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = stock_market_mng.objects.all()
    serializer_class = StockMarketMngSerializer