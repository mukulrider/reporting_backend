from __future__ import unicode_literals
from django.views import generic
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from django.contrib.humanize.templatetags.humanize import intcomma, intword
import json
import re
import logging
import time
from .models import sales_heirarchy, supplier_view, forecast_budget_data, roles_and_intent, weather_weekly_details, executive_inflation, executive_price_index, promo_view, competitor_price_bucket, competitor_market_share, competitor_outperform, competitor_price_index, calendar_dim_hierarchy, latest_week

from django.utils import six
import numpy as np

# from .NPD_test import outperformance_calculations
import pandas as pd
from django_pandas.io import read_frame


import datetime

from django.conf import settings
# from sqlalchemy import *
import gzip
# from sklearn import preprocessing
# import xgboost as xgb
import pickle

import json  ##added

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from django.http import JsonResponse
import math
from django.db.models import Count, Min, Max, Sum, Avg, F, FloatField, Case, When, Value, Q
from rest_framework_extensions.cache.decorators import cache_response
import collections
import hashlib
from django.core.cache import cache

#Promo Filter data


timestr = time.strftime("%Y%m%d")

logging.basicConfig(filename='logs/reporting_views_'+timestr+'.log',level=logging.DEBUG,format='%(asctime)s %(message)s',datefmt='%m/%d/%Y %I:%M:%S %p')



class promotion_filterdata_week(APIView):
    # @cache_response()
    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}
        print("---------------------")
        week_id = args.get('tesco_week__iexact')
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = tesco_week_int['cw_max']

        if week_id is None:
            week_id = max_week

        else:
            week_id = int(week_id)

        print(week_id)
        print(type(week_id))

        kwargs = {
                    'tesco_week__iexact' : week_id

        }

        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))

        if not args:

            # print("inside default")
            weeks_data = read_frame(calendar_dim_hierarchy.objects.all().filter(tesco_week__gte = 201626).filter(tesco_week__lte = max_week ).values('tesco_week').order_by('-tesco_week'))
            #weeks_data = weeks_data[weeks_data['tesco_week'] >= 201646 and weeks_data['tesco_week'] <= 201705]

            # print("After replacing")
            # print(heirarchy)


            data ={'tesco_week' : weeks_data.tesco_week.unique()}
            week = pd.DataFrame(data)
            week['selected']=False
            week['disabled'] =False


            week_df = weeks_data[['tesco_week']].drop_duplicates()


            week_df = pd.merge(week_df,week,how='left')
            week_df['selected'] =week_df['selected'].fillna(False)
            week_df['disabled'] =week_df['disabled'].fillna(False)

            week_df = week_df.rename(columns={'tesco_week': 'name'})



            week_final = week_df.to_json(orient='records')
            week_final = json.loads(week_final)

            a = {}
            a['name']='tesco_week'
            a['items']=week_final



            final = []
            final.append(a)
 
        else:
            weeks_data = read_frame(calendar_dim_hierarchy.objects.all().filter(tesco_week__gte=201626).filter(
                tesco_week__lte=max_week).values('tesco_week').order_by('-tesco_week'))
            #weeks_data = weeks_data[weeks_data['tesco_week'] >= 201646 and weeks_data['tesco_week'] >= 201705]

            week_df = weeks_data[['tesco_week']].drop_duplicates()
            


            week_temp = read_frame(calendar_dim_hierarchy.objects.filter(**kwargs).values('tesco_week'))

            # print("Comm name ")
            data ={'tesco_week' : week_temp.tesco_week.unique()}
            week_name = pd.DataFrame(data)
            # print(len(week_name))

            
            if len(week_name)==1:
                 week_name['selected']=True
                 week_name['disabled']=False
                 week_df = pd.merge(week_df,week_name,how='left')
                 week_df['selected'] =week_df['selected'].fillna(False)
                 week_df['disabled'] =week_df['disabled'].fillna(True)
                 week_df = week_df.rename(columns={'tesco_week': 'name'})
            else:
                 week_name['selected']=False
                 week_name['disabled']=False
                 week_df = pd.merge(week_df,week_name,how='left')
                 week_df['selected'] =week_df['selected'].fillna(False)
                 week_df['disabled'] =week_df['disabled'].fillna(True)
                 week_df = week_df.rename(columns={'tesco_week': 'name'})


            week_final = week_df.to_json(orient='records')
            week_final = json.loads(week_final)

            a = {}
            a['name']='tesco_week'
            a['items']=week_final


 
            final = []
            final.append(a)

            # print(final)
        return JsonResponse(final, safe=False)


# Promo Filtered data


def col_distinct(kwargs, col_name, kwargs_header):
    queryset = sales_heirarchy.objects.filter(**kwargs_header).filter(**kwargs).values(col_name).order_by(col_name).distinct()
    base_product_number_list = [k.get(col_name) for k in queryset]
    return base_product_number_list


def make_json_promo(sent_req, kwargs_header,default_check):
    print('*********************\n       FILTERS2 \n*********************')
    cols = ['store_type','commercial_name', 'category_name', 'buying_controller', 'buyer', 'junior_buyer', 'product_subgroup', 'brand_indicator']

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
        sent_req  = default_check
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
        print('\n********* \n' + col_name + '\n*********')
        # print('sent_req.get(col_name):', sent_req.get(col_name))
        col_unique_list = col_distinct({}, col_name, kwargs_header)
        col_unique_list_name.append({'name': col_name,
                                     'unique_elements': col_unique_list})
        col_unique_list_name_obj[col_name] = col_unique_list
        # args sent as url params
        kwargs2 = {reqobj + '__in': sent_req.get(reqobj) for reqobj in sent_req.keys()}

        category_of_sent_obj_list = col_distinct(kwargs2, col_name, kwargs_header)
        print(len(category_of_sent_obj_list))
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
                            print('keys:', i, sent_req.get(i))
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
                           'required': True if col_name == 'store_type' or col_name == 'buying_controller' else False
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


class promo_filterdata(APIView):
    def get(self, request):
        print(request.GET)
        obj = {}
        obj2 = {}
        get_keys = request.GET.keys()
        default_keys = request.GET.keys()
        for i in get_keys:
            # print(request.GET.getlist(i))
            obj[i] = request.GET.getlist(i)
        for i in default_keys:
            # print(request.GET.getlist(i))
            obj2[i] = request.GET.getlist(i)
        print("obj2-----------------------------")
        print(obj2)
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


        if buyer_header is None:
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        # hash_object = hashlib.md5(json.dumps(obj).encode())
        # hexdigest = hash_object.hexdigest()
        # print('>>>>>>', hexdigest)
        #
        # cached_filter = cache.get(hexdigest + '_reporting')
        # if cached_filter is not None:
        #     print('from cache')
        #     return cached_filter
        # else:
        #     print('not from cache')
        filter_json = make_json_promo(obj, kwargs_header,default_check)
            # cache.set(hexdigest + '_reporting', filter_json)
        return filter_json

#Promo View

