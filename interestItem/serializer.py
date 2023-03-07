from rest_framework import serializers  # serializer import
from .models import interest_item  # 선언한 모델 import

class InterestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = interest_item  # 모델 설정
        fields = ('acct_no', 'code', 'name', 'through_price', 'leave_price', 'resist_price', 'support_price', 'trend_high_price', 'trend_low_price', 'last_chg_date') #필드 설정