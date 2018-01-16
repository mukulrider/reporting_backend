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
import math
import logging
import time
from .models import sales_heirarchy, supplier_view, calendar_dim_hierarchy, latest_week

from django.utils import six
import numpy as np

# from .NPD_test import outperformance_calculations
import pandas as pd
from django_pandas.io import read_frame
timestr = time.strftime("%Y%m%d")
logging.basicConfig(filename='logs/reporting_views_'+timestr+'.log', level=logging.DEBUG,
					format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
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
from django.db.models import Count, Min, Max, Sum, Avg, F, FloatField, Case, When, Value, Q
import collections


class supplier_filterdata_week(APIView):
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

			print(final)
		return JsonResponse(final,safe=False)

class supplier_view_kpi(APIView):
	def get(self, request, *args):

		print("args recieved")
		args = {reqobj + '__in' : request.GET.getlist(reqobj) for reqobj in request.GET.keys()}

		print("before popping out cookies", args)
		#### for week tab
		week_flag = args.pop('week_flag__in', [1])
		print("week_flag testing")

		#### for current week value
		tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
		max_week = [tesco_week_int['cw_max']]
		cw_week = args.pop('tesco_week__in', max_week)
		# print(type(cw_week))

		#### for kpi type tab
		kpi_type = args.pop('kpi_type__in', ['Value'])
		kpi_type_check = kpi_type[0]
		store_type = args.pop('store_type__in', ["Main Estate", "Express"])

		##### parent supplier
		parent = args.pop('parent_supplier__in', None)
		print("supplier view kpi", parent)

		#### supplier
		supplier = args.pop('supplier__in', None)

		print("args after pop")
		print(args)


		###Cookies, SSO
		user_id = args.pop('user_id__in', None)
		designation = args.pop('designation__in', None)
		user_name = args.pop('user_name__in', None)
		buying_controller_header = args.pop('buying_controller_header__in', None)
		buyer_header = args.pop('buyer_header__in', None)

		print("after popping out cookies", args)
		print("latest week...............", cw_week)
		###### convert "and" to "and"
		# products=sales_heirarchy.objects.filter(**args).values('product_id').distinct()

		if not args:
			if ((buyer_header is None) or (buyer_header == '')):
				kwargs_header = {
					'buying_controller__in': buying_controller_header
				}
			else:
				kwargs_header = {
					'buying_controller__in': buying_controller_header,
					'buyer__in': buyer_header
				}
			products = sales_heirarchy.objects.filter(**kwargs_header).values(
				'product_id').distinct()

		else:
			# print("entered else")
			products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
			# print(products[:10])

		def box1(x, y, z, a, b, title, week_flag):
			# Total sales
			# print("entered box1")

			def week_selection(cw_week, week_flag):
				week_ordered = calendar_dim_hierarchy.objects.filter(tesco_week__lte=cw_week).values(
					'tesco_week').order_by('-tesco_week').distinct()
				last_week = week_ordered[1]
				last_week = last_week['tesco_week']
				if (week_flag == 1):
					week_logic = week_ordered[:1]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 2):
					week_logic = week_ordered[:4]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))  # ###print("Inside elif 1")

				elif (week_flag == 3):
					week_logic = week_ordered[:13]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 4):

					week_logic = week_ordered[:26]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 5):

					current_week = int(cw_week)
					for_x = int(str(current_week)[-2:])
					week_logic = week_ordered[:for_x]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				week = {"last_week": last_week, "week_var": week_var}
				return week

			week = week_selection(int(cw_week[0]), int(week_flag[0]))
			print("week.........",week, "Week type.......", type(week))
			# print("week var")
			# print(week)
			# print(week["week_var"])

			# if not args:
			# 	kwargs_inclu_sup = {
			# 		'tesco_week__in': week["week_var"],
			# 		'product_id__in': products
			# 	}
            #
			# 	kwargs_inclu_last = {
			# 		'tesco_week': week["last_week"],
			# 		'product_id__in': products}
            #
			# 	kwargs_exclu_sup = {
			# 		'tesco_week__in': week["week_var"],
			# 		'product_id__in': products
			# 	}
            #
			# 	kwargs_exclu_last = {
			# 		'tesco_week': week["last_week"],
			# 		'product_id__in': products}
			# else:
			kwargs_inclu_sup = {
				'tesco_week__in': week["week_var"],
				'product_id__in': products,
				'parent_supplier__in': parent,
				'supplier__in': supplier,
				'store_type__in': store_type
			}
			kwargs_inclu_sup = dict(filter(lambda item: item[1] is not None, kwargs_inclu_sup.items()))
			kwargs_inclu_sup_exclu_product = {
				'tesco_week__in': week["week_var"],
				'parent_supplier__in': parent,
				'supplier__in': supplier,
				'store_type__in': store_type
			}
			kwargs_inclu_sup_exclu_product = dict(filter(lambda item: item[1] is not None, kwargs_inclu_sup_exclu_product.items()))

			kwargs_inclu_last = {
				'tesco_week': week["last_week"],
				'product_id__in': products,
				'parent_supplier__in': parent,
				'supplier__in': supplier,
				'store_type__in': store_type
			}

			kwargs_inclu_last = dict(filter(lambda item: item[1] is not None, kwargs_inclu_last.items()))

			kwargs_exclu_sup = {
				'tesco_week__in': week["week_var"],
				'product_id__in': products,
				'store_type__in': store_type
			}

			kwargs_exclu_last = {
				'tesco_week': week["last_week"],
				'product_id__in': products,
				'store_type__in': store_type
			}

				############# IF ELSE NOT NEEDED AS KWARGS BEING PASSED #############

			# print("kwargs inclu sup")
			# print(kwargs_inclu_sup)
			current_week_data = supplier_view.objects.filter(**kwargs_inclu_sup).aggregate(Total_sales_cw=Sum(x),
																						   Total_sales_cw_lfl=Sum(y),
																						   Total_sales_cw_ly_lfl=Sum(z),
																						   Total_sales_cw_ly=Sum(b))
			##print(current_week_data)

			last_week_data = supplier_view.objects.filter(**kwargs_inclu_last).aggregate(Total_sales_lw=Sum(x),
																						 Total_sales_lw_lfl=Sum(y))
			##print(last_week_data)

			inclu_sup_tw = supplier_view.objects.filter(**kwargs_inclu_sup).aggregate(sales_cw_filtered=Sum(x),
																					  sales_cw_ly_filtered=Sum(b),
																					  sales_cw_filtered_lfl=Sum(y),
																					  sales_cw_ly_filtered_lfl=Sum(z))
			inclu_sup_tw_exclu_product = read_frame(supplier_view.objects.filter(**kwargs_inclu_sup_exclu_product).values_list(a))
			print(len(inclu_sup_tw_exclu_product))
			inclu_sup_tw_exclu_product = inclu_sup_tw_exclu_product[a].unique()
			print(len(inclu_sup_tw_exclu_product))
			print(type(inclu_sup_tw_exclu_product))
			print(inclu_sup_tw_exclu_product)
			inclu_sup_tw_exclu_product = pd.DataFrame(inclu_sup_tw_exclu_product)
			inclu_sup_tw_exclu_product_sum = inclu_sup_tw_exclu_product.sum().astype(float)
			inclu_sup_tw_exclu_product_sum = float(inclu_sup_tw_exclu_product_sum[0])
			print(inclu_sup_tw_exclu_product_sum, type(inclu_sup_tw_exclu_product_sum))
			exclu_sup_tw = supplier_view.objects.filter(**kwargs_exclu_sup).aggregate(sales_cw_filtered_above=Sum(x),
																					  sales_cw_ly_filtered_above=Sum(b),
																					  sales_cw_filtered_above_lfl=Sum(
																						  y),
																					  sales_cw_ly_filtered_above_lfl=Sum(
																						  z))
			##print(exclu_sup_tw)
			inclu_sup_lw = supplier_view.objects.filter(**kwargs_inclu_last).aggregate(sales_lw_wow_filtered=Sum(x))
			##print(inclu_sup_lw)
			exclu_sup_lw = supplier_view.objects.filter(**kwargs_exclu_last).aggregate(
				sales_lw_wow_filtered_above=Sum(x))
			##print(exclu_sup_lw)

			##Sales excluding supplier
			try:
				cw_sales_exclu_sup = format(exclu_sup_tw['sales_cw_filtered_above'], '.1f')
				cw_sales_exclu_sup_lfl = format(exclu_sup_tw['sales_cw_filtered_above_lfl'], '.1f')
			except:
				cw_sales_exclu_sup = 0
				cw_sales_exclu_sup_lfl = 0

			try:
				cw_sales = format(current_week_data['Total_sales_cw'], '.1f')
				cw_sales_lfl = format(current_week_data['Total_sales_cw_lfl'], '.1f')
			except:
				cw_sales = 0
				cw_sales_lfl = 0
			# Last Sales
			try:
				lw_sales = format(last_week_data['Total_sales_lw'], '.0f')
				lw_sales_lfl = format(last_week_data['Total_sales_lw_lfl'], '.1f')
			except:
				lw_sales = 0
				lw_sales_lfl = 0
			# ####print(lw_sales)
			# ####print(type(lw_sales))

			sales_growth_yoy = inclu_sup_tw['sales_cw_filtered']
			sales_growth_ly_yoy = inclu_sup_tw['sales_cw_ly_filtered']
			sales_growth_above_yoy = exclu_sup_tw['sales_cw_filtered_above']
			sales_growth_ly_above_yoy = exclu_sup_tw['sales_cw_ly_filtered_above']

			try:
				sales_growth_yoy_1 = format(
					((sales_growth_yoy - sales_growth_ly_yoy) / sales_growth_ly_above_yoy) * 100, '.1f')
			except:
				sales_growth_yoy_1 = 0

			try:
				sales_growth_yoy_2 = format(
					((sales_growth_above_yoy - sales_growth_ly_above_yoy) / sales_growth_ly_above_yoy) * 100, '.1f')
			except:
				sales_growth_yoy_2 = 0
			# volume calculation

			sales_growth_yoy_lfl = inclu_sup_tw['sales_cw_filtered_lfl']
			sales_growth_ly_yoy_lfl = inclu_sup_tw['sales_cw_ly_filtered_lfl']
			sales_growth_above_yoy_lfl = exclu_sup_tw['sales_cw_filtered_above_lfl']
			sales_growth_ly_above_yoy_lfl = exclu_sup_tw['sales_cw_ly_filtered_above_lfl']

			try:
				sales_growth_yoy_lfl_1 = format(
					((sales_growth_yoy_lfl - sales_growth_ly_yoy_lfl) / sales_growth_ly_above_yoy_lfl) * 100, '.2f')
			except:
				sales_growth_yoy_lfl_1 = 0

			try:
				sales_growth_yoy_lfl_2 = format(((
												 sales_growth_above_yoy_lfl - sales_growth_ly_above_yoy_lfl) / sales_growth_ly_above_yoy_lfl) * 100,
												'.2f')
			except:
				sales_growth_yoy_lfl_2 = 0

			sales_growth_wow = inclu_sup_tw['sales_cw_filtered']
			sales_growth_lw_wow = inclu_sup_lw['sales_lw_wow_filtered']
			sales_growth_above_wow = exclu_sup_tw['sales_cw_filtered_above']
			sales_growth_lw_above_wow = exclu_sup_lw['sales_lw_wow_filtered_above']

			try:
				print("entered if", sales_growth_wow, "     ",sales_growth_lw_wow,"     ", sales_growth_lw_above_wow)
				sales_growth_wow_1 = format(
					((sales_growth_wow - sales_growth_lw_wow) / sales_growth_lw_above_wow) * 100, '.1f')
			except:
				print("entering except")
				sales_growth_wow_1 = 0
			try:
				sales_growth_wow_2 = format(
					((sales_growth_above_wow - sales_growth_lw_above_wow) / sales_growth_lw_above_wow) * 100, '.1f')
			except:
				sales_growth_wow_2 = 0

			try:
				sales_var_week = format(((current_week_data['Total_sales_cw'] - last_week_data['Total_sales_lw']) / (
				last_week_data['Total_sales_lw'])) * 100, '.1f')
				sales_var_week = float(sales_var_week)
			except:
				sales_var_week = 0

			try:
				sales_var_year = format(((current_week_data['Total_sales_cw'] - current_week_data[
					'Total_sales_cw_ly']) / (current_week_data['Total_sales_cw_ly'])) * 100, '.1f')
				sales_var_year = float(sales_var_year)
			except:
				sales_var_year = 0

			try:
				sales_var_year_lfl = format(((current_week_data['Total_sales_cw_lfl'] - current_week_data[
					'Total_sales_cw_ly_lfl']) / (current_week_data['Total_sales_cw_ly_lfl'])) * 100, '.1f')
				sales_var_year_lfl = float(sales_var_year_lfl)
			except:
				sales_var_year_lfl = 0

			try:
				# cw_category_sales = supplier_view.objects.filter(category_name = "Beers, Wines & Spirits").filter(tesco_week__in = week_var).aggregate(Total_sales_cw = Sum('sales_ty'))
				supp_imp_cat_sales = format(
					((inclu_sup_tw['sales_cw_filtered'] / exclu_sup_tw['sales_cw_filtered_above']) * 100), '.1f')

			except:
				cw_category_sales = 0
				supp_imp_cat_sales = 0

			try:
				if inclu_sup_tw_exclu_product_sum !=0:
					cat_imp_supp_sales = format(float(float(inclu_sup_tw['sales_cw_filtered']) / inclu_sup_tw_exclu_product_sum) * 100, '.1f')
				else:
					cat_imp_supp_sales = 0
			except:
				print("entered else for cat imp to supp sales")
				supp_tesco_sales = 0
				cat_imp_supp_sales = 0

			if kpi_type_check == 'Volume':
				try:
					if float(cw_sales) >= 1000:
						integer_val = int(float(cw_sales) / 1000)
						cw_sales = intcomma(str(integer_val)) + 'K'
					else:
						cw_sales = intcomma(str(cw_sales))

					if float(cw_sales_lfl) >= 1000:
						integer_val = int(float(cw_sales_lfl) / 1000)
						cw_sales_lfl = intcomma(str(integer_val)) + 'K'
					else:
						cw_sales_lfl = intcomma(str(cw_sales_lfl))

					if float(cw_sales_exclu_sup) >= 1000:
						integer_val = int(float(cw_sales_exclu_sup) / 1000)
						cw_sales_exclu_sup = intcomma(str(integer_val)) + 'K'
					else:
						cw_sales_exclu_sup = intcomma(str(cw_sales_exclu_sup))

					if float(cw_sales_exclu_sup_lfl) >= 1000:
						integer_val = int(float(cw_sales_exclu_sup_lfl) / 1000)
						cw_sales_exclu_sup_lfl = intcomma(str(integer_val)) + 'K'
					else:
						cw_sales_exclu_sup_lfl = intcomma(str(cw_sales_exclu_sup_lfl))
				except:
					cw_sales = 0
					cw_sales_lfl = 0
					cw_sales_exclu_sup = 0
					cw_sales_exclu_sup_lfl = 0
			else:
				try:
					if float(cw_sales) >= 1000:
						integer_val = int(float(cw_sales) / 1000)
						cw_sales = '£' + intcomma(str(integer_val)) + 'K'
					else:
						cw_sales = '£' + intcomma(str(cw_sales))

					if float(cw_sales_lfl) >= 1000:
						integer_val = int(float(cw_sales_lfl) / 1000)
						cw_sales_lfl = '£' + intcomma(str(integer_val)) + 'K'
					else:
						cw_sales_lfl = '£' + intcomma(str(cw_sales_lfl))

					if float(cw_sales_exclu_sup) >= 1000:
						integer_val = int(float(cw_sales_exclu_sup) / 1000)
						cw_sales_exclu_sup = '£' + intcomma(str(integer_val)) + 'K'
					else:
						cw_sales_exclu_sup = '£' + intcomma(str(cw_sales_exclu_sup))

					if float(cw_sales_exclu_sup_lfl) >= 1000:
						integer_val = int(float(cw_sales_exclu_sup_lfl) / 1000)
						cw_sales_exclu_sup_lfl = '£' + intcomma(str(integer_val)) + 'K'
					else:
						cw_sales_exclu_sup_lfl = '£' + intcomma(str(cw_sales_exclu_sup_lfl))
				except:
					cw_sales = 0
					cw_sales_lfl = 0
					cw_sales_exclu_sup = 0
					cw_sales_exclu_sup_lfl = 0

			if (int(week_flag[0]) != 1):
				sales_var_week = 'NA'
				sales_growth_wow_1 = 'NA'
				sales_growth_wow_2 = 'NA'
			# else:
			#     sales_var_week = str(sales_var_week) + '%'
			#     sales_growth_wow_1 = str(sales_growth_wow_1) + '%'
			#     sales_growth_wow_2 = str(sales_growth_wow_2) + '%'

			kpi_data = []
			data = {'sales': (cw_sales),
					'cat_sales_TO_SUP':inclu_sup_tw_exclu_product_sum,
					'sales_lfl': (cw_sales_lfl),
					'sales_var_week': sales_var_week,
					'sales_var_year': sales_var_year,
					'sales_var_year_lfl': sales_var_year_lfl,
					'sales_growth_yoy_1': float(sales_growth_yoy_1),
					'sales_growth_yoy_2': float(sales_growth_yoy_2),
					'sales_growth_wow_1': sales_growth_wow_1,
					'sales_growth_wow_2': sales_growth_wow_2,
					'sales_growth_yoy_lfl_1': float(sales_growth_yoy_lfl_1),
					'sales_growth_yoy_lfl_2': float(sales_growth_yoy_lfl_2),
					'supp_imp_cat_sales': float(supp_imp_cat_sales),
					'cat_imp_supp_sales': float(cat_imp_supp_sales),
					'cw_sales_exclu_sup': cw_sales_exclu_sup,
					'cw_sales_exclu_sup_lfl': cw_sales_exclu_sup_lfl,
					'title': title,
					'date': int(cw_week[0])
					}
			logging.info(data)
			kpi_data.append(data)
			# df= pd.DataFrame(data,index = [0])
			# df1 = df.to_json(orient="records")
			# json_data = json.loads(df1)
			return kpi_data

		def sku_rsp(week_flag):

			def week_selection(cw_week, week_flag):
				week_ordered = supplier_view.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
					'-tesco_week').distinct()
				last_week = week_ordered[1]
				last_week = last_week['tesco_week']
				if (week_flag == 1):
					week_logic = week_ordered[:1]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 2):
					week_logic = week_ordered[:4]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))  # ###print("Inside elif 1")

				elif (week_flag == 3):
					week_logic = week_ordered[:13]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 4):

					week_logic = week_ordered[:26]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 5):

					current_week = int(cw_week)
					for_x = int(str(current_week)[-2:])
					week_logic = week_ordered[:for_x]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				week = {"last_week": last_week, "week_var": week_var}
				return week

			week = week_selection(int(cw_week[0]), int(week_flag[0]))


			# if not args:
			# 	kwargs_inclu_sup = {
			# 		'tesco_week__in': week["week_var"],
			# 		'product_id__in': products
			# 	}
            #
			# 	kwargs_inclu_last = {
			# 		'tesco_week__in': [week["last_week"]],
			# 		'product_id__in': products}
            #
			# 	kwargs_exclu_sup = {
			# 		'tesco_week__in': week["week_var"],
			# 		'product_id__in': products
			# 	}
            #
			# 	kwargs_exclu_last = {
			# 		'tesco_week__in': [week["last_week"]],
			# 		'product_id__in': products}
			# else:
			kwargs_inclu_sup = {
				'tesco_week__in': week["week_var"],
				'product_id__in': products,
				'parent_supplier__in': parent,
				'supplier__in': supplier,
				'store_type__in': store_type

			}

			kwargs_inclu_sup = dict(filter(lambda item: item[1] is not None, kwargs_inclu_sup.items()))

			kwargs_inclu_last = {
				'tesco_week__in': [week["last_week"]],
				'product_id__in': products,
				'parent_supplier__in': parent,
				'supplier__in': supplier,
				'store_type__in': store_type
			}
			kwargs_inclu_last = dict(filter(lambda item: item[1] is not None, kwargs_inclu_last.items()))
			kwargs_exclu_sup = {
				'tesco_week__in': week["week_var"],
				'product_id__in': products,
				'store_type__in': store_type
			}
			kwargs_exclu_sup = dict(filter(lambda item: item[1] is not None, kwargs_exclu_sup.items()))

			kwargs_exclu_last = {
				'tesco_week': week["last_week"],
				'product_id__in': products,
				'store_type__in': store_type
			}
			kwargs_exclu_last = dict(filter(lambda item: item[1] is not None, kwargs_exclu_last.items()))

			exclu_sup_tw = supplier_view.objects.filter(**kwargs_exclu_sup).filter(sales_ty__gt=0).aggregate(
				count_cw_filtered_above=Count('product_id', distinct=True))

			inclu_sup_tw = supplier_view.objects.filter(**kwargs_inclu_sup).filter(sales_ty__gt=0).aggregate(
				count_cw_filtered=Count('product_id', distinct=True))

			sku_ly_lfl = supplier_view.objects.filter(**kwargs_inclu_sup).filter(sales_ly_lfl__gt=0).filter(
				sales_ly_lfl__gt=0).aggregate(cnt_sku_cw_lfl=Count('product_id', distinct=True))

			current_week_data = supplier_view.objects.filter(**kwargs_inclu_sup).aggregate(
				cnt_sku_cw=Count('product_id', distinct=True), Total_sales_cw=Sum('sales_ty'),
				Total_sales_cw_lfl=Sum('sales_ty_lfl'), Total_volume_cw=Sum('volume_ty'),
				Total_volume_cw_lfl=Sum('volume_ty_lfl'), Total_sales_cw_ly_lfl=Sum('sales_ly_lfl'),
				Total_volume_cw_ly_lfl=Sum('volume_ly_lfl'), Total_sales_cw_ly=Sum('sales_ly'),
				Total_volume_cw_ly=Sum('volume_ly'))

			current_week_data_sku = supplier_view.objects.filter(**kwargs_inclu_sup).filter(sales_ty__gt=0).aggregate(
				cnt_sku_cw=Count('product_id', distinct=True))

			current_week_data_sku_lfl = supplier_view.objects.filter(**kwargs_inclu_sup).filter(
				sales_ty_lfl__gt=0).aggregate(cnt_sku_cw=Count('product_id', distinct=True))

			last_week_data = supplier_view.objects.filter(**kwargs_inclu_last).aggregate(
				cnt_sku_lw=Count('product_id', distinct=True), Total_sales_lw=Sum('sales_ty'),
				Total_volume_lw=Sum('volume_ty'))

			last_week_data_sku = supplier_view.objects.filter(**kwargs_inclu_last).filter(sales_ty__gt=0).aggregate(
				cnt_sku_lw=Count('product_id', distinct=True))

			sku_total_lfl = current_week_data_sku_lfl['cnt_sku_cw']

			sku_ly_1 = supplier_view.objects.filter(**kwargs_inclu_sup).filter(sales_ly__gt=0).aggregate(
				cnt_sku_ly=Count('product_id', distinct=True))

			try:
				sku_week_var = format(((current_week_data_sku['cnt_sku_cw'] - last_week_data_sku['cnt_sku_lw']) / (
				last_week_data_sku['cnt_sku_lw'])) * 100, '.1f')

			except:
				sku_week_var = 0

			try:
				sku_year_var = format(
					((current_week_data_sku['cnt_sku_cw'] - sku_ly_1['cnt_sku_ly']) / (sku_ly_1['cnt_sku_ly'])) * 100,
					'.1f')

			except:
				sku_year_var = 0

			try:
				sku_year_var_lfl = format(((current_week_data_sku_lfl['cnt_sku_cw'] - sku_ly_lfl['cnt_sku_cw_lfl']) / (
				sku_ly_lfl['cnt_sku_cw_lfl'])) * 100, '.1f')

			except:
				sku_year_var_lfl = 0

			try:
				cnt_products_sup = format(
					((float(inclu_sup_tw['count_cw_filtered']) / exclu_sup_tw['count_cw_filtered_above'])) * 100, '.1f')

			except:
				cnt_products_sup = 0

			###RSP
			try:
				current_rsp = current_week_data['Total_sales_cw'] / current_week_data['Total_volume_cw']
			except:
				current_rsp = 0

			try:
				last_rsp = (last_week_data['Total_sales_lw']) / (last_week_data['Total_volume_lw'])
			except:
				last_rsp = 0

			# current_rsp = format(current_rsp_x,'.1f')
			try:
				current_rsp_lfl = (current_week_data['Total_sales_cw_lfl']) / (current_week_data['Total_volume_cw_lfl'])
			except:
				current_rsp_lfl = 0

			try:
				last_year_rsp_lfl = (current_week_data['Total_sales_cw_ly_lfl']) / (
				current_week_data['Total_volume_cw_ly_lfl'])
			except:
				last_year_rsp_lfl = 0

			try:
				last_year_rsp = (current_week_data['Total_sales_cw_ly']) / (current_week_data['Total_volume_cw_ly'])
			except:
				last_year_rsp = 0

				# RSP Variation
			# ####print("==== RSP Var Check ====")
			try:
				# ####print("==== RSP Var Check try====")
				rsp_var_week = format(((current_rsp - last_rsp) / (last_rsp)) * 100, '.1f')
				rsp_var_week = float(rsp_var_week)
			except:
				# ####print("==== RSP Var Check except====")
				rsp_var_week = 0

			try:
				rsp_var_year = format(((current_rsp - last_year_rsp) / (last_year_rsp)) * 100, '.1f')
				rsp_var_year = float(rsp_var_year)
			except:
				rsp_var_year = 0

			try:
				rsp_var_year_lfl = format(((current_rsp_lfl - last_year_rsp_lfl) / (last_year_rsp_lfl)) * 100, '.1f')
				rsp_var_year_lfl = float(rsp_var_year_lfl)
			except:
				rsp_var_year_lfl = 0

			# ###print("sku check")
			# ###print(sku_ly_1)
			# ###print(current_week_data['cnt_sku_cw'])
			sku_total = current_week_data['cnt_sku_cw']
			if current_rsp_lfl != 0:
				current_rsp_lfl = '£' + str(format(current_rsp_lfl, '.1f'))

			if current_rsp != 0:
				current_rsp = '£' + str(format(current_rsp, '.1f'))

			# data = {
			#         'sku_year_var_lfl':float(sku_year_var_lfl),
			#         'sku_week_var':float(sku_week_var),
			#         'sku_year_var':float(sku_year_var),
			#         'sku_total':float(sku_total),
			#         'sku_total_lfl':float(sku_total_lfl),
			#         'cnt_products_sup': float(cnt_products_sup),
			#         'current_rsp' : float(current_rsp),
			#         'current_rsp_lfl' : float(current_rsp_lfl),
			#         'rsp_var_week' : float(rsp_var_week),
			#         'rsp_var_year' : float(rsp_var_year),
			#         'rsp_var_year_lfl' : float(rsp_var_year_lfl)
			#         }

			if (int(week_flag[0]) != 1):
				rsp_var_week = 'NA'
				sku_week_var = 'NA'

			kpi_data = []
			if kpi_type_check == 'SKU':
				data = {'sales': (sku_total),
						'sales_lfl': (sku_total_lfl),
						'sales_var_week': sku_week_var,
						'sales_var_year': sku_year_var,
						'sales_var_year_lfl': sku_year_var_lfl,
						'sales_growth_yoy_1': '---',
						'sales_growth_yoy_2': '---',
						'sales_growth_wow_1': '---',
						'sales_growth_wow_2': '---',
						'sales_growth_yoy_lfl_1': '---',
						'sales_growth_yoy_lfl_2': '---',
						'supp_imp_cat_sales': '---',
						'cat_imp_supp_sales': '---',
						'cw_sales_exclu_sup': '---',
						'cw_sales_exclu_sup_lfl': '---',
						'title':'Total SKUs'
						}
			elif kpi_type_check == 'ASP':
				data = {'sales': (current_rsp),
						'sales_lfl': (current_rsp_lfl),
						'sales_var_week': rsp_var_week,
						'sales_var_year': rsp_var_year,
						'sales_var_year_lfl': rsp_var_year_lfl,
						'sales_growth_yoy_1': '---',
						'sales_growth_yoy_2': '---',
						'sales_growth_wow_1': '---',
						'sales_growth_wow_2': '---',
						'sales_growth_yoy_lfl_1': '---',
						'sales_growth_yoy_lfl_2': '---',
						'supp_imp_cat_sales': '---',
						'cat_imp_supp_sales': '---',
						'cw_sales_exclu_sup': '---',
						'cw_sales_exclu_sup_lfl': '---',
						'title':'ASP'
						}

			logging.info(data)

			kpi_data.append(data)
			return kpi_data

		if kpi_type_check == 'Value':
			kpi_1 = 'sales_ty'
			kpi_2 = 'sales_ty_lfl'
			kpi_3 = 'sales_ly_lfl'
			kpi_4 = 'cat_sales_ty'
			kpi_5 = 'sales_ly'
			title = 'Total Value'
			data = box1(kpi_1, kpi_2, kpi_3, kpi_4, kpi_5, title, week_flag)
		elif kpi_type_check == 'Volume':
			kpi_1 = 'volume_ty'
			kpi_2 = 'volume_ty_lfl'
			kpi_3 = 'volume_ly_lfl'
			kpi_4 = 'cat_volume_ty'
			kpi_5 = 'volume_ly'
			title = 'Total Volume'
			data = box1(kpi_1, kpi_2, kpi_3, kpi_4, kpi_5, title, week_flag)
		elif kpi_type_check == 'COGS':
			kpi_1 = 'cogs_ty'
			kpi_2 = 'cogs_ty_lfl'
			kpi_3 = 'cogs_ly_lfl'
			kpi_4 = 'cat_cogs_ty'
			kpi_5 = 'cogs_ly'
			title = 'Total COGS'
			data = box1(kpi_1, kpi_2, kpi_3, kpi_4, kpi_5, title, week_flag)
		elif kpi_type_check == 'CGM':
			kpi_1 = 'cgm_ty'
			kpi_2 = 'cgm_ty_lfl'
			kpi_3 = 'cgm_ly_lfl'
			kpi_4 = 'cat_cgm_ty'
			kpi_5 = 'cgm_ly'
			title = 'Total CGM'
			data = box1(kpi_1, kpi_2, kpi_3, kpi_4, kpi_5, title, week_flag)
		elif kpi_type_check == 'Supp_Fund':
			kpi_1 = 'fundxvat_ty'
			kpi_2 = 'fundxvat_ty_lfl'
			kpi_3 = 'fundxvat_ly_lfl'
			kpi_4 = 'cat_fundxvat_ty'
			kpi_5 = 'fundxvat_ly'
			title = 'Total Supplier Funding'
			data = box1(kpi_1, kpi_2, kpi_3, kpi_4, kpi_5, title, week_flag)
		elif kpi_type_check == 'ASP':
			data = sku_rsp(week_flag)
		elif kpi_type_check == 'SKU':
			data = sku_rsp(week_flag)
		else:
			kpi_1 = 'sales_ty'
			kpi_2 = 'sales_ty_lfl'
			kpi_3 = 'sales_ly_lfl'
			kpi_4 = 'cat_sales_ty'
			kpi_5 = 'sales_ly'
			title = 'Total Sales'
			data = box1(kpi_1, kpi_2, kpi_3, kpi_4, kpi_5, title, week_flag)

		return JsonResponse(data, safe=False)