class promo_kpi(APIView):
    def get(self,request,*args):
        # print("args recieved")
        args = {reqobj+'__in' : request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # print(args)
        #for week tab
        week_flag=args.pop('week_flag__in',['Selected Week'])
        week_flag=week_flag[0]
        #for kpi type tab
        kpi_type=args.pop('kpi_type__in',['value'])
        kpi_type=kpi_type[0]


        store_type = args.pop('store_type__in',['Main Estate','Express'])
        print("_____________________storetype")
        print(store_type)
        # print("kpi_type")
        # print(kpi_type)
        #for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)

        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        if(kpi_type =='value'):
            total = 'total_sales'
            total_lfl = 'total_sales_lfl'
            promo = 'promo_sales'
            promo_lfl = 'promo_sales_lfl'
            nonpromo = 'nonpromo_sales'
            nonpromo_lfl = 'nonpromo_sales_lfl'
            kpi_name = 'Value'
            format_type = '£'
        elif (kpi_type == 'profit'):
            total = 'total_profit'
            total_lfl = 'total_profit_lfl'
            promo = 'promo_profit'
            promo_lfl = 'promo_profit_lfl'
            nonpromo = 'nonpromo_profit'
            nonpromo_lfl = 'nonpromo_profit_lfl'
            kpi_name = 'Profit'
            format_type = '£'
        else:
            total = 'total_volume'
            total_lfl = 'total_volume_lfl'
            promo = 'promo_volume'
            promo_lfl = 'promo_volume_lfl'
            nonpromo = 'nonpromo_volume'
            nonpromo_lfl = 'nonpromo_volume_lfl'
            kpi_name = 'Volume'
            format_type = ''
        lastyearweek = currentweek - 100




        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
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




        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
        chart_flag = 0
        week = week_selection(currentweek,week_flag,chart_flag)
        lastyearweek = lastyearweek_selection(week)
        # print("week=====")
        # print(week)
        kwargs = {
            'tesco_week__in': week,
            'product_id__in' : products,
            'store_type__in' : store_type}

        kwargs_lw = {
            'tesco_week': lastweek,
            'product_id__in' : products,
            'store_type__in': store_type}

        kwargs_ly = {
            'tesco_week__in': lastyearweek,
            'product_id__in' : products,
            'store_type__in': store_type
        }


        print("kwargs")
        print(kwargs)

        if kpi_type == 'giveaway':
            current_week_data = promo_view.objects.filter(**kwargs).aggregate(giveaway= Sum('promo_giveaway'),
                                                                               giveaway_lfl = Sum('promo_giveaway')
                                                                               )
            print("Current week data")
            # print(current_week_data)
            last_week_data = promo_view.objects.filter(**kwargs_lw).aggregate(giveaway= Sum('promo_giveaway'),
                                                                               giveaway_lfl = Sum('promo_giveaway')
                                                                               )

            last_year_data = promo_view.objects.filter(**kwargs_ly).aggregate(giveaway= Sum('promo_giveaway'),
                                                                               giveaway_lfl = Sum('promo_giveaway')
                                                                               )

            ########################################### Calculations  #######################################################

            total_kpi = {}
            total_kpi['total'] = format_kpi(current_week_data['giveaway'],'£')
            total_kpi['total_lfl'] = format_kpi(current_week_data['giveaway_lfl'],'£')
            total_kpi['var_total_yoy'] = var_calc(current_week_data['giveaway'],last_year_data['giveaway'])
            total_kpi['var_total_wow'] = var_calc(current_week_data['giveaway'],last_week_data['giveaway'])
            total_kpi['var_total_lfl'] = var_calc(current_week_data['giveaway_lfl'],last_year_data['giveaway_lfl'])


            kpi = {}
            kpi['total'] = total_kpi

            kpi['kpi_name'] = 'Giveaway'
            kpi['selected_week'] = currentweek

        elif kpi_type == 'products_count':

            current_week_total = promo_view.objects.filter(**kwargs).aggregate(product_count=Count('product_id')
                                                                               )
            print("Current week data")
            # print(current_week_data)
            last_week_total = promo_view.objects.filter(**kwargs_lw).aggregate(product_count=Count('product_id')
                                                                               )

            last_year_total = promo_view.objects.filter(**kwargs_ly).aggregate(product_count=Count('product_id')
                                                                               )


            current_week_promo = promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').aggregate(product_count=Count('product_id')
                                                                                )
            print("Current week data")
            # print(current_week_data)
            last_week_promo = promo_view.objects.filter(**kwargs_lw).exclude(promo_type='Non Promo').aggregate(product_count=Count('product_id')
                                                                                )

            last_year_promo = promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').aggregate(product_count=Count('product_id')
                                                                                )


            current_week_nonpromo = promo_view.objects.filter(**kwargs).filter(promo_type='Non Promo').aggregate(
                product_count=Count('product_id')
                )
            print("Current week data")
            # print(current_week_data)
            last_week_nonpromo = promo_view.objects.filter(**kwargs_lw).filter(promo_type='Non Promo').aggregate(
                product_count=Count('product_id')
                )

            last_year_nonpromo = promo_view.objects.filter(**kwargs_ly).filter(promo_type='Non Promo').aggregate(
                product_count=Count('product_id')
                )


            ########################################### Calculations  #######################################################
            try:
                cw_total = format(current_week_total['product_count'], '.0f')
            except:
                cw_total = 0


            # Current Promo
            try:
                cw_promo = format(current_week_promo['product_count'], '.0f')
            except:
                cw_promo = 0
            # Current Non Promo
            try:
                cw_nonpromo = format(current_week_nonpromo['product_count'], '.0f')
            except:
                cw_nonpromo = 0
            # Last Non Promo

            try:
                total_asp = current_week_data['Total_Sales'] / current_week_data['Total_Volume']
            except:
                total_asp = 0
                #    ###########################################       Promo ASP      #######################################################

            try:
                promo_asp = current_week_data['promo_sales'] / current_week_data['promo_Volume']
            except:
                promo_asp = 0

                #    ###########################################       Non Promo ASP  #######################################################

            try:
                nonpromo_asp = current_week_data['nonpromo_sales'] / current_week_data['nonpromo_Volume']
            except:
                nonpromo_asp = 0

            # integer_val = int(float(cw_total) / 1000)
            # total = intcomma((integer_val)) + 'K'
            # integer_val = int(float(cw_promo) / 1000)
            # promo = intcomma((integer_val)) + 'K'
            # integer_val = int(float(cw_nonpromo) / 1000)
            # nonpromo = intcomma((integer_val)) + 'K'



            total_kpi = {}
            total_kpi['total'] = cw_total
            total_kpi['var_total_yoy'] = var_calc(current_week_total['product_count'],last_year_total['product_count'])
            total_kpi['var_total_wow'] = var_calc(current_week_total['product_count'],last_week_total['product_count'])

            promo_kpi = {}
            promo_kpi['promo'] = cw_promo
            promo_kpi['var_promo_yoy'] =  var_calc(current_week_promo['product_count'],last_year_promo['product_count'])
            promo_kpi['var_promo_wow'] = var_calc(current_week_promo['product_count'],last_week_promo['product_count'])

            nonpromo_kpi = {}
            nonpromo_kpi['nonpromo'] = cw_nonpromo
            nonpromo_kpi['var_nonpromo_yoy'] = var_calc(current_week_nonpromo['product_count'],last_year_nonpromo['product_count'])
            nonpromo_kpi['var_nonpromo_wow'] = var_calc(current_week_nonpromo['product_count'],last_week_nonpromo['product_count'])


            kpi = {}
            kpi['total'] = total_kpi
            kpi['promo'] = promo_kpi
            kpi['nonpromo'] = nonpromo_kpi
            kpi['kpi_name'] = 'Product Count'
            kpi['selected_week'] = currentweek




            print('kwargs')
            print(kwargs)
        else:
            current_week_data = promo_view.objects.filter(**kwargs).aggregate(total=Sum(total),
                                                                               total_lfl=Sum(total_lfl),
                                                                               promo=Sum(promo),
                                                                               promo_lfl=Sum(promo_lfl),
                                                                               nonpromo=Sum(nonpromo),
                                                                               nonpromo_lfl=Sum(nonpromo_lfl),
                                                                               Total_Volume=Sum('total_volume'),
                                                                               Total_Sales=Sum('total_sales'),
                                                                               nonpromo_sales=Sum('nonpromo_sales'),
                                                                               nonpromo_Volume=Sum('nonpromo_volume'),
                                                                               promo_sales=Sum('promo_sales'),
                                                                               promo_Volume=Sum('promo_volume'),

                                                                               )
            print("Current week data")
            print(current_week_data)
            last_week_data = promo_view.objects.filter(**kwargs_lw).aggregate(total=Sum(total),
                                                                               total_lfl=Sum(total_lfl),
                                                                               promo=Sum(promo),
                                                                               promo_lfl=Sum(promo_lfl),
                                                                               nonpromo=Sum(nonpromo),
                                                                               nonpromo_lfl=Sum(nonpromo_lfl)
                                                                               )

            last_year_data = promo_view.objects.filter(**kwargs_ly).aggregate(total=Sum(total),
                                                                               total_lfl=Sum(total_lfl),
                                                                               promo=Sum(promo),
                                                                               promo_lfl=Sum(promo_lfl),
                                                                               nonpromo=Sum(nonpromo),
                                                                               nonpromo_lfl=Sum(nonpromo_lfl)
                                                                               )

            ########################################### Calculations  ###################################################

                #    ###########################################       Total ASP      #######################################################

            try:
                total_asp = current_week_data['Total_Sales'] / current_week_data['Total_Volume']
            except:
                total_asp = 0
                #    ###########################################       Promo ASP      #######################################################

            try:
                promo_asp = current_week_data['promo_sales'] / current_week_data['promo_Volume']
            except:
                promo_asp = 0

                #    ###########################################       Non Promo ASP  #######################################################

            try:
                nonpromo_asp = current_week_data['nonpromo_sales'] / current_week_data['nonpromo_Volume']
            except:
                nonpromo_asp = 0


            total_asp_new = '£' + format(total_asp, '.1f')
            promo_asp_new = '£' + format(promo_asp, '.1f')
            nonpromo_asp_new = '£' + format(nonpromo_asp, '.1f')

            asp = {}
            asp["promo_asp"] = promo_asp_new
            asp["nonpromo_asp"] = nonpromo_asp_new

            total_kpi = {}
            total_kpi['total'] = format_kpi(current_week_data['total'],format_type)
            total_kpi['total_lfl'] = format_kpi(current_week_data['total_lfl'],format_type)
            total_kpi['var_total_yoy'] = var_calc(current_week_data['total'],last_year_data['total'])
            total_kpi['var_total_wow'] = var_calc(current_week_data['total'],last_week_data['total'])
            total_kpi['var_total_lfl'] = var_calc(current_week_data['total_lfl'],last_year_data['total_lfl'])

            promo_kpi = {}
            promo_kpi['promo'] = format_kpi(current_week_data['promo'],format_type)
            promo_kpi['promo_lfl'] = format_kpi(current_week_data['promo_lfl'],format_type)
            promo_kpi['var_promo_yoy'] = var_calc(current_week_data['promo'],last_year_data['promo'])
            promo_kpi['var_promo_wow'] = var_calc(current_week_data['promo'],last_week_data['promo'])
            promo_kpi['var_promo_lfl'] = var_calc(current_week_data['promo_lfl'],last_year_data['promo_lfl'])

            nonpromo_kpi = {}
            nonpromo_kpi['nonpromo'] = format_kpi(current_week_data['nonpromo'],format_type)
            nonpromo_kpi['nonpromo_lfl'] = format_kpi(current_week_data['nonpromo_lfl'],format_type)
            nonpromo_kpi['var_nonpromo_yoy'] = var_calc(current_week_data['nonpromo'],last_year_data['nonpromo'])
            nonpromo_kpi['var_nonpromo_wow'] = var_calc(current_week_data['nonpromo'],last_week_data['nonpromo'])
            nonpromo_kpi['var_nonpromo_lfl'] = var_calc(current_week_data['nonpromo_lfl'],last_year_data['nonpromo_lfl'])

            kpi = {}
            kpi['total'] = total_kpi
            kpi['promo'] = promo_kpi
            kpi['nonpromo'] = nonpromo_kpi
            kpi['asp'] = asp
            kpi['kpi_name'] = kpi_name
            kpi['selected_week'] = currentweek
        logging.info(kpi)
        return JsonResponse(kpi, safe=False)



