from __future__ import unicode_literals
from django.contrib.humanize.templatetags.humanize import intcomma, intword
from .models import sales_heirarchy, supplier_view, forecast_budget_data, roles_and_intent, weather_weekly_details, \
    executive_inflation, executive_price_index, competitor_market_share, calendar_dim_hierarchy, uk_holidays, executive_view, \
    promo_contribution, latest_week, roles_and_intent_v2, roles_and_intent_target
import numpy as np
import pandas as pd
from django_pandas.io import read_frame

import json

from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
import math
from django.db.models import Count, Min, Max, Sum, Avg, F, FloatField, Case, When, Value, Q
import logging
import time

# Executive week Filter data
class executive_filterdata_week(APIView):
    # @cache_response()
    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}
        print("---------------------")
        week_id = args.get('tesco_week__iexact')

        if week_id is None:
            tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
            max_week = [tesco_week_int['cw_max']]
            currentweek = args.pop('tesco_week__in', max_week)
            currentweek = int(currentweek[0])
            week_id = currentweek
        else:
            week_id = int(week_id)

        print(type(week_id))

        kwargs = {
            'tesco_week__iexact': week_id

        }
        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))

        if not args:

            print("inside default")

            weeks_data = read_frame(calendar_dim_hierarchy.objects.all().values('tesco_week'))
            weeks_data = weeks_data[(weeks_data["tesco_week"] >= 201626) & (weeks_data['tesco_week'] <= week_id)]
            # weeks_data = weeks_data[weeks_data['tesco_week'] >= 201646 and weeks_data['tesco_week'] <= 201705]

            # print("After replacing")
            # print(heirarchy)


            data = {'tesco_week': weeks_data.tesco_week.unique()}
            week = pd.DataFrame(data)
            week['selected'] = False
            week['disabled'] = False

            week_df = weeks_data[['tesco_week']].drop_duplicates()

            week_df = pd.merge(week_df, week, how='left')
            week_df['selected'] = week_df['selected'].fillna(False)
            week_df['disabled'] = week_df['disabled'].fillna(False)

            week_df = week_df.rename(columns={'tesco_week': 'name'})
            week_df = week_df.sort_values('name', ascending=False)
            week_final = week_df.to_json(orient='records')
            week_final = json.loads(week_final)

            a = {}
            a['name'] = 'tesco_week'
            a['items'] = week_final

            final = []
            final.append(a)

        else:

            weeks_data = read_frame(calendar_dim_hierarchy.objects.all().values('tesco_week'))
            # weeks_data = weeks_data[weeks_data['tesco_week'] >= 201646 and weeks_data['tesco_week'] >= 201705]
            weeks_data = weeks_data[(weeks_data["tesco_week"] >= 201626) & (weeks_data['tesco_week'] <= week_id)]

            week_df = weeks_data[['tesco_week']].drop_duplicates()

            week_temp = read_frame(calendar_dim_hierarchy.objects.filter(**kwargs).values('tesco_week'))

            print("Comm name ")
            data = {'tesco_week': week_temp.tesco_week.unique()}
            week_name = pd.DataFrame(data)
            print(len(week_name))

            if len(week_name) == 1:
                week_name['selected'] = True
                week_name['disabled'] = False
                week_df = pd.merge(week_df, week_name, how='left')
                week_df['selected'] = week_df['selected'].fillna(False)
                week_df['disabled'] = week_df['disabled'].fillna(True)
                week_df = week_df.rename(columns={'tesco_week': 'name'})
            else:
                week_name['selected'] = False
                week_name['disabled'] = False
                week_df = pd.merge(week_df, week_name, how='left')
                week_df['selected'] = week_df['selected'].fillna(False)
                week_df['disabled'] = week_df['disabled'].fillna(True)
                week_df = week_df.rename(columns={'tesco_week': 'name'})
            week_df = week_df.sort_values('name', ascending=False)
            week_final = week_df.to_json(orient='records')
            week_final = json.loads(week_final)

            a = {}
            a['name'] = 'tesco_week'
            a['items'] = week_final

            final = []
            final.append(a)
        logging.info(final)
        return JsonResponse(final, safe=False)


# Executive Filtered data


def col_distinct(kwargs, col_name, kwargs_header):
    print("++++++++++++++++++++ kwargs_header")
    print(kwargs_header)
    queryset = sales_heirarchy.objects.filter(**kwargs_header).filter(**kwargs).values(col_name).order_by(
        col_name).distinct()
    base_product_number_list = [k.get(col_name) for k in queryset]
    return base_product_number_list


global_var = sales_heirarchy.objects.all();

class executive_filterdata(APIView):
    def get(self, request):
        # print(request.GET)
        obj = {}
        get_keys = request.GET.keys()
        obj2 = {}
        default_keys = request.GET.keys()
        for i in get_keys:
            # print(request.GET.getlist(i))
            obj[i] = request.GET.getlist(i)
        print(obj)
        for i in default_keys:
            # print(request.GET.getlist(i))
            obj2[i] = request.GET.getlist(i)
        default_check = obj2
        user_id = default_check.pop('user_id')
        designation = default_check.pop('designation')
        user_name = default_check.pop('user_name')

        user_id = obj.pop('user_id', None)
        designation = obj.pop('designation', None)
        session_id = obj.pop('session_id', None)
        user_name = obj.pop('user_name', None)
        buying_controller_header = obj.pop('buying_controller_header', ['Beers'])
        buyer_header = obj.pop('buyer_header', None)
        store_type = obj.pop('store_type_header',None)

        if ((buyer_header is None) or buyer_header == ['']):
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        sent_req = obj
        # print('*********************      FILTERS2  *********************')
        cols = ['store_type', 'commercial_name', 'category_name', 'buying_controller', 'buyer', 'junior_buyer',
                'product_subgroup',
                'brand_indicator']

        # find lowest element of cols
        lowest = 0
        second_lowest = 0
        element_list = []
        print("sent req.....",sent_req)
        if sent_req != {}:
            print("entered if 123")
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
            print("sent_req.............",sent_req)
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
                    if col_name == cols[0]:
                        return True
                    elif col_name in sent_req.keys():
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
                               'required': True if col_name == 'buying_controller' else False
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
        logging.info({'cols': cols, 'checkbox_list': final_list2})
        return Response({'cols': cols, 'checkbox_list': final_list2})

class OverviewKpis(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if ((buyer_header is None) or buyer_header == ['']):
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }


        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_id').distinct()
            product_subgroup_id = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_subgroup_id').distinct()

        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()  ##print(products)
            product_subgroup_id = sales_heirarchy.objects.filter(**args).values(
                'product_subgroup_id').distinct()

        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)
        print("week for overview kpi")
        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products,
            'store_type__in': store_type}

        kwargs_lw = {
            'tesco_week': lastweek,
            'product_id__in': products,
            'store_type__in': store_type}

        # query for aggregations (current week)
        data_cw = supplier_view.objects.filter(**kwargs).aggregate(sales_cw=Sum('sales_ty'),
                                                                   sales_cw_ly=Sum('sales_ly'),
                                                                   cogs_cw=Sum('cogs_ty'),
                                                                   cogs_cw_ly=Sum('cogs_ly'),
                                                                   volume_cw=Sum('volume_ty'),
                                                                   volume_cw_ly=Sum('volume_ly'),
                                                                   cgm_cw=Sum('cgm_ty'),
                                                                   cgm_cw_ly=Sum('cgm_ly'),
                                                                   volume_cw_lfl=Sum('volume_ty_lfl'),
                                                                   volume_cw_lfl_ly=Sum('volume_ly_lfl'),
                                                                   cogs_cw_lfl=Sum('cogs_ty_lfl'),
                                                                   cogs_cw_lfl_ly=Sum('cogs_ly_lfl'),
                                                                   cgm_cw_lfl=Sum('cgm_ty_lfl'),
                                                                   cgm_cw_lfl_ly=Sum('cgm_ly_lfl'),
                                                                   sales_cw_lfl=Sum('sales_ty_lfl'),
                                                                   sales_cw_lfl_ly=Sum('sales_ly_lfl')
                                                                   )

        # query for aggregations (last week)

        data_lw = supplier_view.objects.filter(**kwargs_lw).aggregate(sales_lw=Sum('sales_ty'),
                                                                      cogs_lw=Sum('cogs_ty'),
                                                                      volume_lw=Sum('volume_ty'),
                                                                      cgm_lw=Sum('cgm_ty'))

        # dataframe for calculations of variations(wow, yoy)

        def calc_kpi(kpi):

            if (kpi == 'Value'):
                total_cw = 'sales_cw'
                total_cw_lfl = 'sales_cw_lfl'
                total_lw = 'sales_lw'
                total_cw_ly = 'sales_cw_ly'
                total_cw_lfl_ly = 'sales_cw_lfl_ly'
                format_type = '£'

            elif (kpi == 'Volume'):
                total_cw = 'volume_cw'
                total_cw_lfl = 'volume_cw_lfl'
                total_lw = 'volume_lw'
                total_cw_ly = 'volume_cw_ly'
                total_cw_lfl_ly = 'volume_cw_lfl_ly'
                format_type = ''

            elif (kpi == 'COGS'):
                total_cw = 'cogs_cw'
                total_cw_lfl = 'cogs_cw_lfl'
                total_lw = 'cogs_lw'
                total_cw_ly = 'cogs_cw_ly'
                total_cw_lfl_ly = 'cogs_cw_lfl_ly'
                format_type = '£'

            else:
                total_cw = 'cgm_cw'
                total_cw_lfl = 'cgm_cw_lfl'
                total_lw = 'cgm_lw'
                total_cw_ly = 'cgm_cw_ly'
                total_cw_lfl_ly = 'cgm_cw_lfl_ly'
                format_type = '£'

            try:
                total = format_kpi(data_cw[total_cw],format_type)
                total_lfl = format_kpi(data_cw[total_cw_lfl],format_type)
                data_frame = {}
                data_frame['var_wow'] = var_calc(data_cw[total_cw],data_lw[total_lw])
                data_frame['var_yoy'] = var_calc(data_cw[total_cw], data_cw[total_cw_ly])
                data_frame['var_lfl'] = var_calc(data_cw[total_cw_lfl], data_cw[total_cw_lfl_ly])
                data_frame['total'] = total
                data_frame['total_lfl'] = total_lfl
            except:
                data_frame = {}
                data_frame['var_wow'] = 0
                data_frame['var_yoy'] = 0
                data_frame['total'] = 0
            return data_frame

        dataframe = {}
        dataframe['value'] = calc_kpi('Value')
        dataframe['volume'] = calc_kpi('Volume')
        dataframe['cogs'] = calc_kpi('COGS')
        dataframe['cgm'] = calc_kpi('CGM')
        overview_performance = dataframe



        try:
            ASP = {}
            ASP['abs']=   format((data_cw['sales_cw'] / data_cw['volume_cw']), '.2f')
            ASP['wow'] = var_calc((data_cw['sales_cw'] / data_cw['volume_cw']),(data_lw['sales_lw'] / data_lw['volume_lw']))
            ASP['yoy'] = var_calc(data_cw['sales_cw'] / data_cw['volume_cw'],data_cw['sales_cw_ly'] / data_cw['volume_cw_ly'])
            ASP['lfl'] = var_calc((data_cw['sales_cw_lfl'] / data_cw['volume_cw_lfl']), (data_cw['sales_cw_lfl_ly'] / data_cw['volume_cw_lfl_ly']))
        except:
            ASP = 0
        try:
            ACP = {}
            ACP['abs']=format((data_cw['cogs_cw'] / data_cw['volume_cw']), '.2f')
            ACP['wow'] = var_calc((data_cw['cogs_cw'] / data_cw['volume_cw']),(data_lw['cogs_lw'] / data_lw['volume_lw']))
            ACP['yoy'] = var_calc((data_cw['cogs_cw'] / data_cw['volume_cw']),(data_cw['cogs_cw_ly'] / data_cw['volume_cw_ly']))
            ACP['lfl'] = var_calc((data_cw['cogs_cw_lfl'] / data_cw['volume_cw_lfl']),(data_cw['cogs_cw_lfl_ly'] / data_cw['volume_cw_lfl_ly']))
        except:
            ACP = 0
        overview_price = {}
        overview_price['ASP'] = ASP
        overview_price['ACP'] = ACP

        # Market Share
        def week_selection_market(week_flag):
            if (week_flag == 'Latest 4 Weeks'):
                week_logic = 'Latest 4 Weeks'

            elif (week_flag == 'Latest 13 Weeks'):
                week_logic = 'Latest 13 Weeks'

            elif (week_flag == 'YTD'):
                week_logic = 'Year To Date'
            elif (week_flag == 'Latest 26 Weeks'):
                week_logic = 'Latest 26 Weeks'
            else:
                week_logic = 'Latest Week'

            print("week logic ",week_logic)
            return week_logic


        print("week_flag called ",week_flag)
        week = week_selection_market(week_flag)
        currentweek_market = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        currentweek_market = currentweek_market['cw_max']

        lastweek_market1 = last_week(currentweek_market)
        lastyearweek_market1 = currentweek_market - 100

        kwargs_market1 = {
            'tesco_week': currentweek_market,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }
        kwargs_lw_market1 = {
            'tesco_week': lastweek_market1,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }
        kwargs_ly_market1 = {
            'tesco_week': lastyearweek_market1,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }
        if(currentweek_market==currentweek):
            market_week_disclaimer = 0
        else:
            currentweek_market = lastweek
            market_week_disclaimer = 1

        lastweek_market = last_week(currentweek_market)
        lastyearweek_market = currentweek_market - 100
        kwargs_market = {
            'tesco_week': currentweek_market,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }

        kwargs_lw_market = {
            'tesco_week': lastweek_market,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }

        kwargs_ly_market = {
            'tesco_week': lastyearweek_market,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }

        print("kwargs_market",kwargs_market1)
        print("kwargs_lw_market",kwargs_lw_market1)
        print("kwargs_ly_market1",kwargs_ly_market1)
        kpi = 'value'
        try:
            exclu_tesco = competitor_market_share.objects.filter(**kwargs_market1).exclude(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))
        except:
            exclu_tesco = 0

        try:
            only_tesco = competitor_market_share.objects.filter(**kwargs_market1).filter(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))
        except:
            only_tesco = 0

        try:
            tesco_share_percent = (only_tesco['total_kpi'] / (only_tesco['total_kpi'] + exclu_tesco['total_kpi'])) * 100
        except:
            tesco_share_percent = 0

        try:
            exclu_tesco_lw = competitor_market_share.objects.filter(**kwargs_lw_market1).exclude(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))
        except:
            exclu_tesco_lw = 0

        try:
            only_tesco_lw = competitor_market_share.objects.filter(**kwargs_lw_market1).filter(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))
        except:
            only_tesco_lw = 0


        try:
            tesco_share_percent_lw = (only_tesco_lw['total_kpi'] / (only_tesco_lw['total_kpi'] + exclu_tesco_lw['total_kpi'])) * 100
        except:
            tesco_share_percent_lw = 0

        try:
            exclu_tesco_ly = competitor_market_share.objects.filter(**kwargs_ly_market1).exclude(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))

        except:
            exclu_tesco_ly = 0

        try:
            only_tesco_ly = competitor_market_share.objects.filter(**kwargs_ly_market1).filter(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))

        except:
            only_tesco_ly = 0

        try:
            tesco_share_percent_ly = (only_tesco_ly['total_kpi'] / (only_tesco_ly['total_kpi'] + exclu_tesco_ly['total_kpi'])) * 100
        except:
            tesco_share_percent_ly = 0

        share_per = {}
        share_per['abs'] = str(float(format(tesco_share_percent,'.1f')))


        if(tesco_share_percent_lw!=0):
            share_per['wow'] = float(format(tesco_share_percent - tesco_share_percent_lw,'.1f'))
        else:
            share_per['wow'] = 'NA'
        if(tesco_share_percent_ly!=0):
            share_per['yoy'] = float(format(tesco_share_percent - tesco_share_percent_ly,'.1f'))
        else:
            share_per['yoy'] = 'NA'

        print("only_tesco['total_kpi']",only_tesco['total_kpi'])
        print("only_tesco_lw['total_kpi']",only_tesco_lw['total_kpi'])
        print("only_tesco_ly['total_kpi']",only_tesco_ly['total_kpi'])

        if only_tesco['total_kpi'] is None:
            share_per['abs'] = 'NA'
        if only_tesco_lw['total_kpi'] is None:
            share_per['wow'] = 'NA'
        if only_tesco_ly['total_kpi'] is None:
            share_per['yoy'] = 'NA'

        opportunity_data = competitor_market_share.objects.filter(**kwargs_market1).filter(
                competitor='Tesco LFL').aggregate(
            opportunity=Sum('opportunity'))
        try:
            opportunity = opportunity_data['opportunity']
        except:
            opportunity = 0

        opportunity_data_lw = competitor_market_share.objects.filter(**kwargs_lw_market1).filter(
                competitor='Tesco LFL').aggregate(
            opportunity=Sum('opportunity'))
        try:
            opportunity_lw = opportunity_data_lw['opportunity']
        except:
            opportunity_lw = 0

        opportunity_data_ly = competitor_market_share.objects.filter(**kwargs_ly_market1).filter(
                competitor='Tesco LFL').aggregate(
            opportunity=Sum('opportunity'))
        try:
            opportunity_ly = opportunity_data_ly['opportunity']
        except:
            opportunity_ly = 0


        opportunity_per = {}
        opportunity_per['yoy'] = var_calc(opportunity, opportunity_ly)
        opportunity_per['wow'] = var_calc(opportunity, opportunity_lw)
        try:
            opportunity_per['abs'] = format_kpi(opportunity, '£')
        except:
            if opportunity_data['opportunity'] is None:
                opportunity_per['abs'] = 'NA'
            else:
                opportunity_per['abs'] = 0

        if opportunity_data_ly['opportunity'] is None:
            opportunity_per['yoy'] = 'NA'

        if opportunity_data_lw['opportunity'] is None:
            opportunity_per['wow'] = 'NA'

        overview_market = {}
        overview_market['share'] = share_per
        overview_market['opportunity'] = opportunity_per
        overview_market['diclaimer_flag'] = market_week_disclaimer
        # convert dataframe to json, combine all dictionaries and return
        overview_perf = overview_performance


        overview = {}
        overview["kpi"] = overview_perf
        overview["price"] = overview_price
        overview["market"] = overview_market
        overview['currentweek'] = max_week
        logging.info(overview)
        # serializer_class = PerformanceSerializer
        return JsonResponse(overview, safe=False)

