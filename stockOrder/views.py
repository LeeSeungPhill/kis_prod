from django.http import JsonResponse
from .models import stock_order, sub_total, stock_search_form
from stockBalance.models import stock_balance
from stockFundMng.models import stock_fund_mng
from stockMarketMng.models import stock_market_mng
from kis import kis_api_resp as resp
from django.utils.dateformat import DateFormat
from datetime import datetime
from datetime import timedelta
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as ms
import pandas_datareader as web
import json
from django.shortcuts import render
import os
import glob
import time
import math
from stockBalance.models import stock_holiday

#URL_BASE = "https://openapivts.koreainvestment.com:29443"   # 모의투자서비스
URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

def assetInfo(request):
    acct_no = request.GET.get('acct_no', '')

    asset_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
    asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()
    stock_order_rtn_list = []
    stock_order_rtn_list.append({'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

    return JsonResponse(stock_order_rtn_list, safe=False)

def orderList(request):
    acct_no = request.GET.get('acct_no', '')
    yyyy = DateFormat(datetime.now()).format('Y')
    mm = DateFormat(datetime.now()).format('m')
    dd = DateFormat(datetime.now()).format('d')

    asset_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
    asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()

    if stock_fund_mng.objects.filter(acct_no=acct_no).count() < 1:
        stock_order_rtn_list = []
    else:
        if stock_market_mng.objects.filter(acct_no=acct_no).count() < 1:
            stock_order_rtn_list = []
        else:
            stock_order_rtn = stock_order.objects.filter(acct_no=acct_no, create_date__year=yyyy, create_date__month=mm, create_date__day=dd).order_by('-create_date')
            stock_order_rtn_list = []
            if len(stock_order_rtn) > 0:

                for i, rtn in enumerate(stock_order_rtn, start=1):

                    if rtn.order_stat == '01' or rtn.total_complete_qty > 0 or rtn.remain_qty > 0:
                        stock_order_rtn_list.append(
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': rtn.buy_price, 'buy_amount': rtn.buy_amount,
                             'sell_price': rtn.sell_price, 'sell_amount': rtn.sell_amount, 'loss_price': rtn.loss_price,
                             'target_price': rtn.target_price, 'trading_type': rtn.trading_type,
                             'asset_risk_num': rtn.asset_risk_num,
                             'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no,
                             'order_stat': rtn.order_stat,
                             'total_complete_qty': rtn.total_complete_qty, 'remain_qty': rtn.remain_qty,
                             'create_date': rtn.create_date,
                             'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num,
                             'stock_asset_risk_num': asset_risk_info.asset_risk_num})

    return JsonResponse(stock_order_rtn_list, safe=False)

def info(request):
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
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

    get_chart(code, company)

    if len(code) > 0:
        # 주식현재가 시세
        a = inquire_price(access_token, app_key, app_secret, code)

        now_price = format(int(a['stck_prpr']), ',d') + "원"                         # 현재가
        high_price = format(int(a['stck_hgpr']), ',d') + "원"                        # 고가
        low_price = format(int(a['stck_lwpr']), ',d') + "원"                         # 저가
        open_price = format(int(a['stck_oprc']), ',d') + "원"                        # 시가
        max_price = format(int(a['stck_mxpr']), ',d') + "원"                         # 상한가
        min_price = format(int(a['stck_llam']), ',d') + "원"                         # 하한가
        volumn = format(int(a['acml_vol']), ',d') + "주"                             # 거래량
        total_market_value = format(int(a['hts_avls']), ',d')                       # 시가총액
        prdy_vol_rate = format(round(float(a['prdy_vrss_vol_rate'])), ',d') + "%"   # 전일대비거래량
    else:
        now_price = ""
        high_price = ""
        low_price = ""
        open_price = ""
        max_price = ""
        min_price = ""
        volumn = ""
        total_market_value = ""
        prdy_vol_rate = ""

    stock_order_rtn_list = []

    stock_order_rtn_list.append(
        {'code': code, 'now_price': now_price, 'high_price': high_price, 'low_price': low_price,
         'open_price': open_price, 'max_price': max_price, 'min_price': min_price, 'volumn': volumn, 'total_market_value': total_market_value, 'prdy_vol_rate': prdy_vol_rate, 'YmdHM': datetime.now().strftime("%Y%m%d") + time.strftime('%H%M')})

    return JsonResponse(stock_order_rtn_list, safe=False)
    #data = {'columns': [Counts, Costs, ]}
    #return HttpResponse(json.dumps(data), content_type='text/json')

def get_chart(code, company):
    pre_day = datetime.today() - timedelta(days=500)
    start = pre_day.strftime("%Y%m%d")
    end = datetime.now().strftime("%Y%m%d")
    
    for f in glob.glob(os.getcwd()+"/templates/stockOrder/" + company + "*.html"):
        os.remove(f) 

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
                      xaxis3=dict(type="category", categoryorder='category ascending'),
                      title=company + "[" + code + "]",
                      yaxis1_title='Stock Price', yaxis2_title='Stocastic', yaxis3_title='Volume',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False,
                      xaxis3_rangeslider_visible=False)
    #fig.show()

    fig.write_html(os.getcwd()+"/templates/stockOrder/" + company + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M') + ".html", auto_open=False)

def detail(request, company):
    link = "stockOrder/"+company+".html"

    return render(request, link)

def subTotal(request):
    tr_subject = request.GET.get('tr_subject', '')
    tr_type = request.GET.get('tr_type', '')
    market_type = request.GET.get('market_type', '')

    subTotal_info = sub_total.objects.filter(tr_subject=tr_subject, tr_type=tr_type, market_type=market_type).order_by('tr_order')

    subTotal_info_rtn_list = []
    if len(subTotal_info) > 0:

        for i, rtn in enumerate(subTotal_info, start=1):

            subTotal_info_rtn_list.append(
                {'tr_day': rtn.tr_day, 'tr_time': rtn.tr_time, 'code': rtn.code, 'name': rtn.name, 'tr_subject': rtn.tr_subject,
                 'tr_type': rtn.tr_type, 'market_type': rtn.market_type, 'tr_order': rtn.tr_order, 'volumn': format(rtn.volumn, ',d')})

    return JsonResponse(subTotal_info_rtn_list, safe=False)

def chart(request):
    code = request.GET.get('code', '')
    company = request.GET.get('company', '')

    get_chart(code, company)

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'code': code, 'name': company + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M')})

    return JsonResponse(stock_info_rtn_list, safe=False)

def send(request):
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    yyyy = DateFormat(datetime.now()).format('Y')
    mm = DateFormat(datetime.now()).format('m')
    dd = DateFormat(datetime.now()).format('d')
    # 금일 미처리 대상 주문정보
    stock_orders = stock_order.objects.filter(acct_no=acct_no,create_date__year=yyyy,create_date__month=mm,create_date__day=dd,proc_yn='N')
    try:
        for i in stock_orders:
            message = ""
            if i.trading_type == "B":       # 매수

                if i.buy_price > i.loss_price:                  # 주문가 매수
                    if i.buy_amount == 0:
                        # 자산번호 = 0 인 경우, 투자금액 설정
                        if i.asset_num == 0:
                            # 주식현재가 시세
                            a = inquire_price(access_token, app_key, app_secret, i.code)
                            print("시가총액 : " + format(int(a['hts_avls']), ',d'))  # 시가총액
                            # 시가총액 5천억원 이상 : 10,000,000원, 2천억원~5천억원 미만 : 5,000,000, 2천억원 미만 : 2,500,000원
                            if int(a['hts_avls']) > 5000:
                                mtl = 10000000
                            elif int(a['hts_avls']) < 2000:
                                mtl = 2500000
                            else:
                                mtl = 5000000

                            stock_fund_mng_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
                            print("stock_fund_mng_info.prvs_rcdl_excc_amt : " + str(stock_fund_mng_info.prvs_rcdl_excc_amt))
                            # 가수도정산금액 1억원 이상 : 10,000,000원, 3천만원 이상 : 7,500,000원, 1천만원 이상 3천만원 미만 : 5,000,000원, 1천만원 미만 :
                            if stock_fund_mng_info.prvs_rcdl_excc_amt > 100000000:
                                sfa = 10000000
                            elif stock_fund_mng_info.prvs_rcdl_excc_amt > 30000000:
                                sfa = 7500000
                            elif stock_fund_mng_info.prvs_rcdl_excc_amt > 10000000:
                                sfa = 5000000
                            else:   # 가수도정산금액 1천만원 미만 : 투자금액 0원 설정(하락추세 및 패턴인 경우, 시장흐름정액 매수 처리 안됨)
                                sfa = 0

                            # 시장흐름정액 기준 투자금액 설정
                            # 상승추세 : 가수도정산금액 > 시가총액 -> 큰 항목 투자금액 설정, 하락추세 및 패턴 : 가수도정산금액 > 시가총액 -> 작은 항목 투자금액 설정
                            print("sfa : " + str(sfa))
                            print("mtl : " + str(mtl))
                            print("stock_fund_mng_info.cash_rate : " + str(stock_fund_mng_info.cash_rate))
                            if stock_fund_mng_info.cash_rate <= 50:
                                if sfa > mtl:
                                    n_asset_sum = sfa
                                else:
                                    n_asset_sum = mtl
                            else:
                                if sfa > mtl:
                                    n_asset_sum = mtl
                                else:
                                    n_asset_sum = sfa

                            # 매수량 = 투자금액 / 매수가
                            n_buy_amount = n_asset_sum / i.buy_price
                            # 매수금액
                            n_buy_sum = i.buy_price * round(n_buy_amount)
                            print("투자금액 : " + str(n_asset_sum))
                            print("매수량 : " + str(round(n_buy_amount)))
                            print("매수금액 : " + str(n_buy_sum))
                        else:   # 자산번호 <> 0 인 경우, 종목손실금액, 매수량 설정
                            # 자산 리스크 현행화
                            asset_risk_change(acct_no, app_key, app_secret, access_token, i.asset_risk_num)
                            market_mng_info = stock_market_mng.objects.filter(acct_no=acct_no,
                                                                              asset_risk_num=i.asset_risk_num,
                                                                              aply_end_dt='99991231').first()
                            # 종목손실금액
                            n_item_loss_sum = market_mng_info.risk_sum / market_mng_info.item_number
                            # 매수량
                            n_buy_amount = n_item_loss_sum / (i.buy_price - i.loss_price)
                            # 매수금액
                            n_buy_sum = i.buy_price * round(n_buy_amount)
                            print("종목손실금액 : " + str(n_item_loss_sum))
                            print("매수량 : " + str(round(n_buy_amount)))
                            print("매수금액 : " + str(n_buy_sum))
                    else:
                        n_buy_amount = i.buy_amount
                        n_buy_sum = i.buy_price * round(n_buy_amount)
                        print("매수량 : " + str(round(n_buy_amount)))
                        print("매수금액 : " + str(n_buy_sum))

                    # 매수 가능(현금) 조회
                    b = inquire_psbl_order(access_token, app_key, app_secret, acct_no)
                    print("매수 가능(현금) : " + format(int(b), ',d'));
                    if int(b) > n_buy_sum: # 매수가능(현금)이 매수금액이 더 큰 경우

                        # 지정가 매수
                        c = order_cash(True, access_token, app_key, app_secret, acct_no, i.code, "00", str(round(n_buy_amount)), str(i.buy_price))
                        if c['ODNO'] != "":
                            stock_order.objects.filter(id=i.id).update(
                                                        proc_yn="Y",
                                                        order_no=int(c['ODNO']),
                                                        order_stat="02",
                                                        buy_price=i.buy_price,
                                                        buy_amount=round(n_buy_amount),
                                                        remain_qty=round(n_buy_amount),
                                                        proc_date=datetime.now()
                            )
                    else:
                        print("매수 가능(현금) 부족")
                        message = "매수 가능(현금) 부족"
                else:
                    if i.buy_price < 0:                         # 시장가 매수

                        # 주식현재가 시세
                        a = inquire_price(access_token, app_key, app_secret, i.code)
                        print("현재가 : " + format(int(a['stck_prpr']), ',d'))  # 현재가
                        i.buy_price = int(a['stck_prpr'])
                        n_buy_amount = i.buy_amount
                        n_buy_sum = i.buy_price * round(n_buy_amount)
                        print("매수량 : " + str(round(n_buy_amount)))
                        print("매수금액 : " + str(n_buy_sum))
                        # 매수 가능(현금) 조회
                        b = inquire_psbl_order(access_token, app_key, app_secret, acct_no)
                        print("매수 가능(현금) : " + format(int(b), ',d'));
                        if int(b) > n_buy_sum:  # 매수가능(현금)이 매수금액이 더 큰 경우
                            # 시장가 매수
                            c = order_cash(True, access_token, app_key, app_secret, acct_no, i.code, "01", str(round(n_buy_amount)), "0")
                            if c['ODNO'] != "":
                                stock_order.objects.filter(id=i.id).update(
                                    proc_yn="Y",
                                    order_no=int(c['ODNO']),
                                    order_stat="02",
                                    buy_price=i.buy_price,
                                    buy_amount=round(n_buy_amount),
                                    remain_qty=round(n_buy_amount),
                                    proc_date=datetime.now()
                                )
                        else:
                            print("매수 가능(현금) 부족")
                            message = "매수 가능(현금) 부족"

            elif i.trading_type == "S":     # 매도

                # 매도 계좌 잔고 조회
                e = get_acct_balance_sell(access_token, app_key, app_secret, acct_no)
                e_purchase_amount = 0
                for j, name in enumerate(e.index):
                    e_code = e['pdno'][j]
                    if e_code == i.code:
                        e_purchase_amount = int(e['hldg_qty'][j])
                        e_name = e['prdt_name'][j]
                print("purchase_amount : " + str(e_purchase_amount))
                if i.asset_num > 0:
                    if i.sell_amount == 0:
                        balance_info = stock_balance.objects.filter(acct_no=acct_no, name=e_name, asset_num=i.asset_num).first()

                        if balance_info.sell_plan_amount > 0:
                            print("sell_plan_amount : " + str(balance_info.sell_plan_amount))
                            i.sell_amount = balance_info.sell_plan_amount
                        else:
                            print("현금비중 :" + str(balance_info.asset_num)[0:2])
                            i.sell_amount = int(str(balance_info.asset_num)[0:2]) * e_purchase_amount * 0.01
                else:
                    if i.sell_amount == 0:
                        i.sell_amount = 50 * e_purchase_amount * 0.01
                print("sell_amount : " + str(round(i.sell_amount)))
                if e_purchase_amount >= i.sell_amount:

                    if i.sell_price < 0:                    # 시장가 매도
                        # 주식현재가 시세
                        a = inquire_price(access_token, app_key, app_secret, i.code)
                        print("현재가 : " + format(int(a['stck_prpr']), ',d'))  # 현재가
                        i.sell_price = int(a['stck_prpr'])
                        # 시장가 매도
                        c = order_cash(False, access_token, app_key, app_secret, acct_no, i.code, "01", str(round(i.sell_amount)), "0")
                    else:
                        # 주문가 매도
                        c = order_cash(False, access_token, app_key, app_secret, acct_no, i.code, "00", str(round(i.sell_amount)), str(i.sell_price))

                    if c['ODNO'] != "":
                        stock_order.objects.filter(id=i.id).update(
                                                    proc_yn="Y",
                                                    order_no=int(c['ODNO']),
                                                    order_stat="02",
                                                    sell_price=i.sell_price,
                                                    sell_amount=round(i.sell_amount),
                                                    remain_qty=round(i.sell_amount),
                                                    proc_date=datetime.now()
                        )
                else:
                    print("매도수량 초과 주문 미처리")
                    message = "매도수량 초과 주문 미처리"

            else:
                print("매매유형 부적합 주문 미처리")
                message = "매매유형 부적합 주문 미처리"


        asset_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
        asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()

        if stock_fund_mng.objects.filter(acct_no=acct_no).count() < 1:
            stock_order_rtn_list = []
        else:
            if stock_market_mng.objects.filter(acct_no=acct_no).count() < 1:
                stock_order_rtn_list = []
            else:
                stock_order_rtn = stock_order.objects.filter(acct_no=acct_no, create_date__year=yyyy, create_date__month=mm, create_date__day=dd).order_by('-create_date')
                stock_order_rtn_list = []
                if len(stock_order_rtn) > 0:
                    for index, rtn in enumerate(stock_order_rtn, start=1):
                        stock_order_rtn_list.append(
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': rtn.buy_price, 'buy_amount': rtn.buy_amount,
                            'sell_price': rtn.sell_price, 'sell_amount': rtn.sell_amount, 'loss_price': rtn.loss_price, 
                            'target_price': rtn.target_price, 'trading_type': rtn.trading_type, 'asset_risk_num': rtn.asset_risk_num,
                            'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no, 'order_stat': rtn.order_stat,
                            'total_complete_qty': rtn.total_complete_qty, 'remain_qty': rtn.remain_qty, 'create_date': rtn.create_date,
                            'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num, 'message':message})

        return JsonResponse(stock_order_rtn_list, safe=False)
    except Exception as e:
        print('잘못된 인덱스입니다.', e)

def update(request):
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    id = request.GET.get('id', '')
    order_no = request.GET.get('order_no', '')
    buy_price = str(int(request.GET.get('buy_price', '').replace(",", "")))
    sell_price = str(int(request.GET.get('sell_price', '').replace(",", "")))
    order_amount = str(int(request.GET.get('order_amount', '').replace(",", "")))

    yyyy = DateFormat(datetime.now()).format('Y')
    mm = DateFormat(datetime.now()).format('m')
    dd = DateFormat(datetime.now()).format('d')

    try:
        message = ""
        # 주식정정취소가능주문 조회
        #e = order_psbl_cancel_revice(access_token, app_key, app_secret, acct_no)
        #for i, name in enumerate(e.index):
        #   e_order_type = e['주문구분명'][i]
        #   e_name = e['종목명'][i]
        #   e_purchase_qty = int(e['주문수량'][i])
        #   e_purchase_price = int(e['주문단가'][i])
        #   e_complete_qty = int(e['총체결수량'][i])
        #   e_remain_qty = int(e['가능수량'][i])

        if int(buy_price) > 0:      # 매수주문 정정
            n_buy_sum = int(buy_price) * int(order_amount)
            print("n_buy_sum : "+str(n_buy_sum))
            # 매수 가능(현금) 조회
            b = inquire_psbl_order(access_token, app_key, app_secret, acct_no)
            print("매수 가능(현금) : " + format(int(b), ',d'));
            if int(b) > n_buy_sum:   # 매수가능(현금)이 매수금액이 더 큰 경우
                # 주식주문(정정)
                c = order_cancel_revice(access_token, app_key, app_secret, acct_no, "01", order_no, order_amount, buy_price)
                if c['ODNO'] != "":
                    stock_order.objects.filter(id=id).update(
                        buy_price=int(buy_price),
                        order_no=int(c['ODNO']),
                        order_stat="05",
                        remain_qty=int(order_amount),
                        proc_date=datetime.now()
                    )
            else:
                print("매수 가능(현금) 부족")
                message = "매수 가능(현금) 부족"

        if int(sell_price) > 0:     # 매도주문 정정

            # 주식주문(정정)
            c = order_cancel_revice(access_token, app_key, app_secret, acct_no, "01", order_no, order_amount, sell_price)
            if c['ODNO'] != "":
                stock_order.objects.filter(id=id).update(
                    sell_price=int(sell_price),
                    order_no=int(c['ODNO']),
                    order_stat="05",
                    remain_qty=int(order_amount),
                    proc_date=datetime.now()
                )

        asset_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
        asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()

        if stock_fund_mng.objects.filter(acct_no=acct_no).count() < 1:
            stock_order_rtn_list = []
        else:
            if stock_market_mng.objects.filter(acct_no=acct_no).count() < 1:
                stock_order_rtn_list = []
            else:
                stock_order_rtn = stock_order.objects.filter(acct_no=acct_no, create_date__year=yyyy, create_date__month=mm, create_date__day=dd).order_by('-create_date')
                stock_order_rtn_list = []
                if len(stock_order_rtn) > 0:
                    for index, rtn in enumerate(stock_order_rtn, start=1):
                        stock_order_rtn_list.append(
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': rtn.buy_price, 'buy_amount': rtn.buy_amount,
                            'sell_price': rtn.sell_price, 'sell_amount': rtn.sell_amount, 'loss_price': rtn.loss_price, 
                            'target_price': rtn.target_price, 'trading_type': rtn.trading_type, 'asset_risk_num': rtn.asset_risk_num,
                            'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no, 'order_stat': rtn.order_stat,
                            'total_complete_qty': rtn.total_complete_qty, 'remain_qty': rtn.remain_qty, 'create_date': rtn.create_date,
                            'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num, 'message': message})

        return JsonResponse(stock_order_rtn_list, safe=False)
    except Exception as e:
        print('잘못된 인덱스입니다.', e)

def cancel(request):
    acct_no = request.GET.get('acct_no', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    id = request.GET.get('id', '')
    order_no = request.GET.get('order_no', '')
    order_price = str(int(request.GET.get('order_price', '').replace(",","")))
    order_amount = str(int(request.GET.get('order_amount', '').replace(",","")))

    yyyy = DateFormat(datetime.now()).format('Y')
    mm = DateFormat(datetime.now()).format('m')
    dd = DateFormat(datetime.now()).format('d')

    try:
        # 주식정정취소가능주문 조회
        #e = order_psbl_cancel_revice(access_token, app_key, app_secret, acct_no)
        #for i, name in enumerate(e.index):
        #    e_order_type = e['주문구분명'][i]
        #    e_name = e['종목명'][i]
        #    e_purchase_qty = int(e['주문수량'][i])
        #    e_purchase_price = int(e['주문단가'][i])
        #    e_complete_qty = int(e['총체결수량'][i])
        #    e_remain_qty = int(e['가능수량'][i])

        # 주식주문(취소)
        c = order_cancel_revice(access_token, app_key, app_secret, acct_no, "02", order_no, order_amount, order_price)
        if c['ODNO'] != "":
            stock_order.objects.filter(id=id).update(
                order_no=int(c['ODNO']),
                order_stat="04",
                remain_qty=int(order_amount),
                proc_date=datetime.now()
            )

        asset_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
        asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, aply_end_dt='99991231').first()

        if stock_fund_mng.objects.filter(acct_no=acct_no).count() < 1:
            stock_order_rtn_list = []
        else:
            if stock_market_mng.objects.filter(acct_no=acct_no).count() < 1:
                stock_order_rtn_list = []
            else:
                stock_order_rtn = stock_order.objects.filter(acct_no=acct_no, create_date__year=yyyy, create_date__month=mm, create_date__day=dd).order_by('-create_date')
                stock_order_rtn_list = []
                if len(stock_order_rtn) > 0:
                    for index, rtn in enumerate(stock_order_rtn, start=1):
                        stock_order_rtn_list.append(
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': rtn.buy_price, 'buy_amount': rtn.buy_amount, 
                            'sell_price': rtn.sell_price, 'sell_amount': rtn.sell_amount, 'loss_price': rtn.loss_price,
                            'target_price': rtn.target_price, 'trading_type': rtn.trading_type, 'asset_risk_num': rtn.asset_risk_num,
                            'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no, 'order_stat': rtn.order_stat,
                            'total_complete_qty': rtn.total_complete_qty, 'remain_qty': rtn.remain_qty, 'create_date': rtn.create_date,
                            'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

        return JsonResponse(stock_order_rtn_list, safe=False)
    except Exception as e:
        print('잘못된 인덱스입니다.', e)

def asset_risk_change(acct_no, app_key, app_secret, access_token, asset_risk_num):
    asset_risk_info = stock_market_mng.objects.filter(acct_no=acct_no, asset_risk_num=asset_risk_num, aply_end_dt='99991231').first()

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
        output2 = ar.getBody().output2

        if ar.isOK() and output2:
            f = pd.DataFrame(output2)
            for i, name in enumerate(f.index):
                u_prvs_rcdl_excc_amt = int(f['prvs_rcdl_excc_amt'][i])  # 가수도 정산 금액
            print("가수도 정산 금액 : " + format(int(u_prvs_rcdl_excc_amt), ',d'))
            if asset_risk_info.market_level_num == "1":  # 하락 지속 후, 기술적 반등
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
            elif asset_risk_info.market_level_num == "2":  # 단기 추세 전환 후, 기술적 반등
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
            elif asset_risk_info.market_level_num == "3":  # 패턴내에서 기술적 반등
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
            elif asset_risk_info.market_level_num == "4":  # 일봉상 추세 전환 후, 눌림구간에서 반등
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
            elif asset_risk_info.market_level_num == "5":  # 상승 지속 후, 패턴내에서 기술적 반등
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

            stock_market_mng.objects.filter(acct_no=acct_no, asset_risk_num=asset_risk_num, aply_end_dt='99991231').update(total_asset=n_asset_sum, risk_rate=n_risk_rate, risk_sum=n_risk_sum, item_number=n_stock_num)
    except Exception as e:
        print('잘못된 인덱스입니다.', e)

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

# 매수 가능(현금) 조회
def inquire_psbl_order(access_token, app_key, app_secret, acct_no):
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "TTTC8908R"}    # tr_id : TTTC8908R[실전투자], VTTC8908R[모의투자]
    params = {
               "CANO": acct_no,
               "ACNT_PRDT_CD": "01",
               "PDNO": "",                     # 종목번호(6자리)
               "ORD_UNPR": "0",                # 1주당 가격
               "ORD_DVSN": "02",               # 02 : 조건부지정가
               "CMA_EVLU_AMT_ICLD_YN": "Y",    # CMA평가금액포함여부
               "OVRS_ICLD_YN": "N"             # 해외포함여부
    }
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)

    return ar.getBody().output['nrcvb_buy_amt']

# 주식주문(현금)
def order_cash(buy_flag, access_token, app_key, app_secret, acct_no, stock_code, ord_dvsn, order_qty, order_price):

    if buy_flag:
        tr_id = "TTTC0802U"  #buy : TTTC0802U[실전투자], VTTC0802U[모의투자]
    else:
        tr_id = "TTTC0801U"  #sell : TTTC0801U[실전투자], VTTC0801U[모의투자]

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": tr_id}
    params = {
               "CANO": acct_no,
               "ACNT_PRDT_CD": "01",
               "PDNO": stock_code,
               "ORD_DVSN": ord_dvsn,    # 00 : 지정가, 01 : 시장가
               "ORD_QTY": order_qty,
               "ORD_UNPR": order_price
    }
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    #res = requests.get(URL, headers=headers, params=params, verify=False)
    res = requests.post(URL, data=json.dumps(params), headers=headers, verify=False)
    ar = resp.APIResp(res)
    #ar.printAll()
    return ar.getBody().output

# 매도 계좌 잔고 조회
def get_acct_balance_sell(access_token, app_key, app_secret, acct_no):
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

    if ar.isOK():
        tdf = pd.DataFrame(ar.getBody().output1)
        tdf.set_index('pdno')
        return tdf[['pdno', 'prdt_name','hldg_qty', 'ord_psbl_qty', 'pchs_avg_pric', 'pchs_amt', 'evlu_amt', 'evlu_pfls_amt', 'evlu_pfls_rt', 'prpr', 'bfdy_cprs_icdc', 'fltt_rt']]
    else:
        ar.printError()
        return pd.DataFrame()

# 주식주문(정정취소)
def order_cancel_revice(access_token, app_key, app_secret, acct_no, cncl_dv, order_no, order_qty, order_price):

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "TTTC0803U"}    # TTTC0803U[실전투자], VTTC0803U[모의투자]
    params = {
               "CANO": acct_no,
               "ACNT_PRDT_CD": "01",
               "KRX_FWDG_ORD_ORGNO": "06010",
               "ORGN_ODNO": order_no,
               "ORD_DVSN": "00",
               "RVSE_CNCL_DVSN_CD": cncl_dv,    # 정정 : 01, 취소 : 02
               "ORD_QTY": str(order_qty),
               "ORD_UNPR": str(order_price),
               "QTY_ALL_ORD_YN": "Y"
    }
    PATH = "uapi/domestic-stock/v1/trading/order-rvsecncl"
    URL = f"{URL_BASE}/{PATH}"
    #res = requests.get(URL, headers=headers, params=params, verify=False)
    res = requests.post(URL, data=json.dumps(params), headers=headers, verify=False)
    ar = resp.APIResp(res)
    #ar.printAll()
    return ar.getBody().output

# 주식정정취소가능주문 조회
def order_psbl_cancel_revice(access_token, app_key, app_secret, acct_no):

    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {access_token}",
               "appKey": app_key,
               "appSecret": app_secret,
               "tr_id": "TTTC8036R"}    # 실전투자
    params = {
               "CANO": acct_no,
               "ACNT_PRDT_CD": "01",
               "CTX_AREA_FK100": '',
               "CTX_AREA_NK100": '',
               "INQR_DVSN_1": '0',
               "INQR_DVSN_2": '0'
    }
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.get(URL, headers=headers, params=params, verify=False)
    ar = resp.APIResp(res)
    ar.printAll()
    if ar.isOK():
        tdf = pd.DataFrame(ar.getBody().output)
        tdf.set_index('odno', inplace=True)
        tdf.drop('', inplace=True)
        cf1 = ['ord_dvsn_name', 'pdno', 'prdt_name', 'rvse_cncl_dvsn_name', 'ord_qty', 'ord_unpr', 'ord_tmd', 'tot_ccld_qty', 'psbl_qty', 'sll_buy_dvsn_cd','ord_dvsn_cd']
        cf2 = ['주문구분명', '종목코드', '종목명', '정정취소구분명', '주문수량', '주문단가', '주문시간', '총체결수량', '가능수량', '매도매수구분코드', '주문구분코드']
        tdf = tdf[cf1]
        ren_dict = dict(zip(cf1, cf2))
        return tdf.rename(columns=ren_dict)
    else:
        ar.printError()
        return pd.DataFrame()

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