class supplier_view_chart_bubble(APIView):
    def get(self, request, *args):

        print("args recieved")
        args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
        # print(args)
        #### for week tab

        ##FOR STORE TYPE
        # print("store type test chart")
        # store_type = args.pop("store_type", "Main Estate")
        # print(store_type)
        # print("store type tested chart")
        week_flag = args.pop('week_flag__in', [1])

        #### for current week value
        tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
        max_week = [tesco_week_int['cw_max']]
        cw_week = args.pop('tesco_week__in', max_week)
        # print(type(cw_week))

        #### for kpi type tab
        kpi_type = args.pop('kpi_type__in', None)

        ##### parent supplier
        # parent=args.pop('parent_supplier',None)

        #### supplier
        # supplier=args.pop('supplier',None)



        ### buying controller
        # buying_controller = args.pop('buying_controller__in', None)

        ### store_type
        store_type = args.pop('store_type__in', None)
        ###Store type nego
        store_type_nego = args.pop('store_type_nego__in', ["Main Estate"])

        # print("store type -----------")
        # print(store_type)
        # print("store type ---------- done")


        ## performance quartile
        performance_quartile = args.pop('performance_quartile__in', None)
        # print("performance_quartile --------------")
        # print(performance_quartile)
        # print("performance_quartile --------------")

        #Cookies SSO

        user_id = args.pop('user_id__in', None)
        designation = args.pop('designation__in', None)
        session_id = args.pop('session_id__in', None)
        user_name = args.pop('user_name__in', None)
        buying_controller_header = args.pop('buying_controller_header__in', None)
        buyer_header = args.pop('buyer_header__in', None)

        # print("args after pop")
        # print(args)

        ###### convert "and" to "and"
        # products=sales_heirarchy.objects.filter(**args).values('product_id').distinct()

        if not args:
            if buyer_header is None:
                kwargs_header = {
                    'buying_controller__in': buying_controller_header
                }
            else:
                kwargs_header = {
                    'buying_controller__in': buying_controller_header,
                    'buyer__in': buyer_header
                }
            products_bc = sales_heirarchy.objects.filter(**kwargs_header).values('product_id').distinct()
            product_description = sales_heirarchy.objects.filter(**kwargs_header).values('product_id','product').distinct()
            # print("products_bc------------------")
            # print(products_bc)
            tesco_week_int = supplier_view.objects.aggregate(cw_max=Max('tesco_week'))
            # cw_week = tesco_week_int['cw_max']

        else:
            # print("emtered else")
            products_bc = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
            product_description = sales_heirarchy.objects.filter(**args).values('product_id', 'product').distinct()

        def table_bubble_clasfc():

            def week_selection(cw_week, week_flag):
                week_ordered = supplier_view.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
                    '-tesco_week').distinct()
                last_week = week_ordered[1]
                last_week = last_week['tesco_week']
                if (week_flag == 1):
                    week_logic = week_ordered[:1]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append((week_logic[i]['tesco_week']))

                elif (week_flag == 2):
                    week_logic = week_ordered[:4]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))  # ###print("Inside elif 1")

                elif (week_flag == 3):
                    week_logic = week_ordered[:13]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                elif (week_flag == 4):

                    week_logic = week_ordered[:26]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                elif (week_flag == 5):

                    current_week = int(cw_week)
                    for_x = int(str(current_week)[-2:])
                    week_logic = week_ordered[:for_x]
                    week_var = []
                    for i in range(len(week_logic)):
                        week_var.append(str(week_logic[i]['tesco_week']))

                week = {"last_week": last_week, "week_var": week_var}
                return week

            week = week_selection(int(cw_week[0]), int(week_flag[0]))
            # print("week_var-------")
            # print(week['week_var'])
            # print(type(week['week_var']))

            # Getting queryset with required columns and also create kwargs for filtering
            kwargs = {
                'tesco_week__in': week['week_var'],
                'product_id__in': products_bc,
                'store_type__in': store_type_nego
            }

            # print(kwargs)
            chart_bubble = supplier_view.objects.filter(**kwargs).values('tesco_week', 'product_id', 'parent_supplier',
                                                                         'supplier', 'sales_ty',
                                                                         'volume_ty', 'cgm_ty', 'rate_of_sale',
                                                                         'store_type')
            # print(chart_bubble)

            # Converting to data frame
            # print("chart bubble frame test------")
            chart_bubble_frame = read_frame(chart_bubble)
            # print(chart_bubble_frame[:10])
            product_description_frame = read_frame(product_description)
            # print(product_description_frame)

            # Kwargs for cps and pps
            kwargs_pps_cps = {
                'tesco_week__in': week['week_var'],
                'store_type__in': store_type_nego,
                'product_id__in': products_bc
            }

            # Creating queryset for pps and cps calculation
            print("queryset pps..... store type start")
            # queryset_pps_storecount = chart_bubble.filter(**kwargs_pps_cps).values('tesco_week', 'product_id').annotate(
            #     store_sum=Sum('store_count', output_field=FloatField()))
            # print("queryset pps store count end", queryset_pps_storecount)
            queryset_pps = chart_bubble.filter(**kwargs_pps_cps).values('tesco_week', 'product_id').annotate(profit_ty=Sum('cgm_ty', output_field=FloatField()), store_sum=Sum('store_count', output_field=FloatField()))
            print("queryset pps.......",queryset_pps)
            queryset_cps = chart_bubble.filter(**kwargs_pps_cps).values('product_id', 'cps_score')

            # Converting to data frame
            dataframe_pps = read_frame(queryset_pps)
            dataframe_cps = read_frame(queryset_cps)

            dataframe_pps = pd.merge(dataframe_pps, dataframe_cps, how='left',
                                         on=['product_id'])
            dataframe_pps['cps_score'] = dataframe_pps['cps_score'].astype('float')
            dataframe_pps = dataframe_pps.drop(dataframe_pps[dataframe_pps.cps_score == 0].index)
            print("dataframe pps--------------------")
            print(dataframe_pps)

            # print("CPS and PPS quartiling")
            # print(dataframe_cps[:10])
            dataframe_cps['cps_score'] = dataframe_cps['cps_score'].astype('float')
            dataframe_cps = dataframe_cps.drop(dataframe_cps[dataframe_cps.cps_score == 0].index)
            dataframe_pps['pps'] = dataframe_pps['profit_ty']/dataframe_pps['store_sum']
            # dataframe_cps['cps_percentile'] = dataframe_cps.groupby(['product_id'])['cps_score'].rank(pct=True) * 100
            dataframe_cps['cps_percentile'] = dataframe_cps['cps_score'].rank(axis=0, method='min', pct=True) * 100
            print("data frame pps..........")
            print(dataframe_pps)
            dataframe_pps['pps'] = dataframe_pps['pps'].astype('float')
            # dataframe_pps['pps_percentile'] = dataframe_pps.groupby(['product_id'])['pps'].rank(pct=True) * 100
            dataframe_pps['pps_percentile'] = dataframe_pps['pps'].rank(axis=0, method='min', pct=True) * 100

            print("rank function done")
            # dataframe_cps['cps_score'] = dataframe_cps['cps_score'].astype('float')
            # dataframe_cps['cps_percentile'] = pd.qcut(dataframe_cps['cps_score'].rank(method='first'), 4, labels=[1,2,3,4])

            # dataframe_pps['pps'] = dataframe_pps['pps'].astype('float')
            # dataframe_pps['pps_percentile'] = pd.qcut(dataframe_pps['pps'].rank(method='first'), 4, labels=[1,2,3,4])
            print("error......................")
            # Merging dataframe with pps and cps to base
            # print(chart_bubble_frame)
            print("Chart bubble frame...",chart_bubble_frame)
            print("dataframe pps.....", dataframe_pps)
            chart_final_frame = pd.merge(chart_bubble_frame, dataframe_pps, how='left',
                                         on=['tesco_week', 'product_id'])
            print("Chart final frame......",chart_final_frame)
            chart_final_frame = pd.merge(chart_final_frame, dataframe_cps, how='left', on=['product_id', 'cps_score'])
            # print(chart_final_frame[:10])

            print("chart final frame error")
            print("chart final frame error 2")
            # print(chart_final_frame.dtypes)
            # print(chart_final_frame)
            chart_final_frame["performance_quartile"] = ''
            # Creating columns cps_label and pps_label

            chart_final_frame.loc[(chart_final_frame["cps_percentile"] < 25) & (
            chart_final_frame["pps_percentile"] >= 50), 'performance_quartile'] = "Low CPS/High Profit"
            chart_final_frame.loc[(chart_final_frame["cps_percentile"] <= 25) & (
            chart_final_frame["pps_percentile"] <= 25), 'performance_quartile'] = "Low CPS/Low Profit"
            chart_final_frame.loc[
                (chart_final_frame["cps_percentile"] >= 50) & (chart_final_frame["cps_percentile"] <= 100) & (
                chart_final_frame["pps_percentile"] >= 50) & (
                chart_final_frame["pps_percentile"] <= 100), 'performance_quartile'] = "High CPS/High Profit"
            chart_final_frame.loc[
                (chart_final_frame["cps_percentile"] >= 75) & (chart_final_frame["cps_percentile"] <= 100) & (
                chart_final_frame["pps_percentile"] <= 50), 'performance_quartile'] = "High CPS/Low Profit"
            chart_final_frame.loc[(chart_final_frame["performance_quartile"] != "Low CPS/High Profit") & (
            chart_final_frame["performance_quartile"] != "Low CPS/Low Profit") & (
                                  chart_final_frame["performance_quartile"] != "High CPS/High Profit") & (
                                  chart_final_frame[
                                      "performance_quartile"] != "High CPS/Low Profit"), 'performance_quartile'] = "Med CPS/Med Profit"
            print("chart final frame error 3")
            # print(chart_final_frame[:10])

            # chart_final_frame['performance_quartile'] = chart_final_frame['cps_label'] +'/'+ chart_final_frame['pps_label']
            # Getting column for product description
            chart_final_frame = pd.merge(chart_final_frame, product_description_frame, how='left', on=['product_id'])
            print("before entering performance quartile", chart_final_frame)

            if performance_quartile != None:
                # chart_final_frame = chart_final_frame.loc[
                #     chart_final_frame.performance_quartile == performance_quartile]
                chart_final_frame = chart_final_frame[chart_final_frame['performance_quartile'].isin(performance_quartile)]
                # print("entered if...", chart_final_frame)
            # Keeping required columns

            bubble_data = chart_final_frame[['product_id', 'cps_score', 'product', 'rate_of_sale', 'store_type','cps_percentile','pps_percentile']]
            bubble_data = bubble_data.rename(index=str,
                                             columns={"product_id": "base_product_number", "cps_percentile": "cps", "pps_percentile": "pps", "product": "long_description",
                                                "rate_of_sale": "rate_of_sale"})
            bubble_data['rate_of_sale'] = bubble_data['rate_of_sale'].astype(float)
            bubble_data['cps'] = bubble_data['cps'].astype(float)
            bubble_data['pps'] = bubble_data['pps'].astype(float)
            print("bubble data",bubble_data,"bubble data type", type(bubble_data))
            bubble_data = bubble_data[np.isfinite(bubble_data['pps'])]
            bubble_data = bubble_data[np.isfinite(bubble_data['cps'])]
            bubble_data = bubble_data.loc[(bubble_data["pps"] > 0)]

            try:
                bubble_data = bubble_data.to_dict(orient='records')

            except:
                bubble_data = 0
            ##print('=========')
            ##print("=============")
            # ##print(columns)
            data = {
                # 'columns':columns,
                'bubble_data': bubble_data
            }
            logging.info(bubble_data)

            return bubble_data

        data = table_bubble_clasfc()
        return JsonResponse(data, safe=False)

