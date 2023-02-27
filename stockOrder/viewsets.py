from rest_framework import viewsets  # viewset import
from .serializer import StockOrderSerializer  # 생성한 serializer import
from .serializer import SubTotalSerializer  # 생성한 serializer import
from .models import stock_order  # stock_order import
from .models import sub_total  # sub_total import

class StockOrderViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = stock_order.objects.all()
    serializer_class = StockOrderSerializer

class SubTotalViewSet(viewsets.ModelViewSet):  # ModelViewSet 활용
    queryset = sub_total.objects.all()
    serializer_class = SubTotalSerializer