def minutesInfo(request):
    code = request.GET.get('code', '')
    company = request.GET.get('company', '')
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')

    for f in glob.glob(os.getcwd()+"/templates/stockOrder/minutes_" + company + "*.html"):
        os.remove(f)

    # 현재일 기준 최근 영업일
    stock_day = get_recent_business_day()

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
            time.sleep(0.5)
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
    fig.write_html(os.getcwd() + "/templates/stockOrder/minutes_" + company + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M') + ".html", auto_open=False)

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'code': code, 'name': company + datetime.now().strftime("%Y%m%d") + time.strftime('%H%M')})

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

def stockSearch(request):
    search_day = request.GET.get('search_day', '')
    search_name = request.GET.get('search_name', '')
    name = request.GET.get('name', '')

    stockSearch_info = stock_search_form.objects.filter(search_day=search_day, search_name=search_name, name__startswith=name).order_by('search_time')

    stockSearch_info_rtn_list = []
    if len(stockSearch_info) > 0:

        for i, rtn in enumerate(stockSearch_info, start=1):
            stockSearch_info_rtn_list.append({'search_dtm': rtn.search_day + " " + rtn.search_time,
                                               'search_name': rtn.search_name, 
                                               'code': rtn.code, 'name': rtn.name, 
                                               'current_price': rtn.current_price,
                                               'high_price': rtn.high_price,
                                               'low_price': rtn.low_price,
                                               'day_rate': float(rtn.day_rate),
                                               'volumn': rtn.volumn,
                                               'volumn_rate': float(rtn.volumn_rate),
                                               'market_total_sum': rtn.market_total_sum})
    else:
        stockSearch_info_rtn_list = []

    return JsonResponse(stockSearch_info_rtn_list, safe=False)

