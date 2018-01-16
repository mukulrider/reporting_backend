from __future__ import unicode_literals

import datetime as DT
from datetime import datetime

import logging
import time
# from .NPD_test import outperformance_calculations
import pandas as pd
import numpy as np
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Max, Sum, Q, Min, F
from django.http import JsonResponse
import re
from rest_framework.views import APIView
from django_pandas.io import read_frame
from .models import sales_heirarchy, calendar_dim_hierarchy, dss_view, latest_date
import json

timestr = time.strftime("%Y%m%d")
logging.basicConfig(filename='logs/reporting_views_'+timestr+'.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

def make_json_daily(sent_req, kwargs_header, default_check):
    cols = ['store_type', 'commercial_name', 'category_name', 'buying_controller', 'buyer', 'junior_buyer',
            'product_subgroup', 'brand_indicator', 'brand_name',
            'product']
    # find lowest element of cols
    lowest = 0
    second_lowest = 0

    element_list = []
    if sent_req != {}:
        print("entered if")
        for i in sent_req.keys():
            if i in cols:
                element_list.append(cols.index(i))
        print(element_list)
    else:
        print("entered else")

        print("sent_req", sent_req, default_check)
        sent_req = default_check
        for i in sent_req.keys():
            if i in cols:
                element_list.append(cols.index(i))
        sent_req = {reqobj.replace('_header', ''): sent_req.get(reqobj) for reqobj in sent_req.keys()}
        print(element_list)

    element_list.sort()

    try:
        lowest = element_list[-1]
    except:
        pass

    try:
        second_lowest = element_list[-2]
    except:
        pass

    lowest_key = cols[lowest]
    second_lowest_key = cols[lowest]

    # print('lowest_key:', lowest_key, '|', 'lowest', lowest)

    final_list = []  # final list to send

    col_unique_list_name = []  # rename
    col_unique_list_name_obj = {}  # rename
    for col_name in cols:
        # print('\n********* \n' + col_name + '\n*********')
        # print('sent_req.get(col_name):', sent_req.get(col_name))
        col_unique_list = col_distinct({}, col_name, kwargs_header)
        col_unique_list_name.append({'name': col_name,
                                     'unique_elements': col_unique_list})
        col_unique_list_name_obj[col_name] = col_unique_list
        # args sent as url params
        kwargs2 = {reqobj + '__in': sent_req.get(reqobj) for reqobj in sent_req.keys()}

        category_of_sent_obj_list = col_distinct(kwargs2, col_name, kwargs_header)
        # print(len(category_of_sent_obj_list))
        sent_obj_category_list = []

        # get unique elements for `col_name`
        for i in category_of_sent_obj_list:
            sent_obj_category_list.append(i)

        def highlight_check(category_unique):
            # print(title)
            if len(sent_req.keys()) > 0:
                highlighted = False
                if col_name in sent_req.keys():
                    if col_name == cols[lowest]:
                        queryset = sales_heirarchy.objects.filter(**{col_name: category_unique})[:1].get()
                        # x = getattr(queryset, cols[lowest])
                        y = getattr(queryset, cols[second_lowest])
                        # print(x, '|', y, '|', cols[lowest], '|',
                        #       'Category_second_last:' + cols[second_lowest],
                        #       '|', col_name,
                        #       '|', category_unique)
                        for i in sent_req.keys():
                            # print('keys:', i, sent_req.get(i))
                            if y in sent_req.get(i) and cols[second_lowest] == i:
                                highlighted = True

                        return highlighted
                    else:
                        return False
                else:
                    if category_unique in sent_obj_category_list:
                        highlighted = True
                    return highlighted
            else:
                return True

        # assign props to send as json response

        y = []
        for title in col_unique_list:
            selected = True if type(sent_req.get(col_name)) == list and title in sent_req.get(col_name) else False
            y.append({'title': title,
                      'resource': {'params': col_name + '=' + title,
                                   'selected': selected},
                      'highlighted': selected if selected else highlight_check(title)})

        final_list.append({'items': y,
                           'input_type': 'Checkbox',
                           'title': col_name,
                           'buying_controller': 'Beers, Wines and Spirits',
                           'id': col_name,
                           'required': True if col_name == 'buying_controller' or col_name == 'store_type' else False
                           })

    def get_element_type(title):
        if title == 'buying_controller':
            return 'Checkbox'
        else:
            return 'Checkbox'

    # sort list with checked at top

    final_list2 = []
    for i in final_list:
        m = []
        for j in i.get('items'):

            if j['resource']['selected']:
                m.append(j)

        for j in i.get('items'):
            if not j['resource']['selected']:
                m.append(j)

        final_list2.append({'items': m,
                            'input_type': get_element_type(i['title']),
                            'title': i['title'],
                            'required': i['required'],
                            'category_director': 'Beers, Wines and Spirits',
                            'id': i['id']})
    return JsonResponse({'cols': cols, 'checkbox_list': final_list2}, safe=False)

def col_distinct(kwargs, col_name, kwargs_header):
    queryset = sales_heirarchy.objects.filter(**kwargs_header).values(col_name).order_by(col_name).distinct()
    base_product_number_list = [k.get(col_name) for k in queryset]
    return base_product_number_list

class dss_filterdata(APIView):
    def get(self, request):
        obj = {}
        get_keys = request.GET.keys()
        obj2 = {}
        default_keys = request.GET.keys()
        for i in get_keys:
            # print(request.GET.getlist(i))
            obj[i] = request.GET.getlist(i)
        # print(obj)
        sent_req = obj
        for i in default_keys:
            # print(request.GET.getlist(i))
            obj2[i] = request.GET.getlist(i)
        # print(obj)
        default_check = obj2
        user_id = default_check.pop('user_id')
        designation = default_check.pop('designation')
        user_name = default_check.pop('user_name')
        # x = read_frame(dss_view.objects.all())
        # x.to_csv('dss.csv')

        user_id = sent_req.pop('user_id')
        designation = sent_req.pop('designation')
        user_name = sent_req.pop('user_name')
        buying_controller_header = sent_req.pop('buying_controller_header')
        buyer_header = sent_req.pop('buyer_header',None)

        if buyer_header is None:
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }
        return make_json_daily(sent_req, kwargs_header, default_check)

