from rest_framework import serializers  # serializer import
from .models import stock_order_complete  # 선언한 모델 import

class StockOrderCompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_order_complete  # 모델 설정
        fields = ('acct_no', 'order_no', 'org_order_no', 'order_type', 'order_dt', 'order_tmd', 'name', 'order_price', 'order_amount', 'total_complete_qty', 'remain_qty', 'total_complete_amt', 'last_chg_date')  # 필드 설정
