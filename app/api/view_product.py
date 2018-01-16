from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.views import generic
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework import status
from django.http import JsonResponse
import math
import re
import environ
import logging
from django.db.models import Count, Min, Max, Sum, Avg, F, FloatField
import datetime
from django.conf import settings
import pandas as pd
from django_pandas.io import read_frame
from django.utils import six
import numpy as np
from .models import product_view_v2, sales_heirarchy, calendar_dim_hierarchy, latest_week, supplier_view
# from .serializers import proddetailsSerializer
from django.core.paginator import Paginator
#from django.contrib.humanize.templatetags.humanize import intcomma
import json
import hashlib
from django.core.cache import cache


# Create your views here.

class supplier_modal(APIView):
    def get(self, request):
        args = {reqobj: request.GET.get(reqobj) for reqobj in request.GET.keys()}

        # authentication variables
        user_id = args.pop('user_id', None)
        designation = args.pop('designation', None)
        user_name = args.pop('user_name', None)
        buying_controller_header = args.pop('buying_controller_header', None)
        buyer_header = args.pop('buyer_header', None)

        # if the user is buying controller
        if buyer_header is None:
            kwargs_header = {
                'buying_controller': buying_controller_header
            }
        # if the user is buyer
        else:
            kwargs_header = {
                'buying_controller': buying_controller_header,
                'buyer': buyer_header
            }
        tesco_week = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = tesco_week['cw_max']

        # for current week value
        currentweek = int(args.pop('tesco_week', max_week))
        cw_week = currentweek
        week_flag = args.pop('week_flag', 'Current Week')
        week_flag = week_flag
        lastweek = cw_week - 1
        store_type = args.pop('store_type', None)
        metric = args.pop('metric_flag', None)
        print("metric",metric)
        if metric == 'Value':
            print("inside value")
            column_ty = 'sales_ty'
            column_ly = 'sales_ly'
            # column_lw = 'sales_lw'
            column_lfl_ty = 'sales_ty_lfl'
            column_lfl_ly = 'sales_ly_lfl'

        elif metric == 'Volume':
            column_ty = 'volume_ty'
            column_ly = 'volume_ly'
            # column_lw = 'sales_volume_lw'
            column_lfl_ty = 'volume_ty_lfl'
            column_lfl_ly = 'volume_ly_lfl'

        elif metric == 'cogs':
            column_ty = 'cogs_ty'
            column_ly = 'cogs_ly'
            # column_lw = 'cogs_lw'
            column_lfl_ty = 'cogs_ty_lfl'
            column_lfl_ly = 'cogs_ly_lfl'

        elif metric == 'cgm':
            column_ty = 'cgm_ty'
            column_ly = 'cgm_ly'
            # column_lw = 'profit_lw'
            column_lfl_ty = 'cgm_ty_lfl'
            column_lfl_ly = 'cgm_ly_lfl'

        selected_product = args.pop('product', None)

        def week_selection(cw_week, week_flag, chart_flag):
            week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                '-tesco_week').distinct()
            last_week = week_ordered[1]
            last_week = last_week['tesco_week']
            if (week_flag == '4'):
                week_logic = week_ordered[:4]
            elif (week_flag == '13'):
                week_logic = week_ordered[:13]
            elif (week_flag == '26'):
                week_logic = week_ordered[:26]
            elif (week_flag == 'YTD'):
                current_week = int(cw_week)
                for_x = int(str(current_week)[-2:])
                week_logic = week_ordered[:for_x]
            else:
                week_logic = week_ordered[:1]

            week_var = []
            for i in range(len(week_logic)):
                week_var.append(week_logic[i]['tesco_week'])
            return week_var

        chart_flag = 1
        week = week_selection(cw_week, week_flag, chart_flag)

        print("inside args")
        print(selected_product)
        product_id = int(selected_product[:8])
        if store_type is None:
            product_df = read_frame(
            sales_heirarchy.objects.filter(product_id=product_id).values('product_id', 'product').distinct())
        else:
            product_df = read_frame(
            sales_heirarchy.objects.filter(store_type=store_type).filter(product_id=product_id).values('product_id', 'product').distinct())
        kwargs = {
            'tesco_week__in': week,
            'product_id__in': product_df['product_id']
        }
        print("kwargs")
        print(kwargs)
        if store_type is None:
            df = read_frame(
            supplier_view.objects.filter(**kwargs).values('product_id', 'parent_supplier', column_ty, column_ly,
                                                          column_lfl_ty, column_lfl_ly).distinct())
        else:
            df = read_frame(
            supplier_view.objects.filter(**kwargs).filter(store_type=store_type).values('product_id', 'parent_supplier', column_ty, column_ly,
                                                          column_lfl_ty, column_lfl_ly).distinct())
        print(df)
        df = df.groupby(['product_id', 'parent_supplier'])[column_ty, column_ly, column_lfl_ty, column_lfl_ly].sum().reset_index()
        df = pd.merge(product_df, df, on=['product_id'], how='left')
        table_dict = []
        for i in range(len(df)):
            data_dict = {}
            data_dict['product'] = df['product'][i]
            data_dict['parent_supplier'] = df['parent_supplier'][i]
            data_dict['metric_ty'] = df[column_ty][i]
            data_dict['metric_ly'] = df[column_ly][i]
            data_dict['metric_ty_lfl'] = df[column_lfl_ty][i]
            data_dict['metric_ly_lfl'] = df[column_lfl_ly][i]
            table_dict.append(data_dict)

        table_data = {}
        table_data["data"] = table_dict

        return JsonResponse(table_data, safe=False)


