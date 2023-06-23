from django.db import models

# Create your models here.
class interest_item(models.Model):
    acct_no = models.IntegerField()                                     # 계좌번호
    code = models.CharField(max_length=100)                             # 종목코드
    name = models.CharField(max_length=100)                             # 종목명
    through_price = models.IntegerField(null=True, blank=True)          # 돌파가격
    leave_price = models.IntegerField(null=True, blank=True)            # 이탈가격
    resist_price = models.IntegerField(null=True, blank=True)           # 저항가격
    support_price = models.IntegerField(null=True, blank=True)          # 지지가격
    trend_high_price = models.IntegerField(null=True, blank=True)       # 추세상단가격
    trend_low_price = models.IntegerField(null=True, blank=True)        # 추세하단가격
    buy_expect_sum = models.IntegerField(null=True, blank=True)         # 매수예상금액
    last_chg_date = models.DateTimeField(auto_now=True)                 # 최종 변경일시

    class Meta:
        unique_together = (('acct_no', 'code'),)