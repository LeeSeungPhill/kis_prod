from django.http import JsonResponse
from .models import interest_item
from datetime import datetime
from kis import kis_api_resp as resp
import requests
import math

#URL_BASE = "https://openapivts.koreainvestment.com:29443"   # 모의투자서비스
URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

def list(request):
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    if interest_item.objects.filter(acct_no=acct_no).count() > 0:

        interest_item_rtn = interest_item.objects.filter(acct_no=acct_no).order_by('-last_chg_date')
        interest_item_rtn_list = []

        today = datetime.now().strftime("%Y%m%d")

        for index, rtn in enumerate(interest_item_rtn, start=1):

            rtn.K_through_price = ""
            rtn.D_leave_price = ""
            rtn.K_resist_price = ""
            rtn.D_support_price = ""
            rtn.K_trend_high_price = ""
            rtn.D_trend_low_price = ""

            if len(rtn.code) == 6:
                # 주식현재가 시세
                a = inquire_price(access_token, app_key, app_secret, rtn.code)
                current_price = format(int(a['stck_prpr']), ',d')
                print("현재가 : "+current_price)
                if int(a['stck_prpr']) > int(rtn.through_price):
                    rtn.K_through_price = "1"
                if int(a['stck_prpr']) < int(rtn.leave_price):
                    rtn.D_leave_price = "1"
                if int(a['stck_prpr']) > int(rtn.resist_price):
                    rtn.K_resist_price = "1"
                if int(a['stck_prpr']) < int(rtn.support_price):
                    rtn.D_support_price = "1"
                if int(a['stck_prpr']) > int(rtn.trend_high_price):
                    rtn.K_trend_high_price = "1"
                if int(a['stck_prpr']) < int(rtn.trend_low_price):
                    rtn.D_trend_low_price = "1"

            elif len(rtn.code) == 4:
                b = inquire_daily_indexchartprice(access_token, app_key, app_secret, rtn.code, today)
                current_price = '{:0,.2f}'.format(float(b['bstp_nmix_prpr']), ',f')
                print("현재가 : " + current_price)
                if math.ceil(float(b['bstp_nmix_prpr'])) > int(rtn.through_price):
                    rtn.K_through_price = "1"
                if math.ceil(float(b['bstp_nmix_prpr'])) < int(rtn.leave_price):
                    rtn.D_leave_price = "1"
                if math.ceil(float(b['bstp_nmix_prpr'])) > int(rtn.resist_price):
                    rtn.K_resist_price = "1"
                if math.ceil(float(b['bstp_nmix_prpr'])) < int(rtn.support_price):
                   rtn.D_support_price = "1"
                if math.ceil(float(b['bstp_nmix_prpr'])) > int(rtn.trend_high_price):
                   rtn.K_trend_high_price = "1"
                if math.ceil(float(b['bstp_nmix_prpr'])) < int(rtn.trend_low_price):
                   rtn.D_trend_low_price = "1"

            interest_item_rtn_list.append(
                {'id': rtn.id, 'acct_no': rtn.acct_no, 'code': rtn.code, 'name': rtn.name, 'K_through_price': rtn.K_through_price, 'D_leave_price': rtn.D_leave_price, 'K_resist_price': rtn.K_resist_price, 'D_support_price': rtn.D_support_price,
                 'K_trend_high_price': rtn.K_trend_high_price, 'D_trend_low_price': rtn.D_trend_low_price, 'stck_prpr': current_price,
                 'through_price': format(int(rtn.through_price), ',d'), 'leave_price': format(int(rtn.leave_price), ',d'), 'resist_price': format(int(rtn.resist_price), ',d'), 'support_price': format(int(rtn.support_price), ',d'),
                 'trend_high_price': format(int(rtn.trend_high_price), ',d'), 'trend_low_price': format(int(rtn.trend_low_price), ',d'), 'last_chg_date': rtn.last_chg_date})

    else:
        interest_item_rtn_list = []

    return JsonResponse(interest_item_rtn_list, safe=False)

