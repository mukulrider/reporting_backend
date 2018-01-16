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
from .models import sales_heirarchy, competitor_price_bucket, competitor_market_share, \
    competitor_outperform, calendar_dim_hierarchy,competitor_price_index_brand,competitor_price_index_basket, latest_week

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

import collections

timestr = time.strftime("%Y%m%d")
logging.basicConfig(filename='logs/reporting_views_'+timestr+'.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

class competitor_filterdata_week(APIView):
    # @cache_response()
    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}
        print("---------------------")
        week_id = args.get('tesco_week__iexact',None)
        tesco_week_flag = args.pop('tesco_week_flag__iexact',0)

        if week_id is None:
            tesco_week_int = competitor_price_bucket.objects.aggregate(cw_max=Max('tesco_week'))
            max_week = tesco_week_int['cw_max']
            currentweek = args.pop('tesco_week__iexact', max_week)
            week_id = currentweek
            flag=1
        else:
            week_id = int(week_id)
            flag=0

        print(type(week_id))

        kwargs = {
            'tesco_week__iexact': week_id

        }
        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))

        if not args:

            print("inside default")

            weeks_data = read_frame(calendar_dim_hierarchy.objects.all().values('tesco_week'))
            weeks_data = weeks_data[(weeks_data["tesco_week"] >= 201646) & (weeks_data['tesco_week'] <= week_id)]
            # weeks_data = weeks_data[weeks_data['tesco_week'] >= 201646 and weeks_data['tesco_week'] <= 201705]

            # print("After replacing")
            # print(heirarchy)


            data = {'tesco_week': weeks_data.tesco_week.unique()}
            week = pd.DataFrame(data)
            if tesco_week_flag==1:
                week.loc[(week["tesco_week"] == week_id), 'selected'] = True
                week.loc[(week["tesco_week"] != week_id), 'selected'] = False
                week.loc[(week["tesco_week"] == week_id), 'disabled'] = True
                week.loc[(week["tesco_week"] != week_id), 'disabled'] = False
            else:
                week['selected'] = False
                week['disabled'] = False
            # week['selected'] = False
            # week['disabled'] = False

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
            weeks_data = weeks_data[(weeks_data["tesco_week"] >= 201646) & (weeks_data['tesco_week'] <= week_id)]

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

            print(final)
        return JsonResponse(final, safe=False)