class OverviewKpiTrends(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if ((buyer_header is None) or buyer_header == ['']):
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        if not args:
            print("args--------------------")
            products = sales_heirarchy.objects.filter(buyer='Meat and Poultry').values(
                'product_id').distinct()
            print("Products++++++++++++")
            print(products)
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products,
            'store_type__in': store_type
        }

        trend_chart = list(
            supplier_view.objects.filter(**kwargs).values('tesco_week').annotate(grouped_sales_ly=Sum('sales_ly'),
                                                                                 grouped_sales_ty=Sum('sales_ty'),
                                                                                 grouped_volume_ly=Sum('volume_ly'),
                                                                                 grouped_volume_ty=Sum('volume_ty'),
                                                                                 grouped_cogs_ly=Sum('cogs_ly'),
                                                                                 grouped_cogs_ty=Sum('cogs_ty'),
                                                                                 grouped_profit_ly=Sum('cgm_ly'),
                                                                                 grouped_profit_ty=Sum(
                                                                                     'cgm_ty')).order_by('tesco_week'))
        trend_chart = pd.DataFrame(trend_chart)

        sales_trend = pd.DataFrame()
        try:
            value_trend = pd.DataFrame()
            value_trend['tesco_week'] = trend_chart['tesco_week'].astype(str)
            value_trend['grouped_sales_ly'] = trend_chart['grouped_sales_ly']
            value_trend['grouped_sales_ty'] = trend_chart['grouped_sales_ty']
            value_trend = value_trend.rename(columns={'grouped_sales_ly': 'value_ly', 'grouped_sales_ty': 'value_ty'})
            value_trend = value_trend.to_json(orient='records')
            value_trend = json.loads(value_trend)
        except:
            value_trend = 0

        try:
            volume_trend = pd.DataFrame()
            volume_trend['tesco_week'] = trend_chart['tesco_week'].astype(str)
            volume_trend['grouped_volume_ly'] = trend_chart['grouped_volume_ly']
            volume_trend['grouped_volume_ty'] = trend_chart['grouped_volume_ty']
            volume_trend = volume_trend.rename(
                columns={'grouped_volume_ly': 'value_ly', 'grouped_volume_ty': 'value_ty'})
            volume_trend = volume_trend.to_json(orient='records')
            volume_trend = json.loads(volume_trend)
        except:
            volume_trend = 0

        try:
            profit_trend = pd.DataFrame()
            profit_trend['tesco_week'] = trend_chart['tesco_week'].astype(str)
            profit_trend['grouped_profit_ly'] = trend_chart['grouped_profit_ly']
            profit_trend['grouped_profit_ty'] = trend_chart['grouped_profit_ty']
            profit_trend = profit_trend.rename(
                columns={'grouped_profit_ly': 'value_ly', 'grouped_profit_ty': 'value_ty'})
            profit_trend = profit_trend.to_json(orient='records')
            profit_trend = json.loads(profit_trend)
        except:
            profit_trend = 0

        try:
            cogs_trend = pd.DataFrame()
            cogs_trend['tesco_week'] = trend_chart['tesco_week'].astype(str)
            cogs_trend['grouped_cogs_ly'] = trend_chart['grouped_cogs_ly']
            cogs_trend['grouped_cogs_ty'] = trend_chart['grouped_cogs_ty']
            cogs_trend = cogs_trend.rename(columns={'grouped_cogs_ly': 'value_ly', 'grouped_cogs_ty': 'value_ty'})
            cogs_trend = cogs_trend.to_json(orient='records')
            cogs_trend = json.loads(cogs_trend)
        except:
            cogs_trend = 0

        try:
            asp_trend = pd.DataFrame()
            asp_trend['tesco_week'] = trend_chart['tesco_week'].astype(str)
            asp_trend['grouped_asp_ly'] = trend_chart['grouped_sales_ly']/trend_chart['grouped_volume_ly']
            asp_trend['grouped_asp_ty'] = trend_chart['grouped_sales_ty']/trend_chart['grouped_volume_ty']
            asp_trend = asp_trend.rename(columns={'grouped_asp_ly': 'value_ly', 'grouped_asp_ty': 'value_ty'})
            asp_trend = asp_trend.to_json(orient='records')
            asp_trend = json.loads(asp_trend)
        except:
            asp_trend = 0


        try:
            acp_trend = pd.DataFrame()
            acp_trend['tesco_week'] = trend_chart['tesco_week'].astype(str)
            acp_trend['grouped_acp_ly'] = trend_chart['grouped_cogs_ly']/trend_chart['grouped_volume_ly']
            acp_trend['grouped_acp_ty'] = trend_chart['grouped_cogs_ty']/trend_chart['grouped_volume_ty']
            acp_trend = acp_trend.rename(columns={'grouped_acp_ly': 'value_ly', 'grouped_acp_ty': 'value_ty'})
            acp_trend = acp_trend.to_json(orient='records')
            acp_trend = json.loads(acp_trend)
        except:
            acp_trend = 0



        overview_trends = {}
        overview_trends["value_trend"] = value_trend
        overview_trends["volume_trend"] = volume_trend
        overview_trends["cgm_trend"] = profit_trend
        overview_trends["cogs_trend"] = cogs_trend
        overview_trends["acp_trend"] = acp_trend
        overview_trends["asp_trend"] = asp_trend
        logging.info(overview_trends)
        return JsonResponse(overview_trends, safe=False)

class roles_and_int(APIView):
    def get(self, request, *args):
        # print("args recieved")
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        chart_flag = 0

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', None)
        buyer_header = args.pop('buyer_header__in', None)

        if not args:
            if buyer_header is not None:
                buying_controller_data = list(
                    sales_heirarchy.objects.filter(buyer__in=buyer_header).values_list('buying_controller',
                                                                                       flat=True).distinct())
            elif buying_controller_header is not None:
                buying_controller_data = list(
                    sales_heirarchy.objects.filter(buying_controller__in=buying_controller_header).values_list(
                        'buying_controller', flat=True).distinct())
        else:
            buying_controller_data = list(
                sales_heirarchy.objects.filter(**args).values_list('buying_controller', flat=True).distinct())

        role_intent = list(
            roles_and_intent_v2.objects.filter(buying_controller__in=buying_controller_data).values('buying_controller',
                                                                                                 'large_stores','express'))
        role_intent = pd.DataFrame(role_intent)

        # role_intent = role_intent.rename(columns={'buying_controller': temp[0]})


        role_intent = role_intent.to_dict(orient='records')
        roles_and_intent_detail = list(
            roles_and_intent_target.objects.filter(buying_controller__in=buying_controller_data).values('buying_controller','type',
                                                                                                 'large_stores','express','benchmark','tesco_as_is','tesco_end_game'))
        roles_and_intent_detail = pd.DataFrame(roles_and_intent_detail)

        # roles_and_intent_tar = roles_and_intent_tar.rename(columns={'type': temp[0]})
        # role_intent = role_intent.append(roles_and_intent_tar, ignore_index=True)

        roles_and_intent_detail = roles_and_intent_detail.to_dict(orient='records')

        data = {}
        data['roles_and_intent'] = role_intent
        data['roles_and_intent_detail'] = roles_and_intent_detail
        logging.info(data)
        return JsonResponse(data, safe=False)

class budget_forecast(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])

        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        product_subgroup = args.pop('product_subgroup__in', None)

        brand_indicator = args.pop('brand_indicator__in', None)

        parent_supplier = args.pop('parent_supplier__in', None)

        supplier = args.pop('supplier__in', None)

        print("args ++++________++++++++++")
        print(args)
        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if ((buyer_header is None) or buyer_header == ['']):
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        if not args:
            junior_buyer = sales_heirarchy.objects.filter(**kwargs_header).values(
                'junior_buyer').distinct()
            products = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_id').distinct()

        else:
            junior_buyer = sales_heirarchy.objects.filter(**args).values('junior_buyer').distinct()
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs_forecast = {
            'tesco_week__in': week,
            'junior_buyer__in': junior_buyer,
        }

        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products,
        }

        # calculate total sales
        data_cw = supplier_view.objects.filter(**kwargs).aggregate(sales_cw=Sum('sales_ty'))

        # calculate total budget and forecast using query
        budget_forecast_list = forecast_budget_data.objects.filter(**kwargs_forecast).aggregate(
            total_budget=Sum('budget_sales'),
            total_forecast=Sum(
                'forecast_sales'))
        try:
            budget = float(budget_forecast_list['total_budget'])
        except:
            budget = 0
        # try:
        forecast = float(budget_forecast_list['total_forecast'])
        print("+++++++++++++++++++++++++++++++")
        print(float(budget_forecast_list['total_forecast']))
        # except:
        # print("entered exception")
        # forecast = 0
        try:
            sales = float(data_cw['sales_cw'])
        except:
            sales = 0

        forecast_budget_chart = [{"label": "budget", "value": budget}, {"label": "sales", "value": sales},
                                 {"label": "forecast", "value": forecast}]

        try:
            forecast_value = ((sales - budget) / budget) * 100
        except:
            forecast_value = 0

        try:
            budget_value = ((sales - forecast) / forecast) * 100
        except:
            print("entered exception")
            budget_value = 0

        strategy_perf = {}
        strategy_perf['chart_data'] = forecast_budget_chart
        strategy_perf['forecast_value'] = float(format(forecast_value,'.1f'))
        strategy_perf['budget_value'] = float(format(budget_value,'.1f'))
        logging.info(strategy_perf)
        return JsonResponse(strategy_perf, safe=False)

class OverviewDriversInternal(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        category_name = args.get('category_name__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        buyer = args.get('buyer__in', None)
        buying_controller = args.get('buying_controller__in', None)
        category_director = args.get('category_director__in', None)
        store_type = args.get('store_type__in', ['Main Estate', 'Express'])

        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)

        lastyearweek = lastyearweek_selection(week)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if junior_buyer is not None:
            transactions = 'junior_area_trx'
            value = 'junior_area_sales'
            volume = 'junior_area_volume'
            area = 'junior_area'
            kwargs_kpi = {
                'tesco_week__in': week,
                'junior_area__in': junior_buyer,
                'store_type__in': store_type
            }
            kwargs_kpi_ly = {
                'tesco_week__in': lastyearweek,
                'junior_area__in': junior_buyer,
                'store_type__in': store_type
            }



        elif buyer is not None:
            transactions = 'buyer_area_trx'
            value = 'buyer_area_sales'
            volume = 'buyer_area_volume'
            area = 'buyer_area'
            kwargs_kpi = {
                'tesco_week__in': week,
                'buyer_area__in': buyer,
                'store_type__in': store_type
            }
            kwargs_kpi_ly = {
                'tesco_week__in': lastyearweek,
                'buyer_area__in': buyer,
                'store_type__in': store_type
            }
        elif buying_controller is not None:
            transactions = 'product_area_trx'
            value = 'product_area_sales'
            volume = 'product_area_volume'
            area = 'product_area'
            kwargs_kpi = {
                'tesco_week__in': week,
                'product_area__in': buying_controller,
                'store_type__in': store_type
            }
            kwargs_kpi_ly = {
                'tesco_week__in': lastyearweek,
                'product_area__in': buying_controller,
                'store_type__in': store_type
            }
        else:

            if ((buyer_header is None) or buyer_header == ['']):
                transactions = 'product_area_trx'
                value = 'product_area_sales'
                volume = 'product_area_volume'
                area='product_area'
                kwargs_kpi = {
                    'product_area__in': buying_controller_header,
                    'store_type__in': store_type,
                    'tesco_week__in': week
                }
                kwargs_kpi_ly = {
                    'product_area__in': buying_controller_header,
                    'store_type__in': store_type,
                    'tesco_week__in': lastyearweek
                }
            else:
                transactions = 'buyer_area_trx'
                value = 'buyer_area_sales'
                volume = 'buyer_area_volume'
                area='buyer_area'
                kwargs_kpi = {
                    'product_area__in': buying_controller_header,
                    'buyer_area__in': buyer_header,
                    'store_type__in': store_type,
                    'tesco_week__in': week
                }
                kwargs_kpi_ly = {
                    'product_area__in': buying_controller_header,
                    'buyer_area__in': buyer_header,
                    'store_type__in': store_type,
                    'tesco_week__in': lastyearweek
                }

        print("kwargs kpi")
        print(kwargs_kpi)

        print("kwargs_kpi_ly")
        print(kwargs_kpi_ly)

        week = week_selection(currentweek, week_flag, chart_flag)

        if not args:
            products = sales_heirarchy.objects.filter(category_name='Beers, Wines and Spirits').values(
                'product_id').distinct()
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()

        lastweek = currentweek - 1

        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products
        }

        if junior_buyer is not None:
            kwargs_promo_contri = {
                'tesco_week__in': week,
                'junior_area__in': junior_buyer
            }
            area='junior_area'

        elif buyer is not None:
            kwargs_promo_contri = {
                'tesco_week__in': week,
                'buyer_area__in': buyer
            }
            area='buyer_area'
        elif buying_controller is not None:
            kwargs_promo_contri = {
                'tesco_week__in': week,
                'product_area__in': buying_controller
            }
            area='product_area'
        elif category_name is not None:
            kwargs_promo_contri = {
                'tesco_week__in': week,
                'category_director__in': category_name
            }
            area='category_director'
        else:

            if ((buyer_header is None) or buyer_header == ['']):
                kwargs_promo_contri = {
                    'product_area__in': buying_controller_header,
                    'tesco_week__in': week

                }
                area='product_area'
            else:
                kwargs_promo_contri = {
                    'product_area__in': buying_controller_header,
                    'buyer_area__in': buyer_header,
                    'tesco_week__in': week
                }
                area='buyer_area'

        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products}

        kwargs_lw = {
            'tesco_week': lastweek,
            'product_id__in': products}

        # query for aggregations (current week)
        data_cw = supplier_view.objects.filter(**kwargs).aggregate(sales_cw=Sum('sales_ty'),
                                                                   sales_cw_ly=Sum('sales_ly'),
                                                                   sales_cw_lfl=Sum('sales_ty_lfl'),
                                                                   sales_cw_ly_lfl=Sum('sales_ly_lfl')
                                                                   )

        # query for aggregations (last week)


        if (currentweek >= 201702):
            kpi_data = list(executive_view.objects.filter(**kwargs_kpi).values(area,transactions, value, volume).distinct())
            print("kpi_data------------------------------")
            print(kpi_data)
            kpi_data_ly = list(executive_view.objects.filter(**kwargs_kpi_ly).values(area, transactions, value, volume).distinct())
            print("kpi_data ly------------------------------")
            print(kpi_data_ly)
            kpi_data = pd.DataFrame(kpi_data)
            kpi_data_ly = pd.DataFrame(kpi_data_ly)
            # print('kpiiiiiiiiiiiiiiii')
            # print(kpi_data)
            print('kpiiiiiiiiii_ last year')
            print(kpi_data_ly)
            try:
                volume_ty = kpi_data[volume].sum()
            except:
                volume_ty = 0
            try:
                value_ty = kpi_data[value].sum()
            except:
                value_ty = 0
            try:
                transaction_ty = kpi_data[transactions].sum()
                print('transaction ty')
                print(transaction_ty)
            except:
                transaction_ty = 0
            print('kpi after')
            print('value_ty',value_ty)
            print('volume_ty',volume_ty)


            try:
                volume_ly = kpi_data_ly[volume].sum()
            except:
                volume_ly = 0
            try:
                value_ly = kpi_data_ly[value].sum()
            except:
                value_ly = 0
            try:
                transaction_ly = kpi_data_ly[transactions].sum()
            except:
                transaction_ly = 0
            print('transactions_ly',transaction_ly)
            print('value_ly',value_ly)
            print('volume_ly',volume_ly)

            kpi_data = {}
            try:
                item_per_basket_ty = volume_ty / transaction_ty
            except:
                item_per_basket_ty = 0
            try:
                item_per_basket_ly = volume_ly / transaction_ly
            except:
                item_per_basket_ly = 0
            try:
                item_price_ty = value_ty / volume_ty
            except:
                item_price_ty = 0
            try:
                item_price_ly = value_ly / volume_ly
            except:
                item_price_ly = 0

            print('item_per_basket_ty',item_per_basket_ty)
            print('item_per_basket_ly',item_per_basket_ly)
            print('item_price_ty',item_price_ty)
            print('item_price_ly',item_price_ly)


            transaction_var = var_calc(transaction_ty,transaction_ly)
            item_per_basket_var = var_calc(item_per_basket_ty,item_per_basket_ly)
            item_price_var = var_calc(item_price_ty,item_price_ly)
            sales_var = var_calc(value_ty,value_ly)
            print('transaction_var',transaction_var)
            print('item_per_basket_var', transaction_var)
            print('item_price_var', item_price_var)
            print('sales_var', sales_var)

            data_available_flag = 'yes'

        else:
            transaction_var = 0
            item_per_basket_var = 0
            item_price_var = 0
            data_available_flag = 'no'

        promo_data = promo_contribution.objects.filter(**kwargs_promo_contri).aggregate(
            grouped_trade_plan_sales_ty=Sum('trade_plan_sales_ty'), grouped_event_sales_ty=Sum('event_sales_ty'),
            grouped_fs_sales_ty=Sum('fs_sales_ty'), grouped_shelf_sales_ty=Sum('shelf_promo_sales_ty'),
            grouped_base_sales_ty=Sum('base_sales_ty'), grouped_trade_plan_sales_ly=Sum('trade_plan_sales_ly'),
            grouped_event_sales_ly=Sum('event_sales_ly'),
            grouped_fs_sales_ly=Sum('fs_sales_ly'), grouped_shelf_sales_ly=Sum('shelf_promo_sales_ly'),
            grouped_base_sales_ly=Sum('base_sales_ly'))

        waterfall_sales_calc_data = supplier_view.objects.filter(**kwargs).aggregate(grouped_sales_ty=Sum('sales_ty'),
                                                                                     grouped_sales_ly=Sum('sales_ly'),
                                                                                     grouped_sales_lfl_ty=Sum(
                                                                                         'sales_ty_lfl'),
                                                                                     grouped_sales_lfl_ly=Sum(
                                                                                         'sales_ly_lfl'))

        try:

            trade_plan_sales_ly = float(promo_data['grouped_event_sales_ly']) + float(promo_data['grouped_fs_sales_ly']) + float(promo_data['grouped_shelf_sales_ly']) + float(promo_data['grouped_base_sales_ly'])
            event_sales = float(promo_data['grouped_event_sales_ty']) - float(promo_data['grouped_event_sales_ly'])
            fs_sales = float(promo_data['grouped_fs_sales_ty']) - float(promo_data['grouped_fs_sales_ly'])
            shelf_sales = float(promo_data['grouped_shelf_sales_ty']) - float(promo_data['grouped_shelf_sales_ly'])
            base_sales = float(promo_data['grouped_base_sales_ty']) - float(promo_data['grouped_base_sales_ly'])
        except:
            trade_plan_sales = 0
            event_sales = 0
            fs_sales = 0
            shelf_sales = 0
            base_sales = 0

        try:
            LFL_growth_per = (waterfall_sales_calc_data['grouped_sales_lfl_ty'] - waterfall_sales_calc_data[
                'grouped_sales_lfl_ly']) / waterfall_sales_calc_data['grouped_sales_lfl_ly']
            LFL_growth_per = float(LFL_growth_per)

        except:
            LFL_growth_per = 0
        print("trade_aasd$$$$$$$$$$$$$$$$$$$$")
        print(float(trade_plan_sales_ly))
        print("event_sales")
        print(float(promo_data['grouped_event_sales_ty']))
        print("fs_sales")
        print(float(promo_data['grouped_fs_sales_ty']))
        print("shelf_sales")
        print(float(promo_data['grouped_shelf_sales_ty']))
        print("base_sales")
        print(float(promo_data['grouped_base_sales_ty']))
        print(buying_controller_header)
        print(kwargs_promo_contri)
        promo_contri_waterfall_chart = [
            {'name': "Sales LY", 'value': float(trade_plan_sales_ly)},
            {'name': "Event Sales", 'value': float(format(event_sales, '.2f'))},
            {'name': "FS Sales", 'value': float(format(fs_sales, '.2f'))},
            {'name': "Shelf Sales", 'value': float(format(shelf_sales, '.2f'))},
            {'name': "Base Sales", 'value': float(format(base_sales, '.2f'))}]

        kpi_contri = {}
        kpi_contri['sales_lfl_var'] = sales_var
        kpi_contri['transaction_var'] = transaction_var
        kpi_contri['item_per_basket_var'] = item_per_basket_var
        kpi_contri['item_price_var'] = item_price_var
        kpi_contri['data_available'] = data_available_flag

        in_drivers_trends = {}
        in_drivers_trends["kpi"] = kpi_contri
        in_drivers_trends["promo"] = promo_contri_waterfall_chart
        logging.info(in_drivers_trends)
        return JsonResponse(in_drivers_trends, safe=False)