class product_performance(APIView):
    def get(self, request):
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

        # authentication variables
        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', None)
        buyer_header = args.pop('buyer_header__in', None)

        # if the user is buying controller
        if buyer_header is None:
            kwargs_header = {
                'buying_controller__in': buying_controller_header
            }
        # if the user is buyer
        else:
            kwargs_header = {
                'buying_controller__in': buying_controller_header,
                'buyer__in': buyer_header
            }

        print("kwargs header", kwargs_header)
        tesco_week = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week['cw_max']]

        # for current week value
        currentweek = args.pop('tesco_week__in', max_week)
        cw_week = int(currentweek[0])
        week_flag = args.pop('week_flag__in', ['Current Week'])
        print("week flag.........", week_flag)
        week_flag = week_flag[0]
        lastweek = cw_week - 1
        store_type_list=args.pop('store_type__in',None)
        if store_type_list is None:
            store_type = None
        else:
            store_type = store_type_list
        metric = args.pop('metric_flag__in', ['Value'])
        metric = metric[0]
        print("metric",metric)

        # Function for calculating week time period
        def week_selection(cw_week, week_flag, chart_flag):
            week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                '-tesco_week').distinct()
            last_week = week_ordered[1]
            last_week = last_week['tesco_week']
            print("last week", last_week)
            # last_week = last_week['tesco_week']
            if (week_flag == 'Latest Week'):
                week_logic = week_ordered[:1]
            if (week_flag == '4'):
                week_logic = week_ordered[:4]
            elif (week_flag == '13'):
                week_logic = week_ordered[:13]
            elif (week_flag == '26'):
                week_logic = week_ordered[:26]
            elif (week_flag == 'YTD'):
                current_week = int(cw_week)
                for_x = int(str(current_week)[-2:])
                week_logic = week_ordered[:for_x]
            else:
                week_logic = week_ordered[:1]

            week_var = []
            for i in range(len(week_logic)):
                week_var.append(week_logic[i]['tesco_week'])

            week = {'week_var': week_var, 'last_week': last_week}
            return week

        chart_flag = 1
        week = week_selection(cw_week, week_flag, chart_flag)
        print("week selected")
        print(week)
        if metric == 'Value':
            print("inside value")
            column_ty = 'sales_value'
            column_ly = 'sales_value_ly'
            column_lw = 'sales_value_lw'
            column_lfl_ty = 'sales_value_lfl'
            column_lfl_ly = 'sales_value_lfl_ly'

        elif metric == 'Volume':
            column_ty = 'sales_volume'
            column_ly = 'sales_volume_ly'
            column_lw = 'sales_volume_lw'
            column_lfl_ty = 'sales_volume_lfl'
            column_lfl_ly = 'sales_volume_lfl_ly'

        elif metric == 'cogs':
            column_ty = 'cogs'
            column_ly = 'cogs_ly'
            column_lw = 'cogs_lw'
            column_lfl_ty = 'cogs_lfl'
            column_lfl_ly = 'cogs_lfl_ly'

        elif metric == 'cgm':
            column_ty = 'profit'
            column_ly = 'profit_ly'
            column_lw = 'profit_lw'
            column_lfl_ty = 'profit_lfl'
            column_lfl_ly = 'profit_lfl_ly'

        # elif metric == 'waste':
        #     column_ty = 'waste'
        #     column_ly = 'waste_ly'
        #     column_lw = 'waste_lw'
        #     column_lfl_ty = 'waste_lfl'
        #     column_lfl_ly = 'waste_lfl_ly'

        print("week var", week)
        if not args:
            print("inside not args")
            products = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
            product_df = read_frame(
                sales_heirarchy.objects.filter(**kwargs_header).values('product_id', 'product').distinct())
            product_id_df=read_frame(sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct())

        else:
            print("inside args")
            products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
            product_df = read_frame(sales_heirarchy.objects.filter(**args).values('product_id', 'product').distinct())
            product_id_df=read_frame(sales_heirarchy.objects.filter(**args).values('product_id').distinct())            

        print("len of final product df")
        print(len(product_df))
        kwargs = {
            'tesco_week__in': week['week_var'],
            'product_id__in': products
        }
        print("kwargs", kwargs)
        kwargs_lw = {
            'tesco_week': week['last_week'],
            'product_id__in': products
        }
        print("kwargs_lw",kwargs_lw)
        if store_type is None:
            df =read_frame(product_view_v2.objects.filter(**kwargs).values('product_id').annotate(sum_column_ty=Sum(column_ty),
                sum_column_lfl_ty=Sum(column_lfl_ty)).distinct())
        else:
            df = read_frame(
                product_view_v2.objects.filter(**kwargs).filter(store_type__in=store_type).values('product_id').annotate(sum_column_ty=Sum(column_ty),
                                                                                       sum_column_lfl_ty=Sum(
                                                                                           column_lfl_ty)).distinct())
        products = df['product_id']
        print("len of df product id",len(products))
        week_ly = list(latest_week.objects.filter(week_ty__in=week['week_var']).values_list('week_ly', flat=True).distinct())

        kwargs_ly = {
            'tesco_week__in': week_ly,
            'product_id__in': products
        }
        print("kwargs_ly",kwargs_ly)
        if store_type is None:
            df_intermediate = read_frame(product_view_v2.objects.filter(**kwargs_lw).values('product_id').annotate(sum_column_lw =Sum(column_ty)).order_by("product_id"))
        else:
            df_intermediate = read_frame(product_view_v2.objects.filter(store_type__in=store_type).filter(**kwargs_lw).values('product_id').annotate(
                sum_column_lw=Sum(column_ty)).order_by("product_id"))

        df = pd.merge(df,df_intermediate, on=['product_id'], how='left')
        if store_type is None:
            df_intermediate = read_frame((product_view_v2.objects.filter(**kwargs_ly).values('product_id').annotate(sum_column_ly=Sum(column_ty)).order_by("product_id")))
        else:
            df_intermediate = read_frame((product_view_v2.objects.filter(**kwargs_ly).filter(store_type__in=store_type).values('product_id').annotate(
                sum_column_ly=Sum(column_ty)).order_by("product_id")))

        df = pd.merge(df,df_intermediate, on=['product_id'], how='left')
        if store_type is None:
            df_intermediate = read_frame((product_view_v2.objects.filter(**kwargs_ly).values('product_id').annotate(sum_column_lfl_ly=Sum(column_lfl_ty)).order_by("product_id")))
        else:
            df_intermediate = read_frame((product_view_v2.objects.filter(**kwargs_ly).filter(store_type__in=store_type).values('product_id').annotate(
                sum_column_lfl_ly=Sum(column_lfl_ty)).order_by("product_id")))

        df = pd.merge(df,df_intermediate, on=['product_id'], how='left')
     

        df= df.fillna(value=0)
       
        df['yoy'] = 0
        df['wow']=0
        df['lfl_percent']=0
        for i in range(len(df)):               
            try:
                df['yoy'][i] = ((df['sum_column_ty'][i] - df['sum_column_ly'][i])/df['sum_column_ly'][i])*100
            except:
                df['yoy'][i] = 0
            try:
                df['lfl_percent'][i] = ((df['sum_column_lfl_ty'][i] - df['sum_column_lfl_ly'][i]) / df['sum_column_lfl_ly'][i])*100
            except:
                df['lfl_percent'][i] = 0
            try:
                df['wow'][i] = ((df['sum_column_ty'][i] - df['sum_column_lw'][i]) / df['sum_column_lw'][i])*100
            except:
                df['wow'][i] = 0

        df['yoy'] = df['yoy'].astype('float').round(decimals=2)
        df['lfl_percent'] = df['lfl_percent'].astype('float').round(decimals=2)                     
        df['wow'] = df['wow'].astype('float').round(decimals=2)

        # df['yoy'] = df['yoy'].astype('str')
        # df['wow'] = df['wow'].astype('str')
        # df['lfl_percent'] = df['lfl_percent'].astype('str')

    
        df = pd.merge(df,product_df, left_on=['product_id'],right_on=['product_id'], how='inner')
        for i in range(0,len(df)):
            if (df['yoy'][i]=='0.0'):
                df['yoy'][i] = "-"
            if (df['wow'][i]=='0.0'):
                df['wow'][i] = "-"
            if (df['lfl_percent'][i]=='0.0'):
                df['lfl_percent'][i] = "-"
                

        df['x_ty'] = df['sum_column_ty'].astype('float').round(decimals=2)
        # df['x_ty'] = df['x_ty'].astype('str')
        df['x_lw'] = df['sum_column_lw'].astype('float').round(decimals=2)
        # df['x_lw'] = df['x_lw'].astype('str')
        df['x_ly'] = df['sum_column_ly'].astype('float').round(decimals=2)
        # df['x_ly'] = df['x_ly'].astype('str')
        df['x_lfl_ty'] = df['sum_column_lfl_ty'].astype('float').round(decimals=2)
        # df['x_lfl_ty'] = df['x_lfl_ty'].astype('str')
        df['x_lfl_ly'] = df['sum_column_lfl_ly'].astype('float').round(decimals=2)
        # df['x_lfl_ly'] = df['x_lfl_ly'].astype('str')
        df.rename(columns={'lfl_percent':'lfl'})
        del(df['sum_column_ty'])
        del(df['sum_column_lw'])
        del(df['sum_column_ly'])
        del(df['sum_column_lfl_ty'])
        del(df['sum_column_lfl_ly'])            

        table_data = {}
        table_data['table_data'] = df.to_dict(orient='records')
        table_data['latest_week'] = max_week

        return JsonResponse(table_data, safe=False)


