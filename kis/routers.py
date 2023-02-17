from rest_framework import routers
from stockOrder.viewsets import StockOrderViewSet
from stockFundMng.viewsets import StockFundMngViewSet
from stockBalance.viewsets import StockBalanceViewSet
from stockMarketMng.viewsets import StockMarketMngViewSet
from stockOrderComplete.viewsets import StockOrderCompleteViewSet
from stockAccount.viewsets import StockAccountViewSet

router = routers.DefaultRouter()
router.register(r'stockOrder', StockOrderViewSet)
router.register(r'stockFundMng', StockFundMngViewSet)
router.register(r'stockBalance', StockBalanceViewSet)
router.register(r'stockMarketMng', StockMarketMngViewSet)
router.register(r'stockOrderComplete', StockOrderCompleteViewSet)
router.register(r'stockAccount', StockAccountViewSet)