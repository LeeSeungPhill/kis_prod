from rest_framework import serializers  # serializer import
from stockBalance.models import stock_balance  # 선언한 모델 import

class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_balance  # 모델 설정
        fields = ('acct_no', 'name', 'purchase_price', 'purchase_amount', 'purchase_sum', 'current_price', 'eval_sum', 'earnings_rate', 'valuation_sum', 'end_loss_price', 'end_target_price', 'trading_plan', 'asset_num', 'sell_plan_sum', 'sell_plan_amount', 'last_chg_date')  # 필드 설정