class sales_trend(APIView):
    def get(self, request):
        args = {reqobj: request.GET.get(reqobj) for reqobj in request.GET.keys()}

        # authentication variables
        user_id = args.pop('user_id', None)
        designation = args.pop('designation', None)
        user_name = args.pop('user_name', None)
        buying_controller_header = args.pop('buying_controller_header', None)
        buyer_header = args.pop('buyer_header', None)

        # if the user is buying controller
        if buyer_header is None:
            kwargs_header = {
                'buying_controller': buying_controller_header
            }
        # if the user is buyer
        else:
            kwargs_header = {
                'buying_controller': buying_controller_header,
                'buyer': buyer_header
            }
        tesco_week = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = tesco_week['cw_max']

        # for current week value
        currentweek = int(args.pop('tesco_week', max_week))
        cw_week = currentweek
        week_flag = args.pop('week_flag', 'Current Week')
        week_flag = week_flag
        lastweek = cw_week - 1
        chart_flag = 1

        store_type = args.pop('store_type', None)
        metric = args.pop('metric_flag', None)
        if metric == 'Value':
            print("inside value")
            column_ty = 'sales_ty'
            column_ly = 'sales_ly'
            # column_lw = 'sales_lw'
            column_lfl_ty = 'sales_ty_lfl'
            column_lfl_ly = 'sales_ly_lfl'

        elif metric == 'Volume':
            column_ty = 'volume_ty'
            column_ly = 'volume_ly'
            # column_lw = 'sales_volume_lw'
            column_lfl_ty = 'volume_ty_lfl'
            column_lfl_ly = 'volume_ly_lfl'

        elif metric == 'cogs':
            column_ty = 'cogs_ty'
            column_ly = 'cogs_ly'
            column_lw = 'cogs_lw'
            column_lfl_ty = 'cogs_ty_lfl'
            column_lfl_ly = 'cogs_ly_lfl'

        elif metric == 'cgm':
            column_ty = 'cgm_ty'
            column_ly = 'cgm_ly'
            # column_lw = 'profit_lw'
            column_lfl_ty = 'cgm_ty_lfl'
            column_lfl_ly = 'cgm_ly_lfl'

        selected_product = args.pop('product', None)

        def week_selection(cw_week, week_flag, chart_flag):
            week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                '-tesco_week').distinct()
            last_week = week_ordered[1]
            last_week = last_week['tesco_week']

            if (week_flag == '4'):
                week_logic = week_ordered[:4]
            elif (week_flag == '13'):
                week_logic = week_ordered[:13]
            elif (week_flag == '26'):
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

        week = week_selection(cw_week, week_flag, chart_flag)
        print("week")
        print(week)
        product_id = selected_product[:8]
        if store_type is None:
            product_df = read_frame(
            sales_heirarchy.objects.filter(product_id=product_id).values('product_id', 'product').distinct())
        else:
            product_df = read_frame(
            sales_heirarchy.objects.filter(store_type=store_type).filter(product_id=product_id).values('product_id', 'product').distinct())
        print(product_df)
        kwargs = {
            'tesco_week__in': week,
            'product_id': product_df['product_id']
        }
        if store_type is None:
            df = read_frame(
            supplier_view.objects.filter(**kwargs).values('tesco_week').annotate(sales_val_ty=Sum(column_ty),
                                                                                 sales_val_ly=Sum(column_ly)))

        else:
            df = read_frame(
            supplier_view.objects.filter(**kwargs).filter(store_type=store_type).values('tesco_week').annotate(sales_val_ty=Sum(column_ty),
                                                                                 sales_val_ly=Sum(column_ly)))
        df['metric_ty'] = df['sales_val_ty'].astype('float')
        df['metric_ly'] = df['sales_val_ly'].astype('float')
        # df['tesco_week'] = df['tesco_week'].astype('int')
        print(df['tesco_week'])
        del (df['sales_val_ty'])
        del (df['sales_val_ly'])

        trend_data = {}
        trend_data["data"] = df.to_dict(orient='records')
        return JsonResponse(trend_data, safe=False)


