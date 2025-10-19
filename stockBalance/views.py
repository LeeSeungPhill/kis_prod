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
import glob
import time
from stockBalance.models import stock_holiday


# Create your views here.

def balanceList(request):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"  # 모의투자서비스
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
                   "tr_id": "TTTC8434R"}  # tr_id : TTTC8434R[실전투자], VTTC8434R[모의투자]
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
        # ar.printAll()
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

            if ar.isOK() and output1:
                balance = pd.DataFrame(output1)

                stock_balance.objects.filter(acct_no=acct_no, proc_yn="Y").update(proc_yn="N", last_chg_date=datetime.now())

                for i, name in enumerate(balance.index):
                    e_code = balance['pdno'][i]
                    e_name = balance['prdt_name'][i]
                    e_purchase_price = balance['pchs_avg_pric'][i]
                    e_purchase_amount = int(balance['hldg_qty'][i])
                    e_purchase_sum = int(balance['pchs_amt'][i])
                    e_current_price = int(balance['prpr'][i])
                    e_eval_sum = int(balance['evlu_amt'][i])
                    e_earnings_rate = balance['evlu_pfls_rt'][i]
                    e_valuation_sum = int(balance['evlu_pfls_amt'][i])
                    e_avail_amount = int(balance['ord_psbl_qty'][i])

                    balance_object = stock_balance.objects.filter(acct_no=acct_no, code=e_code).order_by('-last_chg_date').first()

                    if balance_object is not None:
                    
                        # 자산번호의 매도예정자금이 존재하는 경우, 보유종목 비중별 매도가능금액 및 매도가능수량 계산
                        if stock_fund_mng_info.sell_plan_amt > 0:
                            # 종목 매입금액 비중 = 평가금액 / 총평가금액(예수금총금액 + 유저평가금액) * 100
                            item_eval_gravity = e_eval_sum / u_tot_evlu_amt * 100
                            print("종목 매입금액 비중 : " + format(int(item_eval_gravity), ',d'))
                            # 종목 매도가능금액 = 매도예정자금 * 종목 매입금액 비중 * 0.01
                            e_sell_plan_sum = stock_fund_mng_info.sell_plan_amt * item_eval_gravity * 0.01

                            # 종목 매도가능수량 = 종목 매도가능금액 / 현재가
                            e_sell_plan_amount = e_sell_plan_sum / e_current_price

                            stock_balance.objects.update_or_create(
                                acct_no=acct_no, code=e_code, asset_num=stock_fund_mng_info.asset_num,
                                defaults={'acct_no': acct_no,  # 계좌번호
                                        'code': e_code,  # 종목코드
                                        'name': e_name,  # 종목명
                                        'purchase_price': e_purchase_price,  # 매입가
                                        'purchase_amount': e_purchase_amount,  # 보유수량
                                        'purchase_sum': e_purchase_sum,  # 매입금액
                                        'avail_amount': e_avail_amount, # 주문가능수량
                                        'current_price': e_current_price,  # 현재가
                                        'eval_sum': e_eval_sum,  # 평가금액
                                        'earnings_rate': e_earnings_rate,  # 수익률
                                        'valuation_sum': e_valuation_sum,  # 평가손익금액
                                        'sign_resist_price': balance_object.sign_resist_price,
                                        'sign_support_price': balance_object.sign_support_price,
                                        'end_loss_price': balance_object.end_loss_price,
                                        'end_target_price': balance_object.end_target_price,
                                        'trading_plan': balance_object.trading_plan,
                                        'asset_num': stock_fund_mng_info.asset_num,
                                        'sell_plan_sum': e_sell_plan_sum,  # 매도가능금액
                                        'sell_plan_amount': e_sell_plan_amount,  # 매도가능수량
                                        'limit_price': balance_object.limit_price,  # 손절가
                                        'limit_amt': balance_object.limit_amt,  # 손실금액
                                        'proc_yn': "Y",  # 처리여부
                                        'last_chg_date': datetime.now()
                                        }
                            )
                        else:
                            stock_balance.objects.update_or_create(
                                acct_no=acct_no, code=e_code, asset_num=stock_fund_mng_info.asset_num,
                                defaults={'acct_no': acct_no,  # 계좌번호
                                        'code': e_code,  # 종목코드
                                        'name': e_name,  # 종목명
                                        'purchase_price': e_purchase_price,  # 매입가
                                        'purchase_amount': e_purchase_amount,  # 보유수량
                                        'purchase_sum': e_purchase_sum,  # 매입금액
                                        'avail_amount': e_avail_amount, # 주문가능수량
                                        'current_price': e_current_price,  # 현재가
                                        'eval_sum': e_eval_sum,  # 평가금액
                                        'earnings_rate': e_earnings_rate,  # 수익률
                                        'valuation_sum': e_valuation_sum,  # 평가손익금액
                                        'sign_resist_price': balance_object.sign_resist_price,
                                        'sign_support_price': balance_object.sign_support_price,
                                        'end_loss_price': balance_object.end_loss_price,
                                        'end_target_price': balance_object.end_target_price,
                                        'trading_plan': balance_object.trading_plan,
                                        'asset_num': stock_fund_mng_info.asset_num,
                                        'sell_plan_sum': 0,  # 매도가능금액
                                        'sell_plan_amount': 0,  # 매도가능수량
                                        'limit_price': balance_object.limit_price,  # 손절가
                                        'limit_amt': balance_object.limit_amt,  # 손실금액
                                        'proc_yn': "Y",  # 처리여부
                                        'last_chg_date': datetime.now()
                                        }
                            )

                    else:
                        stock_balance.objects.update_or_create(
                            acct_no=acct_no, code=e_code, asset_num=stock_fund_mng_info.asset_num,
                            defaults={'acct_no': acct_no,  # 계좌번호
                                    'code': e_code,  # 종목코드
                                    'name': e_name,  # 종목명
                                    'purchase_price': e_purchase_price,  # 매입가
                                    'purchase_amount': e_purchase_amount,  # 보유수량
                                    'purchase_sum': e_purchase_sum,  # 매입금액
                                    'avail_amount': e_avail_amount, # 주문가능수량
                                    'current_price': e_current_price,  # 현재가
                                    'eval_sum': e_eval_sum,  # 평가금액
                                    'earnings_rate': e_earnings_rate,  # 수익률
                                    'valuation_sum': e_valuation_sum,  # 평가손익금액
                                    'sign_resist_price': 0,
                                    'sign_support_price': 0,
                                    'end_loss_price': 0,
                                    'end_target_price': 0,
                                    'trading_plan': 0,
                                    'asset_num': stock_fund_mng_info.asset_num,
                                    'sell_plan_sum': 0,  # 매도가능금액
                                    'sell_plan_amount': 0,  # 매도가능수량
                                    'limit_price': balance_object.limit_price,  # 손절가
                                    'limit_amt': balance_object.limit_amt,  # 손실금액
                                    'proc_yn': "Y",  # 처리여부
                                    'last_chg_date': datetime.now()
                                    }
                        )    

            stock_balance_rtn = stock_balance.objects.filter(acct_no=acct_no, proc_yn="Y").order_by('code')
            stock_balance_rtn_list = []

            for index, rtn in enumerate(stock_balance_rtn, start=1):
                rtn.K_sign_resist_price = ""
                rtn.D_sign_support_price = ""
                rtn.K_target_price = ""
                rtn.D_loss_price = ""
                rtn.D_limit_price = ""

                if rtn.sign_resist_price == None:
                    rtn.sign_resist_price = "0"
                if rtn.sign_support_price == None:
                    rtn.sign_support_price = "0"
                if rtn.end_target_price == None:
                   rtn.end_target_price = "0"
                if rtn.end_loss_price == None:
                    rtn.end_loss_price = "0"
                if rtn.limit_price == None:
                    rtn.limit_price = "0"
                if rtn.limit_amt == None:
                    rtn.limit_amt = "0"         

                if int(rtn.current_price) > int(rtn.sign_resist_price):
                    rtn.K_sign_resist_price = "1"
                if int(rtn.current_price) < int(rtn.sign_support_price):
                    rtn.D_sign_support_price = "1"
                if int(rtn.current_price) > int(rtn.end_target_price):
                    rtn.K_target_price = "1"
                if int(rtn.current_price) < int(rtn.end_loss_price):
                    rtn.D_loss_price = "1"
                if int(rtn.current_price) < int(rtn.limit_price):
                    rtn.D_limit_price = "1"    

                a = inquire_price(access_token, app_key, app_secret, rtn.code)

                prdy_vol_rate = format(round(float(a['prdy_vrss_vol_rate'])), ',d')
                print("전일대비거래량 : " + str(prdy_vol_rate))
                total_market_value = format(int(a['hts_avls']), ',d')
                print("시가총액 : " + total_market_value)

                stock_balance_rtn_list.append({'id': rtn.id, 'acct_no': rtn.acct_no, 'code': rtn.code, 'name': rtn.name,
                                               'purchase_price': float(round(float(rtn.purchase_price))),
                                               'purchase_amount': rtn.purchase_amount,
                                               'purchase_sum': rtn.purchase_sum,
                                               'avail_amount': rtn.avail_amount if rtn.avail_amount != None else "0", # 주문가능수량
                                               'current_price': rtn.current_price,
                                               'eval_sum': rtn.eval_sum,
                                               'earnings_rate': rtn.earnings_rate,
                                               'valuation_sum': rtn.valuation_sum,
                                               'K_sign_resist_price': rtn.K_sign_resist_price, 'D_sign_support_price': rtn.D_sign_support_price,
                                               'sign_resist_price': rtn.sign_resist_price,
                                               'sign_support_price': rtn.sign_support_price,
                                               'K_target_price': rtn.K_target_price, 'D_loss_price': rtn.D_loss_price,
                                               'end_loss_price': rtn.end_loss_price,
                                               'end_target_price': rtn.end_target_price,
                                               'trading_plan': rtn.trading_plan if rtn.trading_plan != None else "", 'asset_num': rtn.asset_num,
                                               'sell_plan_sum': rtn.sell_plan_sum if rtn.sell_plan_sum != None else "0",
                                               'sell_plan_amount': rtn.sell_plan_amount if rtn.sell_plan_amount != None else "0",
                                               'prdy_vol_rate': prdy_vol_rate,
                                               'total_market_value': total_market_value,
                                               'limit_price': rtn.limit_price, 
                                               'D_limit_price': rtn.D_limit_price,
                                               'limit_amt': rtn.limit_amt, 
                                               'last_chg_date': rtn.last_chg_date})
        else:
            stock_balance_rtn_list = []

        return JsonResponse(stock_balance_rtn_list, safe=False)
    except Exception as ex:
        print('잘못된 인덱스입니다.', ex)