class supplier_view_top_bottom(APIView):
	def get(self, request, *args):

		# print("args recieved------------ views_supplier xyz")
		args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
		print(args)
		#### for week tab
		week_flag = args.pop('week_flag__in', [1])
		week_flag = int(week_flag[0])
		# print("week flag", week_flag, type(week_flag))

		#### for current week value
		tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
		max_week = [tesco_week_int['cw_max']]
		cw_week = args.pop('tesco_week__in', max_week)
		cw_week = int(cw_week[0])

		#### for kpi type tab
		kpi_type = args.pop('kpi_type__in', ['Value'])
		kpi_type = kpi_type[0]

		##### parent supplier
		parent = args.pop('parent_supplier__in', None)

		#### supplier
		supplier = args.pop('supplier__in', None)

		top_bottom_kpi = args.pop('top_bottom_kpi__in', None)
		print("args after pop 123")
		# print(args)

		user_id = args.pop('user_id__in', None)
		designation = args.pop('designation__in', None)
		session_id = args.pop('session_id__in', None)
		user_name = args.pop('user_name__in', None)
		buying_controller_header = args.pop('buying_controller_header__in', None)
		buyer_header = args.pop('buyer_header__in', None)

		if not args:
			if ((buyer_header is None) or (buyer_header == '')):
				kwargs_header = {
					'buying_controller__in': buying_controller_header
				}
			else:
				kwargs_header = {
					'buying_controller__in': buying_controller_header,
					'buyer__in': buyer_header
				}
			products = sales_heirarchy.objects.filter(**kwargs_header).values(
				'product_id').distinct()
			product_description = read_frame(sales_heirarchy.objects.filter(**kwargs_header).values(
				'product_id','product').distinct())
			# products = sales_heirarchy.objects.filter( buying_controller = "Meat Fish And Veg").values('product_id').distinct()
			# tesco_week_int = supplier_view.objects.aggregate(cw_max=Max('tesco_week'))
			# cw_week = tesco_week_int['cw_max']

		else:
			products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
			product_description = read_frame(sales_heirarchy.objects.filter(**args).values('product_id','product').distinct())

		def top_parent_supplier(sum_kpi, sum_kpi_ly):

			def week_selection(cw_week, week_flag):
				week_ordered = supplier_view.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
					'-tesco_week').distinct()
				last_week = week_ordered[1]
				last_week = last_week['tesco_week']
				if (week_flag == 1):
					week_logic = week_ordered[:1]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 2):
					week_logic = week_ordered[:4]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))  # ###print("Inside elif 1")

				elif (week_flag == 3):
					week_logic = week_ordered[:13]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 4):

					week_logic = week_ordered[:26]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 5):

					current_week = int(cw_week)
					for_x = int(str(current_week)[-2:])
					week_logic = week_ordered[:for_x]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				week = {"last_week": last_week, "week_var": week_var}
				return week

			#week_var = week_selection(cw_week, week_flag)
			week = week_selection(cw_week, week_flag)

			# if not args:
			kwargs = {
				'tesco_week__in': week["week_var"],
				'product_id__in': products
			}

			part_by_val_denom = supplier_view.objects.filter(**kwargs).aggregate(
				val=Sum(sum_kpi, output_field=FloatField()))
			print("part by val denom")
			# print(part_by_val_denom)

			part_by_val_denom = part_by_val_denom['val']

			value_contri_denom = supplier_view.objects.filter(**kwargs).aggregate(
				val=Sum(sum_kpi_ly, output_field=FloatField()))
			print("value contri denom")
			# print(value_contri_denom)
			# print(value_contri_denom)
			value_contri_denom = value_contri_denom['val']
			print("________ value contri before if")
			if (part_by_val_denom == 0):
				part_by_val_list = 0
				print("entered else if ----------------------")
			else:
				#
				part_by_val_list = supplier_view.objects.filter(**kwargs).exclude(parent_supplier='-').values(
					"parent_supplier","supplier").annotate(tot_ty=Sum(sum_kpi, output_field=FloatField()),
												tot_ly=Sum(sum_kpi_ly, output_field=FloatField())).annotate(
					part_by_val=F('tot_ty') * 100 / part_by_val_denom)

			try:
				part_by_val = list(part_by_val_list)
				final_dataframe = pd.DataFrame(part_by_val)
				print("entered if")
			# print("part by value top", part_by_val_top)
			# print("part by val bot", part_by_val_bot)
			except:
				part_by_val = 0
			try:

				final_dataframe['value_growth'] = (final_dataframe['tot_ty'] - final_dataframe['tot_ly']) * 100 / final_dataframe['tot_ly']
				# value_growth_top = value_growth.to_dict(orient="records")
				# print("value growth top:", value_growth_top)
			except:
				print("value growth exception")
				value_growth = 0

			print("value final dataframe",final_dataframe)
			if (value_contri_denom == 0):
				final_dataframe['value_contri'] = 0
			else:
				# print("Contribution to growth denom----------------------")
				# print(value_contri_denom)
				final_dataframe['value_contri'] = (final_dataframe['tot_ty'] - final_dataframe['tot_ly']) * 100 / value_contri_denom

				###Please confirm if this is needed or not
				final_dataframe = final_dataframe[np.isfinite(final_dataframe['value_growth'])]

				# final_dataframe.sort(['part_by_val'], ascending=[1])
				# final_dataframe.sort(['part_by_val'], ascending=[1])
				final_dataframe = final_dataframe.sort_values(by=['part_by_val'], ascending=False)
				print("srt check:",final_dataframe)

				# final_dataframe = pd.merge(final_dataframe,product_description, how='inner',on=['supplier'])
				# print("value contri top : ", value_contri_top)



			final_dataframe = final_dataframe.to_dict(orient="records")
			# print("---- value contri top -----")
			# print(value_contri_top)
			# except:
			# value_contri_top = 0
			# value_contri_bot = 0

			# if top_bottom_kpi!=None:
			#     if top_bottom_kpi[0] == "part_by_val":
			#         print("entered 1")
			#         top = list(part_by_val)
			#     elif top_bottom_kpi[0] == "value_growth":
			#         print("entered 2")
			#         top = value_growth
			#     elif top_bottom_kpi[0] == "value_contribution":
			#         print("entered 3")
			#         top = value_contri
			# else:
			#     top = part_by_val_top
			#     bottom = part_by_val_bot
			data = {
				'dataframe': final_dataframe
			}
			logging.info(data)
			# data = 1
			return data

		if kpi_type == 'Value':
			kpi_1 = 'sales_ty'
			kpi_2 = 'sales_ly'
		elif kpi_type == 'Volume':
			kpi_1 = 'volume_ty'
			kpi_2 = 'volume_ly'
		elif kpi_type == 'COGS':
			kpi_1 = 'cogs_ty'
			kpi_2 = 'cogs_ly'
		elif kpi_type == 'CGM':
			kpi_1 = 'cgm_ty'
			kpi_2 = 'cgm_ly'
		elif kpi_type == 'Supp_Fund':
			kpi_1 = 'fundxvat_ty'
			kpi_2 = 'fundxvat_ly'
		else:
			kpi_1 = 'sales_ty'
			kpi_2 = 'sales_ly'

		data = top_parent_supplier(kpi_1, kpi_2)
		return JsonResponse(data, safe=False)