class product_filterdata_week(APIView):
    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}
        # print('Args:',args)
        # max_record = pd.DataFrame.from_records(product_view.objects.all().values('tesco_week').distinct()).max()
        tesco_week = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = tesco_week['cw_max']
        print("Max Week:",max_week)
        week_id = args.get('tesco_week__iexact',None)

        # print('Week Id:',week_id,type(week_id))

        if week_id is None:
            week_id = max_week
        elif week_id == 'default':
            week_id = max_week
        else:
            week_id = int(week_id)


        kwargs = {
            'tesco_week__iexact': week_id

        }
        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))

        if not args:

            print("inside default")

            weeks_data = read_frame(
                calendar_dim_hierarchy.objects.filter(tesco_week__gte=201627).filter(tesco_week__lte=max_week).values(
                    'tesco_week').order_by('-tesco_week'))


            data = {'tesco_week': weeks_data.tesco_week.unique()}
            week = pd.DataFrame(data)
            week['selected'] = False
            week['disabled'] = False

            week_df = weeks_data[['tesco_week']].drop_duplicates()

            week_df = pd.merge(week_df, week, how='left')
            week_df['selected'] = week_df['selected'].fillna(False)
            week_df['disabled'] = week_df['disabled'].fillna(False)

            week_df = week_df.rename(columns={'tesco_week': 'name'})

            week_final = week_df.to_json(orient='records')
            week_final = json.loads(week_final)

            a = {}
            a['name'] = 'tesco_week'
            a['items'] = week_final

            final = []
            final.append(a)

        else:

            weeks_data = read_frame(calendar_dim_hierarchy.objects.filter(tesco_week__gte=201627).filter(tesco_week__lte=max_week).values('tesco_week').order_by('-tesco_week'))

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

            week_final = week_df.to_json(orient='records')
            week_final = json.loads(week_final)

            a = {}
            a['name'] = 'tesco_week'
            a['items'] = week_final

            final = []
            final.append(a)

            # print(final)
        return JsonResponse(final, safe=False)

