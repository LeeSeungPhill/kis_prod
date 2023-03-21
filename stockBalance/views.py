from django.http import JsonResponse
from .models import stock_balance
from stockFundMng.models import stock_fund_mng
from kis import kis_api_resp as resp
from datetime import datetime
from datetime import timedelta
from django.utils.dateformat import DateFormat
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as ms
import pandas_datareader as web
from django.shortcuts import render
import os
import time
from pykrx import stock

# Create your views here.

def balanceList(request):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"   # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
    yyyy = DateFormat(datetime.now()).format('Y')
    mm = DateFormat(datetime.now()).format('m')
    dd = DateFormat(datetime.now()).format('d')

    try:
        # 잔고조회
        headers = {"Content-Type": "application/json",
                    "authorization": f"Bearer {access_token}",
                    "appKey": app_key,
                    "appSecret": app_secret,
                    "tr_id": "TTTC8434R"}   # tr_id : TTTC8434R[실전투자], VTTC8434R[모의투자]
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
        #ar.printAll()
        output1 = ar.getBody().output1
        output2 = ar.getBody().output2

        if ar.isOK() and output2:
            f = pd.DataFrame(output2)

            for i, name in enumerate(f.index):
                u_dnca_tot_amt = int(f['dnca_tot_amt'][i])  # 예수금총금액
                u_prvs_rcdl_excc_amt = int(f['prvs_rcdl_excc_amt'][i])  # 가수도 정산 금액
                u_thdt_buy_amt = int(f['thdt_buy_amt'][i])  # 금일 매수 금액
                u_thdt_sll_amt = int(f['thdt_sll_amt'][i])  # 금일 매도 금액
                u_thdt_tlex_amt = int(f['thdt_tlex_amt'][i])  # 금일 제비용 금액
                u_scts_evlu_amt = int(f['scts_evlu_amt'][i])  # 유저 평가 금액
                u_tot_evlu_amt = int(f['tot_evlu_amt'][i])  # 총평가금액
                u_nass_amt = int(f['nass_amt'][i])  # 순자산금액(세금비용 제외)
                u_pchs_amt_smtl_amt = int(f['pchs_amt_smtl_amt'][i])  # 매입금액 합계금액
                u_evlu_amt_smtl_amt = int(f['evlu_amt_smtl_amt'][i])  # 평가금액 합계금액
                u_evlu_pfls_smtl_amt = int(f['evlu_pfls_smtl_amt'][i])  # 평가손익 합계금액
                u_bfdy_tot_asst_evlu_amt = int(f['bfdy_tot_asst_evlu_amt'][i])  # 전일총자산 평가금액
                u_asst_icdc_amt = int(f['asst_icdc_amt'][i])  # 자산 증감액

        stock_fund_mng_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()

        if stock_fund_mng.objects.filter(acct_no=acct_no).count() > 0:
            #u_cash_rate_amt = round(u_tot_evlu_amt * stock_fund_mng_info.cash_rate * 0.01, 0)  # 총평가금액 기준 현금 비중 금액
            u_cash_rate_amt = round(200000000 * stock_fund_mng_info.cash_rate * 0.01, 0)  # 총금액(200,000,000원) 기준 현금 비중 금액
            print("현금비중금액 : "+format(int(u_cash_rate_amt), ',d'))
            #u_sell_plan_amt = u_cash_rate_amt - u_prvs_rcdl_excc_amt    # 매도예정자금(총평가금액 기준 현금비중금액 - 가수도 정산금액)
            # u_buy_plan_amt = u_prvs_rcdl_excc_amt - u_cash_rate_amt  # 매수예정자금(가수도 정산금액 - 총평가금액 기준 현금비중금액)

            if u_dnca_tot_amt < u_cash_rate_amt:                        # 예수금총금액 < 현금비중금액 :
                u_buy_plan_amt = 0

                if u_cash_rate_amt > u_evlu_amt_smtl_amt:                   # 현금비중금액 > 평가금액 합계금액 :
                    u_sell_plan_amt = u_cash_rate_amt                           # 매도예정자금 = 현금비중금액
                else:
                    u_sell_plan_amt = u_evlu_amt_smtl_amt - u_cash_rate_amt     # 매도예정자금 = 평가금액 합계금액 - 현금비중금액
            else:
                u_sell_plan_amt = 0
                u_buy_plan_amt = u_prvs_rcdl_excc_amt - u_cash_rate_amt     # 매수예정자금 = 가수도 정산금액 - 현금비중금액

            stock_fund_mng.objects.filter(acct_no=acct_no, asset_num=stock_fund_mng_info.asset_num).update(
                tot_evlu_amt=u_tot_evlu_amt,                # 총평가금액
                dnca_tot_amt=u_dnca_tot_amt,                # 예수금 총금액
                prvs_rcdl_excc_amt=u_prvs_rcdl_excc_amt,    # 가수도 정산금액
                nass_amt=u_nass_amt,                        # 순자산금액(세금비용 제외)
                scts_evlu_amt=u_scts_evlu_amt,              # 유저평가금액
                asset_icdc_amt=u_asst_icdc_amt,             # 자산증감액
                cash_rate_amt=u_cash_rate_amt,              # 총평가금액 기준 현금 비중 금액
                sell_plan_amt=u_sell_plan_amt,              # 매도예정자금(총평가금액 기준 현금비중금액 - 가수도 정산금액)
                buy_plan_amt=u_buy_plan_amt,                # 매수예정자금(가수도 정산금액 - 총평가금액 기준 현금비중금액)
                last_chg_date=datetime.now()
            )

            stock_fund_mng_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()

            if ar.isOK() and output1:
                tdf = pd.DataFrame(output1)
                tdf.set_index('pdno', inplace=True)
                cf1 = ['prdt_name', 'thdt_buyqty', 'thdt_sll_qty', 'hldg_qty', 'ord_psbl_qty', 'pchs_avg_pric', 'pchs_amt', 'evlu_amt', 'evlu_pfls_amt', 'evlu_pfls_rt', 'prpr', 'bfdy_cprs_icdc', 'fltt_rt']
                cf2 = ['종목명', '금일매수수량', '금일매도수량', '보유수량', '매도가능수량', '매입단가', '매입금액', '평가금액', '평가손익금액', '수익율', '현재가', '전일대비', '등락']
                tdf = tdf[cf1]
                tdf[cf1[1:]] = tdf[cf1[1:]].apply(pd.to_numeric)
                ren_dict = dict(zip(cf1, cf2))
                e = tdf.rename(columns=ren_dict)

                stock_balance.objects.filter(acct_no=acct_no, proc_yn="Y").update(proc_yn="N", last_chg_date=datetime.now())

                for i, name in enumerate(e.index):
                    e_name = e['종목명'][i]
                    e_purchase_price = int(e['매입단가'][i])
                    e_purchase_amount = int(e['보유수량'][i])
                    e_purchase_sum = int(e['매입금액'][i])
                    e_current_price = int(e['현재가'][i])
                    e_eval_sum = int(e['평가금액'][i])
                    e_earnings_rate = e['수익율'][i]
                    e_valuation_sum = int(e['평가손익금액'][i])

                    # 자산번호의 매도예정자금이 존재하는 경우, 보유종목 비중별 매도가능금액 및 매도가능수량 계산
                    if u_sell_plan_amt > 0:
                        # 종목 매입금액 비중 = 평가금액 / 총평가금액(예수금총금액 + 유저평가금액) * 100
                        item_eval_gravity = e_eval_sum / u_tot_evlu_amt * 100
                        print("종목 매입금액 비중 : " + format(int(item_eval_gravity), ',d'))
                        # 종목 매도가능금액 = 매도예정자금 * 종목 매입금액 비중 * 0.01
                        e_sell_plan_sum = u_sell_plan_amt * item_eval_gravity * 0.01

                        # 종목 매도가능수량 = 종목 매도가능금액 / 현재가
                        e_sell_plan_amount = e_sell_plan_sum / e_current_price

                        stock_balance.objects.update_or_create(
                            acct_no=acct_no, name=e_name, asset_num=stock_fund_mng_info.asset_num,
                            defaults={'acct_no': acct_no,                       # 계좌번호
                                      'name': e_name,                           # 종목명
                                      'purchase_price': e_purchase_price,       # 매입가
                                      'purchase_amount': e_purchase_amount,     # 보유수량
                                      'purchase_sum': e_purchase_sum,           # 매입금액
                                      'current_price': e_current_price,         # 현재가
                                      'eval_sum': e_eval_sum,                   # 평가금액
                                      'earnings_rate': e_earnings_rate,         # 수익률
                                      'valuation_sum': e_valuation_sum,         # 평가손익금액
                                      'asset_num': stock_fund_mng_info.asset_num,
                                      'sell_plan_sum': e_sell_plan_sum,         # 매도가능금액
                                      'sell_plan_amount': e_sell_plan_amount,   # 매도가능수량
                                      'proc_yn': "Y",                           # 처리여부
                                      'last_chg_date':  datetime.now()
                                      }
                        )
                    else:
                        stock_balance.objects.update_or_create(
                            acct_no=acct_no, name=e_name, asset_num=stock_fund_mng_info.asset_num,
                            defaults={'acct_no': acct_no,                       # 계좌번호
                                      'name': e_name,                           # 종목명
                                      'purchase_price': e_purchase_price,       # 매입가
                                      'purchase_amount': e_purchase_amount,     # 보유수량
                                      'purchase_sum': e_purchase_sum,           # 매입금액
                                      'current_price': e_current_price,         # 현재가
                                      'eval_sum': e_eval_sum,                   # 평가금액
                                      'earnings_rate': e_earnings_rate,         # 수익률
                                      'valuation_sum': e_valuation_sum,         # 평가손익금액
                                      'asset_num': stock_fund_mng_info.asset_num,
                                      'sell_plan_sum': 0,                       # 매도가능금액
                                      'sell_plan_amount': 0,                    # 매도가능수량
                                      'proc_yn': "Y",                           # 처리여부
                                      'last_chg_date': datetime.now()
                                      }
                        )

            stock_balance_rtn = stock_balance.objects.filter(acct_no=acct_no, proc_yn="Y").order_by('-earnings_rate')
            stock_balance_rtn_list = []

            for index, rtn in enumerate(stock_balance_rtn, start=1):
                rtn.K_target_price = ""
                rtn.D_loss_price = ""

                if rtn.end_loss_price == None:
                    rtn.end_loss_price = "0"
                if rtn.end_target_price == None:
                    rtn.end_target_price = "0"

                if int(rtn.current_price) > int(rtn.end_target_price):
                    rtn.K_target_price = "1"
                if int(rtn.current_price) < int(rtn.end_loss_price):
                    rtn.D_loss_price = "1"

                stock_balance_rtn_list.append({'id': rtn.id, 'acct_no': rtn.acct_no, 'name':rtn.name, 'purchase_price': format(int(rtn.purchase_price), ',d'), 'purchase_amount': format(int(rtn.purchase_amount), ',d'), 'purchase_sum':format(int(rtn.purchase_sum), ',d'),
                                               'current_price': format(int(rtn.current_price), ',d'), 'eval_sum': format(int(rtn.eval_sum), ',d'), 'earnings_rate':rtn.earnings_rate, 'valuation_sum': format(int(rtn.valuation_sum), ',d'),
                                               'K_target_price': rtn.K_target_price, 'D_loss_price': rtn.D_loss_price, 'end_loss_price': format(int(rtn.end_loss_price), ',d'), 'end_target_price': format(int(rtn.end_target_price), ',d'), 'trading_plan':rtn.trading_plan, 'asset_num':rtn.asset_num,
                                               'sell_plan_sum':rtn.sell_plan_sum, 'sell_plan_amount':rtn.sell_plan_amount, 'last_chg_date':rtn.last_chg_date})
        else:
            stock_balance_rtn_list = []

        return JsonResponse(stock_balance_rtn_list, safe=False)
    except Exception as ex:
        print('잘못된 인덱스입니다.', ex)