class promo_piechart(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for metric tab
        metric = args.pop('metric__in', ['value'])
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['value'])
        kpi_type = kpi_type[0]
        # for Promo type tab
        promo_type = args.pop('promo_type__in', ['Total Promo'])
        # for current week value

        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        store_type = args.pop('store_type__in',['Main Estate','Express'])


        chart_flag = 0
        week_var = week_selection(currentweek, week_flag, chart_flag)
        lastyearweek = lastyearweek_selection(week_var)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
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

        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
        kwargs_pie = {
            'tesco_week__in': week_var,
            'product_id__in': products,
            'store_type__in': store_type
        }

        if promo_type is None:
            kwargs = {
                'tesco_week__in': week_var,
                'product_id__in': products,
                'store_type__in': store_type
            }

            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': products,
                'store_type__in': store_type
            }
        else:
            kwargs = {
                'tesco_week__in': week_var,
                'product_id__in': products,
                'promo_type__in': promo_type,
                'store_type__in': store_type
            }

            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': products,
                'promo_type__in': promo_type,
                'store_type__in': store_type
            }



        if metric[0] == 'giveaway':
            # Promo Giveaway calculation
            pie_chart_info= list(
                promo_view.objects.filter(**kwargs_pie).exclude(promo_type='Non Promo').values(
                    'promo_type').annotate(value=Sum('promo_giveaway')))
            labels = ['Total', 'PriceCut', 'Multibuy', 'Linksave']

        elif metric[0] == 'products_count':
            pie_chart_info = list(
                promo_view.objects.filter(**kwargs_pie).exclude(promo_type='Non Promo').values('promo_type').annotate(
                    value=Count('product_id', distinct=True)))
            labels = ['Total', 'PriceCut', 'Multibuy', 'Linksave', 'Non Promo']


        elif metric[0] == 'value':
            if (kpi_type == 'value'):
                Total = 'total_sales'
                Promo = 'promo_sales'
            elif (kpi_type == 'volume'):
                Total = 'total_volume'
                Promo = 'promo_volume'
            else:
                Total = 'total_profit'
                Promo = 'promo_profit'

            # Pie chart for promo sales
            pie_chart_info = list(
                promo_view.objects.filter(**kwargs_pie).values('promo_type').annotate(value=Sum(Total)))
            labels = ['Total', 'PriceCut', 'Multibuy', 'Linksave', 'Non Promo']

        try:
            pie_chart_info = pd.DataFrame(pie_chart_info)
            pie_chart_info['value'] = pie_chart_info['value'].astype('float')
            pie_chart_info = pie_chart_info.rename(columns={'promo_type': 'label'})
            temp_label = pie_chart_info['label']

            label = []
            label.extend(['Total Promo'])
            label.extend(list(temp_label))
            label = [x for x in label if x != 'Non Promo']
            label = [x for x in label if x != '?']
            label = [x for x in label if x != 'Other']
            pie_chart_info = pie_chart_info.replace('?','Non Promo')
            pie_chart_info = pie_chart_info.to_dict(orient='records')
            data_available = 'yes'

        except:
            pie_chart_info = 0
            data_available = 'no'
            label = []

        data_dict = {}
        data_dict['piechart'] = pie_chart_info
        data_dict['labels'] = label
        print('data_dict')
        print(data_dict)

        logging.info(data_dict)
        return JsonResponse(data_dict, safe=False)

class promo_trendchart(APIView):
    def get(self, request, *args):

        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for metric tab
        metric = args.pop('metric__in', ['value'])
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['value'])
        kpi_type = kpi_type[0]

        # for Promo type tab
        promo_type = args.pop('promo_type__in', ['Total Promo'])
        # for current week value

        store_type = args.pop('store_type__in', ['Main Estate','Express'])

        line_chart_type = args.pop('line_chart_type__in', ['absolute'])
        line_chart_type = line_chart_type[0]
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        chart_flag = 1
        week_var = week_selection(currentweek, week_flag, chart_flag)
        lastyearweek = lastyearweek_selection(week_var)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
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

        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()



        if (promo_type[0] == 'Total Promo'):
            kwargs = {
                'tesco_week__in': week_var,
                'product_id__in': products,
                'store_type__in': store_type
            }

            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': products,
                'store_type__in': store_type
            }
        else:
            kwargs = {
                'tesco_week__in': week_var,
                'product_id__in': products,
                'promo_type__in': promo_type,
                'store_type__in': store_type
            }

            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': products,
                'promo_type__in': promo_type,
                'store_type__in': store_type
            }



        if metric[0] == 'giveaway':
            trend_promo_ty = list(
                promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    value_ty=Sum('promo_giveaway')).order_by('tesco_week'))
            trend_promo_ly = list(
                promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values(
                    "tesco_week").annotate(value_ly=Sum('promo_giveaway')).order_by('tesco_week'))
            metric = 'Promo Giveaway'
            no_pref = '£'
            no_suffix =''

        elif metric[0] == 'products_count':
            trend_promo_ty = list(
                promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    value_ty=Count('product_id', distinct=True)).order_by('tesco_week'))
            trend_promo_ly = list(
                promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    value_ly=Count('product_id', distinct=True)).order_by('tesco_week'))
            metric = 'Products on Promo'
            no_pref = ''
            no_suffix = ''

        else:

            if (kpi_type == 'value'):
                Total = 'total_sales'
                Promo = 'promo_sales'
                Promo_lfl = 'promo_sales_lfl'
                yaxis_title = 'Value'
                no_pref = '£'
                no_suffix = ''
                metric = 'Value'

            elif(kpi_type == 'volume'):
                Total = 'total_volume'
                Promo = 'promo_volume'
                Promo_lfl = 'promo_volume_lfl'
                yaxis_title = 'Volume'
                no_pref = ''
                no_suffix = ''
                metric = 'Volume'

            elif (kpi_type == 'profit'):
                Total = 'total_profit'
                Promo = 'promo_profit'
                Promo_lfl = 'promo_profit_lfl'
                yaxis_title = 'Profit'
                no_pref = '£'
                no_suffix = ''
                metric = 'CGM'
                line_chart_type = 'absolute'

            if(line_chart_type=='absolute'):
                trend_promo_ty = list(
                    promo_view.objects.filter(**kwargs).values("tesco_week").annotate(value_ty=Sum(Promo)).order_by(
                        'tesco_week'))

                trend_promo_ly = list(
                    promo_view.objects.filter(**kwargs_ly).values("tesco_week").annotate(value_ly=Sum(Promo)).order_by(
                        'tesco_week'))

            else:

                kwargs_par = {
                    'tesco_week__in': week_var,
                    'product_id__in': products,
                    'store_type__in': store_type
                }

                kwargs_par_ly = {
                    'tesco_week__in': lastyearweek,
                    'product_id__in': products,
                    'store_type__in': store_type
                }

                metric = 'Participation'
                no_pref = ''
                no_suffix = '%'
                trend_promo_ty = read_frame(
                    promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values(
                        "tesco_week").annotate(
                         promo_ty=Sum(Promo)).order_by('tesco_week'))

                trend_promo_par = read_frame(promo_view.objects.filter(**kwargs_par).values("tesco_week").annotate(total=Sum(Total)).order_by('tesco_week'))
                trend_promo_ly = read_frame(
                    promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values(
                        "tesco_week").annotate(promo_ly=Sum(Promo)).order_by(
                        'tesco_week'))
                trend_promo_par_ly = read_frame(promo_view.objects.filter(**kwargs_par_ly).values(
                "tesco_week").annotate(total=Sum(Total)).order_by('tesco_week'))

                trend_promo_ty = pd.merge(trend_promo_par,trend_promo_ty, on='tesco_week', how='left')

                trend_promo_ly = pd.merge(trend_promo_par_ly,trend_promo_ly,  on='tesco_week', how='left')

                trend_promo_ty['promo_ty'] = trend_promo_ty['promo_ty'].astype(float)
                trend_promo_ty['total'] = trend_promo_ty['total'].astype(float)
                trend_promo_ty['value_ty'] = trend_promo_ty['promo_ty']*100/trend_promo_ty['total']

                trend_promo_ly['promo_ly'] = trend_promo_ly['promo_ly'].astype(float)
                trend_promo_ly['total'] = trend_promo_ly['total'].astype(float)
                trend_promo_ly['value_ly'] = trend_promo_ly['promo_ly']*100/trend_promo_ly['total']

                trend_promo_ty = trend_promo_ty.fillna(0)
                trend_promo_ly = trend_promo_ly.fillna(0)

        try:
            trend_promo_ty = pd.DataFrame(trend_promo_ty)
            trend_promo_ty['value_ty'] = trend_promo_ty['value_ty'].astype('float')
            trend_promo_ty = trend_promo_ty[np.isfinite(trend_promo_ty['value_ty'])]
            trend_promo_ly = pd.DataFrame(trend_promo_ly)
            trend_promo_ly['value_ly'] = trend_promo_ly['value_ly'].astype('float')
            trend_promo_ly = trend_promo_ly[np.isfinite(trend_promo_ly['value_ly'])]
            trend_promo_ly = trend_promo_ly.rename(columns={'tesco_week': 'tesco_week_ly'})
            trend_promo_ly = trend_promo_ly[np.isfinite(trend_promo_ly['tesco_week_ly'])]
            trend_promo_ly['tesco_week'] = trend_promo_ly['tesco_week_ly'] + 100
            trend = pd.merge(trend_promo_ty, trend_promo_ly, on='tesco_week', how='left')
            trend = trend.fillna(0)
            trend = trend.to_dict(orient='records')
            data_available = 'yes'
        except:
            trend = 0
            data_available = 'no'

        data_dict = {}
        data_dict['trend'] = trend
        data_dict['metric'] = metric
        data_dict['no_pref'] = no_pref
        data_dict['no_suffix'] = no_suffix
        data_dict['data_available'] = data_available

        return JsonResponse(data_dict, safe=False)

