from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.views import generic
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework import status
import pandas as pd
from django_pandas.io import read_frame
from django.http import JsonResponse
import math
import re
from django.db.models import Count, Min, Max, Sum, Avg, F, FloatField
from .models import supp_kantar, latest_week
from django.core.paginator import Paginator
import json


class kantar_calculations(APIView):

    def get(self, request, format=None):

        args = {reqobj + '__in': request.GET.get(reqobj) for reqobj in request.GET.keys()}

        print(args)

        # remove None
        week_id = args.pop('tesco_week__in', None)
        category = args.pop('category__in')
        retailer = args.pop('retailer__in')
        supplier = args.pop('supplier__in')

        if week_id is None:
            tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
            max_week = [tesco_week_int['cw_max']]
            currentweek = args.pop('tesco_week__in', max_week)
            currentweek = int(currentweek[0])
            week_id = currentweek
        else:
            week_id = int(week_id)

        kwargs = {
            'category__in': category,
            'retailer__in': retailer
        }

        kantar_table_df = read_frame(supp_kantar.objects.filter(**kwargs).filter(
            tesco_week=week_id).values('manufacturer', 'retailer', 'spend', 'growthpercent',
                                        'contritogrowthpercent', 'sharepercentret', 'yoysharechange'))
        kantar_table_df = kantar_table_df.to_dict(orient='records')
        print("kantar_table_data:", kantar_table_df)

        growth_perc_df = read_frame(
            supp_kantar.objects.filter(category__in=category).filter(manufacturer__in=supplier).filter(
                tesco_week=week_id).values('retailer', 'growthpercent'))
        growth_perc_df = growth_perc_df.to_dict(orient='records')

        sharepercsuppl_df = read_frame(
            supp_kantar.objects.filter(category__in=category).filter(manufacturer__in=supplier).filter(
                tesco_week=week_id).values('retailer', 'sharepercentsupp'))

        share_perc_suppl_df = sharepercsuppl_df.to_dict(orient='records')

        yoy_share_df = read_frame(
            supp_kantar.objects.filter(category__in=category).filter(manufacturer__in=supplier).filter(
                tesco_week=week_id).values('retailer', 'totsuppsharechange'))

        yoy_share_df = yoy_share_df.to_dict(orient='records')

        kantar_cards_data = {}
        tesco_growth = supp_kantar.objects.filter(category__in=category).filter(manufacturer__in=supplier).filter(
            retailer="Tesco").filter(tesco_week=week_id).values_list('growthpercent', flat=True)
        try:
            tesco_growth_per = float(list(tesco_growth)[0])
        except:
            tesco_growth_per = 0
        kantar_cards_data['tesco_growth_per'] = tesco_growth_per

        market_growth = supp_kantar.objects.filter(category__in=category).filter(manufacturer__in=supplier).filter(
            retailer="Market").filter(tesco_week=week_id).values_list('growthpercent', flat=True)
        try:
            market_growth_per = float(list(market_growth)[0])
        except:
            market_growth_per = 0
        kantar_cards_data['market_growth_per'] = market_growth_per

        opportunity = supp_kantar.objects.filter(category__in=category).filter(manufacturer__in=supplier).filter(
            retailer="Tesco").filter(tesco_week=week_id).values_list('opportunity', flat=True)
        try:
            opportunity_val = float(list(opportunity)[0])
        except:
            opportunity_val = 0
        kantar_cards_data['opportunity_val'] = opportunity_val

        return JsonResponse({'kantar_table_data': kantar_table_df, 'growth_perc_data': growth_perc_df,
                             'share_perc_suppl_data': share_perc_suppl_df, 'yoy_share_data': yoy_share_df,
                             'kantar_cards_data': kantar_cards_data}, safe=False)