def update(request):
    acct_no = request.GET.get('acct_no', '')
    id = request.GET.get('id', '')
    end_loss_price = str(int(request.GET.get('end_loss_price', '').replace(",", "")))
    end_target_price = str(int(request.GET.get('end_target_price', '').replace(",", "")))
    trading_plan = request.GET.get('trading_plan', '')

    stock_balance.objects.filter(id=id).update(
                    end_loss_price=int(end_loss_price),
                    end_target_price=int(end_target_price),
                    trading_plan=trading_plan,
                    last_chg_date=datetime.now()
                )

    stock_balance_rtn = stock_balance.objects.filter(acct_no=acct_no, proc_yn="Y").order_by('-earnings_rate')
    stock_balance_rtn_list = []

    for index, rtn in enumerate(stock_balance_rtn, start=1):
        rtn.K_target_price = ""
        rtn.D_loss_price = ""

        if rtn.end_loss_price == None:
            rtn.end_loss_price = "0"
        if rtn.end_target_price == None:
            rtn.end_target_price = "0"

        if int(rtn.current_price) > int(rtn.end_target_price):
            rtn.K_target_price = "1"
        if int(rtn.current_price) < int(rtn.end_loss_price):
            rtn.D_loss_price = "1"

        stock_balance_rtn_list.append(
            {'id': rtn.id, 'acct_no': rtn.acct_no, 'name': rtn.name, 'purchase_price': format(int(rtn.purchase_price), ',d'),
             'purchase_amount': format(int(rtn.purchase_amount), ',d'),
             'purchase_sum': format(int(rtn.purchase_sum), ',d'),
             'current_price': format(int(rtn.current_price), ',d'), 'eval_sum': format(int(rtn.eval_sum), ',d'),
             'earnings_rate': rtn.earnings_rate, 'valuation_sum': format(int(rtn.valuation_sum), ',d'),
             'K_target_price': rtn.K_target_price, 'D_loss_price': rtn.D_loss_price, 'end_loss_price': format(int(rtn.end_loss_price), ',d'), 'end_target_price': format(int(rtn.end_target_price), ',d'),
             'trading_plan': rtn.trading_plan, 'asset_num': rtn.asset_num,
             'sell_plan_sum': rtn.sell_plan_sum, 'sell_plan_amount': rtn.sell_plan_amount,
             'last_chg_date': rtn.last_chg_date})

    return JsonResponse(stock_balance_rtn_list, safe=False)