class promo_prodtable(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # for metric tab
        metric = args.pop('metric__in', ['value'])
        # for week tab
        week_flag = args.pop('week_flag__in', ['Selected Week'])
        week_flag = week_flag[0]
        # for kpi type tab
        kpi_type = args.pop('kpi_type__in', ['value'])
        kpi_type = kpi_type[0]
        # for Promo type tab
        promo_type = args.pop('promo_type__in', ['Total Promo'])
        # for current week value

        store_type = args.pop('store_type__in', ['Main Estate','Express'])

        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        currentweek = args.pop('tesco_week__in', max_week)
        currentweek = int(currentweek[0])
        lastweek = last_week(currentweek)

        chart_flag = 0
        week_var = week_selection(currentweek, week_flag, chart_flag)
        lastyearweek = lastyearweek_selection(week_var)

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', ['Beers'])
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

        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
            tab_prod_description = list(
                sales_heirarchy.objects.filter(**kwargs_header).values('product_id', 'product','brand_name').distinct())
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
            tab_prod_description = list(
                sales_heirarchy.objects.filter(**args).values('product_id', 'product','brand_name').distinct())
        tab_prod_description = pd.DataFrame(tab_prod_description)

        if promo_type is None:
            kwargs = {
                'tesco_week__in': week_var,
                'product_id__in': products,
                'store_type__in': store_type
            }
            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': products,
                'store_type__in': store_type
            }
        else:
            kwargs = {
                'tesco_week__in': week_var,
                'product_id__in': products,
                'promo_type__in': promo_type,
                'store_type__in': store_type
            }
            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': products,
                'promo_type__in': promo_type,
                'store_type__in': store_type
            }
        if (kpi_type == 'value'):
            Total = 'total_sales'
            Promo = 'promo_sales'
            Promo_lfl = 'promo_sales_lfl'
            yaxis_title = 'Value'
            no_pref = '£'
        elif(kpi_type == 'profit'):
            Total = 'total_profit'
            Promo = 'promo_profit'
            Promo_lfl = 'promo_profit_lfl'
            yaxis_title = 'Profit'
            no_pref = '£'
        elif(kpi_type == 'giveaway'):
            Total = 'total_giveaway'
            Promo = 'promo_giveaway'
            Promo_lfl = 'promo_giveaway_lfl'
            yaxis_title = 'Giveaway'
            no_pref = '£'
        else:
            Total = 'total_volume'
            Promo = 'promo_volume'
            Promo_lfl = 'promo_volume_lfl'
            yaxis_title = 'Volume'
            no_pref = ''
        kwargs_tab = {
            'tesco_week__in': week_var,
            'product_id__in': products,
            'store_type__in': store_type
        }
        kwargs_tab_ly = {
            'tesco_week__in': lastyearweek,
            'product_id__in': products,
            'store_type__in': store_type

        }

        # CALCULATION FOR TABLE
        table_list = list(
            promo_view.objects.filter(**kwargs_tab).values('product_id').exclude(promo_type='Non Promo').annotate(
                promo_ty=Sum(Promo), promo_lfl_ty=Sum(Promo_lfl)).order_by('-promo_ty'))
        table_list_ly = list(promo_view.objects.filter(**kwargs_tab_ly).values('product_id').exclude(
            promo_type='Non Promo').annotate(promo_ly=Sum(Promo), promo_lfl_ly=Sum(Promo_lfl)).order_by(
            '-promo_ly'))
        try:
            table_list = pd.DataFrame(table_list)
            table_list['promo_ty'] = table_list['promo_ty'].astype(int)
            table_list = table_list.fillna(0)
            table_list_ly = pd.DataFrame(table_list_ly)
            table_list_ly['promo_ly'] = table_list_ly['promo_ly'].astype(int)
            table_list_ly = table_list_ly.fillna(0)
            table_list = pd.merge(table_list, table_list_ly, on='product_id', how='left')
            table_list = table_list.fillna(0)
            table_list['promo_lfl_ty'] = table_list['promo_lfl_ty'].astype(float)
            table_list['promo_lfl_ly'] = table_list['promo_lfl_ly'].astype(float)
            table_list['promoted_ly_ind'] = np.where(table_list['promo_ly'] > 0, 'Yes', 'No')
            table_list['promo_lfl_ty'] = table_list['promo_lfl_ty'].astype(float)


            # Fuction for lfl calculation

        except:
            print('exception')

        # Function for Calculating LFL Indicator
        def tabfunc2(row):
            if (row['promo_lfl_ly'] > 0):
                a = round((((row['promo_lfl_ty']-row['promo_lfl_ly'])*100)/row['promo_lfl_ly']),1)
                return a
            else:
                return 'NA'



        def tabfunc(row):
            if (row['promo_ty'] > 0):
                if (row['promo_ly'] == 0):
                    return 'No'
                else:
                    return 'Yes'
            else:
                return 'No'

        try:
            table_list['lfl_ind'] = table_list.apply(tabfunc, axis=1)
        except:
            print("exception")
        try:
            table_list['lfl_var'] =table_list.apply(tabfunc2, axis=1)
        except:
            print("exception")
        try:
            table_list = pd.merge(table_list, tab_prod_description, on='product_id', how='left')
            table_list['product'] = table_list['product'].fillna('')
            table_list = table_list.fillna(0)
            table_list = table_list.rename(
                columns={'promo_ty': 'Promo TY', 'promo_ly': 'Promo LY', 'lfl_ind': 'LFL Indicator',
                         'product': 'Product Description'})
            table_list['index'] = range(0,len(table_list))

            df_new = table_list
            table_list = df_new.to_dict(orient='records')
            data_table = table_list
        except:
            data_table = 0
        sales_data = {}
        sales_data['table_data'] = data_table
        sales_data['col_name'] = yaxis_title
        return JsonResponse(sales_data, safe=False)

