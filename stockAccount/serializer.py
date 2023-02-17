from rest_framework import serializers  # serializer import
from .models import stock_account  # 선언한 모델 import

class StockAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = stock_account  # 모델 설정
        fields = ('acct_no', 'nick_name', 'access_token', 'token_publ_date', 'app_key', 'app_secret', 'tel_no', 'last_chg_date')  # 필드 설정