class kantar_tesco_week_filters(APIView):

    def get(self, request, format=None):
        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}
        week_id = args.get('tesco_week__iexact')

        if week_id is None:
            tesco_week_int = latest_week.objects.values('week_ty').order_by('-week_ty')[1]
            max_week = [tesco_week_int['week_ty']]
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
            weeks_data = read_frame(supp_kantar.objects.all().values('tesco_week'))
            weeks_data = weeks_data[(weeks_data["tesco_week"] >= 201626) & (weeks_data['tesco_week'] <= week_id)]

            data = {'tesco_week': weeks_data.tesco_week.unique()}
            week = pd.DataFrame(data)
            if len(week) == 1:
                week.loc[(week["tesco_week"] == week_id), 'selected'] = True
                week.loc[(week["tesco_week"] != week_id), 'selected'] = False
                week.loc[(week["tesco_week"] == week_id), 'disabled'] = True
                week.loc[(week["tesco_week"] != week_id), 'disabled'] = False
            else:
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

            weeks_data = read_frame(supp_kantar.objects.all().values('tesco_week'))
            weeks_data = weeks_data[(weeks_data["tesco_week"] >= 201626) & (weeks_data['tesco_week'] <= week_id)]

            week_df = weeks_data[['tesco_week']].drop_duplicates()

            week_temp = read_frame(supp_kantar.objects.filter(**kwargs).values('tesco_week'))

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