class promo_product_level_info(APIView):
    def get(self, request, *args):
        # print("args recieved")
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

        sep_args = args_params(args, 0)
        selected = sales_heirarchy.objects.filter(product__in=sep_args['selected_product']).values('product_id').distinct()

        if (sep_args['kpi_type'] == 'value'):
            total = 'total_sales'
            total_lfl = 'total_sales_lfl'
            promo = 'promo_sales'
            promo_lfl = 'promo_sales_lfl'
            nonpromo = 'nonpromo_sales'
            nonpromo_lfl = 'nonpromo_sales_lfl'
            kpi_name = 'Value'
            format_type = '£'
        elif (sep_args['kpi_type'] == 'profit'):

            total = 'total_profit'
            total_lfl = 'total_profit_lfl'
            promo = 'promo_profit'
            promo_lfl = 'promo_profit_lfl'
            nonpromo = 'nonpromo_profit'
            nonpromo_lfl = 'nonpromo_profit_lfl'
            kpi_name = 'Profit'
            format_type = '£'
        else:
            total = 'total_volume'
            total_lfl = 'total_volume_lfl'
            promo = 'promo_volume'
            promo_lfl = 'promo_volume_lfl'
            nonpromo = 'nonpromo_volume'
            nonpromo_lfl = 'nonpromo_volume_lfl'
            kpi_name = 'Volume'
            format_type = '£'

        kwargs = {
            'tesco_week__in': sep_args['week'],
            'product_id__in': selected,
            'store_type__in': sep_args['store_type']}

        kwargs_lw = {
            'tesco_week': sep_args['lastweek'],
            'product_id__in': selected,
            'store_type__in': sep_args['store_type']
        }

        kwargs_ly = {
            'tesco_week__in': sep_args['lastyearweek'],
            'product_id__in': selected,
            'store_type__in': sep_args['store_type']
        }

        if sep_args['kpi_type'] == 'giveaway':
            current_week_data = promo_view.objects.filter(**kwargs).aggregate(giveaway= Sum('promo_giveaway'),
                                                                               giveaway_lfl = Sum('promo_giveaway')
                                                                               )
            print("Current week data")
            # print(current_week_data)
            last_week_data = promo_view.objects.filter(**kwargs_lw).aggregate(giveaway= Sum('promo_giveaway'),
                                                                               giveaway_lfl = Sum('promo_giveaway')
                                                                               )

            last_year_data = promo_view.objects.filter(**kwargs_ly).aggregate(giveaway= Sum('promo_giveaway'),
                                                                               giveaway_lfl = Sum('promo_giveaway')
                                                                               )

            ########################################### Calculations  #######################################################
            try:
                cw_total = format(current_week_data['giveaway'], '.0f')
            except:
                cw_total = 0
            try:
                cw_total_lfl = format(current_week_data['giveawayl_lfl'], '.1f')
            except:
                cw_total_lfl = 0


            var_total_yoy = var_calc(current_week_data['giveaway'],last_year_data['giveaway'])


            var_total_yoy_lfl = var_calc(current_week_data['giveaway_lfl'],last_year_data['giveaway_lfl'])

                #########print("try 1")


            var_total_wow = var_calc(current_week_data['giveaway'],last_week_data['giveaway'])





            integer_val = int(float(cw_total) / 1000)
            total = '£' + intcomma((integer_val)) + 'K'

            integer_val = int(float(cw_total_lfl) / 1000)
            total_lfl = '£' + intcomma((integer_val)) + 'K'


            total_kpi = {}
            total_kpi['total'] = total
            total_kpi['total_lfl'] = total_lfl
            total_kpi['var_total_yoy'] = var_total_yoy
            total_kpi['var_total_wow'] = var_total_wow
            total_kpi['var_total_lfl'] = var_total_yoy_lfl

            kpi = {}
            kpi['total'] = total_kpi

            kpi['kpi_name'] = 'Giveaway'
            kpi['selected_week'] = sep_args['currentweek']



        elif sep_args['kpi_type'] == 'products_count':

            current_week_total = promo_view.objects.filter(**kwargs).aggregate(product_count=Count('product_id')
                                                                               )
            print("Current week data")
            # print(current_week_data)
            last_week_total = promo_view.objects.filter(**kwargs_lw).aggregate(product_count=Count('product_id')
                                                                               )

            last_year_total = promo_view.objects.filter(**kwargs_ly).aggregate(product_count=Count('product_id')
                                                                               )


            current_week_promo = promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').aggregate(product_count=Count('product_id')
                                                                                )
            print("Current week data")
            # print(current_week_data)
            last_week_promo = promo_view.objects.filter(**kwargs_lw).exclude(promo_type='Non Promo').aggregate(product_count=Count('product_id')
                                                                                )

            last_year_promo = promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').aggregate(product_count=Count('product_id')
                                                                                )


            current_week_nonpromo = promo_view.objects.filter(**kwargs).filter(promo_type='Non Promo').aggregate(
                product_count=Count('product_id')
                )
            print("Current week data")
            # print(current_week_data)
            last_week_nonpromo = promo_view.objects.filter(**kwargs_lw).filter(promo_type='Non Promo').aggregate(
                product_count=Count('product_id')
                )

            last_year_nonpromo = promo_view.objects.filter(**kwargs_ly).filter(promo_type='Non Promo').aggregate(
                product_count=Count('product_id')
                )


            ########################################### Calculations  #######################################################
            try:
                cw_total = format(current_week_total['product_count'], '.0f')
            except:
                cw_total = 0

            # Current Promo
            try:
                cw_promo = format(current_week_promo['product_count'], '.0f')
            except:
                cw_promo = 0


            # Current Non Promo
            try:
                cw_nonpromo = format(current_week_nonpromo['product_count'], '.0f')
            except:
                cw_nonpromo = 0
            # Last Non Promo



            total_kpi = {}
            total_kpi['total'] = cw_total
            total_kpi['var_total_yoy'] = var_calc(current_week_total['product_count'],last_year_total['product_count'])
            total_kpi['var_total_wow'] = var_calc(current_week_total['product_count'],last_week_total['product_count'])


            promo_kpi = {}
            promo_kpi['promo'] = cw_promo
            promo_kpi['var_promo_yoy'] = var_calc(current_week_promo['product_count'],last_year_promo['product_count'])
            promo_kpi['var_promo_wow'] = var_calc(current_week_promo['product_count'],last_week_promo['product_count'])

            nonpromo_kpi = {}
            nonpromo_kpi['nonpromo'] = cw_nonpromo
            nonpromo_kpi['var_nonpromo_yoy'] = var_calc(current_week_nonpromo['product_count'],last_year_nonpromo['product_count'])
            nonpromo_kpi['var_nonpromo_wow'] = var_calc(current_week_nonpromo['product_count'],last_week_nonpromo['product_count'])

            kpi = {}
            kpi['total'] = total_kpi
            kpi['promo'] = promo_kpi
            kpi['nonpromo'] = nonpromo_kpi
            kpi['kpi_name'] = 'Product Count'
            kpi['selected_week'] = sep_args['currentweek']

        else:
            current_week_data = promo_view.objects.filter(**kwargs).aggregate(total=Sum(total),
                                                                               total_lfl=Sum(total_lfl),
                                                                               promo=Sum(promo),
                                                                               promo_lfl=Sum(promo_lfl),
                                                                               nonpromo=Sum(nonpromo),
                                                                               nonpromo_lfl=Sum(nonpromo_lfl),
                                                                               Total_Volume=Sum('total_volume'),
                                                                               Total_Sales=Sum('total_sales'),
                                                                               nonpromo_sales=Sum('nonpromo_sales'),
                                                                               nonpromo_Volume=Sum('nonpromo_volume'),
                                                                               promo_sales=Sum('promo_sales'),
                                                                               promo_Volume=Sum('promo_volume'),

                                                                               )

            last_week_data = promo_view.objects.filter(**kwargs_lw).aggregate(total=Sum(total),
                                                                               total_lfl=Sum(total_lfl),
                                                                               promo=Sum(promo),
                                                                               promo_lfl=Sum(promo_lfl),
                                                                               nonpromo=Sum(nonpromo),
                                                                               nonpromo_lfl=Sum(nonpromo_lfl)
                                                                               )

            last_year_data = promo_view.objects.filter(**kwargs_ly).aggregate(total=Sum(total),
                                                                               total_lfl=Sum(total_lfl),
                                                                               promo=Sum(promo),
                                                                               promo_lfl=Sum(promo_lfl),
                                                                               nonpromo=Sum(nonpromo),
                                                                               nonpromo_lfl=Sum(nonpromo_lfl)
                                                                               )

            ########################################### Calculations  #######################################################

                #    ###########################################       Total ASP      #######################################################

            try:
                total_asp = current_week_data['Total_Sales'] / current_week_data['Total_Volume']
            except:
                total_asp = 0
                #    ###########################################       Promo ASP      #######################################################

            try:
                promo_asp = current_week_data['promo_sales'] / current_week_data['promo_Volume']
            except:
                promo_asp = 0

                #    ###########################################       Non Promo ASP  #######################################################

            try:
                nonpromo_asp = current_week_data['nonpromo_sales'] / current_week_data['nonpromo_Volume']
            except:
                nonpromo_asp = 0

            total_asp_new = '£' + format(total_asp, '.1f')
            promo_asp_new = '£' + format(promo_asp, '.1f')
            nonpromo_asp_new = '£' + format(nonpromo_asp, '.1f')

            asp = {}
            asp["promo_asp"] = promo_asp_new
            asp["nonpromo_asp"] = nonpromo_asp_new

            total_kpi = {}
            total_kpi['total'] = format_kpi(current_week_data['total'],format_type)
            total_kpi['total_lfl'] = format_kpi(current_week_data['total_lfl'],format_type)
            total_kpi['var_total_yoy'] = var_calc(current_week_data['total'],last_year_data['total'])
            total_kpi['var_total_wow'] = var_calc(current_week_data['total'],last_week_data['total'])
            total_kpi['var_total_lfl'] = var_calc(current_week_data['total_lfl'],last_year_data['total_lfl'])

            promo_kpi = {}
            promo_kpi['promo'] = format_kpi(current_week_data['promo'],format_type)
            promo_kpi['promo_lfl'] = format_kpi(current_week_data['promo_lfl'],format_type)
            promo_kpi['var_promo_yoy'] = var_calc(current_week_data['promo'],last_year_data['promo'])
            promo_kpi['var_promo_wow'] = var_calc(current_week_data['promo'],last_week_data['promo'])
            promo_kpi['var_promo_lfl'] = var_calc(current_week_data['promo_lfl'],last_year_data['promo_lfl'])

            nonpromo_kpi = {}
            nonpromo_kpi['nonpromo'] = format_kpi(current_week_data['nonpromo'],format_type)
            nonpromo_kpi['nonpromo_lfl'] = format_kpi(current_week_data['nonpromo_lfl'],format_type)
            nonpromo_kpi['var_nonpromo_yoy'] = var_calc(current_week_data['nonpromo'],last_year_data['nonpromo'])
            nonpromo_kpi['var_nonpromo_wow'] = var_calc(current_week_data['nonpromo'],last_week_data['nonpromo'])
            nonpromo_kpi['var_nonpromo_lfl'] = var_calc(current_week_data['nonpromo_lfl'],last_year_data['nonpromo_lfl'])



            kpi = {}
            kpi['total'] = total_kpi
            kpi['promo'] = promo_kpi
            kpi['nonpromo'] = nonpromo_kpi
            kpi['asp'] = asp
            kpi['kpi_name'] = kpi_name
            kpi['selected_week'] = sep_args['currentweek']

        # Pie chart calculation

        kwargs_pie = {
            'tesco_week__in': sep_args['week'],
            'product_id__in': selected,
        }

        print(kwargs_pie)
        print('kwargs_pie')


        if sep_args['metric'][0] == 'value':
            if (sep_args['metric'][0] == 'value'):
                Total = 'total_sales'
                Promo = 'promo_sales'
            elif (sep_args['metric'][0] == 'profit'):
                Total = 'total_profit'
                Promo = 'promo_profit'
            else:
                Total = 'total_volume'
                Promo = 'promo_volume'




            # Pie chart for promo sales
            pie_chart_info = list(
                promo_view.objects.filter(**kwargs_pie).values('promo_type').annotate(value=Sum(Total)))


        elif sep_args['metric'][0] == 'giveaway':
            # Promo Giveaway calculation
            pie_chart_info= list(
                promo_view.objects.filter(**kwargs_pie).exclude(promo_type='Non Promo').values(
                    'promo_type').annotate(value=Sum('promo_giveaway')))

        # try:
        pie_chart = pd.DataFrame(pie_chart_info)
        pie_chart['value'] = pie_chart['value'].astype('float')
        pie_chart = pie_chart.rename(columns={'promo_type': 'label'})

        temp_label = pie_chart['label']
        label = []
        label.extend(['Total Promo'])
        label.extend(list(temp_label))
        label = [x for x in label if x != '?']
        label = [x for x in label if x != 'Non Promo']
        label = [x for x in label if x != 'Other']
        pie_chart = pie_chart.replace('?', 'Non Promo')
        pie_chart = pie_chart.to_dict(orient='records')
        print("pie chart+++++++++++++++++")
        print(pie_chart)
        data_available = 'yes'
        # except:
        #     pie_chart = 0
        #     data_available = 'no'
        #     labels = []

        pie_chart_info = {}
        pie_chart_info['piechart'] = pie_chart
        pie_chart_info['labels'] = label




       #Trend calculation

        chart_flag = 1
        week = week_selection(sep_args['currentweek'],sep_args['week_flag'],chart_flag)
        lastyearweek = lastyearweek_selection(week)
        print("sep_args['promo_type']")
        print(sep_args['promo_type'][0])
        if (sep_args['promo_type'][0] == 'Total Promo' or sep_args['promo_type'] is None):
            kwargs = {
                'tesco_week__in': week,
                'product_id__in': selected,
            }

            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': selected
            }
            print("+_+_+_+_+_+_+")
        else:
            kwargs = {
                'tesco_week__in': week,
                'product_id__in': selected,
                'promo_type__in': sep_args['promo_type']
            }

            kwargs_ly = {
                'tesco_week__in': lastyearweek,
                'product_id__in': selected,
                'promo_type__in': sep_args['promo_type']
            }
        print(kwargs)
        print('kwargs')
        if sep_args['metric'][0] == 'value':
            print("In valueeeeeeeeeeee+++++++++++++++++++++++")
            if (sep_args['kpi_type'] == 'value'):
                Total = 'total_sales'
                Promo = 'promo_sales'
                Promo_lfl = 'promo_sales_lfl'
                yaxis_title = 'Value'
                no_pref = '£'
                no_suffix = ''
                metric = 'Value'
            elif (sep_args['kpi_type'] == 'profit'):
                Total = 'total_profit'
                Promo = 'promo_profit'
                Promo_lfl = 'promo_profit_lfl'
                yaxis_title = 'Profit'
                no_pref = '£'
                no_suffix = ''
                line_chart_type = 'absolute'
                metric = 'Profit'
            else:
                Total = 'total_volume'
                Promo = 'promo_volume'
                Promo_lfl = 'promo_volume_lfl'
                yaxis_title = 'Volume'
                no_pref = ''
                no_suffix = ''
                metric = 'Volume'
            line_chart_type = 'absolute'
            if (line_chart_type == 'absolute'):
                trend_promo_ty = list(
                    promo_view.objects.filter(**kwargs).values("tesco_week").annotate(value_ty=Sum(Promo)).order_by(
                        'tesco_week'))

                trend_promo_ly = list(
                    promo_view.objects.filter(**kwargs_ly).values("tesco_week").annotate(value_ly=Sum(Promo)).order_by(
                        'tesco_week'))

            else:

                kwargs_par = {
                    'tesco_week__in': week_var,
                    'product_id__in': products,
                    'store_type__in': store_type
                }

                kwargs_par_ly = {
                    'tesco_week__in': lastyearweek,
                    'product_id__in': products,
                    'store_type__in': store_type
                }

                metric = 'Participation'
                no_pref = ''
                no_suffix = '%'
                trend_promo_ty = read_frame(
                    promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values(
                        "tesco_week").annotate(
                        promo_ty=Sum(Promo)).order_by('tesco_week'))

                trend_promo_par = read_frame(
                    promo_view.objects.filter(**kwargs_par).values("tesco_week").annotate(total=Sum(Total)).order_by(
                        'tesco_week'))
                trend_promo_ly = read_frame(
                    promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values(
                        "tesco_week").annotate(promo_ly=Sum(Promo)).order_by(
                        'tesco_week'))
                trend_promo_par_ly = read_frame(promo_view.objects.filter(**kwargs_par_ly).values(
                    "tesco_week").annotate(total=Sum(Total)).order_by('tesco_week'))

                trend_promo_ty = pd.merge(trend_promo_par, trend_promo_ty, on='tesco_week', how='left')

                trend_promo_ly = pd.merge(trend_promo_par_ly, trend_promo_ly, on='tesco_week', how='left')

                trend_promo_ty['promo_ty'] = trend_promo_ty['promo_ty'].astype(float)
                trend_promo_ty['total'] = trend_promo_ty['total'].astype(float)
                trend_promo_ty['value_ty'] = trend_promo_ty['promo_ty'] * 100 / trend_promo_ty['total']

                trend_promo_ly['promo_ly'] = trend_promo_ly['promo_ly'].astype(float)
                trend_promo_ly['total'] = trend_promo_ly['total'].astype(float)
                trend_promo_ly['value_ly'] = trend_promo_ly['promo_ly'] * 100 / trend_promo_ly['total']

                trend_promo_ty = trend_promo_ty.fillna(0)
                trend_promo_ly = trend_promo_ly.fillna(0)


        elif sep_args['metric'][0] == 'giveaway':
            trend_promo_ty = list(
                promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    value_ty=Sum('promo_giveaway')).order_by('tesco_week'))
            trend_promo_ly = list(
                promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values(
                    "tesco_week").annotate(value_ly=Sum('promo_giveaway')).order_by('tesco_week'))
            metric = 'Promo Giveaway'
            no_pref = '£'
            no_suffix = ''
        elif sep_args['metric'][0] == 'products_count':
            trend_promo_ty = list(
                promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    value_ty=Count('product_id', distinct=True)).order_by('tesco_week'))
            trend_promo_ly = list(
                promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    value_ly=Count('product_id', distinct=True)).order_by('tesco_week'))
            metric = 'Products on Promo'
            no_pref = ''
            no_suffix = ''
        elif sep_args['metric'][0] == 'participation':
            if (sep_args['kpi_type'] == 'volume'):
                promo = 'promo_volume'
                total = 'total_volume'
            else:
                promo = 'promo_sales'
                total = 'total_sales'

            metric = 'Participation'
            no_pref = ''
            no_suffix = ''
            trend_promo_ty = list(
                promo_view.objects.filter(**kwargs).exclude(promo_type='Non Promo').values("tesco_week").annotate(
                    sum_tot_val=Sum(total), sum_prom_val=Sum(promo)).annotate(
                    value_ty=Case(When(sum_tot_val=0, then=0),
                                  default=100.0 * F('sum_prom_val') / F('sum_tot_val'))).order_by('tesco_week'))
            trend_promo_ly = list(
                promo_view.objects.filter(**kwargs_ly).exclude(promo_type='Non Promo').values(
                    "tesco_week").annotate(sum_tot_val_ly=Sum(total), sum_prom_val_ly=Sum(promo)).annotate(
                    value_ly=Case(When(sum_tot_val_ly=0, then=0),
                                  default=100.0 * F('sum_prom_val_ly') / F('sum_tot_val_ly'))).order_by(
                    'tesco_week'))

        try:
            trend_promo_ty = pd.DataFrame(trend_promo_ty)
            trend_promo_ty['value_ty'] = trend_promo_ty['value_ty'].astype('float')
            trend_promo_ty = trend_promo_ty[np.isfinite(trend_promo_ty['value_ty'])]
            trend_promo_ly = pd.DataFrame(trend_promo_ly)
            trend_promo_ly['value_ly'] = trend_promo_ly['value_ly'].astype('float')
            trend_promo_ly = trend_promo_ly[np.isfinite(trend_promo_ly['value_ly'])]
            trend_promo_ly = trend_promo_ly.rename(columns={'tesco_week': 'tesco_week_ly'})
            trend_promo_ly = trend_promo_ly[np.isfinite(trend_promo_ly['tesco_week_ly'])]
            trend_promo_ly['tesco_week'] = trend_promo_ly['tesco_week_ly'] + 100
            trend = pd.merge(trend_promo_ty, trend_promo_ly, on='tesco_week', how='left')
            trend = trend.fillna(0)
            trend = trend.to_dict(orient='records')
            data_available = 'yes'

        except:
            trend = 0
            data_available = 'no'
            metric = ''
            no_pref = ''
            no_suffix = ''
        trend_info = {}
        trend_info['trend'] = trend
        trend_info['metric'] = metric
        trend_info['no_pref'] = no_pref
        trend_info['no_suffix'] = no_suffix
        trend_info['data_available'] = data_available

        data = {}
        data['kpi_data'] = kpi
        data['pieChartData'] = pie_chart_info
        data['trendChartData'] = trend_info
        logging.info(data)
        return JsonResponse(data, safe=False)

