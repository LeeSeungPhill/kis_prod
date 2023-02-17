from django.db import models

# Create your models here.

class stock_account(models.Model):
    acct_no = models.IntegerField(primary_key=True)                     # 계좌번호
    nick_name = models.CharField(max_length=100)                        # 닉네임
    access_token = models.CharField(max_length=400)                     # 접속토큰
    token_publ_date = models.CharField(max_length=14)                   # 토큰 발행일시(연월일시분초)
    app_key = models.CharField(max_length=100)                          # 앱키
    app_secret = models.CharField(max_length=200)                       # 비밀키
    tel_no = models.CharField(max_length=11)                            # 휴대폰번호
    last_chg_date = models.DateTimeField(auto_now=True)                 # 최종 변경일시