class supplier_view_table_bubble(APIView):
	def get(self, request, *args):

		print("args recieved ------ view_supplier")
		args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
		# print(args)

		##FOR STORE TYPE
		print("store type test table")
		store_type = args.pop("store_type__in", None)

		##store type nego
		store_type_nego = args.pop("store_type_nego__in", ["Main Estate"])
		# print(store_type)
		print("store type tested table")

		#### for week tab

		week_flag = args.pop('week_flag__in', [1])

		#### for current week value
		tesco_week_int = latest_week.objects.aggregate(cw_max=Max('week_ty'))
		max_week = [tesco_week_int['cw_max']]
		cw_week = args.pop('tesco_week__in', max_week)
		# print(type(cw_week))

		#### for kpi type tab
		kpi_type = args.pop('kpi_type__in', None)

		##### parent supplier
		# parent = args.pop('parent_supplier', None)

		#### supplier
		# supplier = args.pop('supplier', None)

		###percentile quartile
		performance_quartile = args.pop('performance_quartile__in', None)

		###search feature
		s = args.pop('search', [''])
		search = s[0]
		print("printing search")
		# print(search)

		###Pagination
		page_no = int(args.pop('page', 1))
		print("args after pop")
		# print(args)

		start_row = (page_no - 1) * 5
		end_row = start_row + 5
		###### convert "and" to "and"
		# products=sales_heirarchy.objects.filter(**args).values('product_id').distinct()


		#Cookies pop
		user_id = args.pop('user_id__in', None)
		designation = args.pop('designation__in', None)
		session_id = args.pop('session_id__in', None)
		user_name = args.pop('user_name__in', None)
		buying_controller_header = args.pop('buying_controller_header__in', None)
		buyer_header = args.pop('buyer_header__in', None)

		if not args:
			print("entered if")
			if ((buyer_header is None) or (buyer_header == '')):
				kwargs_header = {
					'buying_controller__in': buying_controller_header
				}
			else:
				kwargs_header = {
					'buying_controller__in': buying_controller_header,
					'buyer__in': buyer_header
				}
			products = sales_heirarchy.objects.filter(**kwargs_header).values(
				'product_id').distinct()
			# print(products)
			tesco_week_int = supplier_view.objects.aggregate(cw_max=Max('tesco_week'))
			# cw_week = tesco_week_int['cw_max']
			product_description = sales_heirarchy.objects.filter(**kwargs_header).values('product_id',
																								   'product').distinct()

		else:
			print("emtered else")
			products = sales_heirarchy.objects.filter(**args).values('product_id').distinct()
			# print(products)
			product_description = sales_heirarchy.objects.filter(**args).values('product_id', 'product').distinct()

		def table_bubble_clasfc():

			def week_selection(cw_week, week_flag):
				week_ordered = supplier_view.objects.filter(tesco_week__lte=cw_week).values('tesco_week').order_by(
					'-tesco_week').distinct()
				last_week = week_ordered[1]
				last_week = last_week['tesco_week']
				if (week_flag == 1):
					week_logic = week_ordered[:1]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 2):
					week_logic = week_ordered[:4]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))  # ###print("Inside elif 1")

				elif (week_flag == 3):
					week_logic = week_ordered[:13]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 4):

					week_logic = week_ordered[:26]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				elif (week_flag == 5):

					current_week = int(cw_week)
					for_x = int(str(current_week)[-2:])
					week_logic = week_ordered[:for_x]
					week_var = []
					for i in range(len(week_logic)):
						week_var.append(str(week_logic[i]['tesco_week']))

				week = {"last_week": last_week, "week_var": week_var}
				return week

			week = week_selection(int(cw_week[0]), int(week_flag[0]))
			# print("week_var-------")
			# print(week['week_var'])
			# print(type(week['week_var']))

			# Getting queryset with required columns and also create kwargs for filtering
			kwargs = {
				'tesco_week__in': week['week_var'],
				'product_id__in': products,
				'store_type__in': store_type_nego
			}
			# print(kwargs)
			chart_bubble = supplier_view.objects.filter(**kwargs).values('tesco_week', 'product_id', 'parent_supplier', 'sales_ty', 'volume_ty',
																		 'cgm_ty', 'rate_of_sale', 'store_type')
			# print(chart_bubble)

			# Converting to data frame
			print("chart bubble frame test------")
			chart_bubble_frame = read_frame(chart_bubble)
			product_description_frame = read_frame(product_description)
			# print(product_description_frame)

			# Kwargs for cps and pps
			kwargs_pps_cps = {
				'tesco_week__in': week['week_var'],
				'store_type__in': store_type_nego,
				'product_id__in': products
			}

			# Creating queryset for pps and cps calculation
			queryset_pps = chart_bubble.filter(**kwargs_pps_cps).values('tesco_week', 'product_id').annotate(
				profit_ty=Sum('cgm_ty', output_field=FloatField()),
				store_sum=Sum('store_count', output_field=FloatField()))
			queryset_cps = chart_bubble.filter(**kwargs_pps_cps).values('product_id', 'cps_score')

			# Converting to data frame
			dataframe_pps = read_frame(queryset_pps)
			dataframe_cps = read_frame(queryset_cps)
			print("dataframe cps--------------------")
			# print(dataframe_pps)

			print("CPS and PPS quartiling")
			# print(dataframe_cps[:10])
			dataframe_pps = pd.merge(dataframe_pps, dataframe_cps, how='left',
									 on=['product_id'])
			dataframe_pps['cps_score'] = dataframe_pps['cps_score'].astype('float')
			dataframe_pps = dataframe_pps.drop(dataframe_pps[dataframe_pps.cps_score == 0].index)
			print("dataframe pps--------------------")
			print(dataframe_pps)

			# print("CPS and PPS quartiling")
			# print(dataframe_cps[:10])
			dataframe_cps['cps_score'] = dataframe_cps['cps_score'].astype('float')
			dataframe_cps = dataframe_cps.drop(dataframe_cps[dataframe_cps.cps_score == 0].index)
			dataframe_pps['pps'] = dataframe_pps['profit_ty'] / dataframe_pps['store_sum']
			# dataframe_cps['cps_percentile'] = dataframe_cps.groupby(['product_id'])['cps_score'].rank(pct=True) * 100
			dataframe_cps['cps_percentile'] = dataframe_cps['cps_score'].rank(axis=0, method='min', pct=True) * 100
			print("data frame pps..........")
			print(dataframe_pps)
			dataframe_pps['pps'] = dataframe_pps['pps'].astype('float')
			# dataframe_pps['pps_percentile'] = dataframe_pps.groupby(['product_id'])['pps'].rank(pct=True) * 100
			dataframe_pps['pps_percentile'] = dataframe_pps['pps'].rank(axis=0, method='min', pct=True) * 100

			print("rank function done")
			# dataframe_cps['cps_score'] = dataframe_cps['cps_score'].astype('float')
			# dataframe_cps['cps_percentile'] = pd.qcut(dataframe_cps['cps_score'].rank(method='first'), 4, labels=[1,2,3,4])

			# dataframe_pps['pps'] = dataframe_pps['pps'].astype('float')
			# dataframe_pps['pps_percentile'] = pd.qcut(dataframe_pps['pps'].rank(method='first'), 4, labels=[1,2,3,4])
			print("error......................")
			# Merging dataframe with pps and cps to base
			# print(chart_bubble_frame)
			print("Chart bubble frame...", chart_bubble_frame)
			print("dataframe pps.....", dataframe_pps)
			chart_final_frame = pd.merge(chart_bubble_frame, dataframe_pps, how='left',
										 on=['tesco_week', 'product_id'])
			print("Chart final frame......", chart_final_frame)
			chart_final_frame = pd.merge(chart_final_frame, dataframe_cps, how='left', on=['product_id', 'cps_score'])
			# print(chart_final_frame[:10])

			print("chart final frame error")
			print("chart final frame error 2")
			# print(chart_final_frame.dtypes)
			# print(chart_final_frame)
			chart_final_frame["performance_quartile"] = ''

			chart_final_frame.loc[(chart_final_frame["cps_percentile"] < 25) & (
			chart_final_frame["pps_percentile"] >= 50), 'performance_quartile'] = "Low CPS/High Profit"
			chart_final_frame.loc[(chart_final_frame["cps_percentile"] <= 25) & (
			chart_final_frame["pps_percentile"] <= 25), 'performance_quartile'] = "Low CPS/Low Profit"
			chart_final_frame.loc[
				(chart_final_frame["cps_percentile"] >= 50) & (chart_final_frame["cps_percentile"] <= 100) & (
				chart_final_frame["pps_percentile"] >= 50) & (
				chart_final_frame["pps_percentile"] <= 100), 'performance_quartile'] = "High CPS/High Profit"
			chart_final_frame.loc[
				(chart_final_frame["cps_percentile"] >= 75) & (chart_final_frame["cps_percentile"] <= 100) & (
				chart_final_frame["pps_percentile"] <= 50), 'performance_quartile'] = "High CPS/Low Profit"
			chart_final_frame.loc[(chart_final_frame["performance_quartile"] != "Low CPS/High Profit") & (
			chart_final_frame["performance_quartile"] != "Low CPS/Low Profit") & (
								  chart_final_frame["performance_quartile"] != "High CPS/High Profit") & (
								  chart_final_frame[
									  "performance_quartile"] != "High CPS/Low Profit"), 'performance_quartile'] = "Med CPS/Med Profit"
			# print("chart final frame error 31",chart_final_frame)

			# chart_final_frame['performance_quartile'] = chart_final_frame['cps_label'] +'/'+ chart_final_frame['pps_label']
			# Getting column for product description
			chart_final_frame = pd.merge(chart_final_frame, product_description_frame, how='left', on=['product_id'])

			if performance_quartile != None:
				chart_final_frame = chart_final_frame[chart_final_frame['performance_quartile'].isin(performance_quartile)]
			# Keeping required columns
			print('final frame.....', chart_final_frame)
			bubble_data = chart_final_frame[
				['product', 'parent_supplier', 'cps_score', 'pps', 'sales_ty', 'volume_ty', 'cgm_ty',
				 'rate_of_sale']]
			bubble_data = bubble_data.rename(index=str,
											 columns={"product": "base_product_number", "cps_score": "cps"})
			bubble_count = len(bubble_data)
			# print("bubble data befroe drop", len(bubble_data))
			bubble_data = bubble_data.dropna()
			# print("bubble data after drop", len(bubble_data))

			print("bubble count--------")
			# print(bubble_count)
			bubble_data = bubble_data
			bubble_data['rate_of_sale'] = bubble_data['rate_of_sale'].astype(float)
			bubble_data['cps'] = bubble_data['cps'].astype(float)
			bubble_data['pps'] = bubble_data['pps'].astype(float)
			bubble_data['sales_ty'] = bubble_data['sales_ty'].astype(float)
			bubble_data['volume_ty'] = bubble_data['volume_ty'].astype(float)
			bubble_data['cgm_ty'] = bubble_data['cgm_ty'].astype(float)
			bubble_data = bubble_data.loc[(bubble_data["pps"] > 0)]
			table_data = bubble_data.to_dict(orient='records')

			num_pages = math.ceil((bubble_count / 5))
			start_index = (page_no - 1) * 5 + 1
			count = bubble_count
			end_index = page_no * 5

			data = {
				# 'columns':columns,
				'table_data': table_data,
				'page_no': page_no,
				'num_pages': num_pages,
				'start_index': start_index,
				'count': count,
				'end_index': end_index
			}
			logging.info(data)

			return data

		data = table_bubble_clasfc()
		return JsonResponse(data, safe=False)