class OverviewDriversExternal(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)
        lastyearweek = lastyearweek_selection(week)

        kwargs = {
            'tesco_week__in': week
        }
        kwargslw = {
            'tesco_week': lastweek
        }
        kwargsly = {
            'tesco_week__in': lastyearweek
        }

        sunshine_avg = list(weather_weekly_details.objects.filter(**kwargs).values('sunshine_weekly_avg'))
        sunshine_avg_lw = list(weather_weekly_details.objects.filter(**kwargslw).values('sunshine_weekly_avg'))
        sunshine_avg_ly = list(weather_weekly_details.objects.filter(**kwargsly).values('sunshine_weekly_avg'))

        rainfall_avg = list(weather_weekly_details.objects.filter(**kwargs).values('rainfall_weekly_avg'))
        rainfall_avg_lw = list(weather_weekly_details.objects.filter(**kwargslw).values('rainfall_weekly_avg'))
        rainfall_avg_ly = list(weather_weekly_details.objects.filter(**kwargsly).values('rainfall_weekly_avg'))

        temperature_avg = list(weather_weekly_details.objects.filter(**kwargs).values('temperature_weekly_avg'))
        temperature_avg_lw = list(weather_weekly_details.objects.filter(**kwargslw).values('temperature_weekly_avg'))
        temperature_avg_ly = list(weather_weekly_details.objects.filter(**kwargsly).values('temperature_weekly_avg'))

        try:
            sunshine_avg1 = float(format(sunshine_avg[0]['sunshine_weekly_avg'],'.2f'))
            rainfall_avg1 = float(format(rainfall_avg[0]['rainfall_weekly_avg'],'.2f'))
            temperature_avg1 = float(format(temperature_avg[0]['temperature_weekly_avg'],'.2f'))
        except:
            sunshine_avg1 = 0
            rainfall_avg1 = 0
            temperature_avg1 = 0


        if (rainfall_avg1==0):
            rainfall_flag = 'dry'
        elif(rainfall_avg1>0):
            rainfall_flag = 'dry/very light'
        elif(rainfall_avg1==1 ):
            rainfall_flag = 'very light'
        elif(rainfall_avg1>1 ):
            rainfall_flag = 'very light/light to mod'
        elif (rainfall_avg1 == 2):
            rainfall_flag = 'light to mod'
        elif (rainfall_avg1>2):
            rainfall_flag = 'light to mod/moderate'
        elif (rainfall_avg1 == 3):
            rainfall_flag = 'moderate'
        elif (rainfall_avg1>3):
            rainfall_flag = 'moderate/mod to heavy'
        elif (rainfall_avg1 == 4):
            rainfall_flag = 'mod to heavy'
        elif (rainfall_avg1>4):
            rainfall_flag = 'mod to heavy/heavy'
        elif (rainfall_avg1 == 5):
            rainfall_flag = 'heavy'
        elif (rainfall_avg1>5):
            rainfall_flag = 'heavy/very heavy'
        elif (rainfall_avg1 == 6):
            rainfall_flag = 'very heavy'
        elif (rainfall_avg1>5):
            rainfall_flag = 'very heavy/torrential'
        elif (rainfall_avg1 == 7):
            rainfall_flag = 'torrential'
        else:
            rainfall_flag = ''


        ex_drivers = {}
        sunshine = {}
        sunshine['avg'] = sunshine_avg1
        sunshine['wow'] = var_calc(sunshine_avg[0]['sunshine_weekly_avg'],sunshine_avg_lw[0]['sunshine_weekly_avg'])
        sunshine['yoy'] = var_calc(sunshine_avg[0]['sunshine_weekly_avg'],sunshine_avg_ly[0]['sunshine_weekly_avg'])
        rainfall = {}
        rainfall['avg'] = rainfall_avg1
        rainfall['wow'] = var_calc (rainfall_avg[0]['rainfall_weekly_avg'],rainfall_avg_lw[0]['rainfall_weekly_avg'])
        rainfall['yoy'] = var_calc(rainfall_avg[0]['rainfall_weekly_avg'],rainfall_avg_ly[0]['rainfall_weekly_avg'])
        rainfall['type'] = rainfall_flag
        temperature = {}
        temperature['avg'] = temperature_avg1
        temperature['wow'] = var_calc(temperature_avg[0]['temperature_weekly_avg'],temperature_avg_lw[0]['temperature_weekly_avg'])
        temperature['yoy'] = var_calc(temperature_avg[0]['temperature_weekly_avg'],temperature_avg_ly[0]['temperature_weekly_avg'])
        ex_drivers['sunshine'] = sunshine
        ex_drivers['rainfall'] = rainfall
        ex_drivers['temperature'] = temperature

        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'tesco_week__in': week
        }

        holidays_trend = list(
            uk_holidays.objects.filter(**kwargs).values('tesco_week', 'holiday_date', 'holiday_description').distinct())

        for i in range(0, len(holidays_trend)):
            holidays_trend[i]['holiday_date'] = str(holidays_trend[i]['holiday_date'])

        if (holidays_trend == []):
            holidays_trend = pd.DataFrame(columns=('holiday_date', 'holiday_description'))
            for i in range(1):
                holidays_trend.loc[i] = ['------', 'No holidays for the selected time period']
            holidays_trend['holiday_date'] = '-----'
            holidays_trend['holiday_description'] = 'No holidays for the selected time period'
            holidays_trend = holidays_trend.to_dict(orient='records')

        ex_drivers['holidays'] = holidays_trend
        logging.info(ex_drivers)
        return JsonResponse(ex_drivers, safe=False)

class KPI(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)
        category_name = args.get('category_name__in', ['Beers, Wines and Spirits'])
        buying_controller = args.get('buying_controller__in', None)
        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        product_subgroup = args.get('product_subgroup__in', None)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if ((buyer_header is None) or buyer_header == ['']):
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        if product_subgroup is not None:
            junior_buyer_denom = sales_heirarchy.objects.filter(product_subgroup__in=product_subgroup).values(
                'junior_buyer')

            kwargs_contri_denom = {
                'junior_buyer__in': junior_buyer_denom
            }
            level = 'junior_buyer'


        elif junior_buyer is not None:
            buyer_denom = sales_heirarchy.objects.filter(junior_buyer__in=junior_buyer).values('buyer')
            kwargs_contri_denom = {
                'buyer__in': buyer_denom
            }
            level = 'buyer'


        elif buyer is not None:
            buying_controller_denom = sales_heirarchy.objects.filter(buyer__in=buyer).values('buying_controller')
            kwargs_contri_denom = {
                'buying_controller__in': buying_controller_denom
            }
            level = 'buying_controller'


        elif buying_controller is not None:
            category_name_denom = sales_heirarchy.objects.filter(buying_controller__in=buying_controller).values(
                'category_name')
            kwargs_contri_denom = {
                'category_name__in': category_name_denom,
            }

            level = 'category_director'

        elif ((buyer_header is None) or buyer_header == ['']):
            category_name_denom = sales_heirarchy.objects.filter(buying_controller__in=buying_controller_header).values(
                'category_name')
            kwargs_contri_denom = {
                'category_name__in': category_name_denom,
            }
            level = 'category_director'
        else:
            buying_controller_denom = sales_heirarchy.objects.filter(buyer__in=buyer_header).values('buying_controller')
            kwargs_contri_denom = {
                'buying_controller__in': buying_controller_denom,

            }
            level = 'buying_controller'

        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_id').distinct()
            product_subgroup_id = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_subgroup_id').distinct()
            products_denom = sales_heirarchy.objects.filter(**kwargs_contri_denom).values('product_id').distinct()
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
            product_subgroup_id = sales_heirarchy.objects.filter(**args).values('product_subgroup_id').distinct()
            products_denom = sales_heirarchy.objects.filter(**kwargs_contri_denom).values('product_id').distinct()

        chart_flag = 0

        week = week_selection(currentweek, week_flag, chart_flag)
        if (kpi_type == 'Value'):
            total_ty = 'sales_ty'
            total_ty_lfl = 'sales_ty_lfl'
            total_ly = 'sales_ly'
            kpi_name = 'Value'
            kpi = 'value'
            total_ly_lfl = 'sales_ly_lfl'
            total_lw = 'sales_lw'
            format_type = '£'
        elif (kpi_type == 'Volume'):
            total_ty = 'volume_ty'
            total_ty_lfl = 'volume_ty_lfl'
            total_ly = 'volume_ly'
            total_ly_lfl = 'volume_ly_lfl'
            kpi_name = 'Volume'
            kpi = 'volume'
            format_type = ''
        elif (kpi_type == 'COGS'):
            total_ty = 'cogs_ty'
            total_ty_lfl = 'cogs_ty_lfl'
            total_ly = 'cogs_ly'
            total_ly_lfl = 'cogs_ly_lfl'
            kpi_name = 'COGS'
            format_type = '£'
        else:
            total_ty = 'cgm_ty'
            total_ty_lfl = 'cgm_ty_lfl'
            total_ly = 'cgm_ly'
            total_ly_lfl = 'cgm_ly_lfl'
            kpi_name = 'CGM'
            format_type = '£'

        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products,
            'store_type__in': store_type
        }

        kwargs_lw = {
            'tesco_week': lastweek,
            'product_id__in': products,
            'store_type__in': store_type
        }

        kwargs_denom = {
            'tesco_week__in': week,
            'product_id__in': products_denom,
            'store_type__in': store_type
        }

        kwargs_denom_lw = {
            'tesco_week': lastweek,
            'product_id__in': products_denom,
            'store_type__in': store_type
        }

        current_week_data = supplier_view.objects.filter(**kwargs).aggregate(total_ty=Sum(total_ty),
                                                                             total_ty_lfl=Sum(total_ty_lfl),
                                                                             total_ly=Sum(total_ly),
                                                                             total_ly_lfl=Sum(total_ly_lfl))
        ##print(current_week_data)
        last_week_data = supplier_view.objects.filter(**kwargs_lw).aggregate(total_ty=Sum(total_ty),
                                                                             total_ty_lfl=Sum(total_ty_lfl))
        growth_denom_data_outof = supplier_view.objects.filter(**kwargs_denom).aggregate(sales_ly=Sum('sales_ly'),
                                                                                         volume_ly=Sum('volume_ly'),
                                                                                         cogs_ly=Sum('cogs_ly'),
                                                                                         cgm_ly=Sum('cgm_ly'),
                                                                                         sales_ly_lfl=Sum(
                                                                                             'sales_ly_lfl'),
                                                                                         volume_ly_lfl=Sum(
                                                                                             'volume_ly_lfl'),
                                                                                         cogs_ly_lfl=Sum('cogs_ly_lfl'),
                                                                                         cgm_ly_lfl=Sum(
                                                                                             'cgm_ly_lfl'),
                                                                                         sales_ty=Sum('sales_ty'),
                                                                                         volume_ty=Sum('volume_ty'),
                                                                                         cogs_ty=Sum('cogs_ty'),
                                                                                         cgm_ty=Sum('cgm_ty'),
                                                                                         sales_ty_lfl=Sum(
                                                                                             'sales_ty_lfl'),
                                                                                         volume_ty_lfl=Sum(
                                                                                             'volume_ty_lfl'),
                                                                                         cogs_ty_lfl=Sum('cogs_ty_lfl'),
                                                                                         cgm_ty_lfl=Sum('cgm_ty_lfl'))

        growth_denom_lw_data_outof = supplier_view.objects.filter(**kwargs_denom_lw).aggregate(sales_ty=Sum('sales_ty'),
                                                                                               volume_ty=Sum(
                                                                                                   'volume_ty'),
                                                                                               cogs_ty=Sum('cogs_ty'),
                                                                                               cgm_ty=Sum('cgm_ty'))


        if (kpi_type == 'Value'):
            growth_column = 'buyer_outperf_value_pct'
            outperf_column = 'buyer_value_growth'
        else:
            growth_column = 'buyer_outperf_volume_pct'
            outperf_column = 'buyer_volume_growth'

        # try:

        # Total KPI calc

        total_value_total = {}
        total_value_total["total"] = format_kpi(current_week_data['total_ty'],format_type)
        total_value_total["total_lfl"] = format_kpi(current_week_data['total_ty_lfl'],format_type)
        total_value_total['wow'] = var_calc(current_week_data['total_ty'],last_week_data['total_ty'])
        total_value_total['yoy'] = var_calc(current_week_data['total_ty'],current_week_data['total_ly'])
        total_value_total['lfl'] = var_calc(current_week_data['total_ty_lfl'],current_week_data['total_ly_lfl'])



        def total_contr_var(a,b,c):

            if c != 0:
                try:
                    d = float(format(
                        ((a - b) * 100 / c), '.1f'))
                except:
                    d = 0
            else:
                d = 'NA'

            return d

        growth_total = {}
        growth_total["total"] = format_kpi(growth_denom_data_outof[total_ty],format_type)
        growth_total["total_lfl"] = format_kpi(growth_denom_data_outof[total_ty_lfl],format_type)
        growth_total['wow'] = total_contr_var(current_week_data['total_ty'],last_week_data['total_ty'],growth_denom_lw_data_outof[total_ty])
        growth_total['yoy'] = total_contr_var(current_week_data['total_ty'],current_week_data['total_ly'],growth_denom_data_outof[total_ly])
        growth_total['lfl'] = total_contr_var(current_week_data['total_ty_lfl'],current_week_data[
                'total_ly_lfl'],growth_denom_data_outof[total_ly_lfl])
        growth_total['of_wow'] =   var_calc(growth_denom_data_outof[total_ty],growth_denom_lw_data_outof[total_ty])
        growth_total['of_yoy'] = var_calc(growth_denom_data_outof[total_ty],growth_denom_data_outof[total_ly])
        growth_total['of_lfl'] =var_calc(growth_denom_data_outof[total_ty_lfl],growth_denom_data_outof[
                total_ly_lfl])



        # Market Calculation
        def week_selection_market(cw_week, week_flag):
            week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                '-tesco_week').distinct()
            last_week = week_ordered[1]
            last_week = last_week['tesco_week']
            if (week_flag == '4 Weeks'):
                week_logic = 'Latest 4 Weeks'

            elif (week_flag == '13 Weeks'):
                week_logic = 'Latest 13 Weeks'

            elif (week_flag == 'YTD'):
                week_logic = 'Year To Date'

            else:
                week_logic = 'Latest Week'

            return week_logic

        week = week_selection_market(currentweek, week_flag)

        kwargs_market = {
            'tesco_week': currentweek,
            'product_subgroup_id__in': product_subgroup_id,
            'flag': week
        }

        kwargs_lw_market = {
            'tesco_week': lastweek,
            'product_subgroup_id__in': product_subgroup_id
        }

        try:
            exclu_tesco = competitor_market_share.objects.filter(**kwargs_market).exclude(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))

        except:
            exclu_tesco = 0

        try:
            only_tesco = competitor_market_share.objects.filter(**kwargs_market).filter(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))

        except:
            only_tesco = 0

        try:
            only_tesco_last = competitor_market_share.objects.filter(**kwargs_lw_market).filter(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))
            print("only_tesco_last")
            print(only_tesco_last)
        except:
            only_tesco_last = 0
        try:
            tesco_share_percent = format(
                (only_tesco['total_kpi'] / (only_tesco['total_kpi'] + exclu_tesco['total_kpi'])) * 100, '.1f')
        except:
            tesco_share_percent = 0


        opportunity_data = competitor_market_share.objects.filter(**kwargs_market).aggregate(
            opportunity=Sum('opportunity'))

        try:
            opportunity = opportunity_data['opportunity']
        except:
            opportunity = 0
        ##over and out

        try:
            if opportunity > 1000:
                integer_val = int(float(opportunity) / 1000)
                opportunity = '£' + intcomma((integer_val)) + ' K'
            else:
                opportunity = '£' + intcomma(int(float(opportunity)))

        except:
            opportunity = 0


        market = {}
        market['share'] = tesco_share_percent
        market['opportunity'] = opportunity

        kpi = {}
        kpi["total_value"] = total_value_total
        kpi["growth"] = growth_total
        kpi["kpi_name"] = kpi_name
        kpi["market"] = market
        # kpi["growth"] = growth
        logging.info(kpi)
        return JsonResponse(kpi, safe=False)