def info(request):
    company = request.GET.get('company', '')

    # 해당 링크는 한국거래소에서 상장법인목록을 엑셀로 다운로드하는 링크입니다.
    # 다운로드와 동시에 Pandas에 excel 파일이 load가 되는 구조입니다.
    stock_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
    # 필요한 것은 "회사명"과 "종목코드" 이므로 필요없는 column들은 제외
    stock_code = stock_code[['회사명', '종목코드']]
    # 한글 컬럼명을 영어로 변경
    stock_code = stock_code.rename(columns={'회사명': 'company', '종목코드': 'code'})
    # 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌
    stock_code.code = stock_code.code.map('{:06d}'.format)

    if len(stock_code[stock_code.company == company].values) > 0:
        code = stock_code[stock_code.company == company].code.values[0].strip()  ## strip() : 공백제거
    else:
        code = ""

    pre_day = datetime.today() - timedelta(days=500)
    start = pre_day.strftime("%Y%m%d")
    end = datetime.now().strftime("%Y%m%d")
    #print("start : " + start)
    #print("end : " + end)
    df = web.naver.NaverDailyReader(code, start=start, end=end).read()
    #print(df)
    df = df.astype(int)  # Object 데이터를 int로 변환
    df = get_stochastic(df)
    OBV = []
    OBV.append(0)
    for i in range(1, len(df.Close)):
        if df.Close[i] > df.Close[i - 1]:
            OBV.append(OBV[-1] + df['Volume'][i])
        elif df.Close[i] < df.Close[i - 1]:
            OBV.append(OBV[-1] - df['Volume'][i])
        else:
            OBV.append(OBV[-1])
    df['OBV'] = OBV
    # 캔들 차트 객체 생성
    df = df.reset_index()
    df['Date'] = df['Date'].apply(lambda x: datetime.strftime(x, '%Y-%m-%d'))  # Datetime to str
    df['ma10'] = df['Volume'].rolling(10).mean()
    color_fuc = lambda x: 'red' if x >= 0 else 'blue'
    color_list = list(df['Volume'].diff().fillna(0).apply(color_fuc))
    #  스토캐스틱 차트
    kdj_d = go.Scatter(x=df['Date'], y=df['kdj_d'], name="Fast%D", line=dict(color="orange"))
    kdj_j = go.Scatter(x=df['Date'], y=df['kdj_j'], name="Slow%D", line=dict(color="green"))

    data1 = go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                           increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['Date'], y=df['Volume'], name="volumn", marker_color=color_list)

    fig = ms.make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.5,0.2,0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(kdj_d, row=2, col=1)
    fig.add_trace(kdj_j, row=2, col=1)
    fig.add_trace(data2, row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['OBV'], line=dict(color="black"), name='OBV'), row=3, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'),
                      xaxis2=dict(type="category", categoryorder='category ascending'),
                      xaxis3=dict(type="category", categoryorder='category ascending'), title=company+"["+code+"]",
                      yaxis1_title='Stock Price', yaxis2_title='Stocastic', yaxis3_title='Volume',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False, xaxis3_rangeslider_visible=False)
    #fig.show()
    fig.write_html(os.getcwd()+"/templates/stockBalance/"+company+".html")

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'code': code, 'name': company})

    return JsonResponse(stock_info_rtn_list, safe=False)