def make_json(sent_req, kwargs_header, default_check):
    print('*********************\n       FILTERS2 \n*********************')
    hierarchy = ['commercial_name','category_name', 'buying_controller', 'buyer', 'junior_buyer', 'product_subgroup', 'brand_indicator']
    # find lowest element of hierarchy
    lowest = 0
    second_lowest = 0
    element_list = []
    if sent_req != {}:
        print("entered if")
        for i in sent_req.keys():
            if i in hierarchy:
                element_list.append(hierarchy.index(i))
        print(element_list)
    else:
        print("entered else")

        print("sent_req", sent_req, default_check)
        sent_req  = default_check
        for i in sent_req.keys():
            if i in hierarchy:
                element_list.append(hierarchy.index(i))
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
    lowest_key = hierarchy[lowest]
    second_lowest_key = hierarchy[lowest]
    # print('lowest_key:', lowest_key, '|', 'lowest', lowest)
    final_list = []  # final list to send
    col_unique_list_name = []  # rename
    col_unique_list_name_obj = {}  # rename
    for col_name in hierarchy:
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
                if col_name in sent_req.keys():
                    if col_name == hierarchy[lowest]:
                        queryset = sales_heirarchy.objects.filter(**{col_name: category_unique})[:1].get()
                        # x = getattr(queryset, hierarchy[lowest])
                        y = getattr(queryset, hierarchy[second_lowest])
                        # print(x, '|', y, '|', hierarchy[lowest], '|',
                        #       'Category_second_last:' + hierarchy[second_lowest],
                        #       '|', col_name,
                        #       '|', category_unique)
                        for i in sent_req.keys():
                            print('keys:', i, sent_req.get(i))
                            if y in sent_req.get(i) and hierarchy[second_lowest] == i:
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
    return JsonResponse({'hierarchy': hierarchy, 'checkbox_list': final_list2}, safe=False)


class Filters(APIView):
    def get(self, request):
        #print(request.GET)

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

        user_id = sent_req.pop('user_id', None)
        designation = sent_req.pop('designation', None)
        session_id = sent_req.pop('session_id', None)
        user_name = sent_req.pop('user_name', None)
        buying_controller_header = sent_req.pop('buying_controller_header', None)
        buyer_header = sent_req.pop('buyer_header', None)

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
        #     filter_json = make_json(obj, kwargs_header,default_check)
        #     cache.set(hexdigest + '_reporting', filter_json)
        #     return filter_json

        return make_json(obj, kwargs_header, default_check)


def col_distinct(kwargs, col_name,kwargs_header):
 #   kwargs['buyer'] = user_buyer
    queryset = sales_heirarchy.objects.filter(**kwargs_header).values(col_name).order_by(col_name).distinct()
    base_product_number_list = [k.get(col_name) for k in queryset]
    return base_product_number_list



#new filter logic
class product_filters_new(APIView):
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






