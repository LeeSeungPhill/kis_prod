from django.http import JsonResponse
from .models import stock_order, sub_total
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

#URL_BASE = "https://openapivts.koreainvestment.com:29443"   # 모의투자서비스
URL_BASE = "https://openapi.koreainvestment.com:9443"       # 실전서비스

def list(request):
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
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': format(rtn.buy_price, ',d'), 'buy_amount': format(rtn.buy_amount, ',d'),
                             'sell_price': format(rtn.sell_price, ',d'), 'sell_amount': format(rtn.sell_amount, ',d'), 'loss_price': format(rtn.loss_price, ',d'),
                             'target_price': format(rtn.target_price, ',d'), 'trading_type': rtn.trading_type,
                             'asset_risk_num': rtn.asset_risk_num,
                             'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no,
                             'order_stat': rtn.order_stat,
                             'total_complete_qty': format(rtn.total_complete_qty, ',d'), 'remain_qty': format(rtn.remain_qty, ',d'),
                             'create_date': rtn.create_date,
                             'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num,
                             'stock_asset_risk_num': asset_risk_info.asset_risk_num})

            else:
                stock_order_rtn_list.append(
                    {'id': "", 'code': "", 'name': "", 'buy_price': "", 'buy_amount': "",
                     'sell_price': "", 'sell_amount': "", 'loss_price': "",
                     'target_price': "", 'trading_type': "", 'asset_risk_num': "",
                     'asset_num': "", 'proc_yn': "", 'order_no': "", 'order_stat': "",
                     'create_date': "", 'total_complete_qty': "", 'remain_qty': "",
                     'proc_date': "", 'stock_asset_num': asset_info.asset_num,
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

        now_price = format(int(a['stck_prpr']), ',d')   # 현재가
        high_price = format(int(a['stck_hgpr']), ',d')  # 고가
        low_price = format(int(a['stck_lwpr']), ',d')   # 저가
        open_price = format(int(a['stck_oprc']), ',d')  # 시가
        max_price = format(int(a['stck_mxpr']), ',d')   # 상한가
        min_price = format(int(a['stck_llam']), ',d')   # 하한가
        volumn = format(int(a['acml_vol']), ',d')       # 거래량
    else:
        now_price = ""
        high_price = ""
        low_price = ""
        open_price = ""
        max_price = ""
        min_price = ""
        volumn = ""

    stock_order_rtn_list = []

    stock_order_rtn_list.append(
        {'code': code, 'now_price': now_price, 'high_price': high_price, 'low_price': low_price,
         'open_price': open_price, 'max_price': max_price, 'min_price': min_price, 'volumn': volumn})

    return JsonResponse(stock_order_rtn_list, safe=False)
    #data = {'columns': [Counts, Costs, ]}
    #return HttpResponse(json.dumps(data), content_type='text/json')

def get_chart(code, company):
    pre_day = datetime.today() - timedelta(days=500)
    start = pre_day.strftime("%Y%m%d")
    end = datetime.now().strftime("%Y%m%d")
    #print("start : " + start)
    #print("end : " + end)
    df = web.naver.NaverDailyReader(code, start=start, end=end).read()
    #print(df)
    df = df.astype(int)  # Object 데이터를 int로 변환

    # 캔들 차트 객체 생성
    df = df.reset_index()
    df['Date'] = df['Date'].apply(lambda x: datetime.strftime(x, '%Y-%m-%d'))  # Datetime to str
    df['ma10'] = df['Volume'].rolling(10).mean()

    data1 = go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                           increasing_line_color='red', decreasing_line_color='blue', name="candle")
    data2 = go.Bar(x=df['Date'], y=df['Volume'], name="volumn")

    fig = ms.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)
    fig.add_trace(data1, row=1, col=1)
    fig.add_trace(data2, row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['ma10'], line=dict(color="#414b73"), name='MA10'), row=2, col=1)
    fig.update_layout(xaxis1=dict(type="category", categoryorder='category ascending'),
                      xaxis2=dict(type="category", categoryorder='category ascending'), title=company+"["+code+"]",
                      yaxis1_title='Stock Price', yaxis2_title='Volume', xaxis2_title='periods',
                      xaxis1_rangeslider_visible=False, xaxis2_rangeslider_visible=False, )
    #fig.show()

    fig.write_html(os.getcwd()+"/templates/stockOrder/"+company+".html")

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
    stock_info_rtn_list.append({'code': code, 'name': company})

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
            if i.trading_type == "B":       # 매수

                if i.buy_price > i.loss_price:                  # 주문가 매수
                    if i.buy_amount == 0:
                        # 자산번호 = 0 인 경우, 투자금액 설정
                        if i.asset_num == 0:
                            stock_fund_mng_info = stock_fund_mng.objects.filter(acct_no=acct_no).order_by('-last_chg_date').first()
                            # 상승추세 : 5,000,000원, 하락추세 및 패턴 : 2,500,000원
                            if stock_fund_mng_info.cash_rate > 50:
                                n_asset_sum = 5000000
                            else:
                                n_asset_sum = 2500000
                            # 매수량 = 투자금액 / 매수가
                            n_buy_amount = n_asset_sum / i.buy_price
                            # 매수금액
                            n_buy_sum = i.buy_price * round(n_buy_amount)
                            print("투자금액 : " + str(n_asset_sum))
                            print("매수량 : " + str(round(n_buy_amount)))
                            print("매수금액 : " + str(n_buy_sum))
                        else:   # 자산번호 <> 0 인 경우, 종목손실금액, 매수량 설정
                            market_mng_info = stock_market_mng.objects.filter(acct_no=acct_no,asset_risk_num=i.asset_risk_num).first()
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
                        c = order_cash(False, access_token, app_key, app_secret, acct_no, i.code, "00", str(round(i.sell_amount)), str(i.sell_price))
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

            else:
                print("매매유형 부적합 주문 미처리")


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
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': format(rtn.buy_price, ',d'), 'buy_amount': format(rtn.buy_amount, ',d'),
                            'sell_price': format(rtn.sell_price, ',d'), 'sell_amount': format(rtn.sell_amount, ',d'), 'loss_price': format(rtn.loss_price, ',d'),
                            'target_price': format(rtn.target_price, ',d'), 'trading_type': rtn.trading_type, 'asset_risk_num': rtn.asset_risk_num,
                            'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no, 'order_stat': rtn.order_stat,
                            'total_complete_qty': format(rtn.total_complete_qty, ',d'), 'remain_qty': format(rtn.remain_qty, ',d'), 'create_date': rtn.create_date,
                            'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

                else:
                    stock_order_rtn_list.append(
                        {'id': "", 'code': "", 'name': "", 'buy_price': "", 'buy_amount': "",
                         'sell_price': "", 'sell_amount': "", 'loss_price': "",
                         'target_price': "", 'trading_type': "", 'asset_risk_num': "",
                         'asset_num': "", 'proc_yn': "", 'order_no': "", 'order_stat': "",
                         'create_date': "", 'total_complete_qty': "", 'remain_qty': "",
                         'proc_date': "", 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

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
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': format(rtn.buy_price, ',d'), 'buy_amount': format(rtn.buy_amount, ',d'),
                            'sell_price': format(rtn.sell_price, ',d'), 'sell_amount': format(rtn.sell_amount, ',d'), 'loss_price': format(rtn.loss_price, ',d'),
                            'target_price': format(rtn.target_price, ',d'), 'trading_type': rtn.trading_type, 'asset_risk_num': rtn.asset_risk_num,
                            'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no, 'order_stat': rtn.order_stat,
                            'total_complete_qty': format(rtn.total_complete_qty, ',d'), 'remain_qty': format(rtn.remain_qty, ',d'), 'create_date': rtn.create_date,
                            'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

                else:
                    stock_order_rtn_list.append(
                        {'id': "", 'code': "", 'name': "", 'buy_price': "", 'buy_amount': "",
                         'sell_price': "", 'sell_amount': "", 'loss_price': "",
                         'target_price': "", 'trading_type': "", 'asset_risk_num': "",
                         'asset_num': "", 'proc_yn': "", 'order_no': "", 'order_stat': "",
                         'create_date': "", 'total_complete_qty': "", 'remain_qty': "",
                         'proc_date': "", 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

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
                            {'id': rtn.id, 'code': rtn.code, 'name': rtn.name, 'buy_price': format(rtn.buy_price, ',d'), 'buy_amount': format(rtn.buy_amount, ',d'),
                            'sell_price': format(rtn.sell_price, ',d'), 'sell_amount': format(rtn.sell_amount, ',d'), 'loss_price': format(rtn.loss_price, ',d'),
                            'target_price': format(rtn.target_price, ',d'), 'trading_type': rtn.trading_type, 'asset_risk_num': rtn.asset_risk_num,
                            'asset_num': rtn.asset_num, 'proc_yn': rtn.proc_yn, 'order_no': rtn.order_no, 'order_stat': rtn.order_stat,
                            'total_complete_qty': format(rtn.total_complete_qty, ',d'), 'remain_qty': format(rtn.remain_qty, ',d'), 'create_date': rtn.create_date,
                            'proc_date': rtn.proc_date, 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

                else:
                    stock_order_rtn_list.append(
                        {'id': "", 'code': "", 'name': "", 'buy_price': "", 'buy_amount': "",
                         'sell_price': "", 'sell_amount': "", 'loss_price': "",
                         'target_price': "", 'trading_type': "", 'asset_risk_num': "",
                         'asset_num': "", 'proc_yn': "", 'order_no': "", 'order_stat': "",
                         'create_date': "", 'total_complete_qty': "", 'remain_qty': "",
                         'proc_date': "", 'stock_asset_num': asset_info.asset_num, 'stock_asset_risk_num': asset_risk_info.asset_risk_num})

        return JsonResponse(stock_order_rtn_list, safe=False)
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

    return ar.getBody().output['ord_psbl_cash']

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
