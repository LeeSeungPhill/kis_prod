from django.http import JsonResponse
from .models import stock_market_mng
from kis import kis_api_resp as resp
from django.utils.dateformat import DateFormat
from datetime import datetime
import requests
import pandas as pd

# Create your views here.

def list(request):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"   # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
    # 시장레벨번호(1:하락 지속 후, 기술적 반등, 2:단기 추세 전환 후, 기술적 반등, 3:패턴내에서 기술적 반등, 4:일봉상 추세 전환 후, 눌림구간에서 반등, 5:상승 지속 후, 패턴내에서 기술적 반등)
    marketInfo = request.GET.get('market_level', '')

    # marketInfo 값 존재시, 시장 관리 정보 신규 생성
    if marketInfo != '':
        changeDate = DateFormat(datetime.now()).format('Ymd')

        try:
            # 잔고조회
            headers = {"Content-Type": "application/json",
                       "authorization": f"Bearer {access_token}",
                       "appKey": app_key,
                       "appSecret": app_secret,
                       "tr_id": "TTTC8434R"}    # tr_id : TTTC8434R[실전투자], VTTC8434R[모의투자]
            params = {
                "CANO": acct_no,
                'ACNT_PRDT_CD': '01',
                'AFHR_FLPR_YN': 'N',
                'FNCG_AMT_AUTO_RDPT_YN': 'N',
                'FUND_STTL_ICLD_YN': 'N',
                'INQR_DVSN': '01',
                'OFL_YN': 'N',
                'PRCS_DVSN': '01',
                'UNPR_DVSN': '01',
                'CTX_AREA_FK100': '',
                'CTX_AREA_NK100': ''
            }
            PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
            URL = f"{URL_BASE}/{PATH}"
            res = requests.get(URL, headers=headers, params=params, verify=False)
            ar = resp.APIResp(res)
            output2 = ar.getBody().output2

            if ar.isOK() and output2:
                f = pd.DataFrame(output2)
                for i, name in enumerate(f.index):
                    u_prvs_rcdl_excc_amt = int(f['prvs_rcdl_excc_amt'][i])      # 가수도 정산 금액

                if marketInfo == "1":   # 하락 지속 후, 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 30 * 0.01
                    if n_asset_sum < 10000000:
                        n_asset_sum = 10000000
                        n_risk_rate = 2
                        n_stock_num = 2
                    elif n_asset_sum > 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 2
                        n_stock_num = 4
                    else:
                        n_risk_rate = 1.8
                        n_stock_num = 3
                elif marketInfo == "2": # 단기 추세 전환 후, 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 30 * 0.01
                    if n_asset_sum < 20000000:
                        n_asset_sum = 20000000
                        n_risk_rate = 3
                        n_stock_num = 4
                    elif n_asset_sum > 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 4
                        n_stock_num = 6
                    else:
                        n_risk_rate = 3.5
                        n_stock_num = 5
                elif marketInfo == "3": # 패턴내에서 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 50 * 0.01
                    if n_asset_sum < 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 4
                        n_stock_num = 6
                    elif n_asset_sum > 50000000:
                        n_asset_sum = 50000000
                        n_risk_rate = 4
                        n_stock_num = 8
                    else:
                        n_risk_rate = 2.8
                        n_stock_num = 5
                elif marketInfo == "4": # 일봉상 추세 전환 후, 눌림구간에서 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 70 * 0.01
                    if n_asset_sum < 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 5.5
                        n_stock_num = 8
                    elif n_asset_sum > 70000000:
                        n_asset_sum = 70000000
                        n_risk_rate = 3.5
                        n_stock_num = 10
                    else:
                        n_risk_rate = 5
                        n_stock_num = 10
                elif marketInfo == "5": # 상승 지속 후, 패턴내에서 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 50 * 0.01
                    if n_asset_sum < 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 4
                        n_stock_num = 6
                    elif n_asset_sum > 50000000:
                        n_asset_sum = 50000000
                        n_risk_rate = 4
                        n_stock_num = 8
                    else:
                        n_risk_rate = 2.8
                        n_stock_num = 5
                else:
                    n_asset_sum = u_prvs_rcdl_excc_amt * 30 * 0.01
                    if n_asset_sum < 10000000:
                        n_asset_sum = 10000000
                        n_risk_rate = 2
                        n_stock_num = 2
                    elif n_asset_sum > 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 2
                        n_stock_num = 4
                    else:
                        n_risk_rate = 1.8
                        n_stock_num = 3

                n_risk_sum = n_asset_sum * n_risk_rate * 0.01
                print("리스크 금액 : " + format(int(n_risk_sum), ',d'))
                n_asset_risk_num = marketInfo + changeDate

                stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').update(aply_end_dt=changeDate)
                stock_market_mng.objects.update_or_create(
                    asset_risk_num=int(n_asset_risk_num), acct_no=acct_no,
                    defaults={'asset_risk_num': int(n_asset_risk_num),  # 자산리스크번호
                              'acct_no': acct_no,                       # 계좌번호
                              'market_level_num': int(marketInfo),      # 시장레벨번호(1:하락 지속 후, 기술적 반등, 2:단기 추세 전환 후, 기술적 반등, 3:패턴내에서 기술적 반등, 4:일봉상 추세 전환 후, 눌림구간에서 반등, 5:상승 지속 후, 패턴내에서 기술적 반등)
                              'total_asset': n_asset_sum,               # 총자산
                              'risk_rate': n_risk_rate,                 # 리스크(%)
                              'risk_sum': n_risk_sum,                   # 리스크 금액(총자산 * 리스크)
                              'item_number': n_stock_num,               # 종목수
                              'aply_start_dt': changeDate,
                              'aply_end_dt': "99991231"
                              }
                )
        except Exception as e:
            print('잘못된 인덱스입니다.', e)
    elif stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').count() > 0:
        asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()
        try:
            # 잔고조회
            headers = {"Content-Type": "application/json",
                       "authorization": f"Bearer {access_token}",
                       "appKey": app_key,
                       "appSecret": app_secret,
                       "tr_id": "TTTC8434R"}    # tr_id : TTTC8434R[실전투자], VTTC8434R[모의투자]
            params = {
                "CANO": acct_no,
                'ACNT_PRDT_CD': '01',
                'AFHR_FLPR_YN': 'N',
                'FNCG_AMT_AUTO_RDPT_YN': 'N',
                'FUND_STTL_ICLD_YN': 'N',
                'INQR_DVSN': '01',
                'OFL_YN': 'N',
                'PRCS_DVSN': '01',
                'UNPR_DVSN': '01',
                'CTX_AREA_FK100': '',
                'CTX_AREA_NK100': ''
            }
            PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
            URL = f"{URL_BASE}/{PATH}"
            res = requests.get(URL, headers=headers, params=params, verify=False)
            ar = resp.APIResp(res)
            output2 = ar.getBody().output2

            if ar.isOK() and output2:
                f = pd.DataFrame(output2)
                for i, name in enumerate(f.index):
                    u_prvs_rcdl_excc_amt = int(f['prvs_rcdl_excc_amt'][i])      # 가수도 정산 금액
                print("가수도 정산 금액 : " + format(int(u_prvs_rcdl_excc_amt), ',d'))
                if asset_risk_info.market_level_num == "1":   # 하락 지속 후, 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 30 * 0.01
                    if n_asset_sum < 10000000:
                        n_asset_sum = 10000000
                        n_risk_rate = 2
                        n_stock_num = 2
                    elif n_asset_sum > 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 2
                        n_stock_num = 4
                    else:
                        n_risk_rate = 1.8
                        n_stock_num = 3
                elif asset_risk_info.market_level_num == "2": # 단기 추세 전환 후, 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 30 * 0.01
                    if n_asset_sum < 20000000:
                        n_asset_sum = 20000000
                        n_risk_rate = 3
                        n_stock_num = 4
                    elif n_asset_sum > 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 4
                        n_stock_num = 6
                    else:
                        n_risk_rate = 3.5
                        n_stock_num = 5
                elif asset_risk_info.market_level_num == "3": # 패턴내에서 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 50 * 0.01
                    if n_asset_sum < 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 4
                        n_stock_num = 6
                    elif n_asset_sum > 50000000:
                        n_asset_sum = 50000000
                        n_risk_rate = 4
                        n_stock_num = 8
                    else:
                        n_risk_rate = 2.8
                        n_stock_num = 5
                elif asset_risk_info.market_level_num == "4": # 일봉상 추세 전환 후, 눌림구간에서 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 70 * 0.01
                    if n_asset_sum < 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 5.5
                        n_stock_num = 8
                    elif n_asset_sum > 70000000:
                        n_asset_sum = 70000000
                        n_risk_rate = 3.5
                        n_stock_num = 10
                    else:
                        n_risk_rate = 5
                        n_stock_num = 10
                elif asset_risk_info.market_level_num == "5": # 상승 지속 후, 패턴내에서 기술적 반등
                    n_asset_sum = u_prvs_rcdl_excc_amt * 50 * 0.01
                    if n_asset_sum < 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 4
                        n_stock_num = 6
                    elif n_asset_sum > 50000000:
                        n_asset_sum = 50000000
                        n_risk_rate = 4
                        n_stock_num = 8
                    else:
                        n_risk_rate = 2.8
                        n_stock_num = 5
                else:
                    n_asset_sum = u_prvs_rcdl_excc_amt * 30 * 0.01
                    if n_asset_sum < 10000000:
                        n_asset_sum = 10000000
                        n_risk_rate = 2
                        n_stock_num = 2
                    elif n_asset_sum > 30000000:
                        n_asset_sum = 30000000
                        n_risk_rate = 2
                        n_stock_num = 4
                    else:
                        n_risk_rate = 1.8
                        n_stock_num = 3

                n_risk_sum = n_asset_sum * n_risk_rate * 0.01
                print("리스크 금액 : " + format(int(n_risk_sum), ',d'))

                stock_market_mng.objects.filter(acct_no=acct_no, asset_risk_num=asset_risk_info.asset_risk_num, aply_end_dt='99991231').update(total_asset=n_asset_sum, risk_rate=n_risk_rate, risk_sum=n_risk_sum, item_number=n_stock_num)
        except Exception as e:
            print('잘못된 인덱스입니다.', e)

    if stock_market_mng.objects.filter(acct_no=acct_no).count() > 0:

        stock_market_mng_rtn = stock_market_mng.objects.filter(acct_no=acct_no).order_by('-aply_end_dt')
        stock_market_mng_rtn_list = []

        for index, rtn in enumerate(stock_market_mng_rtn, start=1):
            stock_market_mng_rtn_list.append(
                {'asset_risk_num': rtn.asset_risk_num, 'acct_no': rtn.acct_no, 'market_level_num': rtn.market_level_num, 'total_asset': format(int(rtn.total_asset), ',d'), 'risk_rate': rtn.risk_rate,
                 'risk_sum': format(int(rtn.risk_sum), ',d'), 'item_risk_sum': format(int(int(rtn.risk_sum)/int(rtn.item_number)), ',d'), 'item_number': rtn.item_number, 'aply_start_dt': rtn.aply_start_dt, 'aply_end_dt': rtn.aply_end_dt})

    else:
        stock_market_mng_rtn_list = []

    return JsonResponse(stock_market_mng_rtn_list, safe=False)