# competitor filter data
class competitor_filterdata(APIView):
    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}

        # week_id = args.get('tesco_week__iexact')

        com_id = args.get('commercial_name__iexact')

        cat_id = args.get('category_name__iexact')

        bc_id = args.get('buying_controller__iexact')

        buyer_id = args.get('buyer__iexact')

        jr_buyer_id = args.get('junior_buyer__iexact')

        psg_id = args.get('product_subgroup__iexact')

        if com_id is not None:
            com_id = com_id.replace('and', 'and')
        if cat_id is not None:
            cat_id = cat_id.replace('and', 'and')
        if bc_id is not None:
            bc_id = bc_id.replace('and', 'and')
        if buyer_id is not None:
            buyer_id = buyer_id.replace('and', 'and')
        if jr_buyer_id is not None:
            jr_buyer_id = jr_buyer_id.replace('and', 'and')
        if psg_id is not None:
            psg_id = psg_id.replace('and', 'and')

        sent_req = args
        user_id = sent_req.pop('user_id__iexact', None)
        designation = sent_req.pop('designation__iexact', None)
        session_id = sent_req.pop('session_id__iexact', None)
        user_name = sent_req.pop('user_name__iexact', None)
        buying_controller_header = sent_req.pop('buying_controller_header__iexact', None)
        buyer_header = sent_req.pop('buyer_header__iexact', None)

        if buyer_header is None:
            kwargs_header = {
                'buying_controller': buying_controller_header
            }
        else:
            kwargs_header = {
                'buying_controller': buying_controller_header,
                'buyer': buyer_header
            }

        # if week_id is None:
        #     week_id = 201652
        # else:
        #     week_id = int(week_id)


        # print(type(week_id))

        # kwargs = {
        #             'tesco_week__iexact' : week_id

        # }
        # kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))

        kwargs_temp = {
            'commercial_name__iexact': com_id,
            'category_name__iexact': cat_id,
            'buying_controller__iexact': bc_id,
            'buyer__iexact': buyer_id,
            'junior_buyer__iexact': jr_buyer_id,
            'product_subgroup__iexact': psg_id,

        }

        kwargs_temp = dict(filter(lambda item: item[1] is not None, kwargs_temp.items()))

        # regex = re.compile('^HTTP_')
        # auth_token = dict((regex.sub('', header), value) for (header, value)
        #                   in request.META.items() if header.startswith('HTTP'))
        # headers_incoming = auth_token['AUTHORIZATION']
        # underscore_index = headers_incoming.index('___')
        # user_auth_token = headers_incoming[:underscore_index]
        # user_buyer = headers_incoming[underscore_index+3:]
        # kwargs_user = {
        #     'buyer': user_buyer
        # }

        if not args:

            print("inside default")

            df = read_frame(sales_heirarchy.objects.filter(**kwargs_header))
            heirarchy = read_frame(
                sales_heirarchy.objects.all().filter(**kwargs_header).values('commercial_name', 'category_name',
                                                                             'buying_controller', 'buyer',
                                                                             'junior_buyer', 'product_subgroup'))

            df = df.replace(to_replace='and', value='and', regex=True)
            heirarchy = heirarchy.replace(to_replace='and', value='and', regex=True)

            data = {'commercial_name': df.commercial_name.unique()}
            com_name = pd.DataFrame(data)
            com_name['selected'] = False
            com_name['disabled'] = False

            data = {'category_name': df.commercial_name.unique()}
            cat_name = pd.DataFrame(data)
            cat_name['selected'] = False
            cat_name['disabled'] = False

            data = {'buying_controller': df.buying_controller.unique()}
            bc = pd.DataFrame(data)

            bc['selected'] = True
            bc['disabled'] = False

            data = {'buyer': df.buyer.unique()}
            buyer = pd.DataFrame(data)
            if len(buyer) == 1:
                buyer['selected'] = True
                buyer['disabled'] = False
            else:
                buyer['selected'] = False
                buyer['disabled'] = False

            data = {'junior_buyer': df.junior_buyer.unique()}
            jr_buyer = pd.DataFrame(data)
            jr_buyer['selected'] = False
            jr_buyer['disabled'] = False

            data = {'product_subgroup': df.product_subgroup.unique()}
            psg = pd.DataFrame(data)
            psg['selected'] = False
            psg['disabled'] = False

            com_df = heirarchy[['commercial_name']].drop_duplicates()

            cat_df = heirarchy[['category_name']].drop_duplicates()

            bc_df = heirarchy[['buying_controller']].drop_duplicates()

            buyer_df = heirarchy[['buyer']].drop_duplicates()

            jr_buyer_df = heirarchy[['junior_buyer']].drop_duplicates()

            psg_df = heirarchy[['product_subgroup']].drop_duplicates()

            # week_df = weeks_data[['tesco_week']].drop_duplicates()





            # week_df = pd.merge(week_df,week,how='left')
            # week_df['selected'] =week_df['selected'].fillna(False)
            # week_df['disabled'] =week_df['disabled'].fillna(False)

            # week_df = week_df.rename(columns={'tesco_week': 'name'})


            com_df = pd.merge(com_df, com_name, how='left')
            com_df['selected'] = com_df['selected'].fillna(False)
            com_df['disabled'] = com_df['disabled'].fillna(False)

            com_df = com_df.rename(columns={'commercial_name': 'name'})

            cat_df = pd.merge(cat_df, cat_name, how='left')
            cat_df['selected'] = cat_df['selected'].fillna(False)
            cat_df['disabled'] = cat_df['disabled'].fillna(False)

            cat_df = cat_df.rename(columns={'category_name': 'name'})

            bc_df = pd.merge(bc_df, bc, how='left')
            bc_df['selected'] = bc_df['selected'].fillna(False)
            bc_df['disabled'] = bc_df['disabled'].fillna(False)

            bc_df = bc_df.rename(columns={'buying_controller': 'name'})

            buyer_df = pd.merge(buyer_df, buyer, how='left')
            buyer_df['selected'] = buyer_df['selected'].fillna(False)
            buyer_df['disabled'] = buyer_df['disabled'].fillna(False)
            buyer_df = buyer_df.rename(columns={'buyer': 'name'})

            jr_buyer_df = pd.merge(jr_buyer_df, jr_buyer, how='left')
            jr_buyer_df['selected'] = jr_buyer_df['selected'].fillna(False)
            jr_buyer_df['disabled'] = jr_buyer_df['disabled'].fillna(False)
            jr_buyer_df = jr_buyer_df.rename(columns={'junior_buyer': 'name'})

            psg_df = pd.merge(psg_df, psg, how='left')
            psg_df['selected'] = psg_df['selected'].fillna(False)
            psg_df['disabled'] = psg_df['disabled'].fillna(False)
            psg_df = psg_df.rename(columns={'product_subgroup': 'name'})

            # week_final = week_df.to_json(orient='records')
            # week_final = json.loads(week_final)

            # a = {}
            # a['name']='tesco_week'
            # a['items']=week_final




            com_final = com_df.to_json(orient='records')
            com_final = json.loads(com_final)

            b = {}
            b['name'] = 'commercial_name'
            b['items'] = com_final
            b['required'] = False

            cat_final = cat_df.to_json(orient='records')
            cat_final = json.loads(cat_final)

            c = {}
            c['name'] = 'category_name'
            c['items'] = cat_final
            c['required'] = False

            bc_final = bc_df.to_json(orient='records')
            bc_final = json.loads(bc_final)

            d = {}
            d['name'] = 'buying_controller'
            d['items'] = bc_final
            d['required'] = True

            buyer_final = buyer_df.to_json(orient='records')
            buyer_final = json.loads(buyer_final)

            e = {}
            e['name'] = 'buyer'
            e['items'] = buyer_final
            e['required'] = False

            jr_buyer_final = jr_buyer_df.to_json(orient='records')
            jr_buyer_final = json.loads(jr_buyer_final)

            f = {}
            f['name'] = 'junior_buyer'
            f['items'] = jr_buyer_final
            f['required'] = False

            psg_final = psg_df.to_json(orient='records')
            psg_final = json.loads(psg_final)

            g = {}
            g['name'] = 'product_subgroup'
            g['items'] = psg_final
            g['required'] = False

            final = []
            # final.append(a)
            final.append(b)
            final.append(c)
            final.append(d)
            final.append(e)
            final.append(f)
            final.append(g)
        else:
            heirarchy = read_frame(
                sales_heirarchy.objects.filter(**kwargs_header).values('commercial_name', 'category_name',
                                                                       'buying_controller', 'buyer', 'junior_buyer',
                                                                       'product_subgroup'))

            heirarchy = heirarchy.replace(to_replace='and', value='and', regex=True)
            # weeks_data = read_frame(calendar_dim_hierarchy.objects.all().values('tesco_week'))
            # #weeks_data = weeks_data[weeks_data['tesco_week'] >= 201646 and weeks_data['tesco_week'] >= 201705]
            # weeks_data =   weeks_data[(weeks_data["tesco_week"] >= 201646) & (weeks_data['tesco_week'] <= 201705)]

            # print(heirarchy)
            com_df = heirarchy[['commercial_name']].drop_duplicates()
            cat_df = heirarchy[['category_name']].drop_duplicates()
            bc_df = heirarchy[['buying_controller']].drop_duplicates()
            buyer_df = heirarchy[['buyer']].drop_duplicates()
            jr_buyer_df = heirarchy[['junior_buyer']].drop_duplicates()
            psg_df = heirarchy[['product_subgroup']].drop_duplicates()
            # week_df = weeks_data[['tesco_week']].drop_duplicates()


            df = read_frame(sales_heirarchy.objects.filter(**kwargs_header).filter(**kwargs_temp))
            df = df.replace(to_replace='and', value='and', regex=True)

            # week_temp = read_frame(calendar_dim_hierarchy.objects.filter(**kwargs).values('tesco_week'))

            # print("Comm name ")
            # data ={'tesco_week' : week_temp.tesco_week.unique()}
            # week_name = pd.DataFrame(data)
            # print(len(week_name))

            # print("Comm name ")
            data = {'commercial_name': df.commercial_name.unique()}
            com_name = pd.DataFrame(data)
            # print(len(com_name))



            print("Category Name ")
            data = {'category_name': df.category_name.unique()}
            cat_name = pd.DataFrame(data)
            # print(len(cat_name))


            print("BC ")
            data = {'buying_controller': df.buying_controller.unique()}
            bc = pd.DataFrame(data)
            # print(len(bc))

            print("Buyer ")
            data = {'buyer': df.buyer.unique()}
            buyer = pd.DataFrame(data)
            # print(len(buyer))

            print("Jr Buyer ")
            data = {'junior_buyer': df.junior_buyer.unique()}
            jr_buyer = pd.DataFrame(data)
            # print(len(jr_buyer))


            print("PSG ")
            data = {'product_subgroup': df.product_subgroup.unique()}
            psg = pd.DataFrame(data)
            # print(len(psg))



            if len(com_name) == 1:
                com_name['selected'] = True
                com_name['disabled'] = False
                com_df = pd.merge(com_df, com_name, how='left')
                com_df['selected'] = com_df['selected'].fillna(False)
                com_df['disabled'] = com_df['disabled'].fillna(True)
                com_df = com_df.rename(columns={'commercial_name': 'name'})
            else:
                com_name['selected'] = False
                com_name['disabled'] = False
                com_df = pd.merge(com_df, com_name, how='left')
                com_df['selected'] = com_df['selected'].fillna(False)
                com_df['disabled'] = com_df['disabled'].fillna(True)
                com_df = com_df.rename(columns={'commercial_name': 'name'})

            if len(cat_name) == 1:
                cat_name['selected'] = True
                cat_name['disabled'] = False
                cat_df = pd.merge(cat_df, cat_name, how='left')
                cat_df['selected'] = cat_df['selected'].fillna(False)
                cat_df['disabled'] = cat_df['disabled'].fillna(True)
                cat_df = cat_df.rename(columns={'category_name': 'name'})
            else:
                cat_name['selected'] = False
                cat_name['disabled'] = False
                cat_df = pd.merge(cat_df, cat_name, how='left')
                cat_df['selected'] = cat_df['selected'].fillna(False)
                cat_df['disabled'] = cat_df['disabled'].fillna(True)
                cat_df = cat_df.rename(columns={'category_name': 'name'})

            if len(bc) == 1:
                bc['selected'] = True
                bc['disabled'] = False
                bc_df = pd.merge(bc_df, bc, how='left')
                bc_df['selected'] = bc_df['selected'].fillna(False)
                bc_df['disabled'] = bc_df['disabled'].fillna(True)
                bc_df = bc_df.rename(columns={'buying_controller': 'name'})
            else:
                bc['selected'] = False
                bc['disabled'] = False
                bc_df = pd.merge(bc_df, bc, how='left')
                bc_df['selected'] = bc_df['selected'].fillna(False)
                bc_df['disabled'] = bc_df['disabled'].fillna(True)
                bc_df = bc_df.rename(columns={'buying_controller': 'name'})

            if len(buyer) == 1:
                buyer['selected'] = True
                buyer['disabled'] = False
                buyer_df = pd.merge(buyer_df, buyer, how='left')
                buyer_df['selected'] = buyer_df['selected'].fillna(False)
                buyer_df['disabled'] = buyer_df['disabled'].fillna(True)
                buyer_df = buyer_df.rename(columns={'buyer': 'name'})
            else:
                buyer['selected'] = False
                buyer['disabled'] = False
                buyer_df = pd.merge(buyer_df, buyer, how='left')
                buyer_df['selected'] = buyer_df['selected'].fillna(False)
                buyer_df['disabled'] = buyer_df['disabled'].fillna(True)
                buyer_df = buyer_df.rename(columns={'buyer': 'name'})

            if len(jr_buyer) == 1:
                jr_buyer['selected'] = True
                jr_buyer['disabled'] = False
                jr_buyer_df = pd.merge(jr_buyer_df, jr_buyer, how='left')
                jr_buyer_df['selected'] = jr_buyer_df['selected'].fillna(False)
                jr_buyer_df['disabled'] = jr_buyer_df['disabled'].fillna(True)
                jr_buyer_df = jr_buyer_df.rename(columns={'junior_buyer': 'name'})
            else:
                jr_buyer['selected'] = False
                jr_buyer['disabled'] = False
                jr_buyer_df = pd.merge(jr_buyer_df, jr_buyer, how='left')
                jr_buyer_df['selected'] = jr_buyer_df['selected'].fillna(False)
                jr_buyer_df['disabled'] = jr_buyer_df['disabled'].fillna(True)
                jr_buyer_df = jr_buyer_df.rename(columns={'junior_buyer': 'name'})

            if len(psg) == 1:
                psg['selected'] = True
                psg['disabled'] = False
                psg_df = pd.merge(psg_df, psg, how='left')
                psg_df['selected'] = psg_df['selected'].fillna(False)
                psg_df['disabled'] = psg_df['disabled'].fillna(True)
                psg_df = psg_df.rename(columns={'product_subgroup': 'name'})
            else:
                psg['selected'] = False
                psg['disabled'] = False
                psg_df = pd.merge(psg_df, psg, how='left')
                psg_df['selected'] = psg_df['selected'].fillna(False)
                psg_df['disabled'] = psg_df['disabled'].fillna(True)
                psg_df = psg_df.rename(columns={'product_subgroup': 'name'})

            com_final = com_df.to_json(orient='records')
            com_final = json.loads(com_final)

            b = {}
            b['name'] = 'commercial_name'
            b['items'] = com_final
            b['required'] = False

            cat_final = cat_df.to_json(orient='records')
            cat_final = json.loads(cat_final)

            c = {}
            c['name'] = 'category_name'
            c['items'] = cat_final
            c['required'] = False

            bc_final = bc_df.to_json(orient='records')
            bc_final = json.loads(bc_final)

            d = {}
            d['name'] = 'buying_controller'
            d['items'] = bc_final
            d['required'] = True

            buyer_final = buyer_df.to_json(orient='records')
            buyer_final = json.loads(buyer_final)

            e = {}
            e['name'] = 'buyer'
            e['items'] = buyer_final
            e['required'] = False

            jr_buyer_final = jr_buyer_df.to_json(orient='records')
            jr_buyer_final = json.loads(jr_buyer_final)

            f = {}
            f['name'] = 'junior_buyer'
            f['items'] = jr_buyer_final
            f['required'] = False


            psg_final = psg_df.to_json(orient='records')
            psg_final = json.loads(psg_final)

            g = {}
            g['name'] = 'product_subgroup'
            g['items'] = psg_final
            g['required'] = False

            final = []
            # final.append(a)
            final.append(b)
            final.append(c)
            final.append(d)
            final.append(e)
            final.append(f)
            final.append(g)
            print(final)
        return JsonResponse(final, safe=False)

