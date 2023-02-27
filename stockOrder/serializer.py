from rest_framework import serializers  # serializer import
from stockOrder.models import stock_order, sub_total  # 선언한 모델 import

class StockOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_order  # 모델 설정
        fields = ('id', 'acct_no', 'code', 'name', 'buy_price', 'buy_amount', 'sell_price', 'sell_amount', 'loss_price', 'target_price', 'trading_type', 'asset_risk_num', 'asset_num', 'proc_yn', 'order_no', 'order_stat', 'total_complete_qty', 'remain_qty', 'create_date', 'proc_date')  # 필드 설정

class SubTotalSerializer(serializers.ModelSerializer):
    class Meta:
        model = sub_total  # 모델 설정
        fields = ('id', 'tr_day', 'tr_time', 'tr_subject', 'market_type', 'tr_type', 'code', 'name', 'tr_order', 'volumn') #필드 설정