def detail(request, company):
    link = "stockBalance/"+company+".html"

    return render(request, link)

def minutesInfo(request):
    company = request.GET.get('company', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    # 해당 링크는 한국거래소에서 상장법인목록을 엑셀로 다운로드하는 링크입니다.
    # 다운로드와 동시에 Pandas에 excel 파일이 load가 되는 구조입니다.
    stock_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download', header=0)[0]
    # 필요한 것은 "회사명"과 "종목코드" 이므로 필요없는 column들은 제외
    stock_code = stock_code[['회사명', '종목코드']]
    # 한글 컬럼명을 영어로 변경
    stock_code = stock_code.rename(columns={'회사명': 'company', '종목코드': 'code'})
    # 종목코드가 6자리이기 때문에 6자리를 맞춰주기 위해 설정해줌
    stock_code.code = stock_code.code.map('{:06d}'.format)

    if len(stock_code[stock_code.company == company].values) > 0:
        code = stock_code[stock_code.company == company].code.values[0].strip()  ## strip() : 공백제거
    else:
        code = ""

    # 현재일 기준 최근 영업일
    stock_day = stock.get_nearest_business_day_in_a_week(date=datetime.now().strftime("%Y%m%d"))

    if time.strftime('%H%M%S') > '153000':
        hms = '153000'
    elif time.strftime('%H%M%S') < '090000':
        hms = '153000'
    else:
        hms = time.strftime('%H%M%S')

    date_time = []
    op = []
    hg = []
    lw = []
    cl = []
    vol = []

    for i in range(13):
        if hms > '090000':
            b = pd.DataFrame(inquire_time_itemchartprice(access_token, app_key, app_secret, code, hms))  # 30분간 1분봉 조회
            for i, name in enumerate(b.index):
                # date_time.append(datetime.datetime.strptime((b['stck_bsop_date'][i] + b['stck_cntg_hour'][i]), '%Y%m%d%H%M%S'))
                date_time.append(b['stck_bsop_date'][i] + b['stck_cntg_hour'][i][:4])
                op.append(b['stck_oprc'][i])
                hg.append(b['stck_hgpr'][i])
                lw.append(b['stck_lwpr'][i])
                cl.append(b['stck_prpr'][i])
                vol.append(int(b['cntg_vol'][i]))
            hms = (datetime.strptime((stock_day + hms), '%Y%m%d%H%M%S') - timedelta(minutes=30)).strftime('%H%M%S')
            #print(hms)

    df = pd.DataFrame((zip(date_time, op, hg, lw, cl, vol)), columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    #df.set_index(['Date'], inplace=True)
    #print(df)
    df['ma10'] = df['Volume'].rolling(10).mean()
    #df = df.reset_index()
    #df['Date'] = df['Date'].apply(lambda x: datetime.datetime.strftime(x, '%Y%m%d%H%M%S'))
    data1 = go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['Date'], y=df['Volume'], name="volumn", marker_color="green")

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.7,0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(data2, row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=2, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'), xaxis2=dict(type="category", categoryorder='category ascending'), title=company+"["+code+"]", yaxis1_title='Stock Price', yaxis2_title='Volume', xaxis2_title='periods', xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False,)
    #fig.show()
    fig.write_html(os.getcwd() + "/templates/stockBalance/minutes_" + company + ".html")

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'code': code, 'name': company})

    return JsonResponse(stock_info_rtn_list, safe=False)

