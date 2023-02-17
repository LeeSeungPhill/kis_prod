from django.db import models

# Create your models here.

class stock_balance(models.Model):
    acct_no = models.IntegerField()                                     # 계좌번호
    name = models.CharField(max_length=100)                             # 종목명
    purchase_price = models.IntegerField()                              # 매입가
    purchase_amount = models.IntegerField()                             # 보유수량
    purchase_sum = models.BigIntegerField()                             # 매입금액
    current_price = models.IntegerField()                               # 현재가
    eval_sum = models.BigIntegerField()                                 # 평가금액
    earnings_rate = models.IntegerField()                               # 수익률
    valuation_sum = models.BigIntegerField()                            # 평가손익금액
    end_loss_price = models.IntegerField(null=True, blank=True)         # 최종손절가
    end_target_price = models.IntegerField(null=True, blank=True)       # 최종목표가
    trading_plan = models.CharField(max_length=3, null=True)            # 매매계획(B:분할 매수, S:분할 매도, H: 기본홀딩)
    asset_num = models.BigIntegerField()                                # 자산번호(상승->하락전환, 하락->상승전환 구간시 생성)
    sell_plan_sum = models.BigIntegerField(null=True, blank=True)       # 매도가능금액
    sell_plan_amount = models.IntegerField(null=True, blank=True)       # 매도가능수량
    last_chg_date = models.DateTimeField(auto_now=True)	                # 최종 변경일시

    class Meta:
        unique_together = (('acct_no', 'name', 'asset_num'),)
