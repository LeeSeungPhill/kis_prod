from rest_framework import serializers  # serializer import
from .models import stock_market_mng  # 선언한 모델 import

class StockMarketMngSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_market_mng  # 모델 설정
        fields = ('asset_risk_num', 'acct_no', 'market_level_num', 'total_asset', 'risk_rate', 'risk_sum', 'item_number', 'aply_start_dt', 'aply_end_dt')  # 필드 설정