def inquire_time_itemchartprice(access_token, app_key, app_secret, code, time):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"  # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "FHKST03010200",
               "custtype": "P"}
    params = {
            'FID_ETC_CLS_CODE': "",
            'FID_COND_MRKT_DIV_CODE': "J",  # 시장 분류 코드(J : 주식, ETF, ETN U: 업종)
            'FID_INPUT_ISCD': code,
            'FID_INPUT_HOUR_1': time,   # 종목(J)일 경우, 조회 시작일자(HHMMSS)ex) "123000" 입력 시 12시 30분 이전부터 1분 간격으로 조회 업종(U)일 경우, 조회간격(초) (60 or 120 만 입력 가능) ex) "60" 입력 시 현재시간부터 1분간격으로 조회 "120" 입력 시 현재시간부터 2분간격으로 조회
            'FID_PW_DATA_INCU_YN': 'Y'}     # 과거 데이터 포함 여부(Y/N) * 업종(U) 조회시에만 동작하는 구분값 N : 당일데이터만 조회 Y : 이후데이터도 조회(조회시점이 083000(오전8:30)일 경우 전일자 업종 시세 데이터도 같이 조회됨)
    PATH = "uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)

    return ar.getBody().output2

def get_stochastic(df, n=15, m=5, t=3):
    # 입력받은 값이 dataframe이라는 것을 정의해줌
    df = pd.DataFrame(df)

    # n일중 최고가
    ndays_high = df.High.rolling(window=n, min_periods=1).max()
    # n일중 최저가
    ndays_low = df.Low.rolling(window=n, min_periods=1).min()

    # Fast%K 계산
    kdj_k = ((df.Close - ndays_low) / (ndays_high - ndays_low)) * 100
    # Fast%D (=Slow%K) 계산
    kdj_d = kdj_k.ewm(span=m).mean()
    # Slow%D 계산
    kdj_j = kdj_d.ewm(span=t).mean()

    # dataframe에 컬럼 추가
    df = df.assign(kdj_k=kdj_k, kdj_d=kdj_d, kdj_j=kdj_j).dropna()

    return df