class BestWorstInfo(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

        # for week tab
        week_flag = args.pop('week_flag__in', 'Selected Week')
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', 'Value')
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)
        store_type = args.get('store_type__in', ['Main Estate','Express'])
        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)

        if store_type is None:
            store_type = ['Main Estate', 'Express']

        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if junior_buyer is not None:
            kwargs = {
                'junior_buyer__in': junior_buyer,
                'store_type__in': store_type,
                'tesco_week__in': week
            }
            level = 'product_subgroup'



        elif buyer is not None:

            kwargs = {
                'buyer__in': buyer,
                'store_type__in': store_type,
                'tesco_week__in': week
            }
            level = 'junior_buyer'


        elif buying_controller is not None:

            kwargs = {
                'buying_controller__in': buying_controller,
                'store_type__in': store_type,
                'tesco_week__in': week
            }
            level = 'buyer'

        elif ((buyer_header is None) or buyer_header == ['']):
            kwargs = {
                'buying_controller__in': buying_controller_header,
                'store_type__in': store_type,
                'tesco_week__in': week
            }
            level = 'buyer'
        else:
            kwargs = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header,
                'store_type__in': store_type,
                'tesco_week__in': week
            }
            level = 'junior_buyer'


            # if not args:
            #     products = sales_heirarchy.objects.filter(**kwargs_products).values('product_id').distinct()
            # else:
            #     products = sales_heirarchy.objects.filter(**kwargs_products).values('product_id').distinct()

        if (kpi_type == 'Value'):
            total_ty = 'sales_ty'
            total_ly = 'sales_ly'
        elif (kpi_type == 'Volume'):
            total_ty = 'volume_ty'
            total_ly = 'volume_ly'
        elif (kpi_type == 'COGS'):
            total_ty = 'cogs_ty'
            total_ly = 'cogs_ly'
        else:
            total_ty = 'cgm_ty'
            total_ly = 'cgm_ly'

        def list_topbot(a, b, n):
            list_sales_growth_denom = supplier_view.objects.filter(**kwargs).aggregate(total_sum=Sum(b))
            list_sales_growth_denom = list_sales_growth_denom['total_sum']
            list_tb = list(supplier_view.objects.filter(**kwargs).values(level).annotate(grouped_ty=Sum(a),
                                                                                         grouped_ly=Sum(
                                                                                             b)).order_by(
                'grouped_ty'))
            list_tb = pd.DataFrame(list_tb)
            list_tb['cont_to_grwth'] = (list_tb['grouped_ty'] - list_tb[
                'grouped_ly']) * 100 / list_sales_growth_denom
            list_tb['cont_to_grwth'] = list_tb['cont_to_grwth']
            list_tb['grouped_ty'] = list_tb['grouped_ty'].astype(float)
            list_tb['grouped_ly'] = list_tb['grouped_ly'].astype(float)
            list_tb['cont_to_grwth'] = list_tb['cont_to_grwth'].astype(float).round(2)
            length = len(list_tb.index)

            top_5 = list_tb.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[False, False])
            top_5 = top_5[:n]
            if (length <= 5):
                length_less_than_five = 'yes'

            else:
                length_less_than_five = 'no'
            top_5 = top_5.to_dict(orient='records')

            bot_5 = list_tb.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[True, True])
            bot_5 = bot_5[:n]
            bot_5 = bot_5.to_dict(orient='records')
            top = {}
            for i in range(0, n):
                try:

                    name = top_5[i][level]

                    top[i] = {'name': name}
                except:
                    name = '---'

                    top[i] = {'name': name}

            bot = {}
            for i in range(0, n):
                try:

                    name = bot_5[i][level]

                    bot[i] = {'name': name}
                except:
                    name = '---'

                    bot[i] = {'name': name}

            if level == 'junior_buyer':
                level1 = 'Junior Buyer'
            elif level == 'buyer':
                level1 = 'Buyer'
            elif level == 'buying_controller':
                level1 = 'Buying Controller'
            else:
                level1 = 'NA'
            topbot = {'top_5': top, 'bot_5': bot, 'Choose_filters': 'no', 'level': level1, 'kpi_type': kpi_type,
                      'length_less_than_five': length_less_than_five}

            return topbot
        data = list_topbot(total_ty, total_ly, 5)
        logging.info(data)
        return JsonResponse(data, safe=False)

class BestInfo(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)
        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)

        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        selected_level = args.get('selected_level__in', None)
        product_subgroup = args.get('product_subgroup__in', None)
        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if product_subgroup is not None:
            junior_buyer = sales_heirarchy.objects.filter(product_subgroup__in=product_subgroup).values('junior_buyer').distinct()

        if selected_level is not None:
            # try:

            if store_type is None:
                store_type = ['Main Estate', 'Express']

            chart_flag = 1
            week = week_selection(currentweek, week_flag, chart_flag)

            if ((junior_buyer is not None) or (product_subgroup is not None)):

                kwargs = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'product_subgroup__in': selected_level
                }
                kwargs_denom = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'product_subgroup'

            elif buyer is not None:
                kwargs = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level
                }
                kwargs_denom = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'junior_buyer'
            elif buying_controller is not None:
                kwargs = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'buyer__in': selected_level
                }
                kwargs_denom = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'buyer'

            else:

                if (buyer_header is None):
                    kwargs = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week
                    }
                    kwargs_denom = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'buyer'
                else:
                    kwargs = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week
                    }
                    kwargs_denom = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'junior_buyer'

                    kwargs_header = {
                        'buying_controller__in': buying_controller_header,
                        'buyer__in': buyer_header
                    }


            if (kpi_type == 'Value'):
                total_ty = 'sales_ty'
                total_ly = 'sales_ly'
                no_pref = '£'
            elif (kpi_type == 'Volume'):
                total_ty = 'volume_ty'
                total_ly = 'volume_ly'
                no_pref = ''
            elif (kpi_type == 'COGS'):
                total_ty = 'cogs_ty'
                total_ly = 'cogs_ly'
                no_pref = '£'
            else:
                total_ty = 'cgm_ty'
                total_ly = 'cgm_ly'
                no_pref = '£'



            list_supp = {}

            def supp_calc(temp):
                try:
                    supp_share_denom = supplier_view.objects.filter(**kwargs_denom).aggregate(total_sum=Sum(total_ly))
                    supp_share_denom = supp_share_denom['total_sum']
                    supp_df = pd.DataFrame(temp)
                    supp_df['cont_to_grwth'] = (supp_df['grouped_ty'] - supp_df['grouped_ly']) * 100 / supp_share_denom
                    supp_df['grouped_ty'] = supp_df['grouped_ty'].astype(float)
                    supp_df['grouped_ly'] = supp_df['grouped_ly'].astype(float)
                    supp_df['cont_to_grwth'] = supp_df['cont_to_grwth'].astype(float).round(2)
                    supp_df = supp_df.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[False, False])

                    top_5_supp = supp_df
                    top_5_supp = top_5_supp.to_dict(orient='records')
                    supp_df = supp_df.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[True, True])
                    bot_5_supp = supp_df
                    bot_5_supp = bot_5_supp.to_dict(orient='records')
                    return top_5_supp

                except:
                    return 0

            temp = list(
                supplier_view.objects.filter(**kwargs).values('parent_supplier').annotate(grouped_ty=Sum(total_ty),
                                                                                          grouped_ly=Sum(total_ly)))

            top_5_supp = supp_calc(temp)
            top_5 = list(supplier_view.objects.filter(**kwargs).values('tesco_week').annotate(value_ty=Sum(total_ty),
                                                                                              value_ly=Sum(
                                                                                                  total_ly)).order_by(
                'tesco_week'))

            top_5 = pd.DataFrame(top_5)

            top_5['value_ty'] = top_5['value_ty'].astype(float)
            top_5['value_ly'] = top_5['value_ly'].astype(float)

            top_5_kpi_data = supplier_view.objects.filter(**kwargs).values(level).aggregate(value_ty=Sum(total_ty),
                                                                                            value_ly=Sum(total_ly))

            top_5_kpi_denom = supplier_view.objects.filter(**kwargs_denom).aggregate(value=Sum(total_ty))

            kpi_final = top_5_kpi_data
            kpi_denom = top_5_kpi_denom['value']
            try:
                sales_share = kpi_final['value_ty'] * 100 / kpi_denom
            except:
                sales_share = 0
            try:
                cont_to_grwth = ((kpi_final['value_ty'] - kpi_final['value_ly'])) * 100 / kpi_denom
            except:
                cont_to_grwth = 0
            try:
                yoy_var = ((kpi_final['value_ty'] - kpi_final['value_ly'])) * 100 / kpi_final['value_ly']
            except:
                yoy_var = 0

            sales_share = format(sales_share, '.1f')
            cont_to_grwth = format(cont_to_grwth, '.1f')
            yoy_var = format(yoy_var, '.1f')
            # kpi_final['sales_share'] = kpi_final['sales_share']
            # kpi_final['cont_to_grwth'] = kpi_final['cont_to_grwth']
            # kpi_final['yoy_var'] = kpi_final['yoy_var']

            print("kpi_final", kpi_final)
            # kpi_final = kpi_final.to_dict(orient="records")

            # multiline_label = pd.DataFrame({'label':top_5['tesco_week'].astype(str)})

            multiline_trend = pd.DataFrame({'value_ty': top_5['value_ty'].astype(float),
                                            'value_ly': top_5['value_ly'].astype(float),
                                            'tesco_week': top_5['tesco_week'].astype(str)})
            # multiline_ly = pd.DataFrame({'value':top_5['value_ly'].astype(float)})
            # multiline_label = multiline_label.to_dict(orient='records')
            # multiline_ty = multiline_ty.to_dict(orient='records')
            multiline_trend = multiline_trend.to_dict(orient='records')
            if (kpi_type == 'Value'):
                title = 'Value Performance'
                yaxis_title = 'Value'
                legend1 = 'Value TY'
                legend2 = 'Value LY'
            elif (kpi_type == 'Volume'):
                title = 'Volume Performance'
                yaxis_title = 'Volume'
                legend1 = 'Volume TY'
                legend2 = 'Volume LY'
            elif (kpi_type == 'COGS'):
                title = 'COGS Performance'
                yaxis_title = 'COGS'
                legend1 = 'COGS TY'
                legend2 = 'COGS LY'
            else:
                title = 'CGM Performance'
                yaxis_title = 'CGM'
                legend1 = 'CGM TY'
                legend2 = 'CGM LY'
            top_info = {'name': selected_level, 'multiline_trend': multiline_trend,
                        'kpi_type': kpi_type, 'topbot': 'top', 'title': title, 'yaxis_title': yaxis_title,
                        'legend1': legend1, 'legend2': legend2, 'sales_share': sales_share,
                        'cont_to_grwth': cont_to_grwth, 'yoy_var': yoy_var, 'no_pref': no_pref, 'fetch': 'success'}
            # top_chart_prod1 = top_list('sales_ty', 'sales_ly', 1).to_json(orient='index')
            # top_chart_prod1 = json.loads(top_chart_prod1)
            # except:
            #     top_info = {'fetch': 'fail'}
        else:
            print("entering else")
            top_info = {'fetch': 'fail'}
        logging.info(top_info)
        return JsonResponse(top_info, safe=False)

class WorstInfo(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)
        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)

        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        selected_level = args.get('selected_level__in', None)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if store_type is None:
            store_type = ['Main Estate', 'Express']

        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        if selected_level is not None:
            # if category_name is None:
            #     kwargs_products = {
            #     'buying_controller': 'Wines',
            #     'store_type__in': store_type
            #     }
            #     level = 'buyer'
            # elif buying_controller is None:
            #     kwargs_products = {
            #     'buying_controller': 'Wines',
            #     'store_type__in': store_type
            #     }
            #     level = 'buyer'
            if junior_buyer is not None:
                kwargs = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'product_subgroup__in': selected_level
                }
                kwargs_denom = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'product_subgroup'

            if buyer is not None:
                kwargs = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level
                }
                kwargs_denom = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'junior_buyer'
            if buying_controller is not None:
                kwargs = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'buyer__in': selected_level
                }
                kwargs_denom = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'buyer'

            else:

                if ((buyer_header is None) or buyer_header == ['']):
                    kwargs = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'buyer__in': selected_level
                    }
                    kwargs_denom = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'buyer'
                else:
                    kwargs = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'junior_buyer__in': selected_level
                    }
                    kwargs_denom = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'junior_buyer'

                    kwargs_header = {
                        'buying_controller__in': buying_controller_header,
                        'buyer__in': buyer_header
                    }

            # print('levelllllllllllllllllllll')
            # print(level)

            # if not args:
            #     products = sales_heirarchy.objects.filter(**kwargs_products).values('product_id').distinct()
            # else:
            #     products = sales_heirarchy.objects.filter(**kwargs_products).values('product_id').distinct()

            if (kpi_type == 'Value'):
                total_ty = 'sales_ty'
                total_ly = 'sales_ly'
                no_pref = '£'
            elif (kpi_type == 'Volume'):
                total_ty = 'volume_ty'
                total_ly = 'volume_ly'
                no_pref = ''
            elif (kpi_type == 'COGS'):
                total_ty = 'cogs_ty'
                total_ly = 'cogs_ly'
                no_pref = '£'
            else:
                total_ty = 'cgm_ty'
                total_ly = 'cgm_ly'
                no_pref = '£'

            list_supp = {}

            def supp_calc(temp):
                try:
                    supp_share_denom = supplier_view.objects.filter(**kwargs_denom).aggregate(total_sum=Sum(total_ly))
                    supp_share_denom = supp_share_denom['total_sum']
                    supp_df = pd.DataFrame(temp)
                    supp_df['cont_to_grwth'] = (supp_df['grouped_ty'] - supp_df['grouped_ly']) * 100 / supp_share_denom
                    supp_df['grouped_ty'] = supp_df['grouped_ty'].astype(float)
                    supp_df['grouped_ly'] = supp_df['grouped_ly'].astype(float)
                    supp_df['cont_to_grwth'] = supp_df['cont_to_grwth'].astype(float).round(2)
                    supp_df = supp_df.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[True, True])
                    bot_5_supp = supp_df
                    bot_5_supp = bot_5_supp.to_dict(orient='records')
                    return bot_5_supp
                except:
                    return 0

            print('kwargggggggggggggg')
            print(kwargs)
            temp = list(
                supplier_view.objects.filter(**kwargs).values('parent_supplier').annotate(grouped_ty=Sum(total_ty),
                                                                                          grouped_ly=Sum(total_ly)))
            bot_5_supp = supp_calc(temp)
            bot_5 = list(supplier_view.objects.filter(**kwargs).values('tesco_week').annotate(value_ty=Sum(total_ty),
                                                                                              value_ly=Sum(total_ly)))

            bot_5 = pd.DataFrame(bot_5)
            bot_5['value_ty'] = bot_5['value_ty'].astype(float)
            bot_5['value_ly'] = bot_5['value_ly'].astype(float)

            bot_5_kpi_data = supplier_view.objects.filter(**kwargs).aggregate(value_ty=Sum(total_ty),
                                                                              value_ly=Sum(total_ly))

            bot_5_kpi_denom = supplier_view.objects.filter(**kwargs_denom).aggregate(value=Sum(total_ty))
            try:
                sales_share = bot_5_kpi_data['value_ty'] * 100 / bot_5_kpi_denom['value']
            except:
                sales_share = 0
            try:
                cont_to_grwth = ((bot_5_kpi_data['value_ty'] - bot_5_kpi_data['value_ly'])) * 100 / bot_5_kpi_denom[
                    'value']
            except:
                cont_to_grwth = 0
            try:
                yoy_var = ((bot_5_kpi_data['value_ty'] - bot_5_kpi_data['value_ly'])) * 100 / bot_5_kpi_data['value_ly']
            except:
                yoy_var = 0
            sales_share = format(sales_share, '.1f')
            cont_to_grwth = format(cont_to_grwth, '.1f')
            yoy_var = format(yoy_var, '.1f')
            multiline_trend = pd.DataFrame({'value_ty': bot_5['value_ty'].astype(float),
                                            'value_ly': bot_5['value_ly'].astype(float),
                                            'tesco_week': bot_5['tesco_week'].astype(str)})
            # multiline_ly = pd.DataFrame({'value':top_5['value_ly'].astype(float)})
            # multiline_label = multiline_label.to_dict(orient='records')
            # multiline_ty = multiline_ty.to_dict(orient='records')
            multiline_trend = multiline_trend.to_dict(orient='records')
            if (kpi_type == 'Value'):
                title = 'Value Performance'
                yaxis_title = 'Value'
                legend1 = 'Value TY'
                legend2 = 'Value LY'
            elif (kpi_type == 'Volume'):
                title = 'Volume Performance'
                yaxis_title = 'Volume'
                legend1 = 'Volume TY'
                legend2 = 'Volume LY'
            elif (kpi_type == 'COGS'):
                title = 'COGS Performance'
                yaxis_title = 'COGS'
                legend1 = 'COGS TY'
                legend2 = 'COGS LY'
            else:
                title = 'CGM Performance'
                yaxis_title = 'CGM'
                legend1 = 'CGM TY'
                legend2 = 'CGM LY'
            bot_info = {'name': selected_level, 'multiline_trend': multiline_trend, 'bot_5_supp': bot_5_supp,
                        'kpi_type': kpi_type, 'topbot': 'bot', 'title': title, 'yaxis_title': yaxis_title,
                        'legend1': legend1, 'legend2': legend2, 'sales_share': sales_share,
                        'cont_to_grwth': cont_to_grwth, 'yoy_var': yoy_var, 'no_pref': no_pref, 'fetch': 'success'}
        else:
            bot_info = {
                'fetch': 'fail'
            }
        logging.info(bot_info)
        return JsonResponse(bot_info, safe=False)