class data_stage(APIView):
    def get(self, request, format=None, *args):
        args_val = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        dt_sel = args_val.get('dt_sel__iexact', None)
        tesco_week = args_val.get('tesco_week__iexact', None)
        store_type = args.get('store_type__in', ['Main Estate','Express'])
        category_name = args.get('category_name__in', None)
        val_type = int(args_val.get('val_type__iexact', '1'))
        # val_type=1
        buying_controller = args.get('buying_controller__in', None)
        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        product_subgroup = args.get('product_subgroup__in', None)
        brand_indicator = args.get('brand_indicator__in', None)
        brand_name = args.get('brand_name__in', None)
        product = args.get('product__in', None)
        commercial_name = args.get('commercial_name__in', None)
        # store_type = args.get('store_type__in',None)
        # # week_sel = '201601'
        # print(type(val_type))
        # print(dt_sel)
        # dt_sel = datetime(2017, 4, 30)
        if tesco_week is None:
            tesco_week = dss_view.objects.all().aggregate(tesco_week=Max('tesco_week'))
            tesco_week = int(tesco_week['tesco_week'])
            # print(tesco_week)

        if dt_sel is None:
            dt_dataframe = pd.DataFrame(
                list(dss_view.objects.filter(tesco_week__iexact=tesco_week).values('tesco_week').annotate(
                    latest_dt=Max('calendar_date'))))
            # print("check1")
            # print(dt_dataframe)
            dt_sel = datetime.combine(dt_dataframe.loc[0, 'latest_dt'], datetime.min.time())
            # print("check2")
            # print(dt_sel)           
            dt_sel_ordered = latest_date.objects.filter(date_ty__lte=dt_sel).values('date_ty').order_by(
                '-date_ty').distinct()
            # print("Check_____________1", dt_sel_ordered[7])
            # print("Check_____________2", type(dt_sel_ordered[7]))
            date_lw = datetime.combine(dt_sel_ordered[7]['date_ty'], datetime.min.time())
            # print("check3")
            # print(date_lw)

            # date_lw = datetime.strptime(dt_sel_ordered[7], '%Y-%m-%d')
            dt_sel_ly = read_frame(latest_date.objects.filter(date_ty=dt_sel).values('date_ly').distinct())
            date_ly = datetime.combine(dt_sel_ly['date_ly'][0], datetime.min.time())
            # print("check4")
            # print(date_ly)
            # (date_ly.strip())[-10:]
        else:
            dt_sel = datetime.strptime(dt_sel, '%Y-%m-%d')
            dt_sel_ordered = latest_date.objects.filter(date_ty__lte=dt_sel).values('date_ty').order_by(
                '-date_ty').distinct()
            date_lw = datetime.combine(dt_sel_ordered[7]['date_ty'], datetime.min.time())
            # date_lw = datetime.strptime(date_lw, '%Y-%m-%d')
            dt_sel_ly = read_frame(latest_date.objects.filter(date_ty=dt_sel).values('date_ly').distinct())
            date_ly = datetime.combine(dt_sel_ly['date_ly'][0], datetime.min.time())




            #### Getting last year week from the selected week
        tesco_week_lastyear = read_frame(latest_date.objects.filter(week_ty=tesco_week).values('week_ly').distinct())
        tesco_week_lastyear = int(tesco_week_lastyear['week_ly'])
        # print("checkkkkkkkkkkkkkkkkkkkkkk")
        # print(tesco_week_lastyear)





        kwargs_filter = {
            'category_name__in': category_name,
            'buying_controller__in': buying_controller,
            'buyer__in': buyer,
            'junior_buyer__in': junior_buyer,
            'product_subgroup__in': product_subgroup,
            'brand_indicator__in': brand_indicator,
            'brand_name__in': brand_name,
            'product__in': product,
            'store_type__in': store_type,
            'commercial_name__in': commercial_name

        }
        kwargs_filter = dict(filter(lambda item: item[1] is not None, kwargs_filter.items()))

        final_data = {}
        # print(prod_filters)

        user_id = args_val.pop('user_id__iexact', None)
        designation = args_val.pop('designation__iexact', None)
        session_id = args_val.pop('session_id__iexact', None)
        user_name = args_val.pop('user_name__iexact', None)
        buying_controller_header = args_val.pop('buying_controller_header__iexact', None)
        buyer_header = args_val.pop('buyer_header__iexact', None)
        print("buying controller:",buying_controller_header)
        print("buyer:",buyer_header)

        if buyer_header is None:
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        kwargs_header = dict(filter(lambda item: item[1] is not None, kwargs_header.items()))

        if args is None:
            print("entered none args")
            product_id_list = sales_heirarchy.objects.filter(**kwargs_header).values("product_id").distinct()
        else:
            print("entered args")
            product_id_list = sales_heirarchy.objects.filter(**kwargs_filter).values("product_id").distinct()
        # product_id_list = product_id_list[['product_id']].head()
        # x= list(product_id_list['product_id'])
        # print(x)
        # print("TEEEEST22323")
        # print(list(product_id_list))


        ### To get the sales for the current week (daily basis) in selection

        # print(kwargs_graph)


        ### To get the sales for the last year week (daily basis)

        kwargs_current = {
            'store_type__in': store_type,
            'calendar_date__iexact': dt_sel,
            'product_id__in': product_id_list
        }
        print("kwargs3333", kwargs_current)
        kwargs_wow = {
            'store_type__in': store_type,
            'calendar_date__iexact': date_lw,
            'product_id__in': product_id_list
        }
        print("kwargs_wowww", kwargs_wow)
        print("asdasdsad", kwargs_wow['calendar_date__iexact'])

        kwargs_yoy = {
            'store_type__in': store_type,
            'calendar_date__iexact': date_ly,
            'product_id__in': product_id_list
        }
       # print("kwargs____yoyyyyy", kwargs_yoy)

        kwargs_wtd = {
            'store_type__in': store_type,
            'tesco_week__iexact': tesco_week,
            'product_id__in': product_id_list
        }
        # print("kwargs____wtdddddddddd",kwargs_wtd)



        # print("static data.................")
        static_data = list(dss_view.objects.filter(**kwargs_current).values(
            'calendar_date').annotate(tot_sales=Sum('daily_sales'),
                                      tot_vol=Sum('daily_volume'),
                                      tot_cogs=Sum('daily_cogs'),
                                      tot_sales_lfl=Sum('daily_sales_lfl'),
                                      tot_vol_lfl=Sum('daily_volume_lfl'),
                                      tot_cogs_lfl=Sum('daily_cogs_lfl')).annotate(tot_profit=F('tot_sales')- F('tot_cogs'),tot_profit_lfl=F('tot_sales_lfl')- F('tot_cogs_lfl')))
        print("kwargs current",kwargs_current,"static data", static_data)

        # print("static data.................2")
        static_data_lw = list(dss_view.objects.filter(**kwargs_wow).values(
            'calendar_date').annotate(tot_sales=Sum('daily_sales'),
                                      tot_vol=Sum('daily_volume'),
                                      tot_cogs=Sum('daily_cogs'),
                                      tot_sales_lfl=Sum('daily_sales_lfl'),
                                      tot_vol_lfl=Sum('daily_volume_lfl'),
                                      tot_cogs_lfl=Sum('daily_cogs_lfl')).annotate(tot_profit=F('tot_sales')- F('tot_cogs'),tot_profit_lfl=F('tot_sales_lfl')- F('tot_cogs_lfl')))

        # print("static data.................3")
        static_data_ly = list(dss_view.objects.filter(**kwargs_yoy).values(
            'calendar_date').annotate(tot_sales=Sum('daily_sales'),
                                      tot_vol=Sum('daily_volume'),
                                      tot_cogs=Sum('daily_cogs'),
                                      tot_sales_lfl=Sum('daily_sales_lfl'),
                                      tot_vol_lfl=Sum('daily_volume_lfl'),
                                      tot_cogs_lfl=Sum('daily_cogs_lfl'),
                                      tot_profit_lfl=Sum('daily_cogs_lfl')).annotate(tot_profit=F('tot_sales')- F('tot_cogs'),tot_profit_lfl=F('tot_sales_lfl')- F('tot_cogs_lfl')))

        #### To calculate for WTD
        static_data_wtd = dss_view.objects.filter(**kwargs_wtd).filter(calendar_date__lte=dt_sel).aggregate(tot_sales=Sum('daily_sales'),
                                      tot_vol=Sum('daily_volume'),
                                      tot_cogs=Sum('daily_cogs'))
        static_data_wtd_profit  = static_data_wtd['tot_sales'] - static_data_wtd['tot_cogs']

        print("static data wtd", static_data_wtd, "static_data_wtd_profit",static_data_wtd_profit)

        sales = {}
        volume = {}
        cogs = {}
        profit = {}
        # print("static data.................4")
        try:
            sales['sales_var_wow'] = (
                                     (static_data[0]['tot_sales'] - static_data_lw[0]['tot_sales']) / static_data_lw[0][
                                         'tot_sales']) * 100
            print("TY:",static_data[0]['tot_sales'],"LY:",static_data_ly[0]['tot_sales'])
            sales['sales_var_yoy'] = (
                                     (static_data[0]['tot_sales'] - static_data_ly[0]['tot_sales']) / static_data_ly[0][
                                         'tot_sales']) * 100
            sales['sales_var_lfl'] = ((static_data[0]['tot_sales_lfl'] - static_data_ly[0]['tot_sales_lfl']) /
                                      static_data_ly[0]['tot_sales_lfl']) * 100

            sales['sales_var_wow'] = round(sales['sales_var_wow'], 1)
            sales['sales_var_yoy'] = round(sales['sales_var_yoy'], 1)
            sales['sales_var_lfl'] = round(sales['sales_var_lfl'], 1)
        except:
            sales['sales_var_wow'] = 0
            sales['sales_var_yoy'] = 0
            sales['sales_var_lfl'] = 0

        ### adding wtd sales, current sales ,lfl sales
        sales['tot_sales'] = static_data[0]['tot_sales']
        sales['tot_sales_lfl'] = static_data[0]['tot_sales_lfl']
        sales['tot_sales_wtd'] = static_data_wtd['tot_sales']

        try:
            volume['vol_var_wow'] = ((static_data[0]['tot_vol'] - static_data_lw[0]['tot_vol']) / static_data_lw[0][
                'tot_vol']) * 100
            volume['vol_var_yoy'] = ((static_data[0]['tot_vol'] - static_data_ly[0]['tot_vol']) / static_data_ly[0][
                'tot_vol']) * 100
            volume['vol_var_lfl'] = ((static_data[0]['tot_vol_lfl'] - static_data_ly[0]['tot_vol_lfl']) /
                                     static_data_ly[0]['tot_vol_lfl']) * 100

            volume['vol_var_wow'] = round(volume['vol_var_wow'], 1)
            volume['vol_var_yoy'] = round(volume['vol_var_yoy'], 1)
            volume['vol_var_lfl'] = round(volume['vol_var_lfl'], 1)
        except:
            volume['vol_var_wow'] = 0
            volume['vol_var_yoy'] = 0
            volume['vol_var_lfl'] = 0

        volume['tot_vol'] = static_data[0]['tot_vol']
        volume['tot_vol_lfl'] = static_data[0]['tot_vol_lfl']
        volume['tot_vol_wtd'] = static_data_wtd['tot_vol']
        try:
            cogs['cogs_var_wow'] = ((static_data[0]['tot_cogs'] - static_data_lw[0]['tot_cogs']) / static_data_lw[0][
                'tot_cogs']) * 100
            cogs['cogs_var_yoy'] = ((static_data[0]['tot_cogs'] - static_data_ly[0]['tot_cogs']) / static_data_ly[0][
                'tot_cogs']) * 100
            cogs['cogs_var_lfl'] = ((static_data[0]['tot_cogs_lfl'] - static_data_ly[0]['tot_cogs_lfl']) /
                                    static_data_ly[0]['tot_cogs_lfl']) * 100

            cogs['cogs_var_lfl'] = round(cogs['cogs_var_lfl'], 1)
            cogs['cogs_var_yoy'] = round(cogs['cogs_var_yoy'], 1)
            cogs['cogs_var_wow'] = round(cogs['cogs_var_wow'], 1)
        except:
            cogs['cogs_var_wow'] = 0
            cogs['cogs_var_yoy'] = 0
            cogs['cogs_var_lfl'] = 0

        cogs['tot_cogs'] = static_data[0]['tot_cogs']
        cogs['tot_cogs_lfl'] = static_data[0]['tot_cogs_lfl']
        cogs['tot_cogs_wtd'] = static_data_wtd['tot_cogs']

        try:
            profit['profit_var_wow'] = ((static_data[0]['tot_profit'] - static_data_lw[0]['tot_profit']) /
                                        static_data_lw[0]['tot_profit']) * 100
            profit['profit_var_yoy'] = ((static_data[0]['tot_profit'] - static_data_ly[0]['tot_profit']) /
                                        static_data_ly[0]['tot_profit']) * 100
            profit['profit_var_lfl'] = ((static_data[0]['tot_profit_lfl'] - static_data_ly[0]['tot_profit_lfl']) /
                                        static_data_ly[0]['tot_profit_lfl']) * 100

            profit['profit_var_lfl'] = round(profit['profit_var_lfl'], 1)
            profit['profit_var_yoy'] = round(profit['profit_var_yoy'], 1)
            profit['profit_var_wow'] = round(profit['profit_var_wow'], 1)
        except:
            profit['profit_var_wow'] = 0
            profit['profit_var_yoy'] = 0
            profit['profit_var_lfl'] = 0

        profit['tot_profit'] = static_data[0]['tot_profit']
        profit['tot_profit_lfl'] = static_data[0]['tot_profit_lfl']
        profit['tot_profit_wtd'] = static_data_wtd_profit

        margin = {}
        margin['current_day'] = round(
            ((static_data[0]['tot_sales'] - static_data[0]['tot_cogs']) / static_data[0]['tot_sales']) * 100, 2)
        margin['current_day_lfl'] = round(((static_data[0]['tot_sales_lfl'] - static_data[0]['tot_cogs_lfl']) /
                                           static_data[0]['tot_sales_lfl']) * 100, 2)
        margin['wow'] = round((((static_data[0]['tot_sales'] - static_data_lw[0]['tot_sales']) - (
        static_data[0]['tot_cogs'] - static_data_lw[0]['tot_cogs'])) / (
                               static_data[0]['tot_sales'] - static_data_lw[0]['tot_sales'])) * 100, 1)
        margin['yoy'] = round((((static_data[0]['tot_sales'] - static_data_ly[0]['tot_sales']) - (
        static_data[0]['tot_cogs'] - static_data_ly[0]['tot_cogs'])) / (
                               static_data[0]['tot_sales'] - static_data_ly[0]['tot_sales'])) * 100, 1)
        margin['yoy_lfl'] = round((((static_data[0]['tot_sales_lfl'] - static_data_ly[0]['tot_sales_lfl']) - (
            static_data[0]['tot_cogs_lfl'] - static_data_ly[0]['tot_cogs_lfl'])) / (
                                   static_data[0]['tot_sales_lfl'] - static_data_ly[0]['tot_sales_lfl'])) * 100, 1)

        # try:
        # #     sales_wow =
        # print("static_dataIIIIIIIIIIIIIIIIIIIIIIIII",type(cogs))
        # print(static_data)

        final_data = {'cogs': cogs, 'volume': volume, 'sales': sales, 'profit': profit, 'margin': margin}
        logging.info(final_data)
        return JsonResponse(final_data, safe=False)