class promo_mechanic_name_level_info(APIView):
    def get(self, request, *args):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        sep_args = args_params(args,0)

        if buyer_header is None:
            kwargs_header = {
                'buying_controller__in': sep_args['buying_controller_header']
            }
        else:
            kwargs_header = {
                'buying_controller__in': sep_args['buying_controller_header'],
                'buyer__in': sep_args['buyer_header']
            }

        if not args:
            products = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
            tab_prod_description = list(
                sales_heirarchy.objects.filter(**kwargs_header).values('product_id', 'product','brand_name').distinct())
        else:
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
            tab_prod_description = list(
                sales_heirarchy.objects.filter(**args).values('product_id', 'product','brand_name').distinct())
        tab_prod_description = pd.DataFrame(tab_prod_description)

        if sep_args['promo_type'] is None:
            kwargs = {
                'tesco_week__in': sep_args['week'],
                'product_id__in': products,
                'promo_type__in': sep_args['promo_type']
            }
            kwargs_ly = {
                'tesco_week__in': sep_args['lastyearweek'],
                'product_id__in': products,
                'promo_type__in': sep_args['promo_type']
            }
        else:
            kwargs = {
                'tesco_week__in': sep_args['week'],
                'product_id__in': products,
                'promo_type__in': sep_args['promo_type']
            }
            kwargs_ly = {
                'tesco_week__in': sep_args['lastyearweek'],
                'product_id__in': products,
                'promo_type__in': sep_args['promo_type']
            }
        if (sep_args['kpi_type'] == 'value'):
            Total = 'total_sales'
            Promo = 'promo_sales'
            Promo_lfl = 'promo_sales_lfl'
            yaxis_title = 'Value'
            no_pref = '£'
        elif(sep_args['kpi_type'] == 'profit'):
            Total = 'total_profit'
            Promo = 'promo_profit'
            Promo_lfl = 'promo_profit_lfl'
            yaxis_title = 'Profit'
            no_pref = '£'
        elif(sep_args['kpi_type'] == 'giveaway'):
            Total = 'total_giveaway'
            Promo = 'promo_giveaway'
            Promo_lfl = 'promo_giveaway_lfl'
            yaxis_title = 'Giveaway'
            no_pref = '£'
        else:
            Total = 'total_volume'
            Promo = 'promo_volume'
            Promo_lfl = 'promo_volume_lfl'
            yaxis_title = 'Volume'
            no_pref = ''
        kwargs_tab = {
            'tesco_week__in': sep_args['week_var'],
            'product_id__in': products,
            'promo_type__in': sep_args['promo_type']
        }
        kwargs_tab_ly = {
            'tesco_week__in': sep_args['lastyearweek'],
            'product_id__in': products,
            'promo_type__in': sep_args['promo_type']
        }

        # CALCULATION FOR TABLE
        table_list = list(
            promo_view.objects.filter(**kwargs_tab).values('product_id','promo_name').exclude(promo_type='Non Promo').annotate(
                promo_ty=Sum(Promo), promo_lfl_ty=Sum(Promo_lfl)).order_by('-promo_ty'))
        table_list_ly = list(promo_view.objects.filter(**kwargs_tab_ly).values('product_id','promo_name').exclude(
            promo_type='Non Promo').annotate(promo_ly=Sum(Promo), promo_lfl_ly=Sum(Promo_lfl)).order_by(
            '-promo_ly'))
        try:
            table_list = pd.DataFrame(table_list)
            table_list['promo_ty'] = table_list['promo_ty'].astype(int)
            table_list = table_list.fillna(0)
            table_list_ly = pd.DataFrame(table_list_ly)
            table_list_ly['promo_ly'] = table_list_ly['promo_ly'].astype(int)
            table_list_ly = table_list_ly.fillna(0)
            table_list = pd.merge(table_list, table_list_ly, on='product_id', how='left')
            table_list = table_list.fillna(0)
        except:
            table_list = 0

        # Function for Calculating LFL Indicator
        def tabfunc(row):
            if (row['promo_ty'] > 0):
                if (row['promo_ly'] == 0):
                    return 'No'
                else:
                    return 'Yes'
            else:
                return 'No'



        try:
            table_list = pd.merge(table_list, tab_prod_description, on='product_id', how='left')
            table_list['product'] = table_list['product'].fillna('')
            table_list = table_list.fillna(0)
            table_list = table_list.rename(
                columns={'promo_ty': 'Promo TY', 'promo_ly': 'Promo LY',
                         'product': 'Product Description'})
            table_list['index'] = range(0,len(table_list))

            df_new = table_list
            table_list = df_new.to_dict(orient='records')
            data_table = table_list
        except:
            data_table = 0
        sales_data = {}
        sales_data['table_data'] = data_table
        sales_data['col_name'] = yaxis_title
        logging.info(sales_data)
        return JsonResponse(sales_data, safe=False)

