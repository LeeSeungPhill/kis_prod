from rest_framework import viewsets  # viewset import
from .serializer import StockFundMngSerializer  # 생성한 serializer import
from .models import stock_fund_mng  # stock_fund_mng import

class StockFundMngViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = stock_fund_mng.objects.all()
    serializer_class = StockFundMngSerializer