def update(request):
    # id = request.GET.get('id', '')
    code = request.GET.get('code', '')
    sign_resist_price = str(int(request.GET.get('sign_resist_price', '').replace(",", "")))
    sign_support_price = str(int(request.GET.get('sign_support_price', '').replace(",", "")))
    end_target_price = str(int(request.GET.get('end_target_price', '').replace(",", "")))
    end_loss_price = str(int(request.GET.get('end_loss_price', '').replace(",", "")))
    trading_plan = request.GET.get('trading_plan', '')
    limit_amt = str(int(request.GET.get('limit_amt', '').replace(",", "")))

    result = stock_balance.objects.filter(code=code).update(
        sign_resist_price=int(sign_resist_price),
        sign_support_price=int(sign_support_price),
        end_loss_price=int(end_loss_price),
        end_target_price=int(end_target_price),
        trading_plan=trading_plan,
        limit_amt=int(limit_amt),
        last_chg_date=datetime.now()
    )

    return JsonResponse(result, safe=False)


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

    for f in glob.glob(os.getcwd()+"/templates/stockBalance/"+company + "*.html"):
        os.remove(f)

    df = web.naver.NaverDailyReader(code, start=start, end=end).read()
    # print(df)
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

    fig = ms.make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.5, 0.2, 0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(kdj_d, row=2, col=1)
    fig.add_trace(kdj_j, row=2, col=1)
    fig.add_trace(data2, row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['OBV'], line=dict(color="black"), name='OBV'), row=3, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'),
                      xaxis2=dict(type="category", categoryorder='category ascending'),
                      xaxis3=dict(type="category", categoryorder='category ascending'),
                      title=company + "[" + code + "]",
                      yaxis1_title='Stock Price', yaxis2_title='Stocastic', yaxis3_title='Volume',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False,
                      xaxis3_rangeslider_visible=False)
    # fig.show()
    fig.write_html(os.getcwd() + "/templates/stockBalance/" + company + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M') + ".html", auto_open=False)

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'code': code, 'name': company + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M')})

    return JsonResponse(stock_info_rtn_list, safe=False)


def detail(request, company):
    link = "stockBalance/" + company + ".html"

    return render(request, link)


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

def get_recent_business_day():
    today = datetime.today().strftime("%Y%m%d")

    # DB에서 공휴일 목록 가져오기
    holidays = set(stock_holiday.objects.values_list("holiday", flat=True))

    while True:
        # 토요일(5) 또는 일요일(6) 또는 공휴일이면 하루 전으로 이동
        if datetime.strptime(today, "%Y%m%d").weekday() >= 5 or today in holidays:
            today = (datetime.strptime(today, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        else:
            return today  # 최근 영업일 반환

def marketInfo(request):
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
    market = request.GET.get('market', '')
    weekday = request.GET.get('weekday', '')

    if market == "0001":
        if weekday == "D":
            title = "코스피 일봉"
            link = "daykospi"
        elif weekday == "W":
            title = "코스피 주봉"
            link = "weekkospi"
        else:
            title = ""
            link = ""    
    elif market == "1001":
        if weekday == "D":
            title = "코스닥 일봉"
            link = "daykosdak"
        elif weekday == "W":
            title = "코스닥 주봉"
            link = "weekkosdak"    
        else:
            title = ""
            link = ""                
    else:
        title = ""
        link = ""

    for f in glob.glob(os.getcwd()+"/templates/stockBalance/" + link + "*.html"):
        os.remove(f)          

    # 현재일 기준 최근 영업일
    stock_day = get_recent_business_day()
    end = stock_day

    date_time = []
    op = []
    hg = []
    lw = []
    cl = []
    vol = []

    for h in range(1, 7):
        if weekday == "W":
            start = (datetime.strptime(stock_day, '%Y%m%d') - timedelta(weeks=h*50)).strftime('%Y%m%d')    
        else:
            start = (datetime.strptime(stock_day, '%Y%m%d') - timedelta(days=h*70)).strftime('%Y%m%d')    
        b = pd.DataFrame(inquire_daily_marketchartprice(access_token, app_key, app_secret, market, start, end,weekday))
        for i, name in enumerate(b.index):
            date_time.append(b['stck_bsop_date'][i])
            op.append(b['bstp_nmix_oprc'][i])
            hg.append(b['bstp_nmix_hgpr'][i])
            lw.append(b['bstp_nmix_lwpr'][i])
            cl.append(b['bstp_nmix_prpr'][i])
            vol.append(int(b['acml_vol'][i]))
        end = start
        time.sleep(0.5)

    df = pd.DataFrame((zip(date_time, op, hg, lw, cl, vol)), columns=['날짜', '시가', '고가', '저가', '종가', '거래량'])
    # print(df)
    df = df.reset_index()
    #df['날짜'] = df['날짜'].apply(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))
    df['ma10'] = df['거래량'].rolling(10).mean()
    color_fuc = lambda x: 'red' if x >= 0 else 'blue'
    color_list = list(df['거래량'].diff().fillna(0).apply(color_fuc))

    data1 = go.Candlestick(x=df['날짜'], open=df['시가'], high=df['고가'], low=df['저가'], close=df['종가'],
                           increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['날짜'], y=df['거래량'], name="volumn", marker_color=color_list)

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.7, 0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(data2, row=2, col=1)
    fig.add_trace(go.Scatter(x=df['날짜'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=2, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'),
                      xaxis2=dict(type="category", categoryorder='category ascending'),
                      title=title,
                      yaxis1_title='Index', yaxis2_title='Volume',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False)
    # fig.show()
    fig.write_html(os.getcwd() + "/templates/stockBalance/" + link + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M') + ".html", auto_open=False)

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'market': link + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M')})

    return JsonResponse(stock_info_rtn_list, safe=False)


def marketMinutesInfo(request):
    market = request.GET.get('market', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
    minute = request.GET.get('minute', '')

    if market == "0001":
        if minute == "600":
            title = "코스피 10분봉"
            link = "10kospi"
        elif minute == "3600":
            title = "코스피 60분봉"
            link = "60kospi"
        else:
            title = ""
            link = ""            
    elif market == "1001":
        if minute == "600":
            title = "코스닥 10분봉"
            link = "10kosdak"
        elif minute == "3600":    
            title = "코스닥 60분봉"
            link = "60kosdak"
        else:
            title = ""
            link = ""                        
    else:
        title = ""
        link = ""

    for f in glob.glob(os.getcwd()+"/templates/stockBalance/minutes_" + link + "*.html"):
        os.remove(f)                  

    date_time = []
    op = []
    hg = []
    lw = []
    cl = []
    vol = []

    b = pd.DataFrame(inquire_time_marketchartprice(access_token, app_key, app_secret, market, minute))
    for i, name in enumerate(b.index):
        date_time.append(b['stck_bsop_date'][i] + b['stck_cntg_hour'][i][:4])
        op.append(b['stck_oprc'][i])
        hg.append(b['stck_hgpr'][i])
        lw.append(b['stck_lwpr'][i])
        cl.append(b['stck_prpr'][i])
        vol.append(int(b['cntg_vol'][i]))

    df = pd.DataFrame((zip(date_time, op, hg, lw, cl, vol)), columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    # df.set_index(['Date'], inplace=True)
    # print(df)
    df['ma10'] = df['Volume'].rolling(10).mean()
    # df = df.reset_index()
    # df['Date'] = df['Date'].apply(lambda x: datetime.datetime.strftime(x, '%Y%m%d%H%M%S'))
    data1 = go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                           increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['Date'], y=df['Volume'], name="volumn", marker_color="green")

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.005, row_heights=[0.7, 0.3])
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(data2, row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=2, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'),
                      xaxis2=dict(type="category", categoryorder='category ascending'), title=title,
                      yaxis1_title='Index', yaxis2_title='Volume', xaxis2_title='periods',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False, )
    # fig.show()
    fig.write_html(os.getcwd() + "/templates/stockBalance/minutes_" + link + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M') + ".html", auto_open=False)

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'market': link + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M')})

    return JsonResponse(stock_info_rtn_list, safe=False)


def inquire_daily_marketchartprice(access_token, app_key, app_secret, market, start, end, weekday):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"  # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "FHKUP03500100",
               "custtype": "P"}
    params = {
        'FID_COND_MRKT_DIV_CODE': "U",
        'FID_INPUT_ISCD': market,
        'FID_INPUT_DATE_1': start,          # 조회 시작일자 (ex. 20220501)
        'FID_INPUT_DATE_2': end,            # 조회 종료일자 (ex. 20220530)
        'FID_PERIOD_DIV_CODE': weekday}     # D:일봉 W:주봉, M:월봉, Y:년봉
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)
    ar.printAll()
    return ar.getBody().output2

def inquire_time_marketchartprice(access_token, app_key, app_secret, market, minute):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"  # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "FHKST03010200",
               "custtype": "P"}
    params = {
        'FID_COND_MRKT_DIV_CODE': "U",  
        'FID_INPUT_ISCD': market,           # 0001 : 종합, 1001:코스닥종합
        'FID_INPUT_HOUR_1': minute,         # 30, 60 -> 1분, 600-> 10분, 3600 -> 1시간
        'FID_PW_DATA_INCU_YN': 'Y',         # Y (과거) / N (당일)
        'FID_ETC_CLS_CODE': "1",}           # 0: 기본 1:장마감,시간외 제외
    PATH = "uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)

    return ar.getBody().output2

# 주식현재가 시세
def inquire_price(access_token, app_key, app_secret, code):
    #URL_BASE = "https://openapivts.koreainvestment.com:29443"  # 모의투자서비스
    URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

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