class dss_data_graph(APIView):
    def get(self, request, format=None, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        dt_sel = args.get('dt_sel__in', [None])
        dt_sel = dt_sel[0]
        print("dt sel........",dt_sel)
        tesco_week = args.get('tesco_week__in', [None])
        tesco_week = tesco_week[0]
        print("tesco week......",tesco_week)
        store_type = args.get('store_type__in', ['Main Estate','Express'])
        category_name = args.get('category_name__in', None)
        val_type = args.get('val_type__in', ['1'])
        val_type = int(val_type[0])
        # val_type=1
        buying_controller = args.get('buying_controller__in', None)
        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        product_subgroup = args.get('product_subgroup__in', None)
        brand_indicator = args.get('brand_indicator__in', None)
        brand_name = args.get('brand_name__in', None)
        product = args.get('product__in', None)
        commercial_name = args.get('commercial_name__in', None)
        # store_type = args.get('store_type__in',None)
        # # week_sel = '201601'
        # print(type(val_type))
        # print(dt_sel)
        # dt_sel = datetime(2017, 4, 30)
        if tesco_week is None:
            print("entered if for tesco week")
            tesco_week = dss_view.objects.all().aggregate(tesco_week=Max('tesco_week'))
            tesco_week = int(tesco_week['tesco_week'])
            # print(tesco_week)

        if dt_sel is None:
            print("entered dt sel if")
            dt_dataframe = pd.DataFrame(
                list(dss_view.objects.filter(tesco_week=tesco_week).values('tesco_week').annotate(
                    latest_dt=Max('calendar_date'))))
            print("check1")
            print(dt_dataframe)
            dt_sel = datetime.combine(dt_dataframe.loc[0, 'latest_dt'], datetime.min.time())
            # print("check2")
            # print(dt_sel)
            dt_sel_ordered = latest_date.objects.filter(date_ty__lte=dt_sel).values('date_ty').order_by(
                '-date_ty').distinct()
            # print("Check_____________1", dt_sel_ordered[7])
            # print("Check_____________2", type(dt_sel_ordered[7]))
            date_lw = datetime.combine(dt_sel_ordered[7]['date_ty'], datetime.min.time())
            # print("check3")
            # print(date_lw)

            # date_lw = datetime.strptime(dt_sel_ordered[7], '%Y-%m-%d')
            dt_sel_ly = read_frame(latest_date.objects.filter(date_ty=dt_sel).values('date_ly').distinct())
            date_ly = datetime.combine(dt_sel_ly['date_ly'][0], datetime.min.time())
            # print("check4")
            # print(date_ly)
            # (date_ly.strip())[-10:]
        else:
            dt_sel = datetime.strptime(dt_sel, '%Y-%m-%d')
            dt_sel_ordered = latest_date.objects.filter(date_ty__lte=dt_sel).values('date_ty').order_by(
                '-date_ty').distinct()
            date_lw = dt_sel_ordered[7]
            date_lw = datetime.strptime(date_lw, '%Y-%m-%d')
            dt_sel_ly = read_frame(latest_date.objects.filter(date_ty=dt_sel).values('date_ly').distinct())
            date_ly = dt_sel_ly['date_ly']




            #### Getting last year week from the selected week
        tesco_week_lastyear = read_frame(latest_date.objects.filter(week_ty=tesco_week).values('week_ly').distinct())
        tesco_week_lastyear = int(tesco_week_lastyear['week_ly'])
        # print("checkkkkkkkkkkkkkkkkkkkkkk")
        # print(tesco_week_lastyear)


        date_range_ty = latest_date.objects.filter(week_ty=tesco_week).aggregate(date_min=Min('date_ty'),
                                                                                 date_max=Max('date_ty'))
        date_range_ly = latest_date.objects.filter(week_ty=tesco_week_lastyear).aggregate(date_min=Min('date_ty'),
                                                                                          date_max=Max('date_ty'))

        kwargs_filter = {
            'category_name__in': category_name,
            'buying_controller__in': buying_controller,
            'buyer__in': buyer,
            'junior_buyer__in': junior_buyer,
            'product_subgroup__in': product_subgroup,
            'brand_indicator__in': brand_indicator,
            'brand_name__in': brand_name,
            'product__in': product,
            'store_type__in': store_type,
            'commercial_name__in': commercial_name

        }
        kwargs_filter = dict(filter(lambda item: item[1] is not None, kwargs_filter.items()))

        # Determine the metric to be returned
        if val_type == 1:
            val_name = 'daily_sales'
            val_name_lfl = 'daily_sales_lfl'
        elif val_type == 2:
            val_name = 'daily_volume'
            val_name_lfl = 'daily_volume_lfl'
        elif val_type == 3:
            val_name = 'daily_cogs'
            val_name_lfl = 'daily_cogs_lfl'
        else:
            # val_name = 'daily_cgm' ### Have to be uncommented when data for cgm is added to daily sales
            val_name = 'daily_cogs'
            val_name_lfl = 'daily_cogs_lfl'


        final_data = {}
        # print(prod_filters)

        user_id = args.pop('user_id__iexact', None)
        designation = args.pop('designation__iexact', None)
        session_id = args.pop('session_id__iexact', None)
        user_name = args.pop('user_name__iexact', None)
        buying_controller_header = args.pop('buying_controller_header__in', None)
        buyer_header = args.pop('buyer_header__in', None)

        if buyer_header is None:
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        kwargs_header = dict(filter(lambda item: item[1] is not None, kwargs_header.items()))

        if args is None:
            product_id_list = sales_heirarchy.objects.filter(**kwargs_header).values("product_id").distinct()
            product_description = read_frame(
                sales_heirarchy.objects.filter(**kwargs_header).values("product_id", "product",
                                                                       "brand_indicator","brand_name").distinct())
        else:
            product_id_list = sales_heirarchy.objects.filter(**kwargs_filter).values("product_id").distinct()
            product_description = read_frame(
                sales_heirarchy.objects.filter(**kwargs_filter).values("product_id", "product",
                                                                       "brand_indicator","brand_name").distinct())


        ### To get the sales for the current week (daily basis) in selection
        kwargs_graph = {
            'store_type__in': store_type,
            'tesco_week__iexact': tesco_week,
            'product_id__in': product_id_list
        }

        kwargs_current = {
            'store_type__in': store_type,
            'calendar_date__iexact': dt_sel,
            'product_id__in': product_id_list
        }

        kwargs_yoy = {
            'store_type__in': store_type,
            'calendar_date__iexact': date_ly,
            'product_id__in': product_id_list
        }

        # print(kwargs_graph)

        if val_type == 4:
            graph_data = read_frame(dss_view.objects.filter(**kwargs_graph).values('calendar_date').annotate(tot_sales=Sum('daily_sales'),tot_cogs=Sum('daily_cogs')).annotate(tot_val=F('tot_sales') - F('tot_cogs')).order_by(
                    'calendar_date'))
        else:
            graph_data = read_frame(
                dss_view.objects.filter(**kwargs_graph).values('calendar_date').annotate(tot_val=Sum(val_name)).order_by(
                    'calendar_date'))
        graph_data['tot_val'] = graph_data['tot_val'].astype('float')


        ### To calculate the cumulative on a daily basis for the selected week
        calendar_data = read_frame(
            calendar_dim_hierarchy.objects.filter(tesco_week=tesco_week).values('date', 'week_day_str'))
        cum_graph_data = graph_data.copy()
        cum_graph_data['tot_val'] = cum_graph_data['tot_val'].cumsum().astype('float')
        cum_graph_data = pd.merge(cum_graph_data, calendar_data, left_on=['calendar_date'], right_on=['date'],
                                  how='left')
        cum_graph_data = cum_graph_data[['tot_val', 'week_day_str']]

        graph_data = pd.merge(graph_data, calendar_data, left_on=['calendar_date'], right_on=['date'], how='left')
        graph_data = graph_data[['tot_val', 'week_day_str']]

        print("cumulaaaaaaaaaaaaaaaaa")
        print(cum_graph_data)

        # graph_data = graph_data.to_dict(orient='records')
        # cum_graph_data = cum_graph_data.to_dict(orient='records')

        ### To get the sales for the last year week (daily basis)


        kwargs_graph_lastyear = {
            'store_type__in': store_type,
            'tesco_week__iexact': tesco_week_lastyear,
            'product_id__in': product_id_list
        }
        # print(kwargs_graph_lastyear)

        if val_type == 4:
            graph_data_lastyear = read_frame(dss_view.objects.filter(**kwargs_graph_lastyear).values('calendar_date').annotate(tot_sales=Sum('daily_sales'),tot_cogs=Sum('daily_cogs')).annotate(tot_val=F('tot_sales') - F('tot_cogs')).order_by('calendar_date'))
        else:
            graph_data_lastyear = read_frame(
                dss_view.objects.filter(**kwargs_graph_lastyear).values('calendar_date').annotate(tot_val=Sum(val_name)).order_by('calendar_date'))
        graph_data_lastyear['tot_val'] = graph_data_lastyear['tot_val'].astype('float')

        ### To calculate the cumulative on a daily basis for the last year week
        calendar_data = read_frame(
            calendar_dim_hierarchy.objects.filter(tesco_week=tesco_week_lastyear).values('date', 'week_day_str'))

        cum_graph_data_lastyear = graph_data_lastyear.copy()
        cum_graph_data_lastyear['tot_val'] = cum_graph_data_lastyear['tot_val'].cumsum().astype('float')
        cum_graph_data_lastyear = pd.merge(cum_graph_data_lastyear, calendar_data, left_on=['calendar_date'],
                                           right_on=['date'], how='left')
        cum_graph_data_lastyear = cum_graph_data_lastyear.rename(columns={'tot_val': 'tot_val_ly'})
        cum_graph_data_lastyear = cum_graph_data_lastyear[['tot_val_ly', 'week_day_str']]

        graph_data_lastyear = pd.merge(graph_data_lastyear, calendar_data, left_on=['calendar_date'], right_on=['date'],
                                       how='left')
        graph_data_lastyear = graph_data_lastyear.rename(columns={'tot_val': 'tot_val_ly'})
        graph_data_lastyear = graph_data_lastyear[['tot_val_ly', 'week_day_str']]
        # print("cumulaaaaaaaaaaaaaaaaa222")
        # print(cum_graph_data_lastyear)


        ### Combining cumulative for both ty and ly
        combined_cumulative = pd.merge(cum_graph_data, cum_graph_data_lastyear, on=['week_day_str'], how='left')
        combined_cumulative['week_day_str'] = combined_cumulative['week_day_str'].str[:3]
        combined_cumulative['week_day_str'] = combined_cumulative['week_day_str'].str.title()
        combined_graph = pd.merge(graph_data, graph_data_lastyear, on=['week_day_str'], how='left')
        combined_graph['week_day_str'] = combined_graph['week_day_str'].str[:3]
        combined_graph['week_day_str'] = combined_graph['week_day_str'].str.title()

        print("llllllllllllllllllllllllllll")
        print(combined_cumulative)

        combined_graph = combined_graph.to_dict(orient='records')
        # labels = {'tot_val_ly','tot_val'}
        # labels = labels.to_json(orient='records')
        # combined_graph['labels'] = pd.Dataframe(labels)
        combined_cumulative = combined_cumulative.to_dict(orient='records')

        # graph_data = list(dss_view.objects.filter(product_id__in=product_id_list,
        #                                      calendar_date__iexact=(dt_sel)).values(
        #     'calendar_date').annotate(tot_val=Sum(val_name)).order_by('-calendar_date'))
        print("GRAPPGGGGGGGGGGGG")
        print(graph_data)

        final_data["graph_data"] = combined_graph
        final_data["labels_bar"] = ['tot_val_ly', 'tot_val']
        final_data["colors_bar"] = ['#F60909', '#E5F213']
        final_data['cum_graph_data'] = combined_cumulative
        # final_data['cum_graph_data_lastyear'] = cum_graph_data_lastyear

        if val_type==4:
            static_data = read_frame(
                dss_view.objects.filter(**kwargs_current).values('product_id').annotate(tot_sales=Sum('daily_sales'),
                tot_cogs=Sum('daily_cogs'),tot_sales_lfl=Sum('daily_sales_lfl'),tot_cogs_lfl=Sum('daily_cogs_lfl')).annotate(kpi_ty=F('tot_sales') - F('tot_cogs'), kpi_ty_lfl=F('tot_sales_lfl') - F('tot_cogs_lfl')).order_by('calendar_date'))
            static_data['kpi_ty'] = static_data['kpi_ty'].astype('float').round(decimals=2)
            static_data['kpi_ty_lfl'] = static_data['kpi_ty_lfl'].astype('float').round(decimals=2)

            static_data_ly = read_frame(dss_view.objects.filter(**kwargs_yoy).values('product_id').annotate(tot_sales=Sum('daily_sales'),
                tot_cogs=Sum('daily_cogs'),tot_sales_lfl=Sum('daily_sales_lfl'),tot_cogs_lfl=Sum('daily_cogs_lfl')).annotate(kpi_ly=F('tot_sales') - F('tot_cogs'), kpi_ly_lfl=F('tot_sales_lfl') - F('tot_cogs_lfl')).order_by('calendar_date'))
            static_data_ly['kpi_ly'] = static_data_ly['kpi_ly'].astype('float').round(decimals=2)
            static_data_ly['kpi_ly_lfl'] = static_data_ly['kpi_ly_lfl'].astype('float').round(decimals=2)

            dss_table = pd.merge(static_data, static_data_ly, how='inner',on=['product_id'])
            dss_table = pd.merge(dss_table, product_description, how='inner', on=['product_id'])
        else:
            static_data = read_frame(dss_view.objects.filter(**kwargs_current).values(
                'product_id').annotate(kpi_ty=Sum(val_name), kpi_ty_lfl=Sum(val_name_lfl)))
            static_data['kpi_ty'] = static_data['kpi_ty'].astype('float').round(decimals=2)
            static_data['kpi_ty_lfl'] = static_data['kpi_ty_lfl'].astype('float').round(decimals=2)

            static_data_ly = read_frame(dss_view.objects.filter(**kwargs_yoy).values(
                'product_id').annotate(kpi_ly=Sum(val_name),
                                       kpi_ly_lfl=Sum(val_name_lfl)))
            static_data_ly['kpi_ly'] = static_data_ly['kpi_ly'].astype('float').round(decimals=2)
            static_data_ly['kpi_ly_lfl'] = static_data_ly['kpi_ly_lfl'].astype('float').round(decimals=2)

            dss_table = pd.merge(static_data, static_data_ly, how='inner', on=['product_id'])
            dss_table = pd.merge(dss_table, product_description, how='inner', on=['product_id'])

        dss_table = dss_table.to_dict(orient='records')

        graph_data = {'graph_data': final_data, 'date_range_ty': date_range_ty, 'date_range_ly': date_range_ly,
                      'dss_table': dss_table}
        logging.info(graph_data)

        return JsonResponse(graph_data, safe=False)

def make_json_dss_weeks(sent_req):
    print('*********************\n       FILTERS2 \n*********************')
    # hierarchy of data
    print(sent_req)

    hierarchy = ['tesco_week', 'date']
    # find lowest element of hierarchy
    lowest = 0
    second_lowest = 0
    element_list = []
    for i in sent_req.keys():
        if i in hierarchy:
            element_list.append(hierarchy.index(i))
    print(element_list)
    element_list.sort()
    try:
        lowest = element_list[-1]
    except:
        pass
    try:
        second_lowest = element_list[-2]
    except:
        pass
    # lowest_key = hierarchy[lowest]
    # second_lowest_key = hierarchy[second_lowest]
    # print('lowest_key:', lowest_key, '|', 'lowest', lowest)
    final_list = []  # final list to send
    col_unique_list_name_obj = {}  # rename
    for col_name in hierarchy:
        # print('\n********* \n' + col_name + '\n*********')
        # print('sent_req.get(col_name):', sent_req.get(col_name))
        col_unique_list = col_distinct_weeks({}, col_name)
        # print('col_unique_list->',col_unique_list)
        col_unique_list_name_obj[col_name] = col_unique_list
        # print(col_unique_list_name_obj)
        # args sent as url params
        kwargs2 = {reqobj + '__in': sent_req.get(reqobj) for reqobj in sent_req.keys()}
        # print('kwargs2', kwargs2)
        category_of_sent_obj_list = col_distinct_weeks(kwargs2, col_name)

        # print('category_of_sent_obj_list', 'col_name>', col_name, '|', category_of_sent_obj_list)
        # 'buying_controller', 'buyer', 'junior_buyer','product_sub_group_description', 'brand_indicator', 'brand_name'
        # print(len(category_of_sent_obj_list))
        def highlight_check(category_unique_element):
            if len(sent_req.keys()) > 0:
                highlighted = False
                if col_name in sent_req.keys():
                    if col_name == hierarchy[lowest]:
                        queryset = calendar_dim_hierarchy.objects.filter(**{col_name: category_unique_element}).filter(
                            tesco_week__gte=201626).filter(tesco_week__lte=201711)[
                                   :1].get()
                        # x = getattr(queryset, hierarchy[lowest])
                        y = getattr(queryset, hierarchy[second_lowest])
                        # print(x, '|', y, '|', hierarchy[lowest], '|',
                        #       'Category_second_last:' + hierarchy[second_lowest],
                        #       '|', col_name,
                        #       '|', category_unique_element)
                        for i in sent_req.keys():
                            # print('keys:', i, sent_req.get(i))
                            if y in sent_req.get(i) and hierarchy[second_lowest] == i:
                                highlighted = True
                        return highlighted
                    else:
                        return False
                else:
                    if category_unique_element in category_of_sent_obj_list:
                        # print('category_unique_element>>>>>>', category_unique_element, category_of_sent_obj_list)
                        highlighted = True
                    return highlighted
            else:
                return True

        # assign props to send as json response
        y = []
        for category_unique_element in col_unique_list:
            # selected = checked
            # print('sent_req->', sent_req, col_name, category_unique_element, '|', sent_req.get(col_name), type(sent_req.get(col_name)))
            selected = True if type(sent_req.get(col_name)) == list and str(category_unique_element) in sent_req.get(
            col_name) else False

            # highlighted = disabled or enabled
            # print(col_name)
            # print(category_unique_element, type(category_unique_element))
            # print(str(category_unique_element), type(category_unique_element))
            y.append({'title': category_unique_element,
                      'resource': {'params': col_name + '=' + str(category_unique_element),
                                   'selected': selected},
                      'highlighted': selected if selected else highlight_check(category_unique_element)})

        final_list.append({'items': y,
                           'input_type': 'Checkbox',
                           'title': col_name,
                           'id': col_name,
                           'required': True if col_name == 'tesco_week' or col_name == 'date' else False
                           })

    # set element type
    def get_element_type(title):
        if title == 'buying_controller':
            return 'Checkbox'
        else:
            return 'Checkbox'

    # sort list with checked at top
    final_list2 = []
    for i in final_list:
        m = []
        for j in i.get('items'):
            if j['resource']['selected']:
                m.append(j)
        for j in i.get('items'):
            if not j['resource']['selected']:
                m.append(j)
        final_list2.append({'items': m,
                            'input_type': get_element_type(i['title']),
                            'title': i['title'],
                            'required': i['required'],
                            'id': i['id']})
    return JsonResponse({'hierarchy': hierarchy, 'checkbox_list': final_list2}, safe=False)

def col_distinct_weeks(kwargs, col_name):
    queryset = calendar_dim_hierarchy.objects.filter(**kwargs).filter(tesco_week__gte=201626).filter(
        tesco_week__lte=201711).values(col_name).order_by(col_name).distinct()
    base_tesco_date_list = [k.get(col_name) for k in queryset]
    # print(base_tesco_date_list)
    return base_tesco_date_list

class dss_filterdata_weeks(APIView):
    def get(self, request):
        # print(request.GET)
        obj = {}
        get_keys = request.GET.keys()
        for i in get_keys:
            # print(request.GET.getlist(i))
            obj[i] = request.GET.getlist(i)

        # print(obj)
        sent_req = obj

        return make_json_dss_weeks(sent_req)

class dss_filter_week(APIView):
    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}

        tesco_week = args.get('tesco_week__iexact',None)

        if tesco_week == None:
            tesco_week_int = dss_view.objects.aggregate(cw_max=Max('tesco_week'))
            tesco_week_filter = tesco_week_int['cw_max']
        else:
            tesco_week_filter = tesco_week

        tesco_week_data = read_frame(latest_date.objects.filter(week_ty__gte=201701).values(
                    'week_ty').order_by('-week_ty').distinct())
        calender_date = read_frame(latest_date.objects.filter(week_ty=tesco_week_filter).values(
                    'date_ty').order_by('-date_ty').distinct())
        tesco_week_data['week_ty'] = tesco_week_data['week_ty'].astype('float')
        # calender_date['date_ty'] = calender_date['date_ty'].astype('float')


        tesco_week_data = tesco_week_data.to_dict(orient='records')
        calender_date_data = calender_date.to_dict(orient='records')

        data = {
            'tesco_week':tesco_week_data,
            'calender_date':calender_date_data
        }

        return JsonResponse(data, safe=False)