#Function for calculating week time period
def week_selection(cw_week, week_flag,chart_flag):
    week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte = cw_week).values('tesco_week').order_by('-tesco_week').distinct()
    print('cw_week')
    print(cw_week)
    print('week_ordered')
    print(week_ordered)
    last_week = week_ordered[1]
    last_week = last_week['tesco_week']
    if (week_flag == 'Latest 4 Weeks'):
        week_logic = week_ordered[:4]

    elif(week_flag == 'Latest 13 Weeks'):
        week_logic = week_ordered[:13]

    elif(week_flag == 'Latest 26 Weeks'):
        week_logic = week_ordered[:26]

    elif(week_flag == 'YTD'):
        current_week = int(cw_week)
        for_x = int(str(current_week)[-2:])
        week_logic = week_ordered[:for_x]

    else:
        if(chart_flag==1):
            week_logic = week_ordered[:13]
        else:
            week_logic = week_ordered[:1]

    week_var = []
    for i in range(len(week_logic)):
        week_var.append(week_logic[i]['tesco_week'])
    print('week_var')
    print(week_var)

    return week_var

#Function for calculating lastyearweek_selection

def lastyearweek_selection(week):
    last_year_var = [0]*len(week)
    for i in range (0,len(week)):
        last_year_var[i] = week[i]-100
    return last_year_var

#Function for calculating lastweek
def last_week(selected_week):
    x = read_frame(latest_week.objects.all())
    y = x[['week_ty']].drop_duplicates().reset_index(drop=True)
    y = y.sort_values('week_ty',ascending=True)
    y['rank_week'] = range(0,len(y))
    index_thisweek = int(y[y['week_ty']==selected_week].rank_week)
    index_last_week = index_thisweek-1
    last_week = int(y[y['rank_week']==index_last_week].week_ty)
    return(last_week)

#Function for calculating variation
def var_calc(a,b):
    if b != 0:
        try:
            c = format(
            ((a - b) * 100 / b), '.1f')
        except:
            c = 0
    else:
        c = 'NA'

    return c

#Function for seperating arguments