class SupplierInfo(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)
        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)

        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        selected_level = args.get('selected_level__in', None)
        selected_supplier = args.get('selected_supplier__in', None)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)


        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        if junior_buyer is not None:
            kwargs_imp_categ = {
                'tesco_week__in': week,
                'product_subgroup__in': selected_level,
                'store_type__in': store_type
            }
            kwargs_numer = {
                'tesco_week__in': week,
                'product_subgroup__in': selected_level,
                'parent_supplier__in': selected_supplier,
                'store_type__in': store_type
            }
            level = 'product_subgroup'

        if buyer is not None:
            kwargs_imp_categ = {
                'tesco_week__in': week,
                'junior_buyer__in': selected_level,
                'store_type__in': store_type
            }
            kwargs_numer = {
                'tesco_week__in': week,
                'junior_buyer__in': selected_level,
                'parent_supplier__in': selected_supplier,
                'store_type__in': store_type
            }
            level = 'junior_buyer'

        if buying_controller is not None:

            kwargs_imp_categ = {
                'tesco_week__in': week,
                'buyer__in': selected_level,
                'store_type__in': store_type
            }
            kwargs_numer = {
                'tesco_week__in': week,
                'buyer__in': selected_level,
                'parent_supplier__in': selected_supplier,
                'store_type__in': store_type
            }
            level = 'buyer'

        else:

            if ((buyer_header is None) or buyer_header == ['']):
                kwargs_imp_categ = {
                    'tesco_week__in': week,
                    'buyer__in': selected_level,
                    'store_type__in': store_type
                }
                kwargs_numer = {
                    'tesco_week__in': week,
                    'buyer__in': selected_level,
                    'parent_supplier__in': selected_supplier,
                    'store_type__in': store_type

                }
                level = 'buyer'

            else:

                kwargs_imp_categ = {
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level,
                    'store_type__in': store_type
                }
                kwargs_numer = {
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level,
                    'parent_supplier__in': selected_supplier,
                    'store_type__in': store_type
                }
                level = 'junior_buyer'

        kwargs_imp_supp = {
            'tesco_week__in': week,
            'parent_supplier__in': selected_supplier,
            'store_type__in': store_type
        }

        # products = sales_heirarchy.objects.filter(**kwargs_products_selected).values('product_id').distinct()
        # products_supplier = sales_heirarchy.objects.filter(**kwargs_supplier_products).values('product_id').distinct()
        # products_supplier = sales_heirarchy.objects.filter(**kwargs_supplier).values('product_id').distinct()


        if (kpi_type == 'Value'):
            total_ty = 'sales_ty'
            total_ly = 'sales_ly'
        elif (kpi_type == 'Volume'):
            total_ty = 'volume_ty'
            total_ly = 'volume_ly'
        elif (kpi_type == 'COGS'):
            total_ty = 'cogs_ty'
            total_ly = 'cogs_ly'
        else:
            total_ty = 'cgm_ty'
            total_ly = 'cgm_ly'

        imp_supp_denom = supplier_view.objects.filter(**kwargs_imp_supp).aggregate(total_sum=Sum(total_ty))
        imp_supp_denom = imp_supp_denom['total_sum']
        imp_categ_denom = supplier_view.objects.filter(**kwargs_imp_categ).aggregate(total_sum=Sum(total_ty))
        imp_categ_denom = imp_categ_denom['total_sum']
        temp = supplier_view.objects.filter(**kwargs_numer).aggregate(grouped_ty=Sum(total_ty),
                                                                      grouped_ly=Sum(total_ly))
        try:
            imp_to_categ = float(temp['grouped_ty'] * 100 / imp_categ_denom)
        except:
            imp_to_categ = 0
        try:
            imp_to_supp = float(temp['grouped_ty'] * 100 / imp_supp_denom)
        except:
            imp_to_supp = 0
        # chart_id1 = week + kpi_type + topbot + 'chart_id1'
        # chart_id2 = week + kpi_type + topbot + 'chart_id2'


        sup_info_kpi_data = supplier_view.objects.filter(**kwargs_numer).aggregate(value_ty=Sum(total_ty),
                                                                                   value_ly=Sum(total_ly))

        sup_info_kpi_denom = supplier_view.objects.filter(**kwargs_imp_categ).aggregate(value=Sum(total_ty))

        try:
            sales_share = sup_info_kpi_data['value_ty'] * 100 / sup_info_kpi_denom['value']
        except:
            sales_share = 0
        try:
            cont_to_grwth = (sup_info_kpi_data['value_ty'] - sup_info_kpi_data['value_ly']) * 100 / sup_info_kpi_denom[
                'value']
        except:
            cont_to_grwth = 0
        try:
            yoy_var = (sup_info_kpi_data['value_ty'] - sup_info_kpi_data['value_ly']) * 100 / sup_info_kpi_data[
                'value_ly']
        except:
            yoy_var = 0
        sales_share = format(sales_share, '.1f')
        cont_to_grwth = format(cont_to_grwth, '.1f')
        yoy_var = format(yoy_var, '.1f')

        supp_info = {"imp_to_categ": imp_to_categ, "imp_to_supp": imp_to_supp, 'sales_share': sales_share,
                     'cont_to_grwth': cont_to_grwth, 'yoy_var': yoy_var, 'parent_supplier': selected_supplier}

        # supp_info = supp_info.to_json(orient='index')
        # supp_info = supp_info.loads(bot_info)
        logging.info(supp_info)
        return JsonResponse(supp_info, safe=False)