#new filter logic
class daily_sales_filters_new(APIView):
    def get(self, request, format=None):
        # input from header
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        designation = args.pop('designation__in', None)
        user_id = args.pop('user_id__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', None)
        buyer_header = args.pop('buyer_header__in', None)
        # header over
        cols = ['commercial_name', 'category_name', 'buying_controller', 'buyer', 'junior_buyer',
                'product_subgroup', 'store_type', 'brand_indicator']
        if 'admin' in designation:
            kwargs_header = {}
        else:
            if buyer_header is None:
                kwargs_header = {
                    'buying_controller__in': buying_controller_header
                }
            else:
                kwargs_header = {
                    'buying_controller__in': buying_controller_header,
                    'buyer__in': buyer_header
                }
        # input from args
        default = args.pop('default__in', None)
        final = []
        if default is None:
            if not args:
                df = read_frame(sales_heirarchy.objects.filter(**kwargs_header).filter(**args))
                heirarchy = read_frame(
                    sales_heirarchy.objects.filter(**kwargs_header).values('store_type', 'commercial_name',
                                                                           'category_name', 'buying_controller',
                                                                           'buyer', 'junior_buyer',
                                                                           'product_subgroup', 'brand_indicator'))
                for i in heirarchy.columns:
                    ##print(i)
                    data = {i: df[i].unique()}
                    ##print(data)
                    col = pd.DataFrame(data)
                    if i == ('buyer') or i == ('buying_controller'):
                        if len(col) == 1:
                            ##print("inside if loop")
                            col['selected'] = True  ### One change here for default selection of bc logging in
                            col['highlighted'] = False
                        else:
                            col['selected'] = False
                            col['highlighted'] = False
                    else:
                        col['selected'] = False
                        col['highlighted'] = False
                    col_df = heirarchy[[i]].drop_duplicates()
                    ##print(col_df)
                    col_df = pd.merge(col_df, col, how='left')
                    col_df['selected'] = col_df['selected'].fillna(False)
                    col_df['highlighted'] = col_df['highlighted'].fillna(False)
                    col_df = col_df.rename(columns={i: 'title'})
                    ##print("____")
                    ##print(col_df)
                    # col_df['name_supplier'] = col_df['title'].str.split('-').str[1]
                    # col_df = col_df.sort_values(by=['selected', 'name_supplier'],
                    #                             ascending=[False, True])
                    # del col_df['name_supplier']
                    col_df = col_df.sort_values(by=['selected', 'title'], ascending=[False, True])

                    col_df['highlighted'] = ~col_df['highlighted']
                    col_df_sel = col_df[['selected']]
                    col_df['resource'] = col_df_sel.to_dict(orient='records')
                    del col_df['selected']
                    col_df_final = col_df.to_json(orient='records')
                    col_df_final = json.loads(col_df_final)
                    ##print("---------")
                    ##print(col_df_final)
                    a = {}
                    a['id'] = i
                    a['title'] = i
                    if i == ('buying_controller'):
                        a['required'] = True
                    else:
                        a['required'] = False
                    a['items'] = col_df_final
                    a['category_director'] = "Beers, Wines and Spirits"
                    final.append(a)

            else:
                if 'admin' in designation:
                    heirarchy = read_frame(
                        sales_heirarchy.objects.values('commercial_name', 'category_name', 'buying_controller', 'buyer',
                                                       'junior_buyer',
                                                       'product_subgroup', 'store_type', 'brand_indicator'))
                else:
                    heirarchy = read_frame(
                        sales_heirarchy.objects.filter(**kwargs_header).values('commercial_name', 'category_name',
                                                                               'buying_controller', 'buyer',
                                                                               'junior_buyer',
                                                                               'product_subgroup', 'store_type',
                                                                               'brand_indicator'))
                args_list = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
                store_list = args_list.pop('store_type__in', None)
                ##print(store_list)
                if store_list is None:
                    store_list = None
                commercial_name_list = args_list.pop('commercial_name__in', None)
                # if commercial_name_list is None:
                #     commercial_name_list = str(commercial_name_list[0])
                category_name_list = args_list.pop('category_name__in', None)
                # if category_name_list is None:
                #     category_name_list = str(category_name_list[0])
                if 'admin' in designation:
                    bc_list = args_list.pop('buying_controller__in', None)
                    buyer_list = args_list.pop('buyer__in', None)
                else:
                    if 'buying_controller' in designation:
                        bc_list = args_list.pop('buying_controller_header__in', None)
                        buyer_list = args_list.pop('buyer__in', None)
                    else:
                        bc_list = args_list.pop('buying_controller_header__in', None)
                        buyer_list = args_list.pop('buyer_header__in', None)
                jr_buyer_list = args_list.pop('junior_buyer__in', None)
                if jr_buyer_list is None:
                    jr_buyer_list = None
                psg_list = args_list.pop('product_subgroup__in', None)
                if psg_list is None:
                    psg_list = None
                brand_indicator_list = args_list.pop('brand_indicator__in', None)
                if brand_indicator_list is None:
                    brand_indicator_list = None
                # brand_name_list = args_list.pop('brand_name__in', None)
                # if brand_name_list is None:
                #     brand_name_list = None
                #
                # product_list = args_list.pop('product__in', None)
                # if product_list is None:
                #     product_list = None
                com_list = [commercial_name_list, category_name_list, bc_list, buyer_list, jr_buyer_list, psg_list,
                            store_list,
                            brand_indicator_list]  # ,brand_name_list,product_list]
                #print(com_list)
                args_list2 = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
                # com_list = [bc_list, buyer_list, jr_buyer_list, psg_list, brand_indicator_list, parent_supplier_list,
                #            supplier_list, ]
                df = read_frame(sales_heirarchy.objects.filter(**args))
                # final = []
                j = 0
                for i in heirarchy.columns:
                    ##print("loop running for")
                    ##print(i)
                    col_name = i + '__in'
                    col_list2 = args_list2.pop(col_name, None)
                    ##print("____")
                    data = {i: df[i].unique()}
                    col = pd.DataFrame(data)
                    # #print(data)
                    col_df_heirarchy = heirarchy[[i]].drop_duplicates()

                    if 'admin' in designation:
                        if col_list2 is not None:
                            ##print("else part")
                            # #print(col_df)
                            heirarchy_check = read_frame(
                                sales_heirarchy.objects.filter(buying_controller__in=bc_list).values('commercial_name',
                                                                                                     'category_name',
                                                                                                     'buying_controller',
                                                                                                     'buyer',
                                                                                                     'junior_buyer',
                                                                                                     'product_subgroup',
                                                                                                     'store_type',
                                                                                                     'brand_indicator'))
                            # #print("inside buyerrr..")
                            col['selected'] = True
                            col['highlighted'] = False
                            kwargs = {'store_type__in': store_list,
                                      'commercial_name__in': commercial_name_list,
                                      'category_name__in': category_name_list,
                                      'buying_controller__in': bc_list,
                                      'buyer__in': buyer_list,
                                      'junior_buyer__in': jr_buyer_list,
                                      'brand_indicator__in': brand_indicator_list,
                                      'product_subgroup__in': psg_list
                                      # 'brand_name__in': brand_name_list,
                                      # 'product__in': product_list
                                      }
                            kwargs.pop(col_name)
                            kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
                            # #print(kwargs)
                            heirarchy_check = read_frame(
                                sales_heirarchy.objects.filter(**kwargs))
                            col_df_check = pd.merge(col_df_heirarchy,
                                                    heirarchy_check[[i]].drop_duplicates(), how='right')
                            ##print("after merge_1...")
                            # #print(col_df_check)
                            # #print("#printing supplier")
                            # #print(col)
                            col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
                            # #print("after mergeeee...")
                            col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
                            col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
                            ##print("#printing selected cols")
                            ##print(col_df_selected)
                            col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(True)
                            ##print(col_df)
                            col_df = col_df.rename(columns={i: 'title'})
                            j = com_list.index(col_list2)
                            if j < 7:
                                if com_list[j + 1] is not None:
                                    ##print("inside com list next")
                                    col_df = col_df.rename(columns={'title': i})
                                    col_list_df = pd.DataFrame(col_list2, columns={i})
                                    # #print(col_list_df)
                                    data = {i: col_list_df[i].unique()}
                                    ##print(data)
                                    col = pd.DataFrame(data)
                                    col['selected'] = True
                                    col['highlighted'] = False
                                    # #print(parent_supplier)
                                    col_df = pd.merge(col_df_heirarchy, col, how='left')
                                    col_df['selected'] = col_df['selected'].fillna(False)
                                    col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                    col_df = col_df[[i, 'selected', 'highlighted']]
                                    col_df = col_df.rename(columns={i: 'title'})
                                    ##print(col_df)
                        else:
                            col['selected'] = False
                            col['highlighted'] = False
                            col_df = pd.merge(col_df_heirarchy, col, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(True)
                            col_df = col_df.rename(columns={i: 'title'})

                    elif 'buying_controller' in designation:
                        if i == ('buying_controller'):
                            ##print("#printing buying controller...or buyer...")
                            col['selected'] = True
                            col['highlighted'] = False
                            ##print(col)
                            col_df = pd.merge(col_df_heirarchy, col, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(False)
                            col_df = col_df.rename(columns={i: 'title'})
                        else:
                            if col_list2 is not None:
                                ##print("else part")
                                # #print(col_df)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(buying_controller__in=bc_list).values(
                                        'commercial_name',
                                        'category_name',
                                        'buying_controller',
                                        'buyer',
                                        'junior_buyer',
                                        'product_subgroup',
                                        'store_type',
                                        'brand_indicator'))
                                # #print("inside buyerrr..")
                                col['selected'] = True
                                col['highlighted'] = False
                                kwargs = {'store_type__in': store_list,
                                          'commercial_name__in': commercial_name_list,
                                          'category_name__in': category_name_list,
                                          'buying_controller__in': bc_list,
                                          'buyer__in': buyer_list,
                                          'junior_buyer__in': jr_buyer_list,
                                          'brand_indicator__in': brand_indicator_list,
                                          'product_subgroup__in': psg_list
                                          # 'brand_name__in': brand_name_list,
                                          # 'product__in': product_list
                                          }
                                kwargs.pop(col_name)
                                kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
                                # #print(kwargs)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(**kwargs))
                                col_df_check = pd.merge(col_df_heirarchy,
                                                        heirarchy_check[[i]].drop_duplicates(), how='right')
                                ##print("after merge_1...")
                                # #print(col_df_check)
                                # #print("#printing supplier")
                                # #print(col)
                                col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
                                # #print("after mergeeee...")
                                col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
                                col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
                                ##print("#printing selected cols")
                                ##print(col_df_selected)
                                col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                ##print(col_df)
                                col_df = col_df.rename(columns={i: 'title'})
                                j = com_list.index(col_list2)
                                if j < 7:
                                    if com_list[j + 1] is not None:
                                        ##print("inside com list next")
                                        col_df = col_df.rename(columns={'title': i})
                                        col_list_df = pd.DataFrame(col_list2, columns={i})
                                        # #print(col_list_df)
                                        data = {i: col_list_df[i].unique()}
                                        ##print(data)
                                        col = pd.DataFrame(data)
                                        col['selected'] = True
                                        col['highlighted'] = False
                                        # #print(parent_supplier)
                                        col_df = pd.merge(col_df_heirarchy, col, how='left')
                                        col_df['selected'] = col_df['selected'].fillna(False)
                                        col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                        col_df = col_df[[i, 'selected', 'highlighted']]
                                        col_df = col_df.rename(columns={i: 'title'})
                                        ##print(col_df)
                            else:
                                col['selected'] = False
                                col['highlighted'] = False
                                col_df = pd.merge(col_df_heirarchy, col, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                col_df = col_df.rename(columns={i: 'title'})

                    else:
                        if i == ('buying_controller') or i == ('buyer'):
                            ##print("#printing buying controller...or buyer...")
                            col['selected'] = True
                            col['highlighted'] = False
                            ##print(col)
                            col_df = pd.merge(col_df_heirarchy, col, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(False)
                            col_df = col_df.rename(columns={i: 'title'})
                        else:
                            if col_list2 is not None:
                                ##print("else part")
                                # #print(col_df)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(buying_controller__in=bc_list).values('commercial_name',
                                                                                                         'category_name',
                                                                                                         'buying_controller',
                                                                                                         'buyer',
                                                                                                         'junior_buyer',
                                                                                                         'product_subgroup',
                                                                                                         'store_type',
                                                                                                         'brand_indicator'))
                                # #print("inside buyerrr..")
                                col['selected'] = True
                                col['highlighted'] = False
                                kwargs = {'store_type__in': store_list,
                                          'commercial_name__in': commercial_name_list,
                                          'category_name__in': category_name_list,
                                          'buying_controller__in': bc_list,
                                          'buyer__in': buyer_list,
                                          'junior_buyer__in': jr_buyer_list,
                                          'brand_indicator__in': brand_indicator_list,
                                          'product_subgroup__in': psg_list
                                          # 'brand_name__in': brand_name_list,
                                          # 'product__in': product_list
                                          }
                                kwargs.pop(col_name)
                                kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
                                # #print(kwargs)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(**kwargs))
                                col_df_check = pd.merge(col_df_heirarchy,
                                                        heirarchy_check[[i]].drop_duplicates(), how='right')
                                ##print("after merge_1...")
                                # #print(col_df_check)
                                # #print("#printing supplier")
                                # #print(col)
                                col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
                                # #print("after mergeeee...")
                                col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
                                col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
                                ##print("#printing selected cols")
                                ##print(col_df_selected)
                                col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                ##print(col_df)
                                col_df = col_df.rename(columns={i: 'title'})
                                j = com_list.index(col_list2)
                                if j < 7:
                                    if com_list[j + 1] is not None:
                                        ##print("inside com list next")
                                        col_df = col_df.rename(columns={'title': i})
                                        col_list_df = pd.DataFrame(col_list2, columns={i})
                                        # #print(col_list_df)
                                        data = {i: col_list_df[i].unique()}
                                        ##print(data)
                                        col = pd.DataFrame(data)
                                        col['selected'] = True
                                        col['highlighted'] = False
                                        # #print(parent_supplier)
                                        col_df = pd.merge(col_df_heirarchy, col, how='left')
                                        col_df['selected'] = col_df['selected'].fillna(False)
                                        col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                        col_df = col_df[[i, 'selected', 'highlighted']]
                                        col_df = col_df.rename(columns={i: 'title'})
                                        ##print(col_df)
                            else:
                                col['selected'] = False
                                col['highlighted'] = False
                                col_df = pd.merge(col_df_heirarchy, col, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                col_df = col_df.rename(columns={i: 'title'})


                    # col_df['name_supplier'] = col_df['title'].str.split('-').str[1]
                    # col_df = col_df.sort_values(by=['selected', 'name_supplier'],
                    #                                                     ascending=[False, True])
                    # del col_df['name_supplier']
                    col_df = col_df.sort_values(by=['selected', 'title'], ascending=[False, True])
                    # #print(col_df)
                    col_df['highlighted'] = ~col_df['highlighted']
                    ##print("after inverse")
                    ##print(col_df)
                    col_df_sel = col_df[['selected']]
                    col_df['resource'] = col_df_sel.to_dict(orient='records')
                    del col_df['selected']
                    col_df_final = col_df.to_json(orient='records')
                    col_df_final = json.loads(col_df_final)
                    ##print("---------")
                    # #print(col_df_final)
                    a = {}
                    a['id'] = i
                    a['title'] = i
                    if i == ('buying_controller'):
                        a['required'] = True
                    else:
                        a['required'] = False
                    a['items'] = col_df_final
                    a['category_director'] = "Beers, Wines and Spirits"
                    final.append(a)
                    # if i == 'junior_buyer':
                    #    break
                    # #print("#printing finaaall")
                    # #print(final)

        return JsonResponse({'cols': cols, 'checkbox_list': final}, safe=False)






