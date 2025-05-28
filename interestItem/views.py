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

        interest_item_rtn = interest_item.objects.filter(acct_no=acct_no).order_by('code')
        interest_item_rtn_list = []

        today = datetime.now().strftime("%Y%m%d")

        for index, rtn in enumerate(interest_item_rtn, start=1):

            rtn.K_through_price = ""
            rtn.D_leave_price = ""
            rtn.K_resist_price = ""
            rtn.D_support_price = ""
            rtn.K_trend_high_price = ""
            rtn.D_trend_low_price = ""
            total_market_value = 0

            if len(rtn.code) == 6:
                # 주식현재가 시세
                a = inquire_price(access_token, app_key, app_secret, rtn.code)
                current_price = format(int(a['stck_prpr']), ',d')
                print("현재가 : "+current_price)
                prdy_vol_rate = format(round(float(a['prdy_vrss_vol_rate'])), ',d')
                print("전일대비거래량 : " + str(prdy_vol_rate))
                total_market_value = format(int(a['hts_avls']), ',d')
                print("시가총액 : " + total_market_value)
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
                prdy_vol_rate = format(round(int(b['acml_vol']) / int(b['prdy_vol']) * 100), ',d')
                print("전일대비거래량 : " + str(prdy_vol_rate))
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
                 'K_trend_high_price': rtn.K_trend_high_price, 'D_trend_low_price': rtn.D_trend_low_price, 'stck_prpr': current_price, 'prdy_vol_rate': prdy_vol_rate,
                 'through_price': rtn.through_price, 'leave_price': rtn.leave_price, 'resist_price': rtn.resist_price, 'support_price': rtn.support_price,
                 'trend_high_price': rtn.trend_high_price, 'trend_low_price': rtn.trend_low_price, 'buy_expect_sum': rtn.buy_expect_sum, 'total_market_value': total_market_value, 'last_chg_date': rtn.last_chg_date})

    else:
        interest_item_rtn_list = []

    return JsonResponse(interest_item_rtn_list, safe=False)

def update(request):
    # id = request.GET.get('id', '')
    code = request.GET.get('code', '')
    through_price = str(int(request.GET.get('through_price', '').replace(",", "")))
    leave_price = str(int(request.GET.get('leave_price', '').replace(",", "")))
    resist_price = str(int(request.GET.get('resist_price', '').replace(",", "")))
    support_price = str(int(request.GET.get('support_price', '').replace(",", "")))
    trend_high_price = str(int(request.GET.get('trend_high_price', '').replace(",", "")))
    trend_low_price = str(int(request.GET.get('trend_low_price', '').replace(",", "")))
    buy_expect_sum = str(int(request.GET.get('buy_expect_sum', '').replace(",", "")))

    result = interest_item.objects.filter(code=code).update(
        through_price=int(through_price),
        leave_price=int(leave_price),
        resist_price=int(resist_price),
        support_price=int(support_price),
        trend_high_price=int(trend_high_price),
        trend_low_price=int(trend_low_price),
        buy_expect_sum=int(buy_expect_sum),
        last_chg_date=datetime.now()
    )

    return JsonResponse(result, safe=False)

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
