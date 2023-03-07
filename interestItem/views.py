from django.http import JsonResponse
from .models import interest_item

# Create your views here.

def list(request):
    acct_no = request.GET.get('acct_no', '')

    if interest_item.objects.filter(acct_no=acct_no).count() > 0:

        interest_item_rtn = interest_item.objects.filter(acct_no=acct_no).order_by('-last_chg_date')
        interest_item_rtn_list = []

        for index, rtn in enumerate(interest_item_rtn, start=1):
            interest_item_rtn_list.append(
                {'acct_no': rtn.acct_no, 'code': rtn.code, 'name': rtn.name, 'through_price': format(int(rtn.through_price), ',d'),
                 'leave_price': format(int(rtn.leave_price), ',d'), 'resist_price': format(int(rtn.resist_price), ',d'), 'support_price': format(int(rtn.support_price), ',d'),
                 'trend_high_price': format(int(rtn.trend_high_price), ',d'), 'trend_low_price': format(int(rtn.trend_low_price), ',d'), 'last_chg_date': rtn.last_chg_date})

    else:
        interest_item_rtn_list = []

    return JsonResponse(interest_item_rtn_list, safe=False)