class DriversInternalView(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        category_name = args.get('category_name__in', ['Beers, Wines and Spirits'])
        junior_buyer = args.get('junior_buyer__in', None)
        buyer = args.get('buyer__in', None)
        buying_controller = args.get('buying_controller__in', None)
        print("Buying Controller ---------")
        print(buying_controller)
        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)
        lastyearweek = lastyearweek_selection(week)
        store_type = args.get('store_type__in', ['Main Estate', 'Express'])

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if junior_buyer is not None:
            transactions = 'junior_area_trx'
            value = 'junior_area_sales'
            volume = 'junior_area_volume'
            area = 'junior_area'
            kwargs_kpi = {
                'tesco_week__in': week,
                'junior_area__in': junior_buyer,
                'store_type__in': store_type
            }
            kwargs_kpi_ly = {
                'tesco_week__in': lastyearweek,
                'junior_area__in': junior_buyer,
                'store_type__in': store_type
            }
            kwargs_promo = {
                'tesco_week__in': week,
                'junior_area__in': junior_buyer,
            }

        elif buyer is not None:
            transactions = 'buyer_area_trx'
            value = 'buyer_area_sales'
            volume = 'buyer_area_volume'
            area = 'buyer_area'
            kwargs_kpi = {
                'tesco_week__in': week,
                'buyer_area__in': buyer,
                'store_type__in': store_type
            }
            kwargs_kpi_ly = {
                'tesco_week__in': lastyearweek,
                'buyer_area__in': buyer,
                'store_type__in': store_type
            }
            kwargs_promo = {
                'tesco_week__in': week,
                'buyer_area__in': buyer
            }
        elif buying_controller is not None:
            transactions = 'product_area_trx'
            value = 'product_area_sales'
            volume = 'product_area_volume'
            area = 'product_area'
            kwargs_kpi = {
                'tesco_week__in': week,
                'product_area__in': buying_controller,
                'store_type__in': store_type
            }
            kwargs_kpi_ly = {
                'tesco_week__in': lastyearweek,
                'product_area__in': buying_controller,
                'store_type__in': store_type
            }
            kwargs_promo = {
                'tesco_week__in': week,
                'product_area__in': buying_controller,
            }
        else:
            transactions = 'category_area_trx'
            value = 'category_area_sales'
            volume = 'category_area_volume'
            area = 'category_area'
            if ((buyer_header is None) or buyer_header == ['']):
                kwargs_kpi = {
                    'product_area__in': buying_controller_header,
                    'store_type__in': store_type,
                    'tesco_week__in': week
                }
                kwargs_kpi_ly = {
                    'product_area__in': buying_controller_header,
                    'store_type__in': store_type,
                    'tesco_week__in': lastyearweek
                }
                kwargs_promo = {
                    'tesco_week__in': week,
                    'product_area__in': buying_controller_header
                }
            else:
                kwargs_kpi = {
                    'product_area__in': buying_controller_header,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'buyer_area__in': buyer_header
                }
                kwargs_kpi_ly = {
                    'product_area__in': buying_controller_header,
                    'store_type__in': store_type,
                    'tesco_week__in': lastyearweek,
                    'buyer_area__in': buyer_header
                }
                kwargs_promo = {
                    'tesco_week__in': week,
                    'product_area__in': buying_controller_header,
                    'buyer_area__in': buyer_header
                }

        print("++++++++++++++++++++ kwargs for kpi")
        print(kwargs_kpi)
        print(kwargs_kpi_ly)


        if not args:
            products = sales_heirarchy.objects.filter(category_name='Beers, Wines and Spirits').values(
                'product_id').distinct()
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()

        kwargs = {
            'tesco_week__in': week,
            'product_id__in': products,
            'store_type__in': store_type
        }
        print('kwargs')
        print(kwargs)

        overview_trend = list(
            supplier_view.objects.filter(**kwargs).values("tesco_week").annotate(grouped_sales_ty=Sum('sales_ty'),
                                                                                 grouped_sales_ly=Sum('sales_ly'),
                                                                                 grouped_sales_lfl_ty=Sum(
                                                                                     'sales_ty_lfl'),
                                                                                 grouped_sales_lfl_ly=Sum(
                                                                                     'sales_ly_lfl')).order_by(
                'tesco_week').order_by('tesco_week'))

        overview_trend = pd.DataFrame(overview_trend)
        if (currentweek >= 201702):

            kpi_contri_lfl_sales_growth_trend = read_frame(
                executive_view.objects.filter(**kwargs_kpi).filter(tesco_week__gte=201703).values('tesco_week',area).annotate(trans = Sum(transactions),val=Sum(value),vol=Sum(volume)).distinct())

            kpi_contri_lfl_sales_growth_trend_ly = read_frame(
                executive_view.objects.filter(**kwargs_kpi_ly).filter(tesco_week__gte=201603).values('tesco_week',area).annotate(trans = Sum(transactions),val=Sum(value),vol=Sum(volume)).distinct())

            kpi_contri_lfl_sales_growth_trend_ly = kpi_contri_lfl_sales_growth_trend_ly.rename(columns={'trans': 'transaction_ly', 'val': 'value_ly', 'vol': 'volume_ly'})
            kpi_contri_lfl_sales_growth_trend = kpi_contri_lfl_sales_growth_trend.rename(columns={'trans': 'transaction', 'val': 'value', 'vol': 'volume'})

            print("kpi_contri_lfl_sales_growth_trend")
            print(kpi_contri_lfl_sales_growth_trend)
            print("kpi_contri_lfl_sales_growth_trend_ly")
            print(kpi_contri_lfl_sales_growth_trend_ly)

            try:
                kpi_contri_lfl_sales_growth_trend['items_per_basket'] = kpi_contri_lfl_sales_growth_trend['volume'] / \
                                                                        kpi_contri_lfl_sales_growth_trend['transaction']
            except:
                kpi_contri_lfl_sales_growth_trend['items_per_basket'] = 0

            try:
                kpi_contri_lfl_sales_growth_trend['items_per_basket_ly'] = kpi_contri_lfl_sales_growth_trend_ly[
                                                                               'volume_ly'] / \
                                                                           kpi_contri_lfl_sales_growth_trend_ly[
                                                                               'transaction_ly']
            except:
                kpi_contri_lfl_sales_growth_trend['items_per_basket_ly'] = 0
            try:
                kpi_contri_lfl_sales_growth_trend['item_price'] = kpi_contri_lfl_sales_growth_trend['value'] / \
                                                                  kpi_contri_lfl_sales_growth_trend['volume']
            except:
                kpi_contri_lfl_sales_growth_trend['item_price'] = 0
            try:
                kpi_contri_lfl_sales_growth_trend['item_price_ly'] = kpi_contri_lfl_sales_growth_trend_ly['value_ly'] / \
                                                                     kpi_contri_lfl_sales_growth_trend_ly['volume_ly']
            except:
                kpi_contri_lfl_sales_growth_trend['item_price_ly'] = 0
            try:
                kpi_contri_lfl_sales_growth_trend['transaction_ly'] = kpi_contri_lfl_sales_growth_trend_ly[
                    'transaction_ly']
            except:
                kpi_contri_lfl_sales_growth_trend['transaction_ly'] = 0
            kpi_contri_lfl_sales_growth_trend['item_price'] = kpi_contri_lfl_sales_growth_trend['item_price'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['items_per_basket'] = kpi_contri_lfl_sales_growth_trend[
                'items_per_basket'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['item_price_ly'] = kpi_contri_lfl_sales_growth_trend[
                'item_price_ly'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['items_per_basket_ly'] = kpi_contri_lfl_sales_growth_trend[
                'items_per_basket_ly'].fillna(0)

            try:
                kpi_contri_lfl_sales_growth_trend['transaction'] = kpi_contri_lfl_sales_growth_trend[
                    'transaction'].astype(float)
            except:
                kpi_contri_lfl_sales_growth_trend['transaction'] = 0
            try:
                kpi_contri_lfl_sales_growth_trend['transaction_ly'] = kpi_contri_lfl_sales_growth_trend[
                    'transaction_ly'].astype(float)
            except:
                kpi_contri_lfl_sales_growth_trend['transaction_ly'] = 0

            kpi_contri_lfl_sales_growth_trend['item_price'] = kpi_contri_lfl_sales_growth_trend['item_price'].astype(
                float)

            kpi_contri_lfl_sales_growth_trend['item_price_ly'] = kpi_contri_lfl_sales_growth_trend[
                'item_price_ly'].astype(float)

            kpi_contri_lfl_sales_growth_trend['items_per_basket'] = kpi_contri_lfl_sales_growth_trend[
                'items_per_basket'].astype(float)

            kpi_contri_lfl_sales_growth_trend['items_per_basket_ly'] = kpi_contri_lfl_sales_growth_trend[
                'items_per_basket_ly'].astype(float)

            # try:
            kpi_contri_lfl_sales_growth_trend['transaction_var'] = (kpi_contri_lfl_sales_growth_trend[
                                                                        'transaction'] -
                                                                    kpi_contri_lfl_sales_growth_trend_ly[
                                                                        'transaction_ly']) * 100 / \
                                                                   kpi_contri_lfl_sales_growth_trend_ly[
                                                                       'transaction_ly']
            # except:
            #     kpi_contri_lfl_sales_growth_trend['transaction_var'] = 0
            # try:
            kpi_contri_lfl_sales_growth_trend['item_price_var'] = (kpi_contri_lfl_sales_growth_trend['item_price'] -
                                                                       kpi_contri_lfl_sales_growth_trend[
                                                                           'item_price_ly']) * 100 / \
                                                                      kpi_contri_lfl_sales_growth_trend['item_price_ly']
            # except:
            #     kpi_contri_lfl_sales_growth_trend['item_price_var'] = 0

            # try:
            kpi_contri_lfl_sales_growth_trend['items_per_basket_var'] = (kpi_contri_lfl_sales_growth_trend[
                                                                                 'items_per_basket'] -
                                                                             kpi_contri_lfl_sales_growth_trend[
                                                                                 'items_per_basket_ly']) * 100 / \
                                                                            kpi_contri_lfl_sales_growth_trend[
                                                                                'items_per_basket_ly']
            # except:
            #     kpi_contri_lfl_sales_growth_trend['items_per_basket_var'] = 0
            kpi_contri_lfl_sales_growth_trend['transaction_var'] = kpi_contri_lfl_sales_growth_trend[
                'transaction_var'].astype(float)

            kpi_contri_lfl_sales_growth_trend['item_price_var'] = kpi_contri_lfl_sales_growth_trend[
                'item_price_var'].astype(float)

            kpi_contri_lfl_sales_growth_trend['items_per_basket_var'] = kpi_contri_lfl_sales_growth_trend[
                'items_per_basket_var'].astype(float)
            try:
                kpi_contri_lfl_sales_growth_trend['total_growth'] = (kpi_contri_lfl_sales_growth_trend[
                                                                            'value'] -
                                                                        kpi_contri_lfl_sales_growth_trend_ly[
                                                                            'value_ly']) * 100 / \
                                                                       kpi_contri_lfl_sales_growth_trend_ly[
                                                                           'value_ly']
            except:
                kpi_contri_lfl_sales_growth_trend['total_growth'] = 0
            kpi_contri_lfl_sales_growth_trend['total_growth'] = kpi_contri_lfl_sales_growth_trend[
                'total_growth'].astype(float)

            kpi_contri_lfl_sales_growth_trend['total_growth'] = kpi_contri_lfl_sales_growth_trend[
                'total_growth'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['transaction_var'] = kpi_contri_lfl_sales_growth_trend[
                'transaction_var'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['items_per_basket_var'] = kpi_contri_lfl_sales_growth_trend[
                'items_per_basket_var'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['item_price_var'] = kpi_contri_lfl_sales_growth_trend[
                'item_price_var'].fillna(0)

            kpi_contri_lfl_sales_growth_trend['tesco_week'] = kpi_contri_lfl_sales_growth_trend['tesco_week'].astype(
                str)

            kpi_contri_lfl_sales_growth_trend = kpi_contri_lfl_sales_growth_trend.drop(
                ['transaction', 'transaction_ly', 'items_per_basket', 'items_per_basket_ly', 'item_price',
                 'item_price_ly', 'value', 'volume'], axis=1)

            kpi_contri_lfl_sales_growth_trend = kpi_contri_lfl_sales_growth_trend.replace([np.inf, -np.inf], np.nan)

            kpi_contri_lfl_sales_growth_trend = kpi_contri_lfl_sales_growth_trend.fillna(0)

            kpi_contri_lfl_sales_growth_trend = kpi_contri_lfl_sales_growth_trend.to_dict(orient='records')

            data_available_flag = 'yes'


        else:

            data_available_flag = 'no'

            kpi_contri_lfl_sales_growth_trend = 0

        promo_contri_lfl_sales_growth = list(
            promo_contribution.objects.filter(**kwargs_promo).values('tesco_week').annotate(
                grouped_trade_plan_sales_ty=Sum('trade_plan_sales_ty'),
                grouped_trade_plan_sales_ly=Sum('trade_plan_sales_ly'), grouped_event_sales_ty=Sum('event_sales_ty'),
                grouped_event_sales_ly=Sum('event_sales_ly'), grouped_fs_sales_ty=Sum('fs_sales_ty'),
                grouped_fs_sales_ly=Sum('fs_sales_ly'), grouped_shelf_sales_ty=Sum('shelf_promo_sales_ty'),
                grouped_shelf_sales_ly=Sum('shelf_promo_sales_ly'), grouped_base_sales_ty=Sum('base_sales_ty'),
                grouped_base_sales_ly=Sum('base_sales_ly')).order_by('tesco_week'))
        promo_contri_lfl_sales_growth_trend = pd.DataFrame(promo_contri_lfl_sales_growth)

        try:
            promo_contri_lfl_sales_growth_trend['grouped_sales_ty'] = promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_event_sales_ty'] + \
                                                                      promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_fs_sales_ty'] + \
                                                                      promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_base_sales_ty'] + \
                                                                      promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_shelf_sales_ty']
        except:
            promo_contri_lfl_sales_growth_trend['grouped_sales_ty'] = 0

        try:
            promo_contri_lfl_sales_growth_trend['grouped_sales_ly'] = promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_event_sales_ly'] + \
                                                                      promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_fs_sales_ly'] + \
                                                                      promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_base_sales_ly'] + \
                                                                      promo_contri_lfl_sales_growth_trend[
                                                                          'grouped_shelf_sales_ly']
        except:
            promo_contri_lfl_sales_growth_trend['grouped_sales_ly'] = 0
        try:
            promo_contri_lfl_sales_growth_trend['sales_var'] = (overview_trend['grouped_sales_ty'] - overview_trend[
                'grouped_sales_ly']) * 100 / overview_trend['grouped_sales_ly']
        except:
            promo_contri_lfl_sales_growth_trend['sales_var'] = 0


        try:
            promo_contri_lfl_sales_growth_trend['trade_plan_cont_to_growth'] = (promo_contri_lfl_sales_growth_trend[
                                                                                    'grouped_trade_plan_sales_ty'] -
                                                                                promo_contri_lfl_sales_growth_trend[
                                                                                    'grouped_trade_plan_sales_ly']) * 100 / \
                                                                               promo_contri_lfl_sales_growth_trend[
                                                                                   'grouped_sales_ly']
            promo_contri_lfl_sales_growth_trend['event_cont_to_growth'] = (promo_contri_lfl_sales_growth_trend[
                                                                               'grouped_event_sales_ty'] -
                                                                           promo_contri_lfl_sales_growth_trend[
                                                                               'grouped_event_sales_ly']) * 100 / \
                                                                          promo_contri_lfl_sales_growth_trend[
                                                                              'grouped_sales_ly']
            promo_contri_lfl_sales_growth_trend['fs_cont_to_growth'] = (promo_contri_lfl_sales_growth_trend[
                                                                            'grouped_fs_sales_ty'] -
                                                                        promo_contri_lfl_sales_growth_trend[
                                                                            'grouped_fs_sales_ly']) * 100 / \
                                                                       promo_contri_lfl_sales_growth_trend[
                                                                           'grouped_sales_ly']
            promo_contri_lfl_sales_growth_trend['shelf_cont_to_growth'] = (promo_contri_lfl_sales_growth_trend[
                                                                               'grouped_shelf_sales_ty'] -
                                                                           promo_contri_lfl_sales_growth_trend[
                                                                               'grouped_shelf_sales_ly']) * 100 / \
                                                                          promo_contri_lfl_sales_growth_trend[
                                                                              'grouped_sales_ly']
            promo_contri_lfl_sales_growth_trend['base_cont_to_growth'] = (promo_contri_lfl_sales_growth_trend[
                                                                              'grouped_base_sales_ty'] -
                                                                          promo_contri_lfl_sales_growth_trend[
                                                                              'grouped_base_sales_ly']) * 100 / \
                                                                         promo_contri_lfl_sales_growth_trend[
                                                                             'grouped_sales_ly']
            promo_contri_lfl_sales_growth_trend['total_growth'] = (promo_contri_lfl_sales_growth_trend['grouped_sales_ty'] -
                                                                   promo_contri_lfl_sales_growth_trend[
                                                                       'grouped_sales_ly']) * 100 / \
                                                                  promo_contri_lfl_sales_growth_trend['grouped_sales_ly']

            promo_contri_lfl_sales_growth_trend['trade_plan_cont_to_growth'] = promo_contri_lfl_sales_growth_trend[
                'trade_plan_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['event_cont_to_growth'] = promo_contri_lfl_sales_growth_trend[
                'event_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['fs_cont_to_growth'] = promo_contri_lfl_sales_growth_trend[
                'fs_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['base_cont_to_growth'] = promo_contri_lfl_sales_growth_trend[
                'shelf_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['base_cont_to_growth'] = promo_contri_lfl_sales_growth_trend[
                'base_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['total_growth'] = promo_contri_lfl_sales_growth_trend[
                'total_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['tesco_week'] = promo_contri_lfl_sales_growth_trend['tesco_week'].astype(
                str)

        except:
            promo_contri_lfl_sales_growth_trend['trade_plan_cont_to_growth'] = 0
            promo_contri_lfl_sales_growth_trend['trade_plan_cont_to_growth'] = promo_contri_lfl_sales_growth_trend['trade_plan_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['event_cont_to_growth'] = 0
            promo_contri_lfl_sales_growth_trend['event_cont_to_growth'] = promo_contri_lfl_sales_growth_trend['event_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['fs_cont_to_growth'] = 0
            promo_contri_lfl_sales_growth_trend['fs_cont_to_growth'] = promo_contri_lfl_sales_growth_trend['fs_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['base_cont_to_growth'] = 0
            promo_contri_lfl_sales_growth_trend['base_cont_to_growth'] = promo_contri_lfl_sales_growth_trend['base_cont_to_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['total_growth'] = 0
            promo_contri_lfl_sales_growth_trend['total_growth'] = promo_contri_lfl_sales_growth_trend['total_growth'].astype(float)
            promo_contri_lfl_sales_growth_trend['tesco_week'] = 0
            promo_contri_lfl_sales_growth_trend['tesco_week'] = promo_contri_lfl_sales_growth_trend['tesco_week'].astype(str)
            promo_contri_lfl_sales_growth_trend['shelf_cont_to_growth'] = 0
            promo_contri_lfl_sales_growth_trend['shelf_cont_to_growth'] = promo_contri_lfl_sales_growth_trend['shelf_cont_to_growth'].astype(float)


        promo_contri_lfl_sales_growth_trend = promo_contri_lfl_sales_growth_trend.drop(
            ['trade_plan_cont_to_growth', 'grouped_base_sales_ly', 'grouped_base_sales_ty', 'grouped_event_sales_ly',
             'grouped_event_sales_ty', 'grouped_fs_sales_ly', 'grouped_fs_sales_ty', 'grouped_shelf_sales_ly',
             'grouped_shelf_sales_ty', 'grouped_trade_plan_sales_ly', 'grouped_trade_plan_sales_ty', 'grouped_sales_ty',
             'grouped_sales_ly', 'sales_var'], axis=1)

        promo_contri_lfl_sales_growth_trend = promo_contri_lfl_sales_growth_trend.to_dict(orient='records')
        # print("____________________ promo_contri_lfl_sales_growth_trend")
        # print(promo_contri_lfl_sales_growth_trend)
        contri_lfl_sales_growth_trend = {}
        contri_lfl_sales_growth_trend['kpi_data_available_flag'] = data_available_flag
        contri_lfl_sales_growth_trend['kpi'] = kpi_contri_lfl_sales_growth_trend
        contri_lfl_sales_growth_trend['promo'] = promo_contri_lfl_sales_growth_trend
        contri_lfl_sales_growth_trend['promo_legend_label'] = ['Event Sales Growth', 'Feature Space Growth',
                                                               'Shelf Sales Growth', 'Base Sales Growth',
                                                               'Sales Growth']
        contri_lfl_sales_growth_trend['promo_col_label'] = ['event_cont_to_growth', 'fs_cont_to_growth',
                                                            'base_cont_to_growth', 'shelf_cont_to_growth']

        contri_lfl_sales_growth_trend['kpi_legend_label'] = ['Transaction Variation', 'Items Per Basket Variation',
                                                             'Item Price Variation', 'Sales Variation']
        contri_lfl_sales_growth_trend['kpi_col_label'] = ['Transaction', 'Item per basket', 'Item price', 'Sales']
        # print("____________________ contri_lfl_sales_growth_trend")
        # print(contri_lfl_sales_growth_trend)
        logging.info(contri_lfl_sales_growth_trend)
        return JsonResponse(contri_lfl_sales_growth_trend, safe=False)

class DriversExternalView(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # print(args)
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)

        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'tesco_week__in': week
        }
        kwargslw = {
            'tesco_week': lastweek
        }

        lastyearweek = lastyearweek_selection(week)

        weather_data = list(
            weather_weekly_details.objects.filter(tesco_week__in=week).values('tesco_week', 'rainfall_weekly_avg',
                                                                              'sunshine_weekly_avg',
                                                                              'temperature_weekly_avg').order_by(
                'tesco_week'))

        weather_data_ly = list(weather_weekly_details.objects.filter(tesco_week__in=lastyearweek).values('tesco_week',
                                                                                                         'rainfall_weekly_avg',
                                                                                                         'sunshine_weekly_avg',
                                                                                                         'temperature_weekly_avg').order_by(
            'tesco_week'))

        overview_trend = list(
            supplier_view.objects.filter(**kwargs).values('tesco_week').annotate(grouped_sales_ly=Sum('sales_ly'),
                                                                                 grouped_sales_ty=Sum('sales_ty'),
                                                                                 grouped_volume_ly=Sum('volume_ly'),
                                                                                 grouped_volume_ty=Sum('sales_ty'),
                                                                                 grouped_cogs_ly=Sum('cogs_ly'),
                                                                                 grouped_cogs_ty=Sum('cogs_ty'),
                                                                                 grouped_profit_ly=Sum('cgm_ly'),
                                                                                 grouped_profit_ty=Sum(
                                                                                     'cgm_ty')).order_by('tesco_week'))
        rainfall_ty = []
        rainfall_ly = []
        sunshine_ty = []
        sunshine_ly = []
        temp_ty = []
        temp_ly = []
        sales_ty = []
        sales_ly = []

        for i in range(0, len(weather_data)):
            rainfall_ty.insert(i, weather_data[i]['rainfall_weekly_avg'])
            rainfall_ly.insert(i, weather_data_ly[i]['rainfall_weekly_avg'])
            sunshine_ty.insert(i, weather_data[i]['sunshine_weekly_avg'])
            sunshine_ly.insert(i, weather_data_ly[i]['sunshine_weekly_avg'])
            temp_ty.insert(i, weather_data[i]['temperature_weekly_avg'])
            temp_ly.insert(i, weather_data_ly[i]['temperature_weekly_avg'])
            sales_ty.insert(i, overview_trend[i]['grouped_sales_ty'])
            sales_ly.insert(i, overview_trend[i]['grouped_sales_ly'])

        weather_sunshine = pd.DataFrame(weather_data)
        weather_sunshine['tesco_week'] = weather_sunshine['tesco_week'].astype(str)
        weather_sunshine['avg_ty'] = sunshine_ty
        weather_sunshine['avg_ly'] = sunshine_ly
        weather_sunshine['value_ty'] = sales_ty
        weather_sunshine['value_ly'] = sales_ly

        weather_sunshine = weather_sunshine.to_json(orient='records')
        weather_sunshine = json.loads(weather_sunshine)

        weather_rainfall = pd.DataFrame(weather_data)
        weather_rainfall['tesco_week'] = weather_rainfall['tesco_week'].astype(str)
        weather_rainfall['avg_ty'] = rainfall_ty
        weather_rainfall['avg_ly'] = rainfall_ly
        weather_rainfall['value_ty'] = sales_ty
        weather_rainfall['value_ly'] = sales_ly
        weather_rainfall = weather_rainfall.to_json(orient='records')
        weather_rainfall = json.loads(weather_rainfall)

        weather_temperature = pd.DataFrame(weather_data)
        weather_temperature['tesco_week'] = weather_temperature['tesco_week'].astype(str)
        weather_temperature['avg_ty'] = temp_ty
        weather_temperature['avg_ly'] = temp_ly
        weather_temperature['value_ty'] = sales_ty
        weather_temperature['value_ly'] = sales_ly
        weather_temperature = weather_temperature.to_json(orient='records')
        weather_temperature = json.loads(weather_temperature)

        weather = {}
        weather["sunshine"] = weather_sunshine
        weather["rainfall"] = weather_rainfall
        weather["temperature"] = weather_temperature

        chart_flag = 1
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'tesco_week__in': week
        }

        holidays_trend = list(
            uk_holidays.objects.filter(**kwargs).values('tesco_week', 'holiday_date', 'holiday_description').distinct())

        for i in range(0, len(holidays_trend)):
            holidays_trend[i]['holiday_date'] = str(holidays_trend[i]['holiday_date'])

        if (holidays_trend == []):
            holidays_trend = pd.DataFrame(columns=('holiday_date', 'holiday_description'))
            for i in range(1):
                holidays_trend.loc[i] = ['------', 'No holidays for the selected time period']
            holidays_trend['holiday_date'] = '-----'
            holidays_trend['holiday_description'] = 'No holidays for the selected time period'
            holidays_trend = holidays_trend.to_dict(orient='records')

        weather['holidays'] = holidays_trend
        logging.info(weather)
        return JsonResponse(weather, safe=False)

class Pricing(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]
        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)

        category_name = args.get('category_name__in', ['Beers, Wines and Spirits'])

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if ((buyer_header is None) or buyer_header == ['']):
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        if not args:
            product_id = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_id').distinct()
            productsubgroup = sales_heirarchy.objects.filter(**kwargs_header).values(
                'product_subgroup').distinct()
        else:
            product_id = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
            productsubgroup = sales_heirarchy.objects.filter(**args).values('product_subgroup').distinct()

        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'product_id__in': product_id,
            'tesco_week__in': week,
            'store_type__in': store_type
        }

        kwargs_lw = {
            'product_id__in': product_id,
            'tesco_week': lastweek,
            'store_type__in': store_type
        }

        kwargs_pi = {
            'product_subgroup__in': productsubgroup,
            'tesco_week__in': week
        }
        kwargs_pi_lw = {
            'product_subgroup__in': productsubgroup,
            'tesco_week': lastweek
        }

        current_week_data = supplier_view.objects.filter(**kwargs).aggregate(sales_cw=Sum('sales_ty'),
                                                                   sales_cw_ly=Sum('sales_ly'),
                                                                   cogs_cw=Sum('cogs_ty'),
                                                                   cogs_cw_ly=Sum('cogs_ly'),
                                                                   volume_cw=Sum('volume_ty'),
                                                                   volume_cw_ly=Sum('volume_ly'),
                                                                   cgm_cw=Sum('cgm_ty'),
                                                                   cgm_cw_ly=Sum('cgm_ly'),
                                                                   volume_cw_lfl=Sum('volume_ty_lfl'),
                                                                   volume_cw_lfl_ly=Sum('volume_ly_lfl'),
                                                                   cogs_cw_lfl=Sum('cogs_ty_lfl'),
                                                                   cogs_cw_lfl_ly=Sum('cogs_ly_lfl'),
                                                                   cgm_cw_lfl=Sum('cgm_ty_lfl'),
                                                                   cgm_cw_lfl_ly=Sum('cgm_ly_lfl'),
                                                                   sales_cw_lfl=Sum('sales_ty_lfl'),
                                                                   sales_cw_lfl_ly=Sum('sales_ly_lfl')
                                                                   )

        last_week_data = supplier_view.objects.filter(**kwargs_lw).aggregate(sales_lw=Sum('sales_ty'),
                                                                      cogs_lw=Sum('cogs_ty'),
                                                                      volume_lw=Sum('volume_ty'),
                                                                      cgm_lw=Sum('cgm_ty'))

        fisher_inflation_data = executive_inflation.objects.filter(**kwargs).aggregate(
            final_ly_qty_ty_price=Sum('final_ly_qty_ty_price'), final_infl_sales_ly=Sum('final_infl_sales_ly'),
            final_infl_sales_ty=Sum('final_infl_sales_ty'), final_ty_qty_ly_price=Sum('final_ty_qty_ly_price'),
            final_ly_qty_ty_cogs=Sum('final_ly_qty_ty_cogs'), final_infl_cogs_ly=Sum('final_infl_cogs_ly'),
            final_infl_cogs_ty=Sum('final_infl_cogs_ty'), final_ty_qty_ly_cogs=Sum('final_ty_qty_ly_cogs'))
        print('FISHER INFLATION ----------')
        print(fisher_inflation_data)
        index_cw_data = executive_price_index.objects.filter(**kwargs_pi).aggregate(
            derived_sales=Sum('total_derived_sales'), tesco_sales=Sum('total_tesco_sales'))

        index_lw_data = executive_price_index.objects.filter(**kwargs_pi_lw).aggregate(
            derived_sales=Sum('total_derived_sales'), tesco_sales=Sum('total_tesco_sales'))


        # try:
        ASP_fisher_infl =  ((math.sqrt(abs((100+((((fisher_inflation_data['final_ly_qty_ty_price']-fisher_inflation_data['final_infl_sales_ly'])/fisher_inflation_data['final_infl_sales_ly'])*100)))*(100+((((fisher_inflation_data['final_infl_sales_ty']-fisher_inflation_data['final_ty_qty_ly_price'])/fisher_inflation_data['final_ty_qty_ly_price'])*100))))))-100)/100

        ACP_fisher_infl = ((math.sqrt(abs((100+((((fisher_inflation_data['final_ly_qty_ty_cogs']-fisher_inflation_data['final_infl_cogs_ly'])/fisher_inflation_data['final_infl_cogs_ly'])*100)))*(100+((((fisher_inflation_data['final_infl_cogs_ty']-fisher_inflation_data['final_ty_qty_ly_cogs'])/fisher_inflation_data['final_ty_qty_ly_cogs'])*100))))))-100)/100

        # except:
        #
        #     ASP_fisher_infl = 0
        #     ACP_fisher_infl = 0

        try:
            ACP_cw = format(current_week_data['cogs_cw'] / current_week_data['volume_cw'], '.1f')
            ACP_abs = '£' + ACP_cw
            ACP_lfl_cw = format(current_week_data['cogs_cw_lfl'] / current_week_data['volume_cw_lfl'], '.1f')
            ACP_lfl_abs ='£' + ACP_lfl_cw

        except:

            ACP_abs = 0
            ACP_lfl_abs = 0
        ##print(######### ACP INFL ##########)

        ACPInfl_var_yoy = var_calc((current_week_data['cogs_cw'] / current_week_data['volume_cw']),(current_week_data['cogs_cw_ly'] / current_week_data['volume_cw_ly']))
        ACPInfl_var_lfl = var_calc((current_week_data['cogs_cw_lfl'] / current_week_data['volume_cw_lfl']),(current_week_data['cogs_cw_lfl_ly'] / current_week_data['volume_cw_lfl_ly']))
        ACPInfl_var_wow = var_calc((current_week_data['cogs_cw'] / current_week_data['volume_cw']),(last_week_data['cogs_lw'] / last_week_data['volume_lw']))

        ##print(######### ACP Fisher INFL ########)
        ##print(######### ASP #############)
        try:
            ASP_cw = format(current_week_data['sales_cw'] / current_week_data['volume_cw'], '.1f')
            ASP_abs = '£' + ASP_cw
            ASP_lfl_cw = format(current_week_data['sales_cw_lfl'] / current_week_data['volume_cw_lfl'], '.1f')
            ASP_lfl_abs = '£' + ASP_lfl_cw

        except:
            ASP_abs = 0
            ASP_lfl_abs = 0


        ASPInfl_var_yoy = var_calc((current_week_data['sales_cw'] / current_week_data['volume_cw']),(current_week_data['sales_cw_ly'] / current_week_data['volume_cw_ly']))
        ASPInfl_var_lfl = var_calc((current_week_data['sales_cw_lfl'] / current_week_data['volume_cw_lfl']),(current_week_data['sales_cw_lfl_ly'] / current_week_data['volume_cw_lfl_ly']))
        ASPInfl_var_wow = var_calc((current_week_data['sales_cw'] / current_week_data['volume_cw']),(last_week_data['sales_lw'] / last_week_data['volume_lw']))

        try:
            price_index_cw = index_cw_data['derived_sales'] * 100 / index_cw_data['tesco_sales']
            price_index_lw = index_lw_data['derived_sales'] * 100 / index_cw_data['tesco_sales']
            price_index_var_wow = (price_index_cw - price_index_lw) * 100 / price_index_lw
            price_index_var_wow = format(price_index_var_wow, '.1f')
        except:
            price_index_cw = 0
            price_index_lw = 0
            price_index_var_wow = 0
        price_index_cw = format(price_index_cw, '.1f')
        line_count = 56
        print('ASP_fisher_infl')
        print(ASP_fisher_infl)
        print('ACP_fisher_infl')
        print(ACP_fisher_infl)
        ASP_fisher_infl = format(ASP_fisher_infl, '.1f')
        ACP_fisher_infl = format(ACP_fisher_infl, '.1f')
        data = {'price_index_cw': float(price_index_cw),
                'price_index_var_wow': float(price_index_var_wow),
                'line_count': line_count,
                'ASP_abs': ASP_abs,
                'ASP_lfl_abs': ASP_lfl_abs,
                'ASPInfl_var_yoy': float(ASPInfl_var_yoy),
                'ASPInfl_var_lfl': float(ASPInfl_var_lfl),
                'ASPInfl_var_wow': float(ASPInfl_var_wow),
                'ACP_abs': ACP_abs,
                'ACP_lfl_abs': ACP_lfl_abs,
                'ACPInfl_var_yoy': float(ACPInfl_var_yoy),
                'ACPInfl_var_lfl': float(ACPInfl_var_lfl),
                'ACPInfl_var_wow': float(ACPInfl_var_wow),
                'ASP_fisher_infl': float(ASP_fisher_infl),
                'ACP_fisher_infl': float(ACP_fisher_infl),
                }
        logging.info(data)
        return JsonResponse(data, safe=False)

class Holidays(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]

        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        chart_flag = 0
        week = week_selection(currentweek, week_flag, chart_flag)

        kwargs = {
            'tesco_week__in': week
        }

        holidays_trend = list(
            uk_holidays.objects.filter(**kwargs).values('tesco_week', 'holiday_date', 'holiday_description'))

        for i in range(0, len(holidays_trend)):
            holidays_trend[i]['holiday_date'] = str(holidays_trend[i]['holiday_date'])

        if (holidays_trend == []):
            holidays_trend = pd.DataFrame(columns=('holiday_date', 'holiday_description'))
            for i in range(1):
                holidays_trend.loc[i] = ['------', 'No holidays for the selected time period']
            holidays_trend['holiday_date'] = '-----'
            holidays_trend['holiday_description'] = 'No holidays for the selected time period'
            holidays_trend = holidays_trend.to_dict(orient='records')
        logging.info(holidays_trend)
        return JsonResponse(holidays_trend, safe=False)

class executive_best_worst_performance(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)

        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)
        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        product_subgroup = args.get('product_subgroup__in', None)
        selected_level = args.get('selected_level__in', None)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if product_subgroup is not None:
            junior_buyer = sales_heirarchy.objects.filter(product_subgroup__in=product_subgroup).values('junior_buyer').distinct()

        if selected_level is None:
            chart_flag = 0
            week = week_selection(currentweek, week_flag, chart_flag)
            if ((junior_buyer is not None) or (product_subgroup is not None)):
                kwargs = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,

                }
                kwargs_denom = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'product_subgroup'
                level_of = 'Product Subgroup'
                rolled_up = 'junior_buyer'
                rolled_up_of = 'Junior Buyer'

            elif buyer is not None:
                kwargs = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,

                }
                kwargs_denom = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'junior_buyer'
                level_of = 'Junior Buyer'
                rolled_up = 'buyer'
                rolled_up_of = 'Buyer'

            elif buying_controller is not None:
                kwargs = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,

                }
                kwargs_denom = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'buyer'
                level_of = 'Buyer'
                rolled_up = 'buying_controller'
                rolled_up_of = 'Buying Controller'
            else:

                if (buyer_header is None):
                    kwargs = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week
                    }
                    kwargs_denom = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'buyer'
                    level_of = 'Buyer'
                    rolled_up = 'buying_controller'
                    rolled_up_of = 'Buying Controller'
                else:
                    kwargs = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week
                    }
                    kwargs_denom = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'junior_buyer'
                    level_of = 'Junior Buyer'
                    rolled_up = 'buyer'
                    rolled_up_of = 'Buyer'


                    kwargs_header = {
                        'buying_controller__in': buying_controller_header,
                        'buyer__in': buyer_header
                    }


            if (kpi_type == 'Value'):
                total_ty = 'sales_ty'
                total_ly = 'sales_ly'
                no_pref = '£'
            elif (kpi_type == 'Volume'):
                total_ty = 'volume_ty'
                total_ly = 'volume_ly'
                no_pref = ''
            elif (kpi_type == 'COGS'):
                total_ty = 'cogs_ty'
                total_ly = 'cogs_ly'
                no_pref = '£'
            else:
                total_ty = 'cgm_ty'
                total_ly = 'cgm_ly'
                no_pref = '£'
            rolled_up_level_data = read_frame(supplier_view.objects.filter(**kwargs).values(level,rolled_up).distinct())

            top_kpi =read_frame(supplier_view.objects.filter(**kwargs).values(level).annotate(value_ty=Sum(total_ty),
                                                                                         value_ly=Sum(total_ly)))
            top_kpi_data = pd.merge(top_kpi,rolled_up_level_data, how='left', on=[level])
            top_kpi_denom = read_frame(supplier_view.objects.filter(**kwargs_denom).values(rolled_up).annotate(value=Sum(total_ty)))
            top_kpi_denom['rolled_up'] = top_kpi_denom[rolled_up]
            kpi_final = top_kpi_data
            kpi_final['level'] = kpi_final[level]
            kpi_final['rolled_up_level'] = kpi_final[rolled_up]

            def sales_share_calc(row):
                rolled_up_name = row[rolled_up]
                kpi_denom = top_kpi_denom.loc[top_kpi_denom['rolled_up'] == rolled_up_name]
                kpi_denom = float(kpi_denom['value'])
                if (kpi_denom > 0):
                    try:
                        a = (float(row['value_ty'])*100/kpi_denom)
                        a = float(format(a,'.1f'))
                    except:
                        a = 0
                    return a
                else:
                    a = 'NA'
                    return str(a)

            def cont_to_grwth_calc(row):
                rolled_up_name = row[rolled_up]
                kpi_denom = top_kpi_denom.loc[top_kpi_denom['rolled_up'] == rolled_up_name]
                kpi_denom = float(kpi_denom['value'])
                if (row['value_ly'] > 0):
                    a = (float(row['value_ty']-row['value_ly'])*100 / kpi_denom)
                    a = float(format(a,'.1f'))
                    return a
                else:
                    a = 'NA'
                    return str(a)

            try:
                kpi_final['sales_share'] = kpi_final.apply(sales_share_calc, axis=1)
            except:
                kpi_final['sales_share'] = 0

            try:
                kpi_final['cont_to_grwth'] = kpi_final.apply(cont_to_grwth_calc, axis=1)
            except:
                kpi_final['cont_to_grwth'] = 0

            try:
                kpi_final['yoy_var'] = ((kpi_final['value_ty'] - kpi_final['value_ly'])) * 100 / kpi_final['value_ly']
            except:
                kpi_final['yoy_var'] = 0

            kpi_final['value_ly'] = kpi_final['value_ly'].astype('float').round(decimals=2)
            kpi_final['value_ty'] = kpi_final['value_ty'].astype('float').round(decimals=2)
            kpi_final['yoy_var'] = kpi_final['yoy_var'].astype('float').round(decimals=1)
            kpi_final['index'] = range(0, len(kpi_final))
            kpi_final['key'] = range(0, len(kpi_final))
            kpi_final = kpi_final.rename(columns={level: 'level_name'})
            kpi_final = kpi_final.sort(['value_ty'], ascending=[0])
            kpi_final = kpi_final.to_dict(orient="records")
            data = {}
            data['table_data'] = kpi_final
            data['kpi_type'] = kpi_type
            data['level'] = level_of
            data['rolled_up_level'] = rolled_up_of

        else:
            print("entering else")
            data = {'fetch': 'fail'}
        logging.info(data)
        return JsonResponse(data, safe=False)

