from django.db import models

# Create your models here.
class stock_order_complete(models.Model):
    acct_no = models.IntegerField()                                     # 계좌번호
    order_no = models.CharField(max_length=10)                          # 주문번호
    org_order_no = models.CharField(max_length=10)                      # 원 주문번호
    order_type = models.CharField(max_length=100)                       # 주문구분
    order_dt = models.CharField(max_length=8)                           # 주문일자
    order_tmd = models.CharField(max_length=6)                          # 주문시각
    name = models.CharField(max_length=100)                             # 종목명
    order_price = models.CharField(max_length=100)                      # 주문가
    order_amount = models.CharField(max_length=100)                     # 주문수량
    total_complete_qty = models.CharField(max_length=100)               # 총체결수량
    remain_qty = models.CharField(max_length=100)                       # 잔여수량
    total_complete_amt = models.CharField(max_length=100)               # 총체결금액
    last_chg_date = models.DateTimeField(auto_now=True)                 # 최종 변경일시

    class Meta:
        unique_together = (('acct_no', 'order_no', 'org_order_no'),)