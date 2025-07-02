from rest_framework import serializers  # serializer import
from stockBalance.models import stock_balance  # 선언한 모델 import

class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_balance  # 모델 설정
        fields = ('acct_no', 'code', 'name', 'purchase_price', 'purchase_amount', 'purchase_sum', 'avail_amount', 'current_price', 'eval_sum', 'earnings_rate', 'valuation_sum', 'sign_support_price', 'sign_resist_price', 'end_loss_price', 'end_target_price', 'trading_plan', 'limit_price', 'limit_amt', 'asset_num', 'sell_plan_sum', 'sell_plan_amount', "proc_yn', "'last_chg_date')  # 필드 설정