def args_params(args,chart_flag):
    sep_args = {}
    # for metric tab
    sep_args['metric'] = args.pop('metric__in', ['value'])
    # for week tab
    week_flag = args.pop('week_flag__in', ['Selected Week'])
    sep_args['week_flag'] = week_flag[0]
    # for kpi type tab
    kpi_type = args.pop('kpi_type__in', ['value'])
    sep_args['kpi_type'] = kpi_type[0]
    # for Promo type tab
    sep_args['promo_type'] = args.pop('promo_type__in', ['Total Promo'])
    # for current week value

    sep_args['store_type'] = args.pop('store_type__in', ['Main Estate', 'Express'])

    tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
    max_week = tesco_week_int['cw_max']
    currentweek = args.pop('tesco_week__in', [max_week])

    currentweek = currentweek[0]
    sep_args['currentweek'] = int(currentweek)

    sep_args['lastweek'] = last_week(currentweek)

    sep_args['week'] = week_selection(sep_args['currentweek'], sep_args['week_flag'], chart_flag)
    sep_args['lastyearweek'] = lastyearweek_selection(sep_args['week'])

    # Product selection
    sep_args['selected_product'] = args.pop('selected__in', None)

    sep_args['user_id'] = args.pop('user_id__in', None)
    sep_args['designation'] = args.pop('designation__in', None)
    sep_args['session_id'] = args.pop('session_id__in', None)
    sep_args['user_name'] = args.pop('user_name__in', None)
    sep_args['buying_controller_header'] = args.pop('buying_controller_header__in', ['Beers'])
    sep_args['buyer_header'] = args.pop('buyer_header__in', None)


    return sep_args

#Function to formatting kpi
def format_kpi(a,format_type):
    if (format_type == '£'):
        integer_val = int(float(a) / 1000)
        a = '£' + intcomma((integer_val)) + 'K'

    else:
        integer_val = int(float(a) / 1000)
        a = intcomma((integer_val)) + 'K'

    return a

# new filter logic
class promo_filters_new(APIView):
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
                            print("inside if loop")
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
                    #print("loop running for")
                    #print(i)
                    col_name = i + '__in'
                    col_list2 = args_list2.pop(col_name, None)
                    #print("____")
                    data = {i: df[i].unique()}
                    col = pd.DataFrame(data)
                    # print(data)
                    col_df_heirarchy = heirarchy[[i]].drop_duplicates()

                    if 'admin' in designation:
                        if col_list2 is not None:
                            #print("else part")
                            # print(col_df)
                            heirarchy_check = read_frame(
                                sales_heirarchy.objects.filter(buying_controller__in=bc_list).values('commercial_name',
                                                                                                     'category_name',
                                                                                                     'buying_controller',
                                                                                                     'buyer',
                                                                                                     'junior_buyer',
                                                                                                     'product_subgroup',
                                                                                                     'store_type',
                                                                                                     'brand_indicator'))
                            # print("inside buyerrr..")
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
                            # print(kwargs)
                            heirarchy_check = read_frame(
                                sales_heirarchy.objects.filter(**kwargs))
                            col_df_check = pd.merge(col_df_heirarchy,
                                                    heirarchy_check[[i]].drop_duplicates(), how='right')
                            #print("after merge_1...")
                            # print(col_df_check)
                            # print("printing supplier")
                            # print(col)
                            col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
                            # print("after mergeeee...")
                            col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
                            col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
                            #print("printing selected cols")
                            #print(col_df_selected)
                            col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(True)
                            #print(col_df)
                            col_df = col_df.rename(columns={i: 'title'})
                            j = com_list.index(col_list2)
                            if j < 7:
                                if com_list[j + 1] is not None:
                                    #print("inside com list next")
                                    col_df = col_df.rename(columns={'title': i})
                                    col_list_df = pd.DataFrame(col_list2, columns={i})
                                    # print(col_list_df)
                                    data = {i: col_list_df[i].unique()}
                                    #print(data)
                                    col = pd.DataFrame(data)
                                    col['selected'] = True
                                    col['highlighted'] = False
                                    # print(parent_supplier)
                                    col_df = pd.merge(col_df_heirarchy, col, how='left')
                                    col_df['selected'] = col_df['selected'].fillna(False)
                                    col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                    col_df = col_df[[i, 'selected', 'highlighted']]
                                    col_df = col_df.rename(columns={i: 'title'})
                                    #print(col_df)
                        else:
                            col['selected'] = False
                            col['highlighted'] = False
                            col_df = pd.merge(col_df_heirarchy, col, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(True)
                            col_df = col_df.rename(columns={i: 'title'})

                    elif 'buying_controller' in designation:
                        if i == ('buying_controller'):
                            #print("printing buying controller...or buyer...")
                            col['selected'] = True
                            col['highlighted'] = False
                            #print(col)
                            col_df = pd.merge(col_df_heirarchy, col, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(False)
                            col_df = col_df.rename(columns={i: 'title'})
                        else:
                            if col_list2 is not None:
                                #print("else part")
                                # print(col_df)
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
                                # print("inside buyerrr..")
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
                                # print(kwargs)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(**kwargs))
                                col_df_check = pd.merge(col_df_heirarchy,
                                                        heirarchy_check[[i]].drop_duplicates(), how='right')
                                #print("after merge_1...")
                                # print(col_df_check)
                                # print("printing supplier")
                                # print(col)
                                col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
                                # print("after mergeeee...")
                                col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
                                col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
                                #print("printing selected cols")
                                #print(col_df_selected)
                                col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                #print(col_df)
                                col_df = col_df.rename(columns={i: 'title'})
                                j = com_list.index(col_list2)
                                if j < 7:
                                    if com_list[j + 1] is not None:
                                        #print("inside com list next")
                                        col_df = col_df.rename(columns={'title': i})
                                        col_list_df = pd.DataFrame(col_list2, columns={i})
                                        # print(col_list_df)
                                        data = {i: col_list_df[i].unique()}
                                        #print(data)
                                        col = pd.DataFrame(data)
                                        col['selected'] = True
                                        col['highlighted'] = False
                                        # print(parent_supplier)
                                        col_df = pd.merge(col_df_heirarchy, col, how='left')
                                        col_df['selected'] = col_df['selected'].fillna(False)
                                        col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                        col_df = col_df[[i, 'selected', 'highlighted']]
                                        col_df = col_df.rename(columns={i: 'title'})
                                        #print(col_df)
                            else:
                                col['selected'] = False
                                col['highlighted'] = False
                                col_df = pd.merge(col_df_heirarchy, col, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                col_df = col_df.rename(columns={i: 'title'})

                    else:
                        if i == ('buying_controller') or i == ('buyer'):
                            #print("printing buying controller...or buyer...")
                            col['selected'] = True
                            col['highlighted'] = False
                            #print(col)
                            col_df = pd.merge(col_df_heirarchy, col, how='left')
                            col_df['selected'] = col_df['selected'].fillna(False)
                            col_df['highlighted'] = col_df['highlighted'].fillna(False)
                            col_df = col_df.rename(columns={i: 'title'})
                        else:
                            if col_list2 is not None:
                                #print("else part")
                                # print(col_df)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(buying_controller__in=bc_list).values('commercial_name',
                                                                                                         'category_name',
                                                                                                         'buying_controller',
                                                                                                         'buyer',
                                                                                                         'junior_buyer',
                                                                                                         'product_subgroup',
                                                                                                         'store_type',
                                                                                                         'brand_indicator'))
                                # print("inside buyerrr..")
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
                                # print(kwargs)
                                heirarchy_check = read_frame(
                                    sales_heirarchy.objects.filter(**kwargs))
                                col_df_check = pd.merge(col_df_heirarchy,
                                                        heirarchy_check[[i]].drop_duplicates(), how='right')
                                #print("after merge_1...")
                                # print(col_df_check)
                                # print("printing supplier")
                                # print(col)
                                col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
                                # print("after mergeeee...")
                                col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
                                col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
                                #print("printing selected cols")
                                #print(col_df_selected)
                                col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
                                col_df['selected'] = col_df['selected'].fillna(False)
                                col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                #print(col_df)
                                col_df = col_df.rename(columns={i: 'title'})
                                j = com_list.index(col_list2)
                                if j < 7:
                                    if com_list[j + 1] is not None:
                                        #print("inside com list next")
                                        col_df = col_df.rename(columns={'title': i})
                                        col_list_df = pd.DataFrame(col_list2, columns={i})
                                        # print(col_list_df)
                                        data = {i: col_list_df[i].unique()}
                                        #print(data)
                                        col = pd.DataFrame(data)
                                        col['selected'] = True
                                        col['highlighted'] = False
                                        # print(parent_supplier)
                                        col_df = pd.merge(col_df_heirarchy, col, how='left')
                                        col_df['selected'] = col_df['selected'].fillna(False)
                                        col_df['highlighted'] = col_df['highlighted'].fillna(True)
                                        col_df = col_df[[i, 'selected', 'highlighted']]
                                        col_df = col_df.rename(columns={i: 'title'})
                                        #print(col_df)
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
                    # print(col_df)
                    col_df['highlighted'] = ~col_df['highlighted']
                    #print("after inverse")
                    #print(col_df)
                    col_df_sel = col_df[['selected']]
                    col_df['resource'] = col_df_sel.to_dict(orient='records')
                    del col_df['selected']
                    col_df_final = col_df.to_json(orient='records')
                    col_df_final = json.loads(col_df_final)
                    #print("---------")
                    # print(col_df_final)
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
                    # print("printing finaaall")
                    # print(final)

        return JsonResponse({'cols': cols, 'checkbox_list': final}, safe=False)



