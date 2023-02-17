from rest_framework import serializers  # serializer import
from stockFundMng.models import stock_fund_mng  # 선언한 모델 import

class StockFundMngSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_fund_mng  # 모델 설정
        fields = ('asset_num', 'acct_no', 'cash_rate', 'tot_evlu_amt', 'cash_rate_amt', 'dnca_tot_amt', 'prvs_rcdl_excc_amt', 'nass_amt', 'scts_evlu_amt', 'asset_icdc_amt','sell_plan_amt', 'buy_plan_amt', 'last_chg_date')  # 필드 설정