def marketInfo(request):
    market = request.GET.get('market', '')

    if market == "1001":
        title = "코스피"
        link = "kospi"
    elif market == "2001":
        title = "코스닥"
        link = "kosdak"
    else:
        title = ""
        link = ""

    pre_day = datetime.today() - timedelta(days=500)
    start = pre_day.strftime("%Y%m%d")
    end = datetime.now().strftime("%Y%m%d")
    #print("start : " + start)
    #print("end : " + end)
    df = stock.get_index_ohlcv(start, end, market)
    #print(df)
    df = df.reset_index()
    df['날짜'] = df['날짜'].apply(lambda x: datetime.strftime(x, '%Y-%m-%d'))
    df['ma10'] = df['거래량'].rolling(10).mean()
    color_fuc = lambda x: 'red' if x >= 0 else 'blue'
    color_list = list(df['거래량'].diff().fillna(0).apply(color_fuc))

    data1 = go.Candlestick(x=df['날짜'], open=df['시가'], high=df['고가'], low=df['저가'], close=df['종가'], increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['날짜'], y=df['거래량'], name="volumn", marker_color=color_list)

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.7,0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(data2, row=2, col=1)
    fig.add_trace(go.Scatter(x=df['날짜'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=2, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'),
                      xaxis2=dict(type="category", categoryorder='category ascending'),
                      title=title,
                      yaxis1_title='Index', yaxis2_title='Volume',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False)
    #fig.show()
    fig.write_html(os.getcwd()+"/templates/stockBalance/"+link+".html")

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'market': link})

    return JsonResponse(stock_info_rtn_list, safe=False)

