from django.http import JsonResponse
from .models import stock_order_complete
from stockOrder.models import stock_order
from stockFundMng.models import stock_fund_mng
from stockMarketMng.models import stock_market_mng
from kis import kis_api_resp as resp
from datetime import datetime
import time
import requests
import pandas as pd

# Create your views here.

def basic(request):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"   # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    stock_fund_mng_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
    market_mng_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()

    try:
        # 일별 주문 체결 조회
        headers = {"Content-Type": "application/json",
                   "authorization": f"Bearer {access_token}",
                   "appKey": app_key,
                   "appSecret": app_secret,
                   "tr_id": "TTTC8001R"}    # tr_id : TTTC8001R[실전투자], VTTC8001R[모의투자]
        params = {
            "CANO": acct_no,
            "ACNT_PRDT_CD": '01',
            "INQR_STRT_DT": datetime.now().strftime('%Y%m%d'),
            "INQR_END_DT": datetime.now().strftime('%Y%m%d'),
            "SLL_BUY_DVSN_CD": '00',
            "INQR_DVSN": '00',
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "INQR_DVSN_2": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        PATH = "uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        URL = f"{URL_BASE}/{PATH}"
        res = requests.get(URL, headers=headers, params=params, verify=False)
        ar = resp.APIResp(res)
        #ar.printAll()
        output1 = ar.getBody().output1

        if ar.isOK() and output1:
            tdf = pd.DataFrame(output1)
            tdf.set_index('odno')
            d = tdf[['odno', 'prdt_name', 'ord_dt', 'ord_tmd', 'orgn_odno', 'sll_buy_dvsn_cd_name', 'pdno', 'ord_qty', 'ord_unpr', 'avg_prvs', 'cncl_yn', 'tot_ccld_amt', 'tot_ccld_qty', 'rmn_qty', 'cncl_cfrm_qty']]

            for i, name in enumerate(d.index):
                if d['odno'][i] != "":
                    d_order_no = int(d['odno'][i])
                else:
                    d_order_no = ""
                if d['orgn_odno'][i] != "":
                    d_org_order_no = int(d['orgn_odno'][i])
                else:
                    d_org_order_no = ""
                d_order_type = d['sll_buy_dvsn_cd_name'][i]
                d_order_dt = d['ord_dt'][i]
                d_order_tmd = d['ord_tmd'][i]
                d_code = d['pdno'][i]
                d_name = d['prdt_name'][i]
                d_order_price = d['ord_unpr'][i]
                d_order_amount = d['ord_qty'][i]
                d_total_complete_qty = d['tot_ccld_qty'][i]
                d_remain_qty = d['rmn_qty'][i]
                d_total_complete_amt = d['tot_ccld_amt'][i]

                d_buy_price = 0
                d_buy_amount = 0
                d_sell_price = 0
                d_sell_amount = 0
                d_trading_type = ""

                if d_order_type == '매수' or d_order_type == '매수정정' or d_order_type == '매수취소':
                    d_buy_price = int(d_order_price)
                    d_buy_amount = int(d_order_amount)
                    d_trading_type = 'B'

                if d_order_type == '매도' or d_order_type == '매도정정' or d_order_type == '매도취소':
                    d_sell_price = int(d_order_price)
                    d_sell_amount = int(d_order_amount)
                    d_trading_type = 'S'

                if d_order_no != "":

                    order_complete_info = stock_order_complete.objects.filter(acct_no=acct_no, order_no=d_order_no, org_order_no=d_org_order_no)

                    if len(order_complete_info) < 1:    # KIS 일별주문체결조회 주문번호의 해당하는 일별체결정보 미존재시 처리
                        stock_order_complete.objects.update_or_create(acct_no=acct_no, order_no=d_order_no, org_order_no=d_org_order_no,
                                                                      defaults={
                                                                          'acct_no': acct_no,
                                                                          'order_no': d_order_no,
                                                                          'org_order_no': d_org_order_no,
                                                                          'order_type': d_order_type,
                                                                          'order_dt': d_order_dt, 'order_tmd': d_order_tmd,
                                                                          'name': d_name, 'order_price': d_order_price,
                                                                          'order_amount': d_order_amount,
                                                                          'total_complete_qty': d_total_complete_qty,
                                                                          'remain_qty': d_remain_qty,
                                                                          'total_complete_amt': d_total_complete_amt
                                                                      }
                                                                      )
                        if int(d_total_complete_qty) > 0:   # order_stat = '03' 체결
                            stock_order.objects.update_or_create(acct_no=acct_no, order_no=d_order_no, code=d_code,
                                                                 defaults={
                                                                     'acct_no': acct_no, 'code': d_code, 'name': d_name, 'buy_price': d_buy_price,
                                                                     'buy_amount': d_buy_amount, 'sell_price': d_sell_price,
                                                                     'sell_amount': d_sell_amount,
                                                                     'loss_price': 0, 'target_price': 0,
                                                                     'trading_type': d_trading_type, 'proc_yn': 'Y',
                                                                     'order_no': d_order_no, 'order_stat': '03',
                                                                     'total_complete_qty': d_total_complete_qty,
                                                                     'remain_qty': d_remain_qty,
                                                                     'asset_risk_num': market_mng_info.asset_risk_num,
                                                                     'asset_num': stock_fund_mng_info.asset_num,
                                                                     'create_date': time.mktime(datetime.strptime(d_order_dt+d_order_tmd, '%Y%m%d%H%M%S').timetuple()),
                                                                     'proc_date': datetime.now()
                                                                 }
                                                                 )
                        if int(d_order_price) == 0:         # order_stat = '04' 취소
                            stock_order.objects.update_or_create(acct_no=acct_no, order_no=d_order_no, code=d_code,
                                                                 defaults={
                                                                     'acct_no': acct_no, 'code': d_code, 'name': d_name,
                                                                     'buy_price': d_buy_price,
                                                                     'buy_amount': d_buy_amount, 'sell_price': d_sell_price,
                                                                     'sell_amount': d_sell_amount,
                                                                     'loss_price': 0, 'target_price': 0,
                                                                     'trading_type': d_trading_type, 'proc_yn': 'Y',
                                                                     'order_no': d_order_no, 'order_stat': '04',
                                                                     'total_complete_qty': d_total_complete_qty,
                                                                     'remain_qty': d_remain_qty,
                                                                     'asset_risk_num': market_mng_info.asset_risk_num,
                                                                     'asset_num': stock_fund_mng_info.asset_num,
                                                                     'create_date': time.mktime(
                                                                         datetime.strptime(d_order_dt + d_order_tmd,
                                                                                           '%Y%m%d%H%M%S').timetuple()),
                                                                     'proc_date': datetime.now()
                                                                 }
                                                                 )


                    else:
                        for index, rtn in enumerate(order_complete_info, start=1):
                            # KIS 일별주문체결조회의 잔여량 또는 체결량이 일별체결정보 잔여량 또는 체결량보다 작거나, 클 경우 처리
                            if int(d_remain_qty) < int(rtn.remain_qty) or int(d_total_complete_qty) > int(rtn.total_complete_qty):
                                stock_order_complete.objects.update_or_create(acct_no=acct_no, order_no=d_order_no, org_order_no=d_org_order_no,
                                    defaults={
                                            'acct_no': acct_no, 'order_no': d_order_no, 'org_order_no': d_org_order_no, 'order_type': d_order_type, 'order_dt': d_order_dt, 'order_tmd': d_order_tmd,
                                            'name': d_name, 'order_price': d_order_price, 'order_amount': d_order_amount, 'total_complete_qty': d_total_complete_qty, 'remain_qty': d_remain_qty,
                                            'total_complete_amt': d_total_complete_amt
                                    }
                                )

                                stock_order.objects.update_or_create(acct_no=acct_no, order_no=d_order_no, code=d_code,
                                    defaults={
                                            'acct_no': acct_no, 'code': d_code, 'name': d_name, 'buy_price': d_buy_price, 'buy_amount': d_buy_amount, 'sell_price': d_sell_price, 'sell_amount': d_sell_amount,'loss_price': 0, 'target_price': 0,
                                            'trading_type': d_trading_type, 'proc_yn': 'Y', 'order_no': d_order_no, 'order_stat': '03', 'total_complete_qty': d_total_complete_qty, 'remain_qty': d_remain_qty,
                                            'asset_risk_num': market_mng_info.asset_risk_num, 'asset_num': stock_fund_mng_info.asset_num, 'create_date': time.mktime(datetime.strptime(d_order_dt+d_order_tmd, '%Y%m%d%H%M%S').timetuple()), 'proc_date': datetime.now()
                                    }
                                )
    except Exception as e:
        print('잘못된 인덱스입니다.', e)

    order_complete_rtn = stock_order_complete.objects.filter(acct_no=acct_no, order_dt=datetime.now().strftime('%Y%m%d')).order_by('-order_tmd')

    order_complete_rtn_list = []
    if len(order_complete_rtn) > 0:
        for index, rtn in enumerate(order_complete_rtn, start=1):

            if int(rtn.total_complete_qty) > 0 or int(rtn.remain_qty) > 0:

                if stock_order.objects.filter(acct_no=acct_no, order_no=rtn.order_no).count() > 0:
                    chk_order = stock_order.objects.filter(acct_no=acct_no, order_no=rtn.order_no).first()
                    order_stat = chk_order.order_stat
                    if int(rtn.total_complete_qty) > 0:
                        order_stat = '03'
                    if int(rtn.order_price) == 0:
                        order_stat = '04'

                    if int(rtn.total_complete_qty) != chk_order.total_complete_qty or int(rtn.remain_qty) != chk_order.remain_qty:
                        stock_order.objects.filter(id=chk_order.id).update(name=rtn.name, order_stat=order_stat, total_complete_qty=rtn.total_complete_qty, remain_qty=rtn.remain_qty, proc_date=datetime.now())

            order_complete_rtn_list.append(
                {'acct_no': rtn.acct_no, 'order_no': rtn.order_no, 'org_order_no': rtn.org_order_no, 'order_type': rtn.order_type, 'order_dt': rtn.order_dt,
                 'order_tmd': rtn.order_tmd, 'name': rtn.name, 'order_price': format(int(rtn.order_price), ',d'), 'order_amount': format(int(rtn.order_amount), ',d'),
                 'total_complete_qty': format(int(rtn.total_complete_qty), ',d'), 'remain_qty': format(int(rtn.remain_qty), ',d'), 'total_complete_amt': format(int(rtn.total_complete_amt), ',d')}
            )

    return JsonResponse(order_complete_rtn_list, safe=False)