def col_distinct(kwargs, col_name, kwargs_header):
	queryset = sales_heirarchy.objects.filter(**kwargs_header).values(col_name).order_by(col_name).distinct()
	base_product_number_list = [k.get(col_name) for k in queryset]
	return base_product_number_list

class filters_supplier(APIView):
	def get(self, request):
		# print(request.GET)
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
		print("object", obj)
		sent_req = obj
		default_check = obj2
		user_id = default_check.pop('user_id')
		designation = default_check.pop('designation')
		user_name = default_check.pop('user_name')

		print("defauly check 1", default_check, "sent_rer 1", sent_req)
		user_id = sent_req.pop('user_id',None)
		designation = sent_req.pop('designation',None)
		user_name = sent_req.pop('user_name',None)
		buying_controller_header = sent_req.pop('buying_controller_header',None)
		buyer_header = sent_req.pop('buyer_header',None)
		# store_type = obj.pop('store_type_header')

		if ((buyer_header is None) or (buyer_header == '')):
			kwargs_header = {
				'buying_controller__in': buying_controller_header
			}
		else:
			kwargs_header = {
				'buying_controller__in': buying_controller_header,
				'buyer__in': buyer_header
			}
		print("defauly check", default_check, "sent_rer", sent_req)
		return make_json_supplier(sent_req, kwargs_header, default_check)

