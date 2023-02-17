from django.db import models

# Create your models here.

class stock_market_mng(models.Model):
    asset_risk_num = models.IntegerField()                          # 자산리스크번호
    acct_no = models.IntegerField()                                 # 계좌번호
    market_level_num = models.CharField(max_length=1)               # 시장레벨번호(1:하락 지속 후, 기술적 반등, 2:단기 추세 전환 후, 기술적 반등, 3:패턴내에서 기술적 반등, 4:일봉상 추세 전환 후, 눌림구간에서 반등, 5:상승 지속 후, 패턴내에서 기술적 반등)
    total_asset = models.BigIntegerField()                          # 총자산
    risk_rate = models.DecimalField(max_digits=3, decimal_places=1) # 리스크(%)
    risk_sum = models.BigIntegerField()                             # 리스크 금액(총자산 * 리스크)
    item_number = models.IntegerField()                             # 종목수
    aply_start_dt = models.CharField(max_length=8, null=True)       # 적용시작일시
    aply_end_dt = models.CharField(max_length=8, null=True)         # 적용종료일시

    class Meta:
        unique_together = (('asset_risk_num', 'acct_no'),)