def runStockSearch(request):
    app_key = request.GET.get('app_key', '')
    app_secret = request.GET.get('app_secret', '')
    access_token = request.GET.get('access_token', '')
    search_choice = request.GET.get('search_choice', '')

    today = datetime.now().strftime("%Y%m%d")
    time = datetime.now().strftime("%H%M")

    # 조건검색명
    if search_choice == '0':
        search_name = "거래폭발"
    elif search_choice == '1':
        search_name = "단기추세"
    elif search_choice == '2':
        search_name = "투자혁명"

    def inquire_search_result(access_token, app_key, app_secret, id, seq):

        headers = {"Content-Type": "application/json",
                   "authorization": f"Bearer {access_token}",
                   "appKey": app_key,
                   "appSecret": app_secret,
                   "tr_id": "HHKST03900400",
                   "custtype": "P"}
        params = {
            'user_id': id,
            'seq': seq
        }
        PATH = "/uapi/domestic-stock/v1/quotations/psearch-result"
        URL = f"{URL_BASE}/{PATH}"
        res = requests.get(URL, headers=headers, params=params, verify=False)
        ar = resp.APIResp(res)
        #ar.printAll()
        return ar.getBody().output2

    item_search = inquire_search_result(access_token, app_key, app_secret, 'phills2', search_choice)  # 종목조건검색 조회
    
    for i in item_search:
        stock_search_form.objects.update_or_create(search_day=today, code=i['code'], search_name=search_name,
            defaults={'search_day':today,
                      'search_time':time,
                      'search_name':search_name,
                      'code':i['code'],
                      'name':i['name'],
                      'low_price':math.ceil(float(i['low'])),
                      'high_price':math.ceil(float(i['high'])),
                      'current_price':math.ceil(float(i['price'])),
                      'day_rate':i['chgrate'],
                      'volumn':math.ceil(float(i['acml_vol'])),
                      'volumn_rate':i['chgrate2'],
                      'market_total_sum':int(round(float(i['stotprice']))),
                      'cdate':datetime.now()
                     }
        )

    stockSearch_info = stock_search_form.objects.filter(search_day=today, search_name=search_name).order_by('search_time')

    stockSearch_info_rtn_list = []
    if len(stockSearch_info) > 0:

        for i, rtn in enumerate(stockSearch_info, start=1):
            stockSearch_info_rtn_list.append({'search_dtm': rtn.search_day + " " + rtn.search_time,
                                               'search_name': rtn.search_name, 
                                               'code': rtn.code, 'name': rtn.name, 
                                               'current_price': rtn.current_price,
                                               'high_price': rtn.high_price,
                                               'low_price': rtn.low_price,
                                               'day_rate': float(rtn.day_rate),
                                               'volumn': rtn.volumn,
                                               'volumn_rate': float(rtn.volumn_rate),
                                               'market_total_sum': rtn.market_total_sum})
    else:
        stockSearch_info_rtn_list = []

    return JsonResponse(stockSearch_info_rtn_list, safe=False)