# Competitor View

class competitor_view_range(APIView):
    def get(self, request, *args):
        ##print("args recieved")
        print("entered function for range change------------------------")
        args = {reqobj: request.GET.get(reqobj) for reqobj in request.GET.keys()}

        # for week tab
        week_flag = args.pop('week_flag', None)

        # for kpi tab
        kpi_type = args.pop('kpi_type', None)

        # for current week value
        tesco_week_int = competitor_price_bucket.objects.aggregate(cw_max=Max('tesco_week'))
        max_week = tesco_week_int['cw_max']
        cw_week = int(args.pop('tesco_week', max_week))
        # cw_week = int(args.pop('tesco_week',201652))

        ##Cookies info
        user_id = args.pop('user_id', None)
        designation = args.pop('designation', None)
        session_id = args.pop('session_id', None)
        user_name = args.pop('user_name', None)
        buying_controller_header = args.pop('buying_controller_header', None)
        buyer_header = args.pop('buyer_header', None)

        ##print(week_flag)

        def range_change(week_flag):

            def week_selection(cw_week, week_flag):
                week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values(
                    'tesco_week').order_by('-tesco_week').distinct()
                last_week = week_ordered[1]
                last_week = last_week['tesco_week']

                if (week_flag == 'Latest 4 Weeks'):
                    week_logic = week_ordered[:4]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))  # ##print("Inside elif 1")

                elif (week_flag == 'Latest 13 Weeks'):
                    week_logic = week_ordered[:13]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                elif (week_flag == 'Latest 52 Weeks'):

                    week_logic = week_ordered[:52]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                elif (week_flag == 'YTD'):

                    current_week = int(cw_week)
                    for_x = int(str(current_week)[-2:])
                    week_logic = week_ordered[:for_x]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))
                else:
                    week_logic = week_ordered[:1]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                week = {"last_week": last_week, "week_var": week_var}
                return week

            week = week_selection(cw_week, week_flag)
            # print(week_flag)
            # print("++++++++++++++++++ week ++++++++++++++++++++++++++++++++++==")
            # print(week)
            if not args:
                if buyer_header is None:
                    kwargs_header = {
                        'buying_controller': buying_controller_header
                    }
                else:
                    kwargs_header = {
                        'buying_controller': buying_controller_header,
                        'buyer': buyer_header
                    }
                productsubgroup = sales_heirarchy.objects.filter(**kwargs_header).values('product_subgroup').distinct()

                print("Default value---------------------------")
                # print(type(productsubgroup))
                # print(productsubgroup)

            else:
                productsubgroup = sales_heirarchy.objects.filter(**args).values('product_subgroup').distinct()
                print("product_subgroup_competitor_price_bucket")
                # print(productsubgroup)
                # print(productsubgroup[0])
                print(week['week_var'])

            print(week['week_var'])
            kwargs = {
                'tesco_week__in': week['week_var'],
                'product_subgroup__in': productsubgroup
            }

            min_max_asp = competitor_price_bucket.objects.filter(**kwargs).aggregate(max_asp=Max('asp'),min_asp=Min('asp'))
            data = {}
            data['min_asp'] = min_max_asp['min_asp']
            data['max_asp'] = min_max_asp['max_asp']
            data['offset'] = abs(data['min_asp'] - data['max_asp']) / 5
            data['first_quantile'] = round(data['min_asp'], 2)
            data['second_quantile'] = round(data['first_quantile'] + data['offset'], 2)
            data['third_quantile'] = round(data['second_quantile'] + data['offset'], 2)
            data['fourth_quantile'] = round(data['third_quantile'] + data['offset'], 2)
            data['fifth_quantile'] = round(data['fourth_quantile'] + data['offset'], 2)
            data['sixth_quantile'] = round(data['fifth_quantile'] + data['offset'], 2)
            data = pd.DataFrame([data],columns=['fifth_quantile', 'first_quantile', 'fourth_quantile', 'max_asp', 'min_asp',
                                         'offset', 'second_quantile', 'sixth_quantile', 'third_quantile'])
            print("kwargs")
            print(kwargs)
            # x_axis = ["£0-£7.5", "£7.6-£12", "£12.1-£14", "£14.1-£19", "£19.1-£21", "£21.1-£23", "£23.1-£27",
            #           "£27.1-£35", "Greater than £35"]

            x_axis = ['£' + str(data["first_quantile"][0]) + ' - ' + '£' + str(data["second_quantile"][0]),
                      '£' + str(data["second_quantile"][0]) + ' - ' + '£' + str(data["third_quantile"][0]),
                      '£' + str(data["third_quantile"][0]) + ' - ' + '£' + str(data["fourth_quantile"][0]),
                      '£' + str(data["fourth_quantile"][0]) + ' - ' + '£' + str(data["fifth_quantile"][0]),
                      '£' + str(data["fifth_quantile"][0]) + ' - ' + '£' + str(data["sixth_quantile"][0])]
            colors = ["#B2B2B2", "#7FB256", "#0931F6", "#C288D6", "#896219", "#EE1C2E"]

            ##### Select tesco week -- Jasdeep, need to change 201620 to variable
            retailers = list(
                competitor_price_bucket.objects.filter(**kwargs).values_list('retailer', flat=True).distinct().order_by(
                    'retailer'))
            print('retailers',retailers)
            # print(retailers)

            # print("Retailers")
            # print(retailers)

            range_chart = [0] * len(retailers)
            label_data = []

            appended_value = []
            for j in range(0, len(retailers)):
                # print("====================== Retailer Calc ")
                # print(retailers[j])

                ##### Need to change filtering and remove Tesco filter---- Jasdeep
                # test = list(competitor_price_bucket.objects.filter(retailer__in = [retailers[j]]).filter(**kwargs).values('product','asp').distinct())
                # try:
                test = read_frame(competitor_price_bucket.objects.filter(**kwargs).filter(retailer=retailers[j]).values(
                    'product_subgroup', 'product_id', 'asp').distinct())
                print("test------------")
                # print(len(test))

                sum_var = [0]*5
                sum_var[0] = len(test.loc[(test["asp"] >= float(data["first_quantile"][0])) & (
                test["asp"] < float(data["second_quantile"][0]))])
                sum_var[1] = len(test.loc[(test["asp"] >= float(data["second_quantile"][0])) & (
                test["asp"] < float(data["third_quantile"][0]))])
                sum_var[2] = len(test.loc[(test["asp"] >= float(data["third_quantile"][0])) & (
                test["asp"] < float(data["fourth_quantile"][0]))])
                sum_var[3] = len(test.loc[(test["asp"] >= float(data["fourth_quantile"][0])) & (
                test["asp"] < float(data["fifth_quantile"][0]))])
                sum_var[4] = len(test.loc[(test["asp"] >= float(data["fifth_quantile"][0])) & (
                test["asp"] < float(data["sixth_quantile"][0]))])

                try:
                    chart_data = pd.DataFrame({'value': sum_var})
                    chart_data['value'] = chart_data['value'].astype(float)
                    chart_data = chart_data.to_dict(orient='records')
                    label_data.append(retailers[j])
                    range_chart[j] = chart_data
                except:
                    chart_data = 0
                    label_data = 0
                    range_chart = 0

                try:

                    for k in range(0, len(sum_var)):
                        appended_value.append(
                            {'id': retailers[j], 'sku_gravity': sum_var[k], 'price_gravity': x_axis[k]}
                        )
                except:
                    appended_value = 0


                    # print("Appended Value")
                    # print(appended_value)

            # data = []
            # data['line1'] = line1
            # data['line2'] = line2
            chart_label = {"data": appended_value, "axis_data": x_axis, 'colors': colors}
            # json_data = json.dumps(chart_label)
            logging.info(chart_label)
            return chart_label

        data = range_change(week_flag)
        # ##print("received data---------")
        # ##print(data)
        return JsonResponse(data, safe=False)

