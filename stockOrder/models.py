from django.db import models

# Create your models here.
class stock_order(models.Model):
    id = models.AutoField(primary_key=True)                                 # id(pk : 1씩 자동증가)
    acct_no = models.IntegerField()                                         # 계좌번호
    code = models.CharField(max_length=100)                                 # 종목코드
    name = models.CharField(max_length=100)                                 # 종목명
    buy_price = models.IntegerField(null=True, blank=True)                  # 매수가
    buy_amount = models.IntegerField(null=True, blank=True)                 # 매수량
    sell_price = models.IntegerField(null=True, blank=True)                 # 매도가
    sell_amount = models.IntegerField(null=True, blank=True)                # 매도량
    loss_price = models.IntegerField(null=True, blank=True)                 # 손절가
    target_price = models.IntegerField(null=True, blank=True)               # 목표가
    trading_type = models.CharField(max_length=1, null=True)                # 매매유형(B:매수, S:매도)
    asset_risk_num = models.IntegerField()                                  # 자산리스크번호(총자산, 계좌리스크, 종목수 기준)
    asset_num = models.BigIntegerField()                                    # 자산번호(상승->하락전환, 하락->상승전환 구간시 생성)
    proc_yn = models.CharField(max_length=1, null=True)                     # 처리여부
    order_no = models.CharField(max_length=10)                              # 주문번호
    order_stat = models.CharField(max_length=10)                            # 주문상태(01:신청, 02:등록, 03:체결, 04:취소, 05:정정)
    total_complete_qty = models.IntegerField(null=True, blank=True)         # 총체결수량
    remain_qty = models.IntegerField(null=True, blank=True)                 # 잔여수량
    create_date = models.DateTimeField(auto_now_add=True)                   # 생성일시
    proc_date = models.DateTimeField(auto_now=True)                         # 처리일시