from django.http import JsonResponse
from .models import stock_fund_mng
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
    assetInfo = request.GET.get('market_change', '')    # market_change=d : 하락, market_change=u : 상승

    # assetInfo 값 존재시, 자산 관리 정보 신규 생성
    if assetInfo != '':
        n_asset_date = DateFormat(datetime.now()).format('Ymd')
        if assetInfo == "d":
            n_cash_rate = 70  # 하락 추세
        elif assetInfo == "u":
            n_cash_rate = 30  # 상승 추세
        else:
            n_cash_rate = 50  # 패턴 움직임
        n_asset_num = str(n_cash_rate) + n_asset_date

        s1 = stock_fund_mng.objects.create(asset_num=int(n_asset_num), acct_no=acct_no, cash_rate=n_cash_rate)
        s1.save()

    if stock_fund_mng.objects.filter(acct_no=acct_no).count() > 0:
        stock_fund_mng_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()

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
                    u_tot_evlu_amt = int(f['tot_evlu_amt'][i])              # 총평가금액
                    u_dnca_tot_amt = int(f['dnca_tot_amt'][i])              # 예수금총금액
                    u_nass_amt = int(f['nass_amt'][i])                      # 순자산금액(세금비용 제외)
                    u_prvs_rcdl_excc_amt = int(f['prvs_rcdl_excc_amt'][i])  # 가수도 정산 금액
                    u_thdt_buy_amt = int(f['thdt_buy_amt'][i])              # 금일 매수 금액
                    u_thdt_sll_amt = int(f['thdt_sll_amt'][i])              # 금일 매도 금액
                    u_scts_evlu_amt = int(f['scts_evlu_amt'][i])            # 유저 평가 금액
                    u_asst_icdc_amt = int(f['asst_icdc_amt'][i])            # 자산 증감액

                u_cash_rate_amt = round(u_tot_evlu_amt * stock_fund_mng_info.cash_rate * 0.01, 0)   # 총평가금액 기준 현금 비중 금액
                print("총평가금액 기준 현금비중금액 : " + format(int(u_cash_rate_amt), ',d'))
                u_sell_plan_amt = u_cash_rate_amt - u_prvs_rcdl_excc_amt  # 매도예정자금(총평가금액 기준 현금비중금액 - 가수도 정산금액)
                if u_sell_plan_amt < 0:
                    u_sell_plan_amt = 0

                u_buy_plan_amt = u_prvs_rcdl_excc_amt - u_cash_rate_amt   # 매수예정자금(가수도 정산금액 - 총평가금액 기준 현금비중금액)
                if u_buy_plan_amt < 0:
                    u_buy_plan_amt = 0

                stock_fund_mng.objects.filter(acct_no=acct_no, asset_num=stock_fund_mng_info.asset_num).update(
                    tot_evlu_amt=u_tot_evlu_amt,                # 총평가금액
                    dnca_tot_amt=u_dnca_tot_amt,                # 예수금 총금액
                    prvs_rcdl_excc_amt=u_prvs_rcdl_excc_amt,    # 가수도 정산금액
                    nass_amt=u_nass_amt,                        # 순자산금액(세금비용 제외)
                    scts_evlu_amt = u_scts_evlu_amt,            # 유저평가금액
                    asset_icdc_amt = u_asst_icdc_amt,           # 자산증감액
                    cash_rate_amt = u_cash_rate_amt,            # 총평가금액 기준 현금 비중 금액
                    sell_plan_amt = u_sell_plan_amt,            # 매도 예정 자금(총평가금액 기준 현금비중금액 - 가수도 정산금액)
                    buy_plan_amt = u_buy_plan_amt,               # 매수 예정 자금(가수도 정산금액 - 총평가금액 기준 현금비중금액)
                    last_chg_date = datetime.now()
                )
        except Exception as e:
            print('잘못된 인덱스입니다.', e)

        stock_fund_mng_rtn = stock_fund_mng.objects.filter(acct_no=acct_no, asset_num=stock_fund_mng_info.asset_num).order_by('-last_chg_date')
        stock_fund_mng_rtn_list = []

        for index, rtn in enumerate(stock_fund_mng_rtn, start=1):
            stock_fund_mng_rtn_list.append(
                {'asset_num': rtn.asset_num, 'acct_no': rtn.acct_no, 'cash_rate': rtn.cash_rate, 'tot_evlu_amt': format(int(rtn.tot_evlu_amt), ',d'),
                 'cash_rate_amt': format(int(rtn.cash_rate_amt), ',d'), 'dnca_tot_amt': format(int(rtn.dnca_tot_amt), ',d'), 'prvs_rcdl_excc_amt': format(int(rtn.prvs_rcdl_excc_amt), ',d'),
                 'nass_amt': format(int(rtn.nass_amt), ',d'), 'scts_evlu_amt': format(int(rtn.scts_evlu_amt), ',d'), 'asset_icdc_amt': format(int(rtn.asset_icdc_amt), ',d'),
                 'sell_plan_amt': format(int(rtn.sell_plan_amt), ',d'), 'buy_plan_amt': format(int(rtn.buy_plan_amt), ',d'), 'last_chg_date': rtn.last_chg_date})

    else:
        stock_fund_mng_rtn_list = []

    return JsonResponse(stock_fund_mng_rtn_list, safe=False)