class competitor_market_outperformance(APIView):
    def get(self, request, *args):
        # print("args recieved")
        args = {reqobj: request.GET.get(reqobj) for reqobj in request.GET.keys()}
        # print(args)
        # for week tab
        week_flag = args.pop('week_flag', None)

        # for kpi type tab
        kpi = args.pop('kpi_type', 'value')

        # for current week value
        tesco_week_int = competitor_outperform.objects.aggregate(cw_max=Max('tesco_week'))
        max_week = tesco_week_int['cw_max']
        cw_week = int(args.pop('tesco_week', max_week))
        # cw_week = int(args.pop('tesco_week', 201652))

        user_id = args.pop('user_id', None)
        designation = args.pop('designation', None)
        session_id = args.pop('session_id', None)
        user_name = args.pop('user_name', None)
        buying_controller_header = args.pop('buying_controller_header', None)
        buyer_header = args.pop('buyer_header', None)

        def week_selection(cw_week, week_flag):
            week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                '-tesco_week').distinct()
            last_week = week_ordered[1]
            last_week = last_week['tesco_week']
            if (week_flag == 'Latest 4 Weeks'):
                week_logic = week_ordered[:4]
                week_var = []
                for i in range(len(week_logic)):
                    week_var.append(str(week_logic[i]['tesco_week']))  # ##print("Inside elif 1")

            elif (week_flag == 'Latest 13 Weeks'):
                week_logic = week_ordered[:13]
                week_var = []
                for i in range(len(week_logic)):
                    week_var.append(str(week_logic[i]['tesco_week']))

            elif (week_flag == 'Latest 52 Weeks'):

                week_logic = week_ordered[:52]
                week_var = []
                for i in range(len(week_logic)):
                    week_var.append(str(week_logic[i]['tesco_week']))

            elif (week_flag == 'YTD'):

                current_week = int(cw_week)
                for_x = int(str(current_week)[-2:])
                week_logic = week_ordered[:for_x]
                week_var = []
                for i in range(len(week_logic)):
                    week_var.append(str(week_logic[i]['tesco_week']))
            else:
                week_logic = week_ordered[:1]
                week_var = []
                for i in range(len(week_logic)):
                    week_var.append(str(week_logic[i]['tesco_week']))

            week = {"last_week": last_week, "week_var": week_var}
            return week

        # if not args:
        #     product_subgroup= ['W61HA - CREAM LIQUEURS']
        # else:
        #     product_subgroup = sales_heirarchy.objects.filter(**args).values('product_subgroup').distinct()

        week_var = week_selection(cw_week, week_flag)

        if not args:
            # category_name_data = "Beers, Wines and Spirits"
            if buyer_header is None:
                kwargs = {
                    'buying_controller': buying_controller_header
                }
                selection = "buying_Controller"
            else:
                kwargs = {
                    'buying_controller': buying_controller_header,
                    'buyer': buyer_header
                }
                selection = "buyer"
        else:
            product_subgroup_data = args.pop('product_subgroup', None)
            junior_buyer_data = args.pop('junior_buyer', None)
            buyer_data = args.pop('buyer', None)
            buying_controller_data = args.pop('buying_controller', None)
            category_name_data = args.pop('category_name', None)
            commercial_name_data = args.pop('ccomercial_name', None)


            if product_subgroup_data != None:
                selection = 'product_subgroup'
                kwargs = {
                    'product_subgroup': product_subgroup_data
                }
            elif junior_buyer_data != None:
                selection = 'junior_buyer'
                kwargs = {
                    'junior_buyer': junior_buyer_data
                }
            elif buyer_data != None:
                selection = 'buyer'
                kwargs = {
                    'buyer': buyer_data
                }
            elif buying_controller_data != None:
                selection = 'buying_controller'
                kwargs = {
                    'buying_controller': buying_controller_data
                }
            elif category_name_data != None:
                selection = 'category'
                kwargs = {
                    'category': category_name_data
                }
            elif commercial_name_data != None:
                selection = 'commercial_area'
                kwargs = {
                    'commercial_area': commercial_name_data
                }


                # print("args-------------------!!!!!!")
                # print(args)
                # print(type(args))
                # x = list(args)
                # print(x[0])
                ######## IMPORTANT########
                ####### Filter should work based on last filter selected ##########################

        # print("kwargs")
        # print(kwargs)
        outperform_1 = selection + "_outperf_" + kpi + "_pct"
        growth = selection + "_" + kpi + "_" + "growth"

        # test = competitor_outperform.objects.filter(**kwargs).values('product_subgroup').distinct()
        print("test")
        print(kwargs)
        try:
            exclu_tesco_chart = competitor_outperform.objects.filter(**kwargs).exclude(competitor='Tesco LFL').values(
                'tesco_week', growth, outperform_1).order_by('tesco_week').distinct()
            # print("exclu_tesco_chart")
            print("exclu_tesco_chart entered try")
        except:
            print("exclu_tesco_chart entered else")
            exclu_tesco_chart = 0

        try:
            only_tesco_chart = competitor_outperform.objects.filter(**kwargs).filter(competitor='Tesco LFL').values(
                'tesco_week', growth, outperform_1).order_by('tesco_week').distinct()
        except:
            only_tesco_chart = 0

        try:
            for i in range(0, len(only_tesco_chart)):
                only_tesco_chart[i][growth] = format(float(only_tesco_chart[i][growth])*100, '.3f')
                only_tesco_chart[i][outperform_1] = format(float(only_tesco_chart[i][outperform_1])*100, '.3f')
        except:
            only_tesco_chart = 0

        try:
            for i in range(0, len(exclu_tesco_chart)):
                exclu_tesco_chart[i][growth] = format(float(exclu_tesco_chart[i][growth])*100, '.3f')
                exclu_tesco_chart[i][outperform_1] = format(float(exclu_tesco_chart[i][outperform_1])*100, '.3f')
        except:
            exclu_tesco_chart = 0

        try:
            exclu_tesco_pd = read_frame(exclu_tesco_chart)
            only_tesco_pd = read_frame(only_tesco_chart)
        except:
            exclu_tesco_pd = 0
            only_tesco_pd = 0

        try:
            label_week = pd.DataFrame({'label': exclu_tesco_pd['tesco_week']})
        except:
            label_week = 0

        try:
            label_week['label'] = label_week['label'].astype(float)
        except:
            label_week = 0

        try:
            market_outperform = pd.DataFrame({'value': exclu_tesco_pd[outperform_1]})
        except:
            market_outperform = 0

        try:
            market_growth = pd.DataFrame({'value': exclu_tesco_pd[growth]})
        except:
            market_growth = 0

        try:
            tesco_outperform = pd.DataFrame({'value': only_tesco_pd[outperform_1]})
        except:
            tesco_outperform = 0
        try:
            tesco_growth = pd.DataFrame({'value': only_tesco_pd[growth]})
        except:
            tesco_growth = 0
        data = []
        try:
            for i in range(len(label_week)):
                dict_try = {}
                dict_try = {
                    "market_growth": market_growth['value'][i],
                    "label_week": label_week['label'][i],
                    "tesco_growth": tesco_growth['value'][i],
                    "market_outperform": market_growth['value'][i],
                    "tesco_outperform": tesco_outperform['value'][i]
                }
                data.append(dict_try)
                # print("data from outperformance")
                # print(data)
        except:
            dict_try = {}
            dict_try = {
                "market_growth": '0',
                "label_week": '0',
                "tesco_growth": '0',
                "market_outperform": '0',
                "tesco_outperform": '0'
            }
            data.append(dict_try)

        final_dict = {"data": data}
        logging.info(data)

        ##print("received data---------")
        ##print(data)
        return JsonResponse(data, safe=False)

