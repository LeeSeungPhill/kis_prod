from django.db import models

# Create your models here.
class stock_fund_mng(models.Model):
    asset_num = models.BigIntegerField()                                # 자산번호(상승->하락전환, 하락->상승전환 구간시 생성)
    acct_no = models.IntegerField()                                     # 계좌번호
    cash_rate = models.IntegerField()                                   # 현금비중(상승추세:현금비중 30%, 패턴:현금비중 50%, 하락추세:현금비중 70%)
    tot_evlu_amt = models.BigIntegerField(null=True, blank=True)        # 총평가금액
    cash_rate_amt = models.BigIntegerField(null=True, blank=True)       # 총평가금액 기준 현금 비중 금액
    dnca_tot_amt = models.BigIntegerField(null=True, blank=True)        # 예수금 총금액
    prvs_rcdl_excc_amt = models.BigIntegerField(null=True, blank=True)  # 가수도 정산금액
    nass_amt = models.BigIntegerField(null=True, blank=True)            # 순자산금액(세금비용 제외)
    scts_evlu_amt = models.BigIntegerField(null=True, blank=True)       # 유저평가금액
    asset_icdc_amt = models.BigIntegerField(null=True, blank=True)      # 자산증감액
    sell_plan_amt = models.BigIntegerField(null=True, blank=True)       # 매도예정자금(총평가금액 기준 현금비중금액 - 가수도 정산금액)
    buy_plan_amt = models.BigIntegerField(null=True, blank=True)        # 매수예정자금(가수도 정산금액 - 총평가금액 기준 현금비중금액)
    last_chg_date = models.DateTimeField(auto_now=True)                 # 최종 변경일시

    class Meta:
        unique_together = (('asset_num', 'acct_no'),)