class exec_selected_level_performance(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)

        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)

        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        product_subgroup = args.get('product_subgroup__in', None)
        selected_level = args.get('selected_level__in', None)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if product_subgroup is not None:
            junior_buyer = sales_heirarchy.objects.filter(product_subgroup__in=product_subgroup).values('junior_buyer').distinct()

        print("--------- selected level --------------")
        print(selected_level)
        if selected_level is not None:
            try:
                print("selected level is not none")

                chart_flag = 0
                week = week_selection(currentweek, week_flag, chart_flag)

                if ((junior_buyer is not None) or (product_subgroup is not None)):
                    kwargs = {
                        'junior_buyer__in': junior_buyer,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'product_subgroup__in': selected_level
                    }
                    kwargs_denom = {
                        'junior_buyer__in': junior_buyer,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'product_subgroup'

                elif buyer is not None:
                    kwargs = {
                        'buyer__in': buyer,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'junior_buyer__in': selected_level
                    }
                    kwargs_denom = {
                        'buyer__in': buyer,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'junior_buyer'
                elif buying_controller is not None:
                    kwargs = {
                        'buying_controller__in': buying_controller,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'buyer__in': selected_level
                    }
                    kwargs_denom = {
                        'buying_controller__in': buying_controller,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'buyer'

                else:

                    if (buyer_header is None):
                        kwargs = {
                            'buying_controller__in': buying_controller_header,
                            'store_type__in': store_type,
                            'tesco_week__in': week,
                            'buyer__in': selected_level
                        }
                        kwargs_denom = {
                            'buying_controller__in': buying_controller_header,
                            'store_type__in': store_type,
                            'tesco_week__in': week,
                        }
                        level = 'buyer'
                    else:
                        kwargs = {
                            'buyer__in': buyer_header,
                            'store_type__in': store_type,
                            'tesco_week__in': week,
                            'junior_buyer__in': selected_level
                        }
                        kwargs_denom = {
                            'buyer__in': buyer_header,
                            'store_type__in': store_type,
                            'tesco_week__in': week,
                        }
                        level = 'junior_buyer'

                        kwargs_header = {
                            'buying_controller__in': buying_controller_header,
                            'buyer__in': buyer_header
                        }

                # if not args:
                #     products = sales_heirarchy.objects.filter(**kwargs_products).values('product_id').distinct()
                # else:
                #     products = sales_heirarchy.objects.filter(**kwargs_products).values('product_id').distinct()

                if (kpi_type == 'Value'):
                    total_ty = 'sales_ty'
                    total_ly = 'sales_ly'
                    no_pref = '£'
                elif (kpi_type == 'Volume'):
                    total_ty = 'volume_ty'
                    total_ly = 'volume_ly'
                    no_pref = ''
                elif (kpi_type == 'COGS'):
                    total_ty = 'cogs_ty'
                    total_ly = 'cogs_ly'
                    no_pref = '£'
                else:
                    total_ty = 'cgm_ty'
                    total_ly = 'cgm_ly'
                    no_pref = '£'

                # kwargs_denom = {
                #     'tesco_week__in': week,
                #     'product_id__in': products
                # }
                # print("denommmmmmmmmmmmmmmmm")
                # print(kwargs_denom)



                list_supp = {}

                def supp_calc(temp):
                    try:
                        supp_share_denom = supplier_view.objects.filter(**kwargs_denom).aggregate(
                            total_sum=Sum(total_ly))
                        supp_share_denom = supp_share_denom['total_sum']
                        supp_df = pd.DataFrame(temp)
                        supp_df['cont_to_grwth'] = (supp_df['grouped_ty'] - supp_df[
                            'grouped_ly']) * 100 / supp_share_denom
                        supp_df['grouped_ty'] = supp_df['grouped_ty'].astype(float)
                        supp_df['grouped_ly'] = supp_df['grouped_ly'].astype(float)
                        supp_df['cont_to_grwth'] = supp_df['cont_to_grwth'].astype(float).round(1)
                        supp_df = supp_df.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[False, False])

                        top_5_supp = supp_df
                        top_5_supp = top_5_supp.to_dict(orient='records')
                        supp_df = supp_df.sort_values(by=['grouped_ty', 'cont_to_grwth'], ascending=[True, True])
                        bot_5_supp = supp_df
                        bot_5_supp = bot_5_supp.to_dict(orient='records')
                        return top_5_supp

                    except:
                        return 0

                temp = list(
                    supplier_view.objects.filter(**kwargs).values('parent_supplier').annotate(grouped_ty=Sum(total_ty),
                                                                                              grouped_ly=Sum(total_ly)))

                # print(temp)
                top_5_supp = supp_calc(temp)
                print("supppppppppppppppp")
                print(top_5_supp)
                top_5 = list(
                    supplier_view.objects.filter(**kwargs).values('tesco_week').annotate(value_ty=Sum(total_ty),
                                                                                         value_ly=Sum(
                                                                                             total_ly)).order_by(
                        'tesco_week'))

                top_5 = pd.DataFrame(top_5)
                top_5['value_ty'] = top_5['value_ty'].astype(float)
                top_5['value_ly'] = top_5['value_ly'].astype(float)

                top_5_kpi_data = supplier_view.objects.filter(**kwargs).aggregate(value_ty=Sum(total_ty),
                                                                                  value_ly=Sum(total_ly))

                top_5_kpi_denom = supplier_view.objects.filter(**kwargs_denom).aggregate(value=Sum(total_ty))

                # multiline_label = pd.DataFrame({'label':top_5['tesco_week'].astype(str)})
                multiline_trend = pd.DataFrame({'value_ty': top_5['value_ty'].astype(float),
                                                'value_ly': top_5['value_ly'].astype(float),
                                                'tesco_week': top_5['tesco_week'].astype(str)})
                # multiline_ly = pd.DataFrame({'value':top_5['value_ly'].astype(float)})
                # multiline_label = multiline_label.to_dict(orient='records')
                # multiline_ty = multiline_ty.to_dict(orient='records')
                multiline_trend = multiline_trend.to_dict(orient='records')
                if (kpi_type == 'Value'):
                    title = 'Value Performance'
                    yaxis_title = 'Value'
                    legend1 = 'Value TY'
                    legend2 = 'Value LY'
                elif (kpi_type == 'Volume'):
                    title = 'Volume Performance'
                    yaxis_title = 'Volume'
                    legend1 = 'Volume TY'
                    legend2 = 'Volume LY'
                elif (kpi_type == 'COGS'):
                    title = 'COGS Performance'
                    yaxis_title = 'COGS'
                    legend1 = 'COGS TY'
                    legend2 = 'COGS LY'
                else:
                    title = 'CGM Performance'
                    yaxis_title = 'CGM'
                    legend1 = 'CGM TY'
                    legend2 = 'CGM LY'
                top_info = {'name': selected_level, 'multiline_trend': multiline_trend,
                            'kpi_type': kpi_type, 'title': title, 'yaxis_title': yaxis_title,
                            'legend1': legend1, 'legend2': legend2, 'no_pref': no_pref, 'fetch': 'success'}
            # top_chart_prod1 = top_list('sales_ty', 'sales_ly', 1).to_json(orient='index')
            # top_chart_prod1 = json.loads(top_chart_prod1)
            except:
                top_info = {'fetch': 'fail'}
        else:
            top_info = {'fetch': 'fail'}
        logging.info(top_info)
        return JsonResponse(top_info, safe=False)

class exec_supplier_info(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        print("args",args)
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        store_type = args.pop('store_type__in',['Main Estate','Express'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['Value'])
        kpi_type = kpi_type[0]

        # for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])

        lastweek = last_week(currentweek)

        category_name = args.get('category_name__in', None)
        buying_controller = args.get('buying_controller__in', None)
        buyer = args.get('buyer__in', None)
        junior_buyer = args.get('junior_buyer__in', None)
        product_subgroup = args.get('product_subgroup__in', None)
        selected_level = args.get('selected_level__in', None)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
        buyer_header = args.pop('buyer_header__in', None)

        if selected_level is not None:
            chart_flag = 1
            week = week_selection(currentweek, week_flag, chart_flag)
            if (week_flag=='Latest Week') | (week_flag=='Selected Week'):
                week_curr=currentweek
            else:
                week_curr = week

            if ((junior_buyer is not None) or (product_subgroup is not None)):

                kwargs = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'product_subgroup__in': selected_level
                }
                kwargs_denom = {
                    'junior_buyer__in': junior_buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                }
                level = 'product_subgroup'

                kwargs_imp_categ = {
                    'tesco_week__in': week,
                    'product_subgroup__in': selected_level,
                    'store_type__in': store_type
                }
                kwargs_numer = {
                    'tesco_week__in': week,
                    'product_subgroup__in': selected_level,
                    'store_type__in': store_type,
                }
                level = 'product_subgroup'

            elif buyer is not None:
                print("entered if final buyer")
                kwargs = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level
                }
                kwargs_denom = {
                    'buyer__in': buyer,
                    'store_type__in': store_type,
                    'tesco_week__in': week
                }
                level = 'junior_buyer'

                kwargs_imp_categ = {
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level,
                    'store_type__in': store_type
                }
                kwargs_numer = {
                    'tesco_week__in': week,
                    'junior_buyer__in': selected_level,
                    'store_type__in': store_type
                }
            elif buying_controller is not None:
                print("entered if final buying controller")
                kwargs = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week,
                    'buyer__in': selected_level
                }
                kwargs_denom = {
                    'buying_controller__in': buying_controller,
                    'store_type__in': store_type,
                    'tesco_week__in': week
                }
                level = 'buyer'
                kwargs_imp_categ = {
                    'tesco_week__in': week,
                    'buyer__in': selected_level,
                    'store_type__in': store_type
                }

                kwargs_numer = {
                    'tesco_week__in': week,
                    'buyer__in': selected_level,
                    'store_type__in': store_type
                }


            else:

                if (buyer_header is None):
                    print("entered if final")
                    kwargs = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'buyer__in': selected_level
                    }
                    kwargs_denom = {
                        'buying_controller__in': buying_controller_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }
                    level = 'buyer'

                    kwargs_imp_categ = {
                        'tesco_week__in': week,
                        'store_type__in': store_type,
                        'buyer__in': selected_level

                    }
                    kwargs_numer = {
                        'tesco_week__in': week,
                        'store_type__in': store_type,
                        'buyer__in': selected_level
                    }
                else:
                    print("entered else final")
                    kwargs = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                        'junior_buyer__in': selected_level
                    }
                    kwargs_denom = {
                        'buyer__in': buyer_header,
                        'store_type__in': store_type,
                        'tesco_week__in': week,
                    }

                    kwargs_header = {
                        'buying_controller__in': buying_controller_header,
                        'buyer__in': buyer_header
                    }

                    kwargs_imp_categ = {
                        'tesco_week__in': week,
                        'junior_buyer__in': selected_level,
                        'store_type__in': store_type
                    }
                    kwargs_numer = {
                        'tesco_week__in': week,
                        'junior_buyer__in': selected_level,
                        'store_type__in': store_type
                    }
                    level = 'junior_buyer'

        if (kpi_type == 'Value'):
            total_ty = 'sales_ty'
            total_ly = 'sales_ly'
            cat_total_ty = 'cat_sales_ty'
        elif (kpi_type == 'Volume'):
            total_ty = 'volume_ty'
            total_ly = 'volume_ly'
            cat_total_ty = 'cat_volume_ty'
        elif (kpi_type == 'COGS'):
            total_ty = 'cogs_ty'
            total_ly = 'cogs_ly'
            cat_total_ty = 'cat_cogs_ty'
        else:
            total_ty = 'cgm_ty'
            total_ly = 'cgm_ly'
            cat_total_ty = 'cat_cgm_ty'

        list_supp = {}

        imp_supp_denom = supplier_view.objects.filter(**kwargs_imp_categ).aggregate(
            total_sum_sup_denom=Sum(total_ty), total_sum_sup_denom_ly=Sum(total_ly))

        imp_categ_denom = supplier_view.objects.filter(**kwargs_imp_categ).annotate(
            total_sum_categ_denom=Sum(cat_total_ty))

        imp_categ_denom3 = supplier_view.objects.filter(**kwargs_imp_categ).aggregate(
            total_sum_categ_denom=Sum(total_ty))
        print("imp_categ_denom3", imp_categ_denom3)
        imp_categ_denom1 = pd.DataFrame(imp_categ_denom3,index=[0])
        print("xxxxxxxx",imp_categ_denom1)
        imp_categ_denom2=imp_categ_denom1['total_sum_categ_denom'][0]
        print("imp_categ_denom2", imp_categ_denom2)


        imp_categ_denom = read_frame(imp_categ_denom)
        kwargs_ps_total = {
            'store_type__in': store_type,
            'tesco_week__in': week,

        }
        print("new code")
        value_ty = read_frame(
            supplier_view.objects.filter(**kwargs_ps_total).values('tesco_week','store_type','parent_supplier',cat_total_ty).distinct())
        value_ty_group = value_ty.groupby(['parent_supplier'], as_index=False).agg({cat_total_ty: sum})
        value_ty_group[cat_total_ty] = value_ty_group[cat_total_ty].astype(float)

        print("kwargs_ps_Total",kwargs_ps_total)
        print("kwargs_imp_categ",kwargs_imp_categ)
        temp = supplier_view.objects.filter(**kwargs_imp_categ).values('parent_supplier').annotate(
            grouped_ty=Sum(total_ty),
            grouped_ly=Sum(total_ly))
        temp = read_frame(temp)

        # result = pd.merge(imp_categ_denom1, temp, how='inner', on=['parent_supplier'])
        result=pd.DataFrame()
        result=pd.DataFrame(temp)
        print("result tem",result.head())
        result['total_sum_categ_denom'] = imp_categ_denom2
        print("result 1",result.head())
        result['grouped_ty']=result['grouped_ty'].astype(float)
        result['total_sum_categ_denom']=result['total_sum_categ_denom'].astype(float)
        result = result[(result.total_sum_categ_denom != 0)]
        result['imp_to_categ'] = result['grouped_ty'] * 100 / result['total_sum_categ_denom']
        # result['imp_to_ps'] = result['grouped_ty'] * 100 / imp_supp_denom['total_sum_sup_denom']
        result = pd.merge(result,value_ty_group,how='inner', on=['parent_supplier'])
        print("result 2", result)
        result['imp_to_ps'] = result['grouped_ty']* 100 / result[cat_total_ty]
        print("result[imp_to_ps]",result.head())
        print("kwargs_numer",kwargs_numer)
        sup_info_kpi_data = supplier_view.objects.filter(**kwargs_numer).values('parent_supplier').annotate(
            value_ty=Sum(total_ty),
            value_ly=Sum(total_ly))

        sup_info_kpi_data = read_frame(sup_info_kpi_data)
        result = pd.merge(result, sup_info_kpi_data, how='inner', on=['parent_supplier'])
        print("final result dataframe")
        print(result.head())
        result['yoy_var'] = 0

        for i in range(len(result)):
            try:
                result['sales_share'] = result['value_ty'] * 100 / imp_supp_denom['total_sum_sup_denom']
            except:
                result['sales_share'] = 0
            try:
                result['cont_to_grwth'] = (result['value_ty'] - result['value_ly']) * 100 / imp_supp_denom[
                    'total_sum_sup_denom_ly']
            except:
                result['cont_to_grwth'] = 0
            try:
                result['yoy_var'][i] = (result['value_ty'][i] - result['value_ly'][i]) * 100 / result[
                    'value_ly'][i]
            except:
                result['yoy_var'][i] = 0

        result = result.round({'grouped_ly': 2, 'value_ly': 2})
        result['grouped_ly'] = result['grouped_ly'].astype('float').round(decimals=2)
        result['cont_to_grwth'] = result['cont_to_grwth'].astype('float').round(decimals=1)
        result['imp_to_categ'] = result['imp_to_categ'].astype('float').round(decimals=1)
        result['imp_to_ps'] = result['imp_to_ps'].astype('float').round(decimals=1)
        result['value_ly'] = result['value_ly'].astype('float').round(decimals=2)
        result['total_sum_categ_denom'] = result['total_sum_categ_denom'].astype('float').round(decimals=2)
        result['grouped_ty'] = result['grouped_ty'].astype('float').round(decimals=2)
        result['value_ty'] = result['value_ty'].astype('float').round(decimals=2)
        result['yoy_var'] = result['yoy_var'].astype('float').round(decimals=1)
        result['sales_share'] = result['sales_share'].astype('float').round(decimals=1)
        result=result.fillna(0)
        result = result.sort(['value_ty'], ascending=[0])
        result = result.to_dict(orient='records')
        logging.info(result)
        return JsonResponse(result, safe=False)