class competitor_market_share_1(APIView):
    def get(self, request, *args):
        ##print("competitor_market_share")
        print("args recieved")
        args = {reqobj: request.GET.get(reqobj) for reqobj in request.GET.keys()}
        # print("args before popping")
        # print(args)
        # for week tab
        week_flag = args.pop('week_flag', "Current Week")
        # print(week_flag)

        # for kpi type tab
        # print("args before popping kpi")
        # print(args)
        kpi = args.pop('kpi_type', 'value')
        # print("args after popping kpi")
        # print(args)

        # print(kpi)
        # for current week value
        tesco_week_int = competitor_market_share.objects.aggregate(cw_max=Max('tesco_week'))
        max_week = tesco_week_int['cw_max']
        cw_week = int(args.pop('tesco_week', max_week))
        print("cw week....",type(cw_week),cw_week)
        # cw_week = int(args.pop('tesco_week',201652))


        # Cookies settings
        print("cookie pop")
        user_id = args.pop('user_id', None)
        designation = args.pop('designation', None)
        session_id = args.pop('session_id', None)
        user_name = args.pop('user_name', None)
        buying_controller_header = args.pop('buying_controller_header', None)
        buyer_header = args.pop('buyer_header', None)
        print("buying_controller_header", buying_controller_header, "buyer_header", buyer_header)
        # def market_position_pi(kpi):

        week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
            '-tesco_week').distinct()
        # print(week_ordered)
        last_week = week_ordered[1]
        last_week = last_week['tesco_week']

        def week_selection(week_flag):

            if (week_flag == 'Latest 4 Weeks'):
                week_logic = 'Latest 4 Weeks'

            elif (week_flag == 'Latest 13 Weeks'):
                week_logic = 'Latest 13 Weeks'

            elif (week_flag == 'Latest 52 Weeks'):
                week_logic = 'Latest 52 Weeks'

            elif (week_flag == 'YTD'):
                week_logic = 'Year To Date'
            else:
                week_logic = 'Latest Week'

            week = week_logic
            return week

        # if not args:
        week = week_selection(week_flag)
        if not args:
            print("entered buyer controller if")
            if buyer_header is None:
                kwargs_header = {
                    'buying_controller': buying_controller_header
                }
                print("entered bc 1123456789", kwargs_header)
            else:
                kwargs_header = {
                    'buying_controller': buying_controller_header,
                    'buyer': buyer_header
                }

            product_subgroup = sales_heirarchy.objects.filter(**kwargs_header).values('product_subgroup').distinct()

        else:
            print("entered else")
            product_subgroup = sales_heirarchy.objects.filter(**args).values('product_subgroup').distinct()
            print("product subgroup:",product_subgroup)
        kwargs = {
            'tesco_week': cw_week,
            'product_subgroup__in': product_subgroup,
            'flag': week
        }
        # print("kwargs")
        # print(kwargs)

        kwargs_last = {
            'tesco_week': last_week,
            'product_subgroup__in': product_subgroup,
            'flag': week
        }

        try:
            exclu_tesco = competitor_market_share.objects.filter(**kwargs).exclude(competitor='Tesco LFL').aggregate(
                total_kpi=Sum(kpi))
            print("Exclu tesco")
            print(exclu_tesco)
        except:
            print("entered exception exclu tesco")
            exclu_tesco = 0

        ##print("Exclude tesco")
        # ##print(exclu_tesco)
        try:
            only_tesco = competitor_market_share.objects.filter(**kwargs).filter(competitor='Tesco LFL').aggregate(
                total_kpi=Sum(kpi))
            ##print("only tesco")
            ##print(only_tesco)
        except:
            print("entered exception only tesco")
            only_tesco = 0

        ##print("Only tesco")
        # ##print(only_tesco)
        try:
            only_tesco_data = competitor_market_share.objects.filter(**kwargs).filter(competitor='Tesco LFL').aggregate(
                total_kpi=Sum(kpi))

        except:
            only_tesco_data = 0
        try:
            only_tesco_last = competitor_market_share.objects.filter(**kwargs_last).filter(
                competitor='Tesco LFL').aggregate(total_kpi=Sum(kpi))
            ##print("Only tesco last")
            ##print(only_tesco_last)
        except:
            only_tesco_last = 0
            print(only_tesco_last)
        try:
            tesco_share_percent = format(
                (only_tesco['total_kpi'] / (only_tesco['total_kpi'] + exclu_tesco['total_kpi'])) * 100, '.1f')
        except:
            tesco_share_percent = 0
        ##print("tesco_share_percent")
        ##print(tesco_share_percent)
        try:
            competitor_share_percent = format(
                (exclu_tesco['total_kpi'] / (only_tesco['total_kpi'] + exclu_tesco['total_kpi'])) * 100, '.1f')
        except:
            competitor_share_percent = 0
        ##print("competitor_share_percent")
        ##print(competitor_share_percent)
        try:

            tesco_share_data = float(format(
                ((only_tesco_data['total_kpi'] - only_tesco_last['total_kpi']) / only_tesco_last['total_kpi']) * 100,
                '.1f'))
        except:
            tesco_share_data = 0

        if week_flag != 'Current Week' and week_flag != 'None':
            tesco_share_data = 'NA'

        competitor_pi = []
        tesco = {}
        tesco['label'] = "Market Share"
        tesco['pie_chart_value'] = float(competitor_share_percent)
        competitor_pi.append(tesco)
        market = {}
        market['label'] = "Tesco Share"
        market['pie_chart_value'] = float(tesco_share_percent)
        competitor_pi.append(market)
        print("Competitor_pi:", competitor_pi);
        data = {
            "pie_chart_value": competitor_pi,
            "tesco_share_data": tesco_share_data
        }
        logging.info(data)

        ##print("received data---------")
        return JsonResponse(data, safe=False)

