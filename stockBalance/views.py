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

# Create your views here.

def list(request):
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

                stock_balance.objects.filter(acct_no=acct_no, asset_num=stock_fund_mng_info.asset_num, last_chg_date__year=yyyy, last_chg_date__month=mm, last_chg_date__day=dd).delete()

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
                                      'sell_plan_amount': e_sell_plan_amount    # 매도가능수량
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
                                      'sell_plan_amount': 0                     # 매도가능수량
                                      }
                        )

            stock_balance_rtn = stock_balance.objects.filter(acct_no=acct_no, asset_num=stock_fund_mng_info.asset_num, last_chg_date__year=yyyy, last_chg_date__month=mm, last_chg_date__day=dd).order_by('-earnings_rate')
            stock_balance_rtn_list = []

            for index, rtn in enumerate(stock_balance_rtn, start=1):
                stock_balance_rtn_list.append({'acct_no': rtn.acct_no, 'name':rtn.name, 'purchase_price':format(int(rtn.purchase_price), ',d'), 'purchase_amount':format(int(rtn.purchase_amount), ',d'), 'purchase_sum':format(int(rtn.purchase_sum), ',d'),
                                               'current_price':format(int(rtn.current_price), ',d'), 'eval_sum':format(int(rtn.eval_sum), ',d'), 'earnings_rate':rtn.earnings_rate, 'valuation_sum':format(int(rtn.valuation_sum), ',d'),
                                               'end_loss_price':rtn.end_loss_price, 'end_target_price':rtn.end_target_price, 'trading_plan':rtn.trading_plan, 'asset_num':rtn.asset_num,
                                               'sell_plan_sum':rtn.sell_plan_sum, 'sell_plan_amount':rtn.sell_plan_amount, 'last_chg_date':rtn.last_chg_date})
        else:
            stock_balance_rtn_list = []

        return JsonResponse(stock_balance_rtn_list, safe=False)
    except Exception as ex:
        print('잘못된 인덱스입니다.', ex)

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
    fig.write_html(os.getcwd()+"/templates/stockBalance/"+company+".html")

    stock_info_rtn_list = []
    stock_info_rtn_list.append({'code': code, 'name': company})

    return JsonResponse(stock_info_rtn_list, safe=False)

def detail(request, company):
    link = "stockBalance/"+company+".html"

    return render(request, link)