from .models import stock_account
from datetime import datetime
from kis import auth as auth
from django.http import JsonResponse

# Create your views here.

def basic(request):
    nick_name = request.GET.get('nick_name', '')

    stock_account_info = stock_account.objects.filter(nick_name=nick_name).first()

    if len(stock_account_info.app_key) > 0:
        access_token = stock_account_info.access_token
        token_publ_date = stock_account_info.token_publ_date

        if len(access_token) > 0:
            YmdHMS = datetime.now()
            validTokenDate = datetime.strptime(token_publ_date,'%Y%m%d%H%M%S')
            diff = YmdHMS - validTokenDate

            if diff.days >= 1:    # 토큰 유효기간(1일) 만료 재발급
                access_token = auth.basic(stock_account_info.app_key, stock_account_info.app_secret)
                token_publ_date = datetime.now().strftime("%Y%m%d%H%M%S")

                stock_account.objects.filter(nick_name=nick_name).update(access_token=access_token, token_publ_date=token_publ_date, last_chg_date=datetime.now())
        else:   # 토큰발급(최초)
            access_token = auth.basic(stock_account_info.app_key, stock_account_info.app_secret)
            token_publ_date = datetime.now().strftime("%Y%m%d%H%M%S")

            stock_account.objects.filter(nick_name=nick_name).update(access_token=access_token, token_publ_date=token_publ_date, last_chg_date=datetime.now())

    stock_account_rtn = stock_account.objects.filter(nick_name=nick_name).first()
    stock_account_rtn_list = []

    if len(stock_account_rtn.access_token) > 0:
        stock_account_rtn_list.append({'acct_no': stock_account_rtn.acct_no, 'access_token': stock_account_rtn.access_token, 'token_publ_date': stock_account_rtn.token_publ_date, 'app_key': stock_account_rtn.app_key, 'app_secret': stock_account_rtn.app_secret, 'tel_no': stock_account_rtn.tel_no})

    return JsonResponse(stock_account_rtn_list, safe=False)

def init(request):
    nick_name = request.GET.get('nick_name', '')

    stock_account_info = stock_account.objects.filter(nick_name=nick_name).first()

    if len(stock_account_info.app_key) > 0:
        stock_account.objects.filter(nick_name=nick_name).update(access_token='', token_publ_date='', last_chg_date=datetime.now())

    stock_account_rtn = stock_account.objects.filter(nick_name=nick_name).first()
    stock_account_rtn_list = []

    if len(stock_account_rtn.access_token) > 0:
        stock_account_rtn_list.append(
                {'acct_no': stock_account_rtn.acct_no, 'access_token': stock_account_rtn.access_token,
                 'token_publ_date': stock_account_rtn.token_publ_date, 'app_key': stock_account_rtn.app_key,
                 'app_secret': stock_account_rtn.app_secret, 'tel_no': stock_account_rtn.tel_no})

    return JsonResponse(stock_account_rtn_list, safe=False)