def marketMinutesInfo(request):
    market = request.GET.get('market', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    if market == "0001":
        title = "코스피 15분봉"
        link = "kospi"
    elif market == "1001":
        title = "코스닥 15분봉"
        link = "kosdak"
    else:
        title = ""
        link = ""

    date_time = []
    op = []
    hg = []
    lw = []
    cl = []
    vol = []

    b = pd.DataFrame(inquire_time_marketchartprice(access_token, app_key, app_secret, market))
    for i, name in enumerate(b.index):
        date_time.append(b['stck_bsop_date'][i] + b['stck_cntg_hour'][i][:4])
        op.append(b['stck_oprc'][i])
        hg.append(b['stck_hgpr'][i])
        lw.append(b['stck_lwpr'][i])
        cl.append(b['stck_prpr'][i])
        vol.append(int(b['cntg_vol'][i]))

    df = pd.DataFrame((zip(date_time, op, hg, lw, cl, vol)), columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    #df.set_index(['Date'], inplace=True)
    #print(df)
    df['ma10'] = df['Volume'].rolling(10).mean()
    #df = df.reset_index()
    #df['Date'] = df['Date'].apply(lambda x: datetime.datetime.strftime(x, '%Y%m%d%H%M%S'))
    data1 = go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['Date'], y=df['Volume'], name="volumn", marker_color="green")

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.7,0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(data2, row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=2, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'), xaxis2=dict(type="category", categoryorder='category ascending'), title=title, yaxis1_title='Index', yaxis2_title='Volume', xaxis2_title='periods', xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False,)
    #fig.show()
    fig.write_html(os.getcwd() + "/templates/stockBalance/minutes_"+link+".html")

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'market': link})

    return JsonResponse(stock_info_rtn_list, safe=False)

def inquire_time_marketchartprice(access_token, app_key, app_secret, market):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"  # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "FHKST03010200",
               "custtype": "P"}
    params = {
            'FID_ETC_CLS_CODE': "",
            'FID_COND_MRKT_DIV_CODE': "U",  # 시장 분류 코드(J : 주식, ETF, ETN U: 업종)
            'FID_INPUT_ISCD': market,
            'FID_INPUT_HOUR_1': '900', # 종목(J)일 경우, 조회 시작일자(HHMMSS)ex) "123000" 입력 시 12시 30분 이전부터 1분 간격으로 조회 업종(U)일 경우, 조회간격(초) (60 or 120 만 입력 가능) ex) "60" 입력 시 현재시간부터 1분간격으로 조회 "120" 입력 시 현재시간부터 2분간격으로 조회
            'FID_PW_DATA_INCU_YN': 'N'}     # 과거 데이터 포함 여부(Y/N) * 업종(U) 조회시에만 동작하는 구분값 N : 당일데이터만 조회 Y : 이후데이터도 조회(조회시점이 083000(오전8:30)일 경우 전일자 업종 시세 데이터도 같이 조회됨)
    PATH = "uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)

    return ar.getBody().output2