def make_json_supplier(sent_req, kwargs_header, default_check):
	# find lowest element of cols
	cols = ['store_type', 'commercial_name', 'category_name', 'buying_controller', 'buyer', 'junior_buyer',
			'product_subgroup', 'brand_indicator', 'parent_supplier', 'supplier']

	lowest = 0
	second_lowest = 0

	element_list = []
	print("send request", sent_req)

	print("sent re1",type(sent_req))
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
			# print("selected", type(sent_req.get(col_name)), title,sent_req.get(col_name) )
			y.append({'title': title,
					  'resource': {'params': col_name + '=' + title,
								   'selected': selected},
					  'highlighted': selected if selected else highlight_check(title)})

		final_list.append({'items': y,
						   'input_type': 'Checkbox',
						   'title': col_name,
						   'buying_controller': 'Beers, Wines and Spirits',
						   'id': col_name,
						   'required': True if col_name == 'category_name' or col_name == 'parent_supplier' or col_name == 'supplier' else False
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
	return Response({'cols': cols, 'checkbox_list': final_list2})


#new filter logic
# class supplier_filters_new(APIView):
# 	def get(self, request, format=None):
# 		# input from header
# 		args = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
#
# 		designation = args.pop('designation__in', None)
# 		user_id = args.pop('user_id__in', None)
# 		session_id = args.pop('session_id__in', None)
# 		user_name = args.pop('user_name__in', None)
# 		buying_controller_header = args.pop('buying_controller_header__in', None)
# 		buyer_header = args.pop('buyer_header__in', None)
# 		#col_index = args.pop(col_index__in,0)
# 		# header over
# 		cols = ['commercial_name', 'category_name', 'buying_controller', 'buyer', 'junior_buyer',
# 				'product_subgroup','store_type','brand_indicator', 'parent_supplier', 'supplier']
#
# 		if 'admin' in designation:
# 			kwargs_header = {}
# 		else:
# 			if buyer_header is None:
# 				kwargs_header = {
# 					'buying_controller__in': buying_controller_header
# 				}
# 			else:
# 				kwargs_header = {
# 					'buying_controller__in': buying_controller_header,
# 					'buyer__in': buyer_header
# 				}
# 		# input from args
# 		default = args.pop('default__in', None)
# 		final = []
# 		pre_selected = []
# 		mid_final = []
# 		pre_selected_final = []
# 		if default is None:
# 			if not args:
#
# 				df = read_frame(sales_heirarchy.objects.filter(**kwargs_header).filter(**args))
# 				heirarchy = read_frame(
# 					sales_heirarchy.objects.filter(**kwargs_header).values('store_type', 'commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
# 																		'product_subgroup', 'brand_indicator', 'parent_supplier', 'supplier'))
#
#
# 				for i in heirarchy.columns:
# 					#print(i)
# 					data = {i: df[i].unique()}
# 					#print(data)
# 					col = pd.DataFrame(data)
# 					if i == ('buyer') or i == ('buying_controller') or i == ('commercial_name') or i == ('category_name'):
# 						if len(col) == 1:
# 							#print("inside if loop")
# 							col['selected'] = True  ### One change here for default selection of bc logging in
# 							col['highlighted'] = False
# 						else:
# 							col['selected'] = False
# 							col['highlighted'] = False
#
# 					else:
# 						col['selected'] = False
# 						col['highlighted'] = False
#
# 					col_df = heirarchy[[i]].drop_duplicates()
# 					#print(col_df)
# 					col_df = pd.merge(col_df, col, how='left')
# 					col_df['selected'] = col_df['selected'].fillna(False)
# 					col_df['highlighted'] = col_df['highlighted'].fillna(False)
# 					col_df = col_df.rename(columns={i: 'title'})
# 					#print("____")
# 					#print(col_df)
#
# 					col_df = col_df.sort_values(by='title', ascending=True)
# 					col_df['highlighted'] = ~col_df['highlighted']
# 					col_df_sel = col_df[['selected']]
# 					col_df['resource'] = col_df_sel.to_dict(orient='records')
# 					del col_df['selected']
# 					col_df_final = col_df.to_json(orient='records')
# 					col_df_final = json.loads(col_df_final)
#
# 					#print("---------")
# 					#print(col_df_final)
#
# 					a = {}
# 					a['id'] = i
# 					a['title'] = i
# 					if i == ('category_name') or i ==('parent_supplier') or i ==('supplier'):
# 						a['required'] = True
# 					else:
# 						a['required'] = False
# 					if 'admin' in designation:
# 						a['pre_selected'] = False
# 					else:
# 						if 'buying_controller' in designation:
# 							print("BC in designation")
# 							if  i == ('buying_controller') or i == ('commercial_name') or i == ('category_name'):
# 								a['pre_selected'] = True
# 							else:
# 								print("else part")
# 								a['pre_selected'] = False
# 						else:
# 							if i == ('buyer') or i == ('buying_controller') or i == ('commercial_name') or i == (
# 							'category_name'):
# 								a['pre_selected'] = True
# 							else:
# 								a['pre_selected'] = False
# 					a['items'] = col_df_final
# 					a['category_director'] = "Beers, Wines and Spirits"
#
# 					mid_final.append(a)
#
# 			else:
#
# 				if 'admin' in designation:
# 					heirarchy = read_frame(
# 						sales_heirarchy.objects.values('commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
# 																		'product_subgroup', 'store_type','brand_indicator', 'parent_supplier', 'supplier'))
# 				else:
# 					heirarchy = read_frame(sales_heirarchy.objects.filter(**kwargs_header).values( 'commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
# 																		'product_subgroup','store_type', 'brand_indicator', 'parent_supplier', 'supplier'))
#
#
# 				args_list = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
# 				store_list = args_list.pop('store_type__in', None)
# 				#print(store_list)
# 				if store_list is None:
# 					store_list = None
#
# 				commercial_name_list = args_list.pop('commercial_name__in', None)
# 				#if commercial_name_list is None:
# 				#     commercial_name_list = str(commercial_name_list[0])
#
# 				category_name_list = args_list.pop('category_name__in', None)
# 				# if category_name_list is None:
# 				#     category_name_list = str(category_name_list[0])
#
# 				if 'admin' in designation:
# 					bc_list = args_list.pop('buying_controller__in', None)
# 					buyer_list = args_list.pop('buyer__in', None)
# 				else:
# 					if 'buying_controller' in designation:
# 						bc_list = args_list.pop('buying_controller_header__in', None)
# 						buyer_list = args_list.pop('buyer__in', None)
# 					else:
# 						bc_list = args_list.pop('buying_controller_header__in', None)
# 						buyer_list = args_list.pop('buyer_header__in', None)
#
# 				bc_list_1  = args_list.pop('buying_controller__in', None)
# 				buyer_list_1 = args_list.pop('buyer__in', None)
# 				#
#
# 				if bc_list_1 is None:
# 					bc_list_1 = None
# 				if buyer_list_1 is None:
# 					buyer_list_1 = None
# 				jr_buyer_list = args_list.pop('junior_buyer__in', None)
# 				if jr_buyer_list is None:
# 					 jr_buyer_list = None
#
# 				psg_list = args_list.pop('product_subgroup__in', None)
# 				if psg_list is None:
# 					 psg_list = None
#
# 				brand_indicator_list = args_list.pop('brand_indicator__in', None)
# 				if brand_indicator_list is None:
# 					 brand_indicator_list = None
#
# 				parent_supplier_list = args_list.pop('parent_supplier__in', None)
# 				if parent_supplier_list is None:
# 					 parent_supplier_list = None
#
# 				supplier_list = args_list.pop('supplier__in', None)
# 				if supplier_list is None:
# 					 supplier_list = None
#
# 				# if 'admin' in designation:
# 				com_list = [commercial_name_list,category_name_list,bc_list,buyer_list,jr_buyer_list,psg_list,store_list,
# 							brand_indicator_list,parent_supplier_list,supplier_list]
# 				# else:
# 				# 	if 'buying_controller' in designation:
# 				# 		com_list = [commercial_name_list, category_name_list, bc_list, buyer_list_1, jr_buyer_list,
# 				# 					psg_list, store_list,
# 				# 					brand_indicator_list, parent_supplier_list, supplier_list]
# 				# 	else:
# 				# 		com_list = [commercial_name_list, category_name_list, bc_list, buyer_list, jr_buyer_list,
# 				# 					psg_list, store_list,
# 				# 					brand_indicator_list, parent_supplier_list, supplier_list]
# 				# #print(com_list)
# 				if 'buying_controller' in designation:
# 					com_list_1 = [commercial_name_list, category_name_list, bc_list_1, buyer_list, jr_buyer_list, psg_list, store_list,
# 								brand_indicator_list, parent_supplier_list, supplier_list]
# 				else:
# 					com_list_1 = [commercial_name_list, category_name_list, bc_list_1, buyer_list_1, jr_buyer_list,
# 								  psg_list, store_list,
# 								  brand_indicator_list, parent_supplier_list, supplier_list]
# 				#print(com_list_1)
# 				args_list2 = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
#
# 				df = read_frame(sales_heirarchy.objects.filter(**args))
# 				#final = []
# 				j=0
# 				for i in heirarchy.columns:
# 					print("loop running for")
# 					print(i)
# 					col_name = i + '__in'
# 					col_list2 = args_list2.pop(col_name, None)
# 					#print("____")
# 					data = {i: df[i].unique()}
#
# 					col = pd.DataFrame(data)
# 					#print(data)
# 					col_df_heirarchy = heirarchy[[i]].drop_duplicates()
#
# 					# if 'admin' in designation:
# 					# 	if com_list_1[j - 1] is None:
# 					#
# 					# 		# print("if previous is none")
# 					# 		# print("inside com list next", com_list[j - 1], com_list)
# 					# 		for k in range(j):
# 					# 			# print("inside for loop")
# 					# 			col_name_pre = cols[k]
# 					# 			kwargs_preselect = {'store_type__in': store_list,
# 					# 								'commercial_name__in': commercial_name_list,
# 					# 								'category_name__in': category_name_list,
# 					# 								'buying_controller__in': bc_list,
# 					# 								'buyer__in': buyer_list,
# 					# 								'junior_buyer__in': jr_buyer_list,
# 					# 								'brand_indicator__in': brand_indicator_list,
# 					# 								'product_subgroup__in': psg_list,
# 					# 								'brand_name__in': brand_name_list,
# 					# 								'product__in': product_list
# 					# 								}
# 					# 			kwargs_preselect = dict(filter(lambda item: item[1] is not None, kwargs_preselect.items()))
# 					# 			heirarchy_check_1 = read_frame(
# 					# 				sales_heirarchy.objects.filter(**kwargs_preselect))
# 					# 			col_df_pre = heirarchy_check_1[[col_name_pre]].drop_duplicates()
# 					# 			col_df_pre['selected'] = True
# 					# 			col_df_pre['highlighted'] = False
# 					# 			col_df_pre = col_df_pre[[col_name_pre, 'selected', 'highlighted']]
# 					# 			col_df_pre = col_df_pre.rename(columns={col_name_pre: 'title'})
# 					# 			col_df_pre = col_df_pre.sort_values(by='title', ascending=True)
# 					# 			# print(col_df_pre)
# 					# 			col_df_pre = col_df_pre.sort_values(by=['selected', 'title'], ascending=[False, True])
# 					# 			col_df_pre['highlighted'] = ~col_df_pre['highlighted']
# 					# 			# print("after inverse")
# 					# 			# print(col_df_pre)
# 					# 			col_df_pre_sel = col_df_pre[['selected']]
# 					# 			col_df_pre['resource'] = col_df_pre_sel.to_dict(orient='records')
# 					# 			del col_df_pre['selected']
# 					# 			col_df_pre_final = col_df_pre.to_json(orient='records')
# 					# 			col_df_pre_final = json.loads(col_df_pre_final)
# 					# 			a = {}
# 					# 			a['id'] = col_name_pre
# 					# 			a['title'] = col_name_pre
# 					# 			if col_name_pre == ('buying_controller'):
# 					# 				a['required'] = True
# 					# 			else:
# 					# 				a['required'] = False
# 					# 			a['items'] = col_df_pre_final
# 					# 			a['category_director'] = "Beers, Wines and Spirits"
# 					# 			a['pre_selected'] = True
# 					# 			pre_selected.append(a)
# 					# else:
#
# 					# if i == ('buying_controller') or i == ('commercial_name') or i == ('category_name') or i ==('junior_buyer') or i == ('buyer'):
# 					# 	print("printing buying controller...or buyer...")
# 					# 	col['selected'] = True
# 					# 	col['highlighted'] = False
# 					# 	print(col)
# 					# 	col_df = pd.merge(col_df_heirarchy, col, how='left')
# 					# 	col_df['selected'] = col_df['selected'].fillna(False)
# 					# 	col_df['highlighted'] = col_df['highlighted'].fillna(False)
# 					# 	col_df = col_df.rename(columns={i: 'title'})
# 					#
# 					# 	col_df = col_df.sort_values(by=['selected', 'title'], ascending=[False, True])
# 					# 	col_df['highlighted'] = ~col_df['highlighted']
# 					# 	print("after inverse")
# 					# 	print(col_df)
# 					# 	col_df_sel = col_df[['selected']]
# 					# 	col_df['resource'] = col_df_sel.to_dict(orient='records')
# 					# 	del col_df['selected']
# 					# 	col_df_final = col_df.to_json(orient='records')
# 					# 	col_df_final = json.loads(col_df_final)
# 					#
# 					# 	a = {}
# 					# 	a['id'] = i
# 					# 	a['title'] = i
# 					# 	if i == ('category_name') or i == ('parent_supplier') or i == ('supplier'):
# 					# 		a['required'] = True
# 					# 	else:
# 					# 		a['required'] = False
# 					# 	a['items'] = col_df_final
# 					# 	a['pre_selected'] = True
# 					# 	a['category_director'] = "Beers, Wines and Spirits"
# 					# 	final.append(a)
#
# 					# else:
# 					# 	#k = com_list.index(col_list2)
# 					if col_list2 is not None:
# 						print("else part")
# 						#print(col_df)
#
# 						if 'admin' in designation:
# 							kwargs_header = {
# 								# 'commercial_name__in':commercial_name_list,
# 								# 'category_name__in':category_name_list,
# 								# 'buying_controller__in':bc_list
# 							}
# 							# kwargs_header = dict(filter(lambda item: item[1] is not None, kwargs_header.items()))
#
# 							heirarchy_check = read_frame(
# 								sales_heirarchy.objects.filter(**kwargs_header).values('commercial_name',
# 																					   'category_name',
# 																					   'buying_controller', 'buyer',
# 																					   'junior_buyer',
# 																					   'product_subgroup',
# 																					   'store_type',
# 																					   'brand_indicator',
# 																					   'brand_name',
# 																					   'parent_supplier','supplier'))
# 						else:
# 							heirarchy_check = read_frame(
# 								sales_heirarchy.objects.filter(buying_controller__in=bc_list).values(
# 									'commercial_name', 'category_name', 'buying_controller', 'buyer',
# 									'junior_buyer',
# 									'product_subgroup', 'store_type', 'brand_indicator', 'brand_name',
# 									'parent_supplier','supplier'))
#
# 						# print("inside buyerrr..")
# 						col['selected'] = True
# 						col['highlighted'] = False
# 						kwargs = {'store_type__in': store_list,
# 								'commercial_name__in':commercial_name_list,
# 								'category_name__in':category_name_list,
# 								'buying_controller__in':bc_list,
# 								'buyer__in': buyer_list,
# 								'junior_buyer__in': jr_buyer_list,
# 								'brand_indicator__in': brand_indicator_list,
# 								'product_subgroup__in': psg_list,
# 								'parent_supplier__in': parent_supplier_list,
# 								'supplier__in': supplier_list
# 						}
# 						kwargs.pop(col_name)
# 						kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
#
# 						heirarchy_check = read_frame(
# 							sales_heirarchy.objects.filter(**kwargs))
# 						col_df_check = pd.merge(col_df_heirarchy,
# 												heirarchy_check[[i]].drop_duplicates(), how='right')
#
#
# 						col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
# 						#print("after mergeeee...")
# 						col_df_selected['selected'] = col_df_selected['selected'].fillna(False)
# 						col_df_selected['highlighted'] = col_df_selected['highlighted'].fillna(False)
# 						print("printing selected cols")
# 						print(col_df_selected)
#
# 						col_df = pd.merge(col_df_heirarchy, col_df_selected, how='left')
# 						col_df['selected'] = col_df['selected'].fillna(False)
# 						col_df['highlighted'] = col_df['highlighted'].fillna(True)
# 						#print(col_df)
# 						col_df = col_df.rename(columns={i: 'title'})
#
# 						print('printing com list and col list \n',com_list,col_list2)
# 						#j = com_list.index(col_list2)
#
# 						#j=next(a for a, val in zip(range(len(com_list) - 1, -1, -1), reversed(com_list)) if val == col_list2)
#
# 						j = max(a for a, val in enumerate(com_list)if val == col_list2)
# 						# if i == 'buyer' and  buyer_list == jr_buyer_list:
# 						# 	j = j-1
# 						# else:
# 						# 	j=j
# 						print("----printing j")
# 						print(j)
# 						if j < 9:
# 							#print("inside j<9 info")
# 							if com_list[j + 1] is not None:
# 								#print("inside com list next",com_list[j+1],com_list)
# 								col_df = col_df.rename(columns={'title': i})
# 								col_list_df = pd.DataFrame(col_list2, columns={i})
# 								#print(col_list_df)
# 								data = {i: col_list_df[i].unique()}
# 								#print(data)
# 								col = pd.DataFrame(data)
# 								col['selected'] = True
# 								col['highlighted'] = False
# 								# print(parent_supplier)
#
# 								col_df = pd.merge(col_df_heirarchy, col, how='left')
# 								col_df['selected'] = col_df['selected'].fillna(False)
# 								col_df['highlighted'] = col_df['highlighted'].fillna(True)
# 								col_df = col_df[[i, 'selected', 'highlighted']]
# 								col_df = col_df.rename(columns={i: 'title'})
# 								#print(col_df)
# 							#if 'admin' in designation:
# 							if com_list_1[j - 1] is None:
# 								pre_selected = []
# 								#print("if previous is none")
# 								#print("inside com list next", com_list[j - 1], com_list)
# 								for k in range(j):
# 									print("inside for loop")
# 									col_name_pre = cols[k]
# 									print(col_name_pre)
# 									if col_name_pre == 'product_subgroup':
# 										break
# 									else:
# 										kwargs_preselect = {'store_type__in': store_list,
# 															'commercial_name__in': commercial_name_list,
# 															'category_name__in': category_name_list,
# 															'buying_controller__in': bc_list,
# 															'buyer__in': buyer_list,
# 															'junior_buyer__in': jr_buyer_list,
# 															'brand_indicator__in': brand_indicator_list,
# 															'product_subgroup__in': psg_list,
# 															'parent_supplier__in': parent_supplier_list,
# 															'supplier__in': supplier_list
# 															}
# 										kwargs_preselect = dict(filter(lambda item: item[1] is not None, kwargs_preselect.items()))
# 										heirarchy_check_1 = read_frame(
# 											sales_heirarchy.objects.filter(**kwargs_preselect))
# 										col_df_pre = heirarchy_check_1[[col_name_pre]].drop_duplicates()
# 										col_df_pre['selected'] = True
# 										col_df_pre['highlighted'] = False
# 										col_df_pre = col_df_pre[[col_name_pre, 'selected', 'highlighted']]
# 										col_df_pre = col_df_pre.rename(columns={col_name_pre: 'title'})
# 										col_df_pre = col_df_pre.sort_values(by='title', ascending=True)
# 										#print(col_df_pre)
# 										col_df_pre = col_df_pre.sort_values(by=['selected', 'title'], ascending=[False, True])
# 										col_df_pre['highlighted'] = ~col_df_pre['highlighted']
# 										#print("after inverse")
# 										#print(col_df_pre)
# 										col_df_pre_sel = col_df_pre[['selected']]
# 										col_df_pre['resource'] = col_df_pre_sel.to_dict(orient='records')
# 										del col_df_pre['selected']
# 										col_df_pre_final = col_df_pre.to_json(orient='records')
# 										col_df_pre_final = json.loads(col_df_pre_final)
# 										a = {}
# 										a['id'] = col_name_pre
# 										a['title'] = col_name_pre
# 										if col_name_pre == ('category_name') or col_name_pre == ('parent_supplier') or col_name_pre == ('supplier'):
# 											a['required'] = True
# 										else:
# 											a['required'] = False
# 										a['items'] = col_df_pre_final
# 										a['category_director'] = "Beers, Wines and Spirits"
# 										a['pre_selected'] = True
# 										pre_selected.append(a)
#
# 							#
#
# 						# col_df = col_df.sort_values(by=['selected', 'title'], ascending=[False, True])
# 						# col_df['highlighted'] = ~col_df['highlighted']
# 						# print("after inverse")
# 						# print(col_df)
# 						# col_df_sel = col_df[['selected']]
# 						# col_df['resource'] = col_df_sel.to_dict(orient='records')
# 						# del col_df['selected']
# 						# col_df_final = col_df.to_json(orient='records')
# 						# col_df_final = json.loads(col_df_final)
# 						#
# 						# a = {}
# 						# a['id'] = i
# 						# a['title'] = i
# 						# if i == ('category_name') or i == ('parent_supplier') or i == ('supplier'):
# 						# 	a['required'] = True
# 						# else:
# 						# 	a['required'] = False
# 						# a['items'] = col_df_final
# 						# a['pre_selected'] = False
# 						# a['category_director'] = "Beers, Wines and Spirits"
# 						# final.append(a)
# 					else:
#
# 						col['selected'] = False
# 						col['highlighted'] = False
# 						col_df = pd.merge(col_df_heirarchy, col, how='left')
# 						col_df['selected'] = col_df['selected'].fillna(False)
# 						col_df['highlighted'] = col_df['highlighted'].fillna(True)
# 						col_df = col_df.rename(columns={i: 'title'})
#
# 					col_df['name_supplier'] = col_df['title'].str.split('-').str[1]
# 					col_df = col_df.sort_values(by=['selected', 'name_supplier'], ascending=[False, True])
# 					del col_df['name_supplier']
#
# 					#col_df = col_df.sort_values(by=['selected', 'title'], ascending=[False, True])
# 					col_df['highlighted'] = ~col_df['highlighted']
# 					print("after inverse")
# 					print(col_df)
# 					col_df_sel = col_df[['selected']]
# 					col_df['resource'] = col_df_sel.to_dict(orient='records')
# 					del col_df['selected']
# 					col_df_final = col_df.to_json(orient='records')
# 					col_df_final = json.loads(col_df_final)
#
#
# 					a = {}
# 					a['id'] = i
# 					a['title'] = i
# 					if i == ('category_name') or i ==('parent_supplier') or i ==('supplier'):
# 						a['required'] = True
# 					else:
# 						a['required'] = False
# 					a['items'] = col_df_final
# 					a['pre_selected'] = False
# 					a['category_director'] = "Beers, Wines and Spirits"
# 					final.append(a)
# 					#print('printing final')
# 					#print(final)
#
# 					#print(pre_selected)
# 					title_names = []
# 					for k in range(len(pre_selected)):
# 						print('\n',pre_selected[k]['title'])
# 						print('\n',title_names)
# 						if pre_selected[k]['title'] not in title_names:
# 							title_names.append(pre_selected[k]['title'])
#
#
#
# 					#title_names = list(set(title_names))
# 					mid_final = pre_selected + [x for x in final if x['title'] not in title_names]
#
# 					#print(i)
# 					# if i == 'store_type':
# 					# 	 break
#
#
# 		return JsonResponse({'cols': cols,'checkbox_list': mid_final}, safe=False)
#

class supplier_filters_new(APIView):
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
				'product_subgroup','store_type','brand_indicator', 'parent_supplier', 'supplier']
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
					sales_heirarchy.objects.filter(**kwargs_header).values('store_type', 'commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
																		'product_subgroup', 'brand_indicator', 'parent_supplier', 'supplier'))
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
					col_df['name_supplier'] = col_df['title'].str.split('-').str[1]
					col_df = col_df.sort_values(by=['selected', 'name_supplier'],
												ascending=[False, True])
					del col_df['name_supplier']
					#col_df = col_df.sort_values(by=['selected','title'], ascending=[False,True])
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
						sales_heirarchy.objects.values('commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
																		'product_subgroup', 'store_type','brand_indicator', 'parent_supplier', 'supplier'))
				else:
					heirarchy = read_frame(sales_heirarchy.objects.filter(**kwargs_header).values( 'commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
																		'product_subgroup','store_type', 'brand_indicator', 'parent_supplier', 'supplier'))
				args_list = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
				store_list = args_list.pop('store_type__in', None)
				#print(store_list)
				if store_list is None:
					store_list = None
				commercial_name_list = args_list.pop('commercial_name__in', None)
				#if commercial_name_list is None:
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
				parent_supplier_list = args_list.pop('parent_supplier__in', None)
				if parent_supplier_list is None:
					 parent_supplier_list = None
				supplier_list = args_list.pop('supplier__in', None)
				if supplier_list is None:
					 supplier_list = None
				com_list = [commercial_name_list,category_name_list,bc_list,buyer_list,jr_buyer_list,psg_list,store_list,
							brand_indicator_list,parent_supplier_list,supplier_list]
				#print(com_list)
				args_list2 = {reqobj + '__in': request.GET.getlist(reqobj) for reqobj in request.GET.keys()}
				#com_list = [bc_list, buyer_list, jr_buyer_list, psg_list, brand_indicator_list, parent_supplier_list,
				#            supplier_list, ]
				df = read_frame(sales_heirarchy.objects.filter(**args))
				#final = []
				j=0
				for i in heirarchy.columns:
					#print("loop running for")
					#print(i)
					col_name = i + '__in'
					col_list2 = args_list2.pop(col_name, None)
					#print("____")
					data = {i: df[i].unique()}
					col = pd.DataFrame(data)
					#print(data)
					col_df_heirarchy = heirarchy[[i]].drop_duplicates()

					if 'admin' in designation:
						if col_list2 is not None:
							#print("else part")
							# print(col_df)
							heirarchy_check = read_frame(
								sales_heirarchy.objects.filter(buying_controller__in=bc_list).values(
									'commercial_name', 'category_name', 'buying_controller', 'buyer',
									'junior_buyer',
									'product_subgroup', 'store_type', 'brand_indicator', 'parent_supplier',
									'supplier'))
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
									  'product_subgroup__in': psg_list,
									  'parent_supplier__in': parent_supplier_list,
									  'supplier__in': supplier_list
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
							if j < 9:
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
						#print("in buying controller designation")
						if i == ('buying_controller'):
							#print("printing buying controller..")
							#print("inside if loop")
							col['selected'] = True  ### One change here for default selection of bc logging in
							col['highlighted'] = False

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
										'commercial_name', 'category_name', 'buying_controller', 'buyer',
										'junior_buyer',
										'product_subgroup', 'store_type', 'brand_indicator', 'parent_supplier',
										'supplier'))
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
										  'product_subgroup__in': psg_list,
										  'parent_supplier__in': parent_supplier_list,
										  'supplier__in': supplier_list
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
								if j < 9:
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

					elif 'buyer' in designation:
						if i == ('buying_controller') or i ==('buyer'):
							#print("printing buying controller..")
							#print("inside if loop")
							col['selected'] = True  ### One change here for default selection of bc logging in
							col['highlighted'] = False

							col_df = pd.merge(col_df_heirarchy, col, how='left')
							col_df['selected'] = col_df['selected'].fillna(False)
							col_df['highlighted'] = col_df['highlighted'].fillna(False)
							col_df = col_df.rename(columns={i: 'title'})

						else:
							if col_list2 is not None:
								#print("else part")
								#print(col_df)
								heirarchy_check = read_frame(
										sales_heirarchy.objects.filter(buying_controller__in=bc_list).values('commercial_name', 'category_name','buying_controller', 'buyer', 'junior_buyer',
																				   'product_subgroup','store_type', 'brand_indicator', 'parent_supplier',
																					'supplier'))
								# print("inside buyerrr..")
								col['selected'] = True
								col['highlighted'] = False
								kwargs = {'store_type__in': store_list,
										'commercial_name__in':commercial_name_list,
										'category_name__in':category_name_list,
										'buying_controller__in':bc_list,
										'buyer__in': buyer_list,
										'junior_buyer__in': jr_buyer_list,
										'brand_indicator__in': brand_indicator_list,
										'product_subgroup__in': psg_list,
										'parent_supplier__in': parent_supplier_list,
										'supplier__in': supplier_list
								}
								kwargs.pop(col_name)
								kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
								#print(kwargs)
								heirarchy_check = read_frame(
									sales_heirarchy.objects.filter(**kwargs))
								col_df_check = pd.merge(col_df_heirarchy,
														heirarchy_check[[i]].drop_duplicates(), how='right')
								#print("after merge_1...")
								#print(col_df_check)
								#print("printing supplier")
								#print(col)
								col_df_selected = pd.merge(col_df_check[[i]], col, how='left')
								#print("after mergeeee...")
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
								if j < 9:
									if com_list[j + 1] is not None:
										#print("inside com list next")
										col_df = col_df.rename(columns={'title': i})
										col_list_df = pd.DataFrame(col_list2, columns={i})
										#print(col_list_df)
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

					if i == 'parent_supplier':
						col_df['name_supplier'] = col_df['title'].str.split('-').str[1]
						col_df = col_df.sort_values(by=['selected', 'name_supplier'],
																			ascending=[False, True])
						del col_df['name_supplier']
					else:
						col_df = col_df.sort_values(by=['selected','title'], ascending=[False,True])
					#print(col_df)
					col_df['highlighted'] = ~col_df['highlighted']
					#print("after inverse")
					#print(col_df)
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
					# if i == 'junior_buyer':
					#    break
					#print("printing finaaall")
					#print(final)

		return JsonResponse({'cols': cols,'checkbox_list': final}, safe=False)