# Function for calculating week time period
def week_selection(cw_week, week_flag, chart_flag):
    week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
        '-tesco_week').distinct()
    last_week = week_ordered[1]
    last_week = last_week['tesco_week']
    if (week_flag == 'Latest 4 Weeks'):
        week_logic = week_ordered[:4]

    elif (week_flag == 'Latest 13 Weeks'):
        week_logic = week_ordered[:13]

    elif (week_flag == 'Latest 26 Weeks'):
        week_logic = week_ordered[:26]

    elif (week_flag == 'YTD'):
        current_week = int(cw_week)
        for_x = int(str(current_week)[-2:])
        week_logic = week_ordered[:for_x]

    else:
        if (chart_flag == 1):
            week_logic = week_ordered[:13]
        else:
            week_logic = week_ordered[:1]

    week_var = []
    for i in range(len(week_logic)):
        week_var.append(week_logic[i]['tesco_week'])

    return week_var

# Function for calculating lastyearweek_selection
def lastyearweek_selection(week):
    last_year_var = [0] * len(week)
    for i in range(0, len(week)):
        last_year_var[i] = week[i] - 100
    return last_year_var

def last_week(selected_week):
    x = read_frame(latest_week.objects.all())
    y = x[['week_ty']].drop_duplicates().reset_index(drop=True)
    y = y.sort_values('week_ty', ascending=True)
    y['rank_week'] = range(0, len(y))
    index_thisweek = int(y[y['week_ty'] == selected_week].rank_week)
    index_last_week = index_thisweek - 1
    last_week = int(y[y['rank_week'] == index_last_week].week_ty)
    return (last_week)

def seperate_args(args):
    args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

    print("_________________args before ++++++++++")

    print(args)
    # for week tab
    week_flag = args.pop('week_flag__in', ['Selected Week'])
    week_flag = week_flag[0]

    # for kpi type tab
    kpi_type = args.pop('kpi_type__in', ['Value'])
    kpi_type = kpi_type[0]

    # for current week value
    tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
    max_week = [tesco_week_int['cw_max']]
    currentweek = args.pop('tesco_week__in', max_week)
    currentweek = int(currentweek[0])
    lastweek = last_week(currentweek)

    user_id = args.pop('user_id__in', None)
    designation = args.pop('designation__in', None)
    session_id = args.pop('session_id__in', None)
    user_name = args.pop('user_name__in', None)
    buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
    buyer_header = args.pop('buyer_header__in', None)

#Function for calculating variation
def var_calc(a,b):
    if b != 0:
        try:
            c = float(format(
            ((a - b) * 100 / b), '.1f'))
        except:
            c = 0
    else:
        c = 'NA'

    return c

#Function to formatting kpi
def format_kpi(a,format_type):
    if (format_type == '£'):
        integer_val = int(float(a) / 1000)
        a = '£' + intcomma((integer_val)) + 'K'

    else:
        integer_val = int(float(a) / 1000)
        a = intcomma((integer_val)) + 'K'

    return a

#new filter logic
class executive_filters_new(APIView):
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
                    #print(i)
                    data = {i: df[i].unique()}
                    #print(data)
                    col = pd.DataFrame(data)
                    if i == ('buyer') or i == ('buying_controller'):
                        if len(col) == 1:
                            #print("inside if loop")
                            col['selected'] = True  ### One change here for default selection of bc logging in
                            col['highlighted'] = False
                        else:
                            col['selected'] = False
                            col['highlighted'] = False
                    else:
                        col['selected'] = False
                        col['highlighted'] = False
                    col_df = heirarchy[[i]].drop_duplicates()
                    #print(col_df)
                    col_df = pd.merge(col_df, col, how='left')
                    col_df['selected'] = col_df['selected'].fillna(False)
                    col_df['highlighted'] = col_df['highlighted'].fillna(False)
                    col_df = col_df.rename(columns={i: 'title'})
                    #print("____")
                    #print(col_df)
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
                    #print("---------")
                    #print(col_df_final)
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
                #print(store_list)
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
        logging.info({'cols': cols, 'checkbox_list': final})
        return JsonResponse({'cols': cols, 'checkbox_list': final}, safe=False)