class competitor_price_index_2(APIView):
    def get(self, request, *args):
        ##print("-------------- competitor_price_index -------------")
        # print("args recieved")
        args = {reqobj: request.GET.get(reqobj) for reqobj in request.GET.keys()}
        # print(args)
        #### for week tab
        week_flag = args.pop('week_flag', None)

        waterfall_index_param = args.pop('waterfall_index_param', 'brand')
        print(waterfall_index_param)

        #### for kpi type tab
        kpi_type = args.pop('kpi_type', None)

        #### for current week value
        tesco_week_int = competitor_price_index_basket.objects.aggregate(cw_max=Max('tw'))
        max_week = tesco_week_int['cw_max']
        cw_week = int(args.pop('tesco_week', max_week))
        print("cw week...... price index",cw_week)
        # cw_week = args.pop('tesco_week', 201713)

        ###Cookies
        user_id = args.pop('user_id', None)
        designation = args.pop('designation', None)
        session_id = args.pop('session_id', None)
        user_name = args.pop('user_name', None)
        buying_controller_header = args.pop('buying_controller_header', None)
        buyer_header = args.pop('buyer_header', None)

        ##print(args)

        ###### convert "and" to "and"

        ##print("product subgroup list")
        ##print(product_subgroup_list)

        def price_index(flag):

            week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                '-tesco_week').distinct()
            last_week = week_ordered[1]
            last_week = last_week['tesco_week']

            def week_selection(cw_week, week_flag):

                if (week_flag == 'Latest 4 Weeks'):
                    week_logic = week_ordered[:4]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))  # ##print("Inside elif 1")

                elif (week_flag == 'Latest 13 Weeks'):
                    week_logic = week_ordered[:13]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                elif (week_flag == 'Latest 52 Weeks'):

                    week_logic = week_ordered[:52]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                elif (week_flag == 'YTD'):

                    current_week = int(cw_week)
                    for_x = int(str(current_week)[-2:])
                    week_logic = week_ordered[:for_x]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))
                else:
                    week_logic = week_ordered[:1]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                week = week_var
                return week

            week = week_selection(cw_week, flag)
            print("week",week)
            print("week var..........",week)
            ##print("week")
            ##print(week)
            if not args:
                if buyer_header is None:
                    kwargs_sso = {
                        'buying_controller': buying_controller_header
                    }
                else:
                    kwargs_sso = {
                        'buying_controller': buying_controller_header,
                        'buyer': buyer_header
                    }
                product_subgroup_sso = sales_heirarchy.objects.filter(**kwargs_sso).values('product_subgroup_id').distinct()
                kwargs = {
                    'product_sub_group_code__in': product_subgroup_sso,
                    'tw__in': week

                }
            else:
                product_subgroup_list = sales_heirarchy.objects.filter(**args).values('product_subgroup_id').distinct()
                kwargs = {
                    'product_sub_group_code__in': product_subgroup_list,
                    'tw__in': week

                }

            def calculating_brand(competitor):
                comp_sales_tw=competitor+'_sales_tw'
                comp_sales_lw=competitor+'_sales_lw'
                tesco_sales_tw=competitor+'_tesco_sales_tw'
                tesco_sales_lw=competitor+'_tesco_sales_lw'
                print("sales lw", tesco_sales_lw)
                competitor_sales_brand = competitor_price_index_brand.objects.filter(**kwargs).filter(brand='B').aggregate(comp_sum_tw=Sum(comp_sales_tw),tesco_sum_tw=Sum(tesco_sales_tw),comp_sum_lw=Sum(comp_sales_lw),tesco_sum_lw=Sum(tesco_sales_lw))
                if competitor_sales_brand['comp_sum_tw'] == None:
                    print("entered if comp brand empty")
                    competitor_sales_brand = {'comp_sum_tw': 0, 'tesco_sum_tw': 0, 'comp_sum_lw': 0, 'tesco_sum_lw': 0}
                competitor_sales_ol = competitor_price_index_brand.objects.filter(**kwargs).filter(
                    brand='OL').aggregate(comp_sum_tw=Sum(comp_sales_tw),tesco_sum_tw=Sum(tesco_sales_tw),comp_sum_lw=Sum(comp_sales_lw),tesco_sum_lw=Sum(tesco_sales_lw))

                if competitor_sales_ol['comp_sum_tw'] == None:
                    print("entered if comp ol empty")
                    competitor_sales_ol = {'comp_sum_tw': 0, 'tesco_sum_tw': 0, 'comp_sum_lw': 0, 'tesco_sum_lw': 0}

                tesco_sales = competitor_price_index_brand.objects.filter(**kwargs).aggregate(tesco_sum_tw=Sum(tesco_sales_tw), tesco_sum_lw=Sum(tesco_sales_lw))
                try:
                    print("1:",competitor_sales_brand['comp_sum_tw'],"2:", competitor_sales_ol['comp_sum_tw'],"3:",competitor_sales_brand['tesco_sum_tw'],"4:",competitor_sales_ol['tesco_sum_tw'],type(competitor_sales_ol['comp_sum_tw']) )
                    tw_data=((float(competitor_sales_brand['comp_sum_tw']) + float(competitor_sales_ol['comp_sum_tw']))/(float(competitor_sales_brand['tesco_sum_tw']) + float(competitor_sales_ol['tesco_sum_tw'])))*100
                    lw_data=((competitor_sales_brand['comp_sum_lw'] + competitor_sales_ol['comp_sum_lw'])/(competitor_sales_brand['tesco_sum_lw'] + competitor_sales_ol['tesco_sum_lw']))*100
                    brand_intermediate_tw=(competitor_sales_brand['comp_sum_tw']-competitor_sales_brand['tesco_sum_tw'])/tesco_sales['tesco_sum_tw']
                    brand_intermediate_lw = (competitor_sales_brand['comp_sum_lw'] - competitor_sales_brand[
                        'tesco_sum_lw']) / tesco_sales['tesco_sum_lw']
                    brand=(brand_intermediate_tw - brand_intermediate_lw)*100

                    ol_intermediate_tw = (competitor_sales_ol['comp_sum_tw'] - competitor_sales_ol['tesco_sum_tw']) / \
                                            tesco_sales['tesco_sum_tw']
                    ol_intermediate_lw = (competitor_sales_ol['comp_sum_lw'] - competitor_sales_ol[
                        'tesco_sum_lw']) / tesco_sales['tesco_sum_lw']
                    ol = (ol_intermediate_tw - ol_intermediate_lw) * 100
                except:
                    print("price index.............. exception")
                    lw_data=0
                    brand=0
                    ol=0
                    tw_data=0

                lw_data = float(lw_data)
                brand = float(brand)
                ol = float(ol)
                tw_data = float(tw_data)

                brand = [{"name": "LW", "value": lw_data},
                                  {"name": "Brand", "value": brand},
                                  {"name": "OL", "value": ol}]
                #,{"name": "TW", "value": tw_data}
                print(brand)
                return brand

            def calculating_basket(competitor):
                comp_sales_tw = competitor + '_sales_tw'
                comp_sales_lw = competitor + '_sales_lw'
                tesco_sales_tw = competitor + '_tesco_sales_tw'
                tesco_sales_lw = competitor + '_tesco_sales_lw'
                print("test def enter")

                try:
                    competitor_sales_ror = competitor_price_index_basket.objects.filter(**kwargs).filter(
                        basket='ROR').aggregate(comp_sum_tw=Sum(comp_sales_tw), tesco_sum_tw=Sum(tesco_sales_tw),
                                             comp_sum_lw=Sum(comp_sales_lw), tesco_sum_lw=Sum(tesco_sales_lw))
                    if competitor_sales_ror['comp_sum_tw']==None:
                        print("entered if comp lmm empty")
                        competitor_sales_ror = {'comp_sum_tw': 0, 'tesco_sum_tw': 0, 'comp_sum_lw': 0, 'tesco_sum_lw': 0}

                    competitor_sales_lmm = competitor_price_index_basket.objects.filter(**kwargs).filter(
                        basket='LMM').aggregate(comp_sum_tw=Sum(comp_sales_tw), tesco_sum_tw=Sum(tesco_sales_tw),
                                              comp_sum_lw=Sum(comp_sales_lw), tesco_sum_lw=Sum(tesco_sales_lw))
                    print("type.......", type(competitor_sales_lmm['comp_sum_tw']))

                    if competitor_sales_lmm['comp_sum_tw']==None:
                        print("entered if comp lmm empty")
                        competitor_sales_lmm = {'comp_sum_tw': 0, 'tesco_sum_tw': 0, 'comp_sum_lw': 0, 'tesco_sum_lw': 0}

                    tesco_sales = competitor_price_index_basket.objects.filter(**kwargs).aggregate(
                        tesco_sum_tw=Sum(tesco_sales_tw), tesco_sum_lw=Sum(tesco_sales_lw))
                    print("competitor sales ror.......",int(competitor_sales_ror['comp_sum_tw']),"::::",comp_sales_tw,"Queryset:",competitor_sales_ror,"type of :", type(competitor_sales_ror))
                    print("competitor sales lmm.......",int(competitor_sales_lmm['comp_sum_tw']),"::::",comp_sales_tw,"Queryset:",competitor_sales_lmm,"type of :", type(competitor_sales_lmm))
                    if int(competitor_sales_ror['comp_sum_tw'])!=0:
                        tw_data = ((competitor_sales_lmm['comp_sum_tw'] + competitor_sales_ror['comp_sum_tw']) / (
                        competitor_sales_lmm['tesco_sum_tw'] + competitor_sales_ror['tesco_sum_tw'])) * 100
                        lw_data = ((competitor_sales_lmm['comp_sum_lw'] + competitor_sales_ror['comp_sum_lw']) / (
                        competitor_sales_lmm['tesco_sum_lw'] + competitor_sales_ror['tesco_sum_lw'])) * 100
                        lmm_intermediate_tw = (competitor_sales_lmm['comp_sum_tw'] - competitor_sales_lmm[
                            'tesco_sum_tw']) / tesco_sales['tesco_sum_tw']
                        lmm_intermediate_lw = (competitor_sales_lmm['comp_sum_lw'] - competitor_sales_lmm[
                            'tesco_sum_lw']) / tesco_sales['tesco_sum_lw']
                        lmm = (lmm_intermediate_tw - lmm_intermediate_lw) * 100

                        ror_intermediate_tw = (competitor_sales_ror['comp_sum_tw'] - competitor_sales_ror['tesco_sum_tw']) / \
                                             tesco_sales['tesco_sum_tw']
                        ror_intermediate_lw = (competitor_sales_ror['comp_sum_lw'] - competitor_sales_ror[
                            'tesco_sum_lw']) / tesco_sales['tesco_sum_lw']
                        ror = (ror_intermediate_tw - ror_intermediate_lw) * 100
                    else:
                        print("entered else")
                        lw_data = 0
                        lmm = 0
                        ror = 0
                        tw_data = 0
                except:
                    print("exception entered......")
                    lw_data = 0
                    lmm = 0
                    ror = 0
                    tw_data = 0
                lw_data = float(lw_data)
                lmm = float(lmm)
                ror = float(ror)
                tw_data = float(tw_data)

                basket = [{"name": "LW", "value": lw_data},
                         {"name": "LMM", "value": lmm},
                         {"name": "ROR", "value": ror}]
                    # ,
                    # {"name": "TW", "value": tw_data}

                return basket

            # JS


            if (waterfall_index_param == 'brand'):

                asda = calculating_brand('asda')
                lidl = calculating_brand('lidl')
                morr = calculating_brand('morr')
                js = calculating_brand('js')
                xaxis = 'Brand'

            else:
                asda = calculating_basket('asda')
                lidl = calculating_basket('lidl')
                morr = calculating_basket('morr')
                js = calculating_basket('js')
                xaxis = 'Basket'

            price_waterfall = {"asda": asda, "aldi": lidl, "morr": morr, "js": js, 'yaxis': 'Price Index',
                               'xaxis': xaxis}

            logging.info(price_waterfall)

            return price_waterfall

        data = price_index(week_flag)
        # ##print("received data---------")
        # ##print(data)
        return JsonResponse(data, safe=False)