def update(request):
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
    id = request.GET.get('id', '')
    through_price = str(int(request.GET.get('through_price', '').replace(",", "")))
    leave_price = str(int(request.GET.get('leave_price', '').replace(",", "")))
    resist_price = str(int(request.GET.get('resist_price', '').replace(",", "")))
    support_price = str(int(request.GET.get('support_price', '').replace(",", "")))
    trend_high_price = str(int(request.GET.get('trend_high_price', '').replace(",", "")))
    trend_low_price = str(int(request.GET.get('trend_low_price', '').replace(",", "")))

    interest_item.objects.filter(id=id).update(
                    through_price=int(through_price),
                    leave_price=int(leave_price),
                    resist_price=int(resist_price),
                    support_price=int(support_price),
                    trend_high_price=int(trend_high_price),
                    trend_low_price=int(trend_low_price),
                    last_chg_date=datetime.now()
                )

    interest_item_rtn = interest_item.objects.filter(acct_no=acct_no).order_by('-last_chg_date')
    interest_item_rtn_list = []

    today = datetime.now().strftime("%Y%m%d")

    for index, rtn in enumerate(interest_item_rtn, start=1):

        rtn.K_through_price = ""
        rtn.D_leave_price = ""
        rtn.K_resist_price = ""
        rtn.D_support_price = ""
        rtn.K_trend_high_price = ""
        rtn.D_trend_low_price = ""

        if len(rtn.code) == 6:
            # 주식현재가 시세
            a = inquire_price(access_token, app_key, app_secret, rtn.code)
            current_price = format(int(a['stck_prpr']), ',d')
            print("현재가 : " + current_price)
            if int(a['stck_prpr']) > int(rtn.through_price):
                rtn.K_through_price = "1"
            if int(a['stck_prpr']) < int(rtn.leave_price):
                rtn.D_leave_price = "1"
            if int(a['stck_prpr']) > int(rtn.resist_price):
                rtn.K_resist_price = "1"
            if int(a['stck_prpr']) < int(rtn.support_price):
                rtn.D_support_price = "1"
            if int(a['stck_prpr']) > int(rtn.trend_high_price):
                rtn.K_trend_high_price = "1"
            if int(a['stck_prpr']) < int(rtn.trend_low_price):
                rtn.D_trend_low_price = "1"

        elif len(rtn.code) == 4:
            b = inquire_daily_indexchartprice(access_token, app_key, app_secret, rtn.code, today)
            current_price = '{:0,.2f}'.format(float(b['bstp_nmix_prpr']), ',f')
            print("현재가 : " + current_price)
            if math.ceil(float(b['bstp_nmix_prpr'])) > int(rtn.through_price):
                rtn.K_through_price = "1"
            if math.ceil(float(b['bstp_nmix_prpr'])) < int(rtn.leave_price):
                rtn.D_leave_price = "1"
            if math.ceil(float(b['bstp_nmix_prpr'])) > int(rtn.resist_price):
                rtn.K_resist_price = "1"
            if math.ceil(float(b['bstp_nmix_prpr'])) < int(rtn.support_price):
                rtn.D_support_price = "1"
            if math.ceil(float(b['bstp_nmix_prpr'])) > int(rtn.trend_high_price):
                rtn.K_trend_high_price = "1"
            if math.ceil(float(b['bstp_nmix_prpr'])) < int(rtn.trend_low_price):
                rtn.D_trend_low_price = "1"

        interest_item_rtn_list.append(
            {'id': rtn.id, 'acct_no': rtn.acct_no, 'code': rtn.code, 'name': rtn.name, 'K_through_price': rtn.K_through_price, 'D_leave_price': rtn.D_leave_price, 'K_resist_price': rtn.K_resist_price, 'D_support_price': rtn.D_support_price,
             'K_trend_high_price': rtn.K_trend_high_price, 'D_trend_low_price': rtn.D_trend_low_price, 'stck_prpr': current_price,
             'through_price': format(int(rtn.through_price), ',d'), 'leave_price': format(int(rtn.leave_price), ',d'), 'resist_price': format(int(rtn.resist_price), ',d'), 'support_price': format(int(rtn.support_price), ',d'),
             'trend_high_price': format(int(rtn.trend_high_price), ',d'), 'trend_low_price': format(int(rtn.trend_low_price), ',d'), 'last_chg_date': rtn.last_chg_date})

    return JsonResponse(interest_item_rtn_list, safe=False)

# 주식현재가 시세
def inquire_price(access_token, app_key, app_secret, code):

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "FHKST01010100"}
    params = {
            'FID_COND_MRKT_DIV_CODE': "J",
            'FID_INPUT_ISCD': code
    }
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)

    return ar.getBody().output

# 국내주식업종기간별시세
def inquire_daily_indexchartprice(access_token, app_key, app_secret, market, stock_day):

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "FHKUP03500100",
               "custtype": "P"}
    params = {
        'FID_COND_MRKT_DIV_CODE': "U",  # 시장 분류 코드(J : 주식, ETF, ETN U: 업종)
        'FID_INPUT_ISCD': market,
        'FID_INPUT_DATE_1': stock_day,
        'FID_INPUT_DATE_2': stock_day,
        'FID_PERIOD_DIV_CODE': 'D'}
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)

    return ar.getBody().output1