class kantar_heirarchy_filter(APIView):
    def get(self, request, format=None):

        args = {reqobj + '__iexact': request.GET.get(reqobj) for reqobj in request.GET.keys()}

        # input from args
        category_name = args.get('category__iexact')
        retailer_name = args.get('retailer__iexact')
        supplier_name = args.get('supplier__iexact')

        kwargs = {
            'category__iexact': category_name,
            'retailer__iexact': retailer_name,
            'manufacturer__iexact': supplier_name,
        }

        kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))

        if not args:
            heirarchy = read_frame(supp_kantar.objects.filter(**kwargs).values('category', 'retailer', 'manufacturer'))

            category_df = heirarchy[['category']].drop_duplicates()
            retailer_df = heirarchy[['retailer']].drop_duplicates()
            manufacturer_df = heirarchy[['manufacturer']].drop_duplicates()

            if len(category_df) == 1:
                category_df['selected'] = True
                category_df['disabled'] = False
            else:
                category_df['selected'] = False
                category_df['disabled'] = False
            category_df = category_df.rename(columns={'category': 'name'})

            if len(retailer_df) == 1:
                retailer_df['selected'] = True
                retailer_df['disabled'] = False
            else:
                retailer_df['selected'] = False
                retailer_df['disabled'] = False
            retailer_df = retailer_df.rename(columns={'retailer': 'name'})

            if len(manufacturer_df) == 1:
                manufacturer_df['selected'] = True
                manufacturer_df['disabled'] = False
            else:
                manufacturer_df['selected'] = False
                manufacturer_df['disabled'] = False
            manufacturer_df = manufacturer_df.rename(columns={'manufacturer': 'name'})

            category_df = category_df.sort_values(by='name', ascending=True)
            category_df_final = category_df.to_json(orient='records')
            category_df_final = json.loads(category_df_final)

            a = {}
            a['name'] = 'category'
            a['items'] = category_df_final

            retailer_df = retailer_df.sort_values(by='name', ascending=True)
            retailer_df_final = retailer_df.to_json(orient='records')
            retailer_df_final = json.loads(retailer_df_final)

            b = {}
            b['name'] = 'retailer'
            b['items'] = retailer_df_final

            manufacturer_df = manufacturer_df.sort_values(by='name', ascending=True)
            manufacturer_df_final = manufacturer_df.to_json(orient='records')
            manufacturer_df_final = json.loads(manufacturer_df_final)

            c = {}
            c['name'] = 'manufacturer'
            c['items'] = manufacturer_df_final

            final_ph = []
            final_ph.append(a)
            final_ph.append(b)
            final_ph.append(c)
            final = {}
            final["hierarchy"] = final_ph

        else:
            df = read_frame(supp_kantar.objects.filter(**kwargs))

            hh = read_frame(supp_kantar.objects.filter(category__in=df.category.unique()).values(
                'category', 'retailer', 'manufacturer'))


            category_df = hh[['category']].drop_duplicates()
            retailer_df = hh[['retailer']].drop_duplicates()
            manufacturer_df = hh[['manufacturer']].drop_duplicates()

            df_temp = read_frame(supp_kantar.objects.filter(category__in=df.category.unique()))

            data = {'category': df.category.unique()}
            category = pd.DataFrame(data)

            data = {'retailer': df.retailer.unique()}
            retailer = pd.DataFrame(data)

            data = {'manufacturer': df.manufacturer.unique()}
            manufacturer = pd.DataFrame(data)

            category['selected'] = True
            category['disabled'] = False
            category_df = pd.merge(category_df, category, how='left')
            category_df['selected'] = category_df['selected'].fillna(False)
            category_df['disabled'] = category_df['disabled'].fillna(True)

            category_df = category_df.rename(columns={'category': 'name'})

            if len(retailer) == 1:
                retailer['selected'] = True
                retailer['disabled'] = False
                retailer_df = pd.merge(retailer_df, retailer, how='left')
                retailer_df['selected'] = retailer_df['selected'].fillna(False)
                retailer_df['disabled'] = retailer_df['disabled'].fillna(True)
                retailer_df = retailer_df.rename(columns={'retailer': 'name'})
            else:
                retailer['selected'] = False
                retailer['disabled'] = False
                retailer_df = pd.merge(retailer_df, retailer, how='left')
                retailer_df['selected'] = retailer_df['selected'].fillna(False)
                retailer_df['disabled'] = retailer_df['disabled'].fillna(True)
                retailer_df = retailer_df.rename(columns={'retailer': 'name'})

            if len(manufacturer) == 1:
                manufacturer['selected'] = True
                manufacturer['disabled'] = False
                manufacturer_df = pd.merge(manufacturer_df, manufacturer, how='left')
                manufacturer_df['selected'] = manufacturer_df['selected'].fillna(False)
                manufacturer_df['disabled'] = manufacturer_df['disabled'].fillna(True)
                manufacturer_df = manufacturer_df.rename(columns={'manufacturer': 'name'})
            else:
                manufacturer['selected'] = False
                manufacturer['disabled'] = False
                manufacturer_df = pd.merge(manufacturer_df, manufacturer, how='left')
                manufacturer_df['selected'] = manufacturer_df['selected'].fillna(False)
                manufacturer_df['disabled'] = manufacturer_df['disabled'].fillna(True)
                manufacturer_df = manufacturer_df.rename(columns={'manufacturer': 'name'})

            category_df = category_df.sort_values(by='name', ascending=True)
            category_df_final = category_df.to_json(orient='records')
            category_df_final = json.loads(category_df_final)

            a = {}
            a['name'] = 'category'
            a['items'] = category_df_final

            retailer_df = retailer_df.sort_values(by='name', ascending=True)
            retailer_df_final = retailer_df.to_json(orient='records')
            retailer_df_final = json.loads(retailer_df_final)

            b = {}
            b['name'] = 'retailer'
            b['items'] = retailer_df_final

            manufacturer_df = manufacturer_df.sort_values(by='name', ascending=True)
            manufacturer_df_final = manufacturer_df.to_json(orient='records')
            manufacturer_df_final = json.loads(manufacturer_df_final)

            c = {}
            c['name'] = 'manufacturer'
            c['items'] = manufacturer_df_final

            final_ph = []
            final_ph.append(a)
            final_ph.append(b)
            final_ph.append(c)

            final = {}
            final["product_hierarchy"] = final_ph

        return JsonResponse(final, safe=False)