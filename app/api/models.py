from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
import uuid
from django.db import models
from django.conf import settings
from datetime import date


# created
class promo_input(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	product_id = models.IntegerField('product_id', blank=True, null=True)
	store_type = models.TextField('selling_area_id', max_length=300, blank=True, null=True)
	promo_type = models.TextField('promo_type', max_length=100, blank=True, null=True)
	flag = models.TextField('flag', max_length=100, blank=True, null=True)
	total_sales = models.DecimalField('total_sales', max_digits=20, decimal_places=10, default=0.0)
	total_sales_lfl = models.DecimalField('total_sales_lfl', max_digits=20, decimal_places=10, default=0.0)
	promo_sales = models.DecimalField('promo_sales', max_digits=20, decimal_places=10, default=0.0)
	promo_sales_lfl = models.DecimalField('promo_sales_lfl', max_digits=20, decimal_places=10, default=0.0)
	total_volume = models.IntegerField('total_volume', blank=True, null=True)
	total_volume_lfl = models.IntegerField('total_volume_lfl', blank=True, null=True)
	promo_volume = models.IntegerField('promo_volume', blank=True, null=True)
	promo_volume_lfl = models.IntegerField('promo_volume_lfl', blank=True, null=True)
	promo_giveaway = models.DecimalField('promo_giveaway', max_digits=20, decimal_places=10, default=0.0)
	promo_giveaway_lfl = models.DecimalField('promo_giveaway_lfl', max_digits=20, decimal_places=10, default=0.0)
	nonpromo_sales_lfl = models.DecimalField('nonpromo_sales_lfl', max_digits=20, decimal_places=10, default=0.0)
	nonpromo_volume_lfl = models.DecimalField('nonpromo_volume_lfl', max_digits=20, decimal_places=10, default=0.0)
	nonpromo_sales = models.DecimalField('nonpromo_sales', max_digits=20, decimal_places=10, default=0.0)
	nonpromo_volume = models.DecimalField('nonpromo_volume', max_digits=20, decimal_places=10, default=0.0)

	def __str__(self):
		return '%s' % (self.Tesco_Week)


# created
class supplier_view(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	commercial_name = models.TextField('commercial_name', max_length=100, blank=True, null=True)
	category_name = models.TextField('category_name', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	buyer = models.TextField('buyer', max_length=100, blank=True, null=True)
	junior_buyer = models.TextField('junior_buyer', max_length=100, blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	product_id = models.IntegerField('product', blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	parent_supplier = models.TextField('parent_supplier', max_length=100, blank=True, null=True)
	supplier = models.TextField('supplier', max_length=100, blank=True, null=True)
	store_count = models.IntegerField('store_count', blank=True, null=True)
	sales_ty = models.DecimalField('sales_ty', max_digits=20, decimal_places=3, default=0.0)
	cat_sales_ty = models.DecimalField('cat_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	volume_ty = models.DecimalField('volume_ty', max_digits=20, decimal_places=3, default=0.0)
	cat_volume_ty = models.DecimalField('cat_volume_ty', max_digits=20, decimal_places=3, default=0.0)
	cogs_ty = models.DecimalField('cogs_ty', max_digits=20, decimal_places=3, default=0.0)
	cat_cogs_ty = models.DecimalField('cat_cogs_ty', max_digits=20, decimal_places=3, default=0.0)
	fundxvat_ty = models.DecimalField('fundxvat_ty', max_digits=20, decimal_places=3, default=0.0)
	cat_fundxvat_ty = models.DecimalField('cat_fundxvat_ty', max_digits=20, decimal_places=3, default=0.0)
	cgm_ty = models.DecimalField('cgm_ty', max_digits=20, decimal_places=3, default=0.0)
	cat_cgm_ty = models.DecimalField('cat_cgm_ty', max_digits=20, decimal_places=3, default=0.0)
	sales_ly = models.DecimalField('sales_ly', max_digits=20, decimal_places=3, default=0.0)
	volume_ly = models.DecimalField('volume_ly', max_digits=20, decimal_places=3, default=0.0)
	cogs_ly = models.DecimalField('cogs_ly', max_digits=20, decimal_places=3, default=0.0)
	fundxvat_ly = models.DecimalField('fundxvat_ly', max_digits=20, decimal_places=3, default=0.0)
	cgm_ly = models.DecimalField('cgm_ly', max_digits=20, decimal_places=3, default=0.0)
	sales_ty_lfl = models.DecimalField('sales_ty_lfl', max_digits=20, decimal_places=3, default=0.0)
	volume_ty_lfl = models.DecimalField('volume_ty_lfl', max_digits=20, decimal_places=3, default=0.0)
	cogs_ty_lfl = models.DecimalField('cogs_ty_lfl', max_digits=20, decimal_places=3, default=0.0)
	cgm_ty_lfl = models.DecimalField('cgm_ty_lfl', max_digits=20, decimal_places=3, default=0.0)
	fundxvat_ty_lfl = models.DecimalField('fundxvat_ty_lfl', max_digits=20, decimal_places=3, default=0.0)
	store_count_lfl = models.IntegerField('store_count_lfl', blank=True, null=True)
	sales_ly_lfl = models.DecimalField('sales_ly_lfl', max_digits=20, decimal_places=3, default=0.0)
	volume_ly_lfl = models.DecimalField('volume_ly_lfl', max_digits=20, decimal_places=3, default=0.0)
	cogs_ly_lfl = models.DecimalField('cogs_ly_lfl', max_digits=20, decimal_places=3, default=0.0)
	fundxvat_ly_lfl = models.DecimalField('fundxvat_ly_lfl', max_digits=20, decimal_places=3, default=0.0)
	cgm_ly_lfl = models.DecimalField('cgm_ly_lfl', max_digits=20, decimal_places=3, default=0.0)
	cps_score = models.DecimalField('cps_score', max_digits=20, decimal_places=12, default=0.0)
	pps = models.DecimalField('pps', max_digits=20, decimal_places=3, default=0.0)
	rate_of_sale = models.DecimalField('rate_of_sale', max_digits=20, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class sales_heirarchy(models.Model):
	commercial_name = models.TextField('commercial_name', max_length=100, blank=True, null=True)
	category_name = models.TextField('category_name', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	buyer = models.TextField('buyer', max_length=100, blank=True, null=True)
	junior_buyer = models.TextField('junior_buyer', max_length=100, blank=True, null=True)
	product_id = models.IntegerField('product_id', blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	product_subgroup_id = models.TextField('product_subgroup_id', max_length=100, blank=True, null=True)
	product = models.TextField('product', max_length=100, blank=True, null=True)
	brand_indicator = models.TextField('brand_indicator', max_length=100, blank=True, null=True)
	brand_name = models.TextField('brand_name', max_length=200, blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	parent_supplier = models.TextField('parent_supplier', max_length=100, blank=True, null=True)
	supplier = models.TextField('supplier', max_length=100, blank=True, null=True)

	def __str__(self):
		return '%s' % (self.store_type)


class supp_kantar(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	category = models.TextField('category', max_length=100, blank=True, null=True)
	manufacturer = models.TextField('manufacturer', max_length=100, blank=True, null=True)
	retailer = models.TextField('retailer', max_length=100, blank=True, null=True)
	spend = models.DecimalField('spend', max_digits=20, decimal_places=10, default=0.0)
	growthpercent = models.DecimalField('growthpercent', max_digits=20, decimal_places=10, default=0.0)
	contritogrowthpercent = models.DecimalField('contritogrowthpercent', max_digits=20, decimal_places=10, default=0.0)
	sharepercentret = models.DecimalField('sharepercentret', max_digits=20, decimal_places=10, default=0.0)
	sharepercentsupp = models.DecimalField('sharepercentsupp', max_digits=20, decimal_places=10, default=0.0)
	yoysharechange = models.DecimalField('yoysharechange', max_digits=20, decimal_places=10, default=0.0)
	totsuppsharechange = models.DecimalField('totsuppsharechange', max_digits=20, decimal_places=10, default=0.0)
	opportunity = models.DecimalField('opportunity', max_digits=20, decimal_places=10, default=0.0)


# created
class executive_view(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	category_area = models.TextField('category_area',max_length=100, blank=True, null=True)
	product_area = models.TextField('product_area',max_length=100, blank=True, null=True)
	buyer_area = models.TextField('buyer_area',max_length=100, blank=True, null=True)
	junior_area = models.TextField('junior_area',max_length=100, blank=True, null=True)
	category_area_trx = models.IntegerField('category_area_trx', blank=True, null=True)
	category_area_sales = models.DecimalField('category_area_sales', max_digits=20, decimal_places=3, default=0.0)
	category_area_volume = models.DecimalField('category_area_volume', max_digits=20, decimal_places=3, default=0.0)
	product_area_trx = models.IntegerField('product_area_trx', blank=True, null=True)
	product_area_sales = models.DecimalField('product_area_sales', max_digits=20, decimal_places=3, default=0.0)
	product_area_volume = models.DecimalField('product_area_volume', max_digits=20, decimal_places=3, default=0.0)
	buyer_area_trx = models.IntegerField('buyer_area_trx', blank=True, null=True)
	buyer_area_sales = models.DecimalField('buyer_area_sales', max_digits=20, decimal_places=3, default=0.0)
	buyer_area_volume = models.DecimalField('buyer_area_volume', max_digits=20, decimal_places=3, default=0.0)
	junior_area_trx = models.IntegerField('junior_area_trx', blank=True, null=True)
	junior_area_sales = models.DecimalField('junior_area_sales', max_digits=20, decimal_places=3, default=0.0)
	junior_area_volume = models.DecimalField('junior_area_volume', max_digits=20, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class promo_contribution(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	commercial_area = models.TextField('commercial_area', max_length=100, blank=True, null=True)
	category_director = models.TextField('category_director', max_length=100, blank=True, null=True)
	product_area = models.TextField('product_area', max_length=100, blank=True, null=True)
	buyer_area = models.TextField('buyer_area', max_length=100, blank=True, null=True)
	junior_area = models.TextField('junior_area', max_length=100, blank=True, null=True)
	trade_plan_sales_ty = models.DecimalField('trade_plan_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	trade_plan_sales_ly = models.DecimalField('trade_plan_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	event_sales_ty = models.DecimalField('event_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	event_sales_ly = models.DecimalField('event_sales_ly', max_digits=20, decimal_places=3, default=0.0)
	fs_sales_ty = models.DecimalField('fs_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	fs_sales_ly = models.DecimalField('fs_sales_ly', max_digits=20, decimal_places=3, default=0.0)
	shelf_promo_sales_ty = models.DecimalField('shelf_promo_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	shelf_promo_sales_ly = models.DecimalField('shelf_promo_sales_ly', max_digits=20, decimal_places=3, default=0.0)
	base_sales_ty = models.DecimalField('base_sales_ty', max_digits=20, decimal_places=3, default=0.0)
	base_sales_ly = models.DecimalField('base_sales_ly', max_digits=20, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class executive_price_index(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	total_tesco_sales = models.DecimalField('total_tesco_sales', max_digits=20, decimal_places=3, default=0.0)
	total_derived_sales = models.DecimalField('total_derived_sales', max_digits=20, decimal_places=3, default=0.0)
	line_count = models.DecimalField('line_count', max_digits=20, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class forecast_budget_data(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	junior_buyer = models.TextField('junior_buyer', max_length=100, blank=True, null=True)
	budget_sales = models.DecimalField('budget_sales', max_digits=14, decimal_places=3, default=0.0)
	forecast_sales = models.DecimalField('forecast_sales', max_digits=14, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class roles_and_intent(models.Model):
	category_director = models.TextField('category_director', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	intent = models.TextField('intent', max_length=100, blank=True, null=True)

	def __str__(self):
		return '%s' % (self.category_director)


class weather_weekly_details(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	sunshine_weekly_avg = models.DecimalField('sunshine_weekly_avg', max_digits=14, decimal_places=3, default=0.0)
	rainfall_weekly_avg = models.DecimalField('rainfall_weekly_avg', max_digits=14, decimal_places=3, default=0.0)
	temperature_weekly_avg = models.DecimalField('temperature_weekly_avg', max_digits=14, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class calendar_dim_hierarchy(models.Model):
	date = models.DateField(blank=True, null=True)
	tesco_week = models.IntegerField('tesco_week')
	quarter_num = models.IntegerField('quarter_num')
	period_num = models.IntegerField('period_num')
	period_start_num = models.IntegerField('period_start_num')
	week_start_date = models.IntegerField('week_start_Date')
	quarter_start_date = models.IntegerField('quarter_start_date')
	week_day_num = models.IntegerField('week_day_num')
	week_day_str = models.TextField('week_day_str', max_length=100, blank=True, null=True)

	def __str__(self):
		return '%s' % (self.tesco_week)


class uk_holidays(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	holiday_date = models.DateField(default=date.today, blank=True)
	holiday_description = models.TextField('holiday_description', max_length=100, blank=True, null=True)

	def __str__(self):
		return '%s' % (self.tesco_week)


class executive_inflation(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	product_id = models.IntegerField('product', blank=True, null=True)
	final_infl_sales_ty = models.DecimalField('Final_Infl_Sales_TY', max_digits=14, decimal_places=3, default=0.0)
	final_infl_sales_ly = models.DecimalField('Final_Infl_Sales_LY', max_digits=14, decimal_places=3, default=0.0)
	final_ty_qty_ly_price = models.DecimalField('Final_TY_Qty_LY_Price', max_digits=14, decimal_places=3, default=0.0)
	final_ly_qty_ty_price = models.DecimalField('Final_LY_Qty_TY_Price', max_digits=14, decimal_places=3, default=0.0)
	final_infl_cogs_ty = models.DecimalField('Final_Infl_cogs_TY', max_digits=14, decimal_places=3, default=0.0)
	final_infl_cogs_ly = models.DecimalField('Final_Infl_cogs_LY', max_digits=14, decimal_places=3, default=0.0)
	final_ty_qty_ly_cogs = models.DecimalField('final_ty_qty_ly_cogs', max_digits=14, decimal_places=3, default=0.0)
	final_ly_qty_ty_cogs = models.DecimalField('final_ly_qty_ty_cogs', max_digits=14, decimal_places=3, default=0.0)

	def __str__(self):
		return '%s' % (self.tesco_week)


class competitor_outperform(models.Model):
	tesco_week = models.IntegerField('week', blank=True, null=True)
	competitor = models.TextField('competitor', max_length=100, blank=True, null=True)
	commercial_area = models.TextField('commercial_area', max_length=100, blank=True, null=True)
	category = models.TextField('category', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	buyer = models.TextField('buyer', max_length=100, blank=True, null=True)
	junior_buyer = models.TextField('junior_buyer', max_length=100, blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	commercial_area_outperf_value_pct = models.DecimalField('commercial_area_outperf_value_pct', max_digits=20,
															decimal_places=3, default=0.0)
	category_outperf_value_pct = models.DecimalField('category_outperf_value_pct', max_digits=20, decimal_places=3,
													 default=0.0)
	buying_controller_outperf_value_pct = models.DecimalField('buying_controller_outperf_value_pct', max_digits=20,
															  decimal_places=3, default=0.0)
	buyer_outperf_value_pct = models.DecimalField('buyer_outperf_value_pct', max_digits=20, decimal_places=3,
												  default=0.0)
	junior_buyer_outperf_value_pct = models.DecimalField('junior_buyer_outperf_value_pct', max_digits=20,
														 decimal_places=3, default=0.0)
	product_subgroup_outperf_value_pct = models.DecimalField('product_subgroup_outperf_value_pct', max_digits=20,
															 decimal_places=3, default=0.0)
	commercial_area_outperf_volume_pct = models.DecimalField('commercial_area_outperf_vol_pct', max_digits=20,
															 decimal_places=3, default=0.0)
	category_outperf_volume_pct = models.DecimalField('category_outperf_vol_pct', max_digits=20, decimal_places=3,
													  default=0.0)
	buying_controller_outperf_volume_pct = models.DecimalField('buying_controller_outperf_vol_pct', max_digits=20,
															   decimal_places=3, default=0.0)
	buyer_outperf_volume_pct = models.DecimalField('buyer_outperf_vol_pct', max_digits=20, decimal_places=3,
												   default=0.0)
	junior_buyer_outperf_volume_pct = models.DecimalField('junior_buyer_outperf_vol_pct', max_digits=20,
														  decimal_places=3, default=0.0)
	product_subgroup_outperf_volume_pct = models.DecimalField('product_subgroup_outperf_vol_pct', max_digits=20,
															  decimal_places=3, default=0.0)
	commercial_area_value_growth = models.DecimalField('commercial_area_value_growth', max_digits=20, decimal_places=3,
													   default=0.0)
	category_value_growth = models.DecimalField('category_value_growth', max_digits=20, decimal_places=3, default=0.0)
	buying_controller_value_growth = models.DecimalField('buying_controller_value_growth', max_digits=20,
														 decimal_places=3, default=0.0)
	buyer_value_growth = models.DecimalField('buyer_value_growth', max_digits=20, decimal_places=3, default=0.0)
	junior_buyer_value_growth = models.DecimalField('junior_buyer_value_growth', max_digits=20, decimal_places=3,
													default=0.0)
	product_subgroup_value_growth = models.DecimalField('product_subgroup_value_growth', max_digits=20,
														decimal_places=3, default=0.0)
	commercial_area_volume_growth = models.DecimalField('commercial_area_vol_growth', max_digits=20, decimal_places=3,
														default=0.0)
	category_volume_growth = models.DecimalField('category_vol_growth', max_digits=20, decimal_places=3, default=0.0)
	buying_controller_volume_growth = models.DecimalField('buying_controller_vol_growth', max_digits=20,
														  decimal_places=3, default=0.0)
	buyer_volume_growth = models.DecimalField('buyer_vol_growth', max_digits=20, decimal_places=3, default=0.0)
	junior_buyer_volume_growth = models.DecimalField('junior_buyer_vol_growth', max_digits=20, decimal_places=3,
													 default=0.0)
	product_subgroup_volume_growth = models.DecimalField('product_subgroup_vol_growth', max_digits=20, decimal_places=3,
														 default=0.0)

	def __str__(self):
		return '%s' % (self.week)


class competitor_price_bucket(models.Model):
	tesco_week = models.IntegerField('week', blank=True, null=True)
	retailer = models.TextField('retailer', max_length=100, blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	product_id = models.IntegerField('product_id', blank=True, null=True)
	asp = models.DecimalField('asp', max_digits=20, decimal_places=3)

	def __str__(self):
		return '%s' % (self.week)


class competitor_market_share(models.Model):
	tesco_week = models.IntegerField('week', blank=True, null=True)
	competitor = models.TextField('competitor', max_length=100, blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	product_subgroup_id = models.TextField('product_subgroup_id', max_length=100, blank=True, null=True)
	value = models.DecimalField('value', max_digits=20, decimal_places=3, default=0.0)
	volume = models.DecimalField('volume', max_digits=20, decimal_places=3, default=0.0)
	opportunity = models.DecimalField('opportunity', max_digits=20, decimal_places=3, default=0.0)
	flag = models.TextField('flag', max_length=100, blank=True, null=True)

	def __str__(self):
		return '%s' % (self.week)


class competitor_price_index(models.Model):
	commercial_area = models.TextField('commercial_area', max_length=100, blank=True, null=True)
	category_director = models.TextField('category_director', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=300, blank=True, null=True)
	buyer = models.TextField('buyer', max_length=300, blank=True, null=True)
	junior_buyer = models.TextField('junior_buyer', max_length=300, blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=300, blank=True, null=True)
	product_id = models.TextField('product_id', max_length=100, blank=True, null=True)
	product_description = models.TextField('product_description', max_length=100, blank=True, null=True)
	brand_indicator = models.TextField('brand_indicator', max_length=300, blank=True, null=True)
	basket_description = models.TextField('basket_description', max_length=300, blank=True, null=True)
	cut_impact_by = models.TextField('cut_impact_by', max_length=300, blank=True, null=True)
	tesco_price_moves = models.TextField('tesco_price_moves', max_length=100, blank=True, null=True)
	tesco_promo_activity = models.TextField('tesco_promo_activity', max_length=100, blank=True, null=True)
	asda_price_moves = models.TextField('asda_price_moves', max_length=100, blank=True, null=True)
	asda_promo_activity = models.TextField('asda_promo_activity', max_length=100, blank=True, null=True)
	morrison_price_moves = models.TextField('morrison_price_moves', max_length=100, blank=True, null=True)
	morrison_promo_activity = models.TextField('morrison_promo_activity', max_length=100, blank=True, null=True)
	js_price_moves = models.TextField('js_price_moves', max_length=100, blank=True, null=True)
	js_promo_activity = models.TextField('js_promo_activity', max_length=100, blank=True, null=True)
	aldi_price_moves = models.TextField('aldi_price_moves', max_length=100, blank=True, null=True)
	aldi_promo_activity = models.TextField('aldi_promo_activity', max_length=100, blank=True, null=True)
	impact_on_asda_lw_index = models.DecimalField('impact_on_asda_lw_index', max_digits=20, decimal_places=10,default=0.0)
	impact_on_asda_wia_index = models.DecimalField('impact_on_asda_wia_index', max_digits=20, decimal_places=10,default=0.0)
	impact_on_asda_tw_index = models.DecimalField('impact_on_asda_tw_index', max_digits=20, decimal_places=10,default=0.0)
	impact_on_morr_lw_index = models.DecimalField('impact_on_morr_lw_index', max_digits=20, decimal_places=10,default=0.0)
	impact_on_morr_wia_index = models.DecimalField('impact_on_morr_wia_index', max_digits=20, decimal_places=10,default=0.0)
	impact_on_morr_tw_index = models.DecimalField('impact_on_morr_tw_index', max_digits=20, decimal_places=10,
												  default=0.0)
	impact_on_js_lw_index = models.DecimalField('impact_on_js_lw_index', max_digits=20, decimal_places=10, default=0.0)
	impact_on_js_wia_index = models.DecimalField('impact_on_js_wia_index', max_digits=20, decimal_places=10,
												 default=0.0)
	impact_on_js_tw_index = models.DecimalField('impact_on_js_tw_index', max_digits=20, decimal_places=10, default=0.0)
	impact_on_aldi_lw_index = models.DecimalField('impact_on_aldi_lw_index', max_digits=20, decimal_places=10,
												  default=0.0)
	impact_on_aldi_wia_index = models.DecimalField('impact_on_aldi_wia_index', max_digits=20, decimal_places=10,
												   default=0.0)
	impact_on_aldi_tw_index = models.DecimalField('impact_on_aldi_tw_index', max_digits=20, decimal_places=10,
												  default=0.0)

	def __str__(self):
		return '%s' % (self.product_id)


class product_view(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	product_id = models.IntegerField('product_id', blank=True, null=True)
	product = models.TextField('product', max_length=100, blank=True, null=True)
	product_subgroup_id = models.TextField('product_subgroup_id', max_length=100, blank=True, null=True)
	product_subgroup = models.TextField('product_subgroup', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	category_name = models.TextField('category_name', max_length=100, blank=True, null=True)
	buyer = models.TextField('buyer', max_length=100, blank=True, null=True)
	junior_buyer = models.TextField('junior_buyer', max_length=100, blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	sales_value = models.DecimalField('sales_value', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_value_lfl = models.DecimalField('sales_value_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_value_lw = models.DecimalField('sales_value_lw', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_value_ly = models.DecimalField('sales_value_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_value_lfl_ly = models.DecimalField('sales_value_lfl_ly', blank=True, max_digits=20, decimal_places=2,
											 default=0.0)
	sales_volume = models.DecimalField('sales_volume', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_volume_lfl = models.DecimalField('sales_volume_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_volume_lw = models.DecimalField('sales_volume_lw', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_volume_ly = models.DecimalField('sales_volume_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_volume_lfl_ly = models.DecimalField('sales_volume_lfl_ly', blank=True, max_digits=20, decimal_places=2,
											  default=0.0)
	cogs = models.DecimalField('cogs', blank=True, max_digits=20, decimal_places=2, default=0.0)
	cogs_lfl = models.DecimalField('cogs_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	cogs_lw = models.DecimalField('cogs_lw', blank=True, max_digits=20, decimal_places=2, default=0.0)
	cogs_ly = models.DecimalField('cogs_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	cogs_lfl_ly = models.DecimalField('cogs_lfl_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit = models.DecimalField('profit', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit_lfl = models.DecimalField('profit_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit_lw = models.DecimalField('profit_lw', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit_ly = models.DecimalField('profit_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit_lfl_ly = models.DecimalField('profit_lfl_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	waste = models.DecimalField('waste', blank=True, max_digits=20, decimal_places=2, default=0.0)
	waste_lfl = models.DecimalField('waste_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	waste_lw = models.DecimalField('waste_lw', blank=True, max_digits=20, decimal_places=2, default=0.0)
	waste_ly = models.DecimalField('waste_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	waste_lfl_ly = models.DecimalField('waste_lfl_ly', blank=True, max_digits=20, decimal_places=2, default=0.0)
	asp = models.DecimalField('asp', blank=True, max_digits=20, decimal_places=2, null=True)
	asp_lw = models.DecimalField('asp_lw', blank=True, max_digits=20, decimal_places=2, null=True)
	asp_diff_lw = models.DecimalField('asp_diff_lw', blank=True, max_digits=20, decimal_places=2, null=True)
	brand_indicator = models.TextField('brand_indicator', max_length=100, blank=True, null=True)
	week_index = models.IntegerField('week_index', blank=True, null=True)
	period_no = models.TextField('period_no', max_length=100, blank=True, null=True)
	rank_cw = models.IntegerField('rank_cw', blank=True, null=True)
	rank_lw = models.IntegerField('rank_lw', blank=True, null=True)
	top20 = models.IntegerField('top20', blank=True, null=True)

	def __str__(self):
		return '%s' % (self.product_id)


class dss_view(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	calendar_date = models.DateField(blank=True, null=True, verbose_name="calendar_date")
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	product_id = models.IntegerField('product_id', blank=True, null=True)
	daily_sales = models.DecimalField('daily_sales', max_digits=14, decimal_places=3, default=0.0)
	daily_volume = models.DecimalField('daily_volume', max_digits=14, decimal_places=3, default=0.0)
	daily_cogs = models.DecimalField('daily_cogs', max_digits=14, decimal_places=3, default=0.0)
	daily_cogs_lfl = models.DecimalField('daily_cogs_lfl', max_digits=14, decimal_places=3, default=0.0)
	daily_sales_lfl = models.DecimalField('daily_sales_lfl', max_digits=14, decimal_places=3, default=0.0)
	daily_volume_lfl = models.DecimalField('daily_volume_lfl', max_digits=14, decimal_places=3, default=0.0)


class latest_week(models.Model):
	week_ty = models.IntegerField('week_ty', blank=True, null=True)
	week_ly = models.IntegerField('week_ly', blank=True, null=True)

class latest_date(models.Model):
	week_ty = models.IntegerField('week_ty', blank=True, null=True)
	date_ty = models.DateField(blank=True, null=True, verbose_name="date_ty")
	week_ly = models.IntegerField('week_ly', blank=True, null=True)
	date_ly = models.DateField(blank=True, null=True, verbose_name="date_ly")


class product_view_v2(models.Model):
	tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
	product_id = models.IntegerField('product_id', blank=True, null=True)
	store_type = models.TextField('store_type', max_length=100, blank=True, null=True)
	sales_value = models.DecimalField('sales_value', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_value_lfl = models.DecimalField('sales_value_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_volume = models.DecimalField('sales_volume', blank=True, max_digits=20, decimal_places=2, default=0.0)
	sales_volume_lfl = models.DecimalField('sales_volume_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	cogs = models.DecimalField('cogs', blank=True, max_digits=20, decimal_places=2, default=0.0)
	cogs_lfl = models.DecimalField('cogs_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit = models.DecimalField('profit', blank=True, max_digits=20, decimal_places=2, default=0.0)
	profit_lfl = models.DecimalField('profit_lfl', blank=True, max_digits=20, decimal_places=2, default=0.0)

	def __str__(self):
		return '%s' % (self.product_id)

class competitor_price_index_basket(models.Model):
	tw = models.IntegerField('tw', blank=True, null=True)
	lw = models.IntegerField('lw', blank=True, null=True)
	product_sub_group_code = models.TextField('product_sub_group_code', max_length=100, blank=True, null=True)
	basket = models.TextField('basket', max_length=100, blank=True, null=True)
	asda_tesco_sales_tw = models.DecimalField('asda_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	asda_tesco_sales_lw = models.DecimalField('asda_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	asda_sales_tw = models.DecimalField('asda_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	asda_sales_lw = models.DecimalField('asda_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	asda_sales_total_tw = models.DecimalField('asda_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	asda_sales_total_lw = models.DecimalField('asda_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	js_tesco_sales_tw = models.DecimalField('js_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											default=0.0)
	js_tesco_sales_lw = models.DecimalField('js_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											default=0.0)
	js_sales_tw = models.DecimalField('js_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	js_sales_lw = models.DecimalField('js_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	js_sales_total_tw = models.DecimalField('js_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											default=0.0)
	js_sales_total_lw = models.DecimalField('js_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											default=0.0)
	morr_tesco_sales_tw = models.DecimalField('morr_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	morr_tesco_sales_lw = models.DecimalField('morr_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	morr_sales_tw = models.DecimalField('morr_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	morr_sales_lw = models.DecimalField('morr_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	morr_sales_total_tw = models.DecimalField('morr_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	morr_sales_total_lw = models.DecimalField('morr_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_tesco_sales_tw = models.DecimalField('aldi_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_tesco_sales_lw = models.DecimalField('aldi_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_sales_tw = models.DecimalField('aldi_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	aldi_sales_lw = models.DecimalField('aldi_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	aldi_sales_total_tw = models.DecimalField('aldi_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_sales_total_lw = models.DecimalField('aldi_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_tesco_sales_tw = models.DecimalField('lidl_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_tesco_sales_lw = models.DecimalField('lidl_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_sales_tw = models.DecimalField('lidl_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	lidl_sales_lw = models.DecimalField('lidl_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	lidl_sales_total_tw = models.DecimalField('lidl_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_sales_total_lw = models.DecimalField('lidl_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	impact_on_lidl_tw_index = models.DecimalField('impact_on_lidl_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_lidl_lw_index = models.DecimalField('impact_on_lidl_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_lidl_wia_index = models.DecimalField('impact_on_lidl_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_aldi_tw_index = models.DecimalField('impact_on_aldi_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_aldi_lw_index = models.DecimalField('impact_on_aldi_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_aldi_wia_index = models.DecimalField('impact_on_aldi_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_morr_tw_index = models.DecimalField('impact_on_morr_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_morr_lw_index = models.DecimalField('impact_on_morr_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_morr_wia_index = models.DecimalField('impact_on_morr_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_asda_tw_index = models.DecimalField('impact_on_asda_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_asda_lw_index = models.DecimalField('impact_on_asda_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_asda_wia_index = models.DecimalField('impact_on_asda_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_js_tw_index = models.DecimalField('impact_on_js_tw_index', blank=True, max_digits=20, decimal_places=10,
												default=0.0)
	impact_on_js_lw_index = models.DecimalField('impact_on_js_lw_index', blank=True, max_digits=20, decimal_places=10,
												default=0.0)
	impact_on_js_wia_index = models.DecimalField('impact_on_js_wia_index', blank=True, max_digits=20, decimal_places=10,
												 default=0.0)

	def __str__(self):
		return '%s' % (self.product_sub_group_code)


class competitor_price_index_brand(models.Model):
	tw = models.IntegerField('tw', blank=True, null=True)
	lw = models.IntegerField('lw', blank=True, null=True)
	product_sub_group_code = models.TextField('product_sub_group_code', max_length=100, blank=True, null=True)
	brand = models.TextField('brand', max_length=100, blank=True, null=True)
	asda_tesco_sales_tw = models.DecimalField('asda_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	asda_tesco_sales_lw = models.DecimalField('asda_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	asda_sales_tw = models.DecimalField('asda_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	asda_sales_lw = models.DecimalField('asda_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	asda_sales_total_tw = models.DecimalField('asda_sales_total_tw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	asda_sales_total_lw = models.DecimalField('asda_sales_total_lw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	js_tesco_sales_tw = models.DecimalField('js_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	js_tesco_sales_lw = models.DecimalField('js_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	js_sales_tw = models.DecimalField('js_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	js_sales_lw = models.DecimalField('js_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	js_sales_total_tw = models.DecimalField('js_sales_total_tw', blank=True, max_digits=20, decimal_places=10,default=0.0)
	js_sales_total_lw = models.DecimalField('js_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											default=0.0)
	morr_tesco_sales_tw = models.DecimalField('morr_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	morr_tesco_sales_lw = models.DecimalField('morr_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	morr_sales_tw = models.DecimalField('morr_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	morr_sales_lw = models.DecimalField('morr_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	morr_sales_total_tw = models.DecimalField('morr_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	morr_sales_total_lw = models.DecimalField('morr_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_tesco_sales_tw = models.DecimalField('aldi_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_tesco_sales_lw = models.DecimalField('aldi_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_sales_tw = models.DecimalField('aldi_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	aldi_sales_lw = models.DecimalField('aldi_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	aldi_sales_total_tw = models.DecimalField('aldi_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	aldi_sales_total_lw = models.DecimalField('aldi_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_tesco_sales_tw = models.DecimalField('lidl_tesco_sales_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_tesco_sales_lw = models.DecimalField('lidl_tesco_sales_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_sales_tw = models.DecimalField('lidl_sales_tw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	lidl_sales_lw = models.DecimalField('lidl_sales_lw', blank=True, max_digits=20, decimal_places=10, default=0.0)
	lidl_sales_total_tw = models.DecimalField('lidl_sales_total_tw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	lidl_sales_total_lw = models.DecimalField('lidl_sales_total_lw', blank=True, max_digits=20, decimal_places=10,
											  default=0.0)
	impact_on_lidl_tw_index = models.DecimalField('impact_on_lidl_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_lidl_lw_index = models.DecimalField('impact_on_lidl_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_lidl_wia_index = models.DecimalField('impact_on_lidl_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_aldi_tw_index = models.DecimalField('impact_on_aldi_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_aldi_lw_index = models.DecimalField('impact_on_aldi_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_aldi_wia_index = models.DecimalField('impact_on_aldi_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_morr_tw_index = models.DecimalField('impact_on_morr_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_morr_lw_index = models.DecimalField('impact_on_morr_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_morr_wia_index = models.DecimalField('impact_on_morr_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_asda_tw_index = models.DecimalField('impact_on_asda_tw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_asda_lw_index = models.DecimalField('impact_on_asda_lw_index', blank=True, max_digits=20,
												  decimal_places=10, default=0.0)
	impact_on_asda_wia_index = models.DecimalField('impact_on_asda_wia_index', blank=True, max_digits=20,
												   decimal_places=10, default=0.0)
	impact_on_js_tw_index = models.DecimalField('impact_on_js_tw_index', blank=True, max_digits=20, decimal_places=10,
												default=0.0)
	impact_on_js_lw_index = models.DecimalField('impact_on_js_lw_index', blank=True, max_digits=20, decimal_places=10,
												default=0.0)
	impact_on_js_wia_index = models.DecimalField('impact_on_js_wia_index', blank=True, max_digits=20, decimal_places=10,
												 default=0.0)
	def __str__(self):
		return '%s' % (self.product_sub_group_code)


class roles_and_intent_v2(models.Model):
	category = models.TextField('category', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	large_stores = models.TextField('large_stores', max_length=100, blank=True, null=True)
	express = models.TextField('express', max_length=100, blank=True, null=True)

class roles_and_intent_target(models.Model):
	category = models.TextField('category', max_length=100, blank=True, null=True)
	buying_controller = models.TextField('buying_controller', max_length=100, blank=True, null=True)
	type = models.TextField('type', max_length=100, blank=True, null=True)
	large_stores = models.TextField('large_stores', max_length=100, blank=True, null=True)
	express = models.TextField('express', max_length=100, blank=True, null=True)
	benchmark = models.TextField('benchmark', max_length=100, blank=True, null=True)
	tesco_as_is = models.DecimalField('tesco_as_is', blank=True, max_digits=20, decimal_places=2, default=0.0)
	tesco_end_game = models.DecimalField('tesco_end_game', blank=True, max_digits=20, decimal_places=2, default=0.0)


class promo_view(models.Model):
    tesco_week = models.IntegerField('tesco_week', blank=True, null=True)
    product_id = models.IntegerField('product_id', blank=True, null=True)
    store_type = models.TextField('selling_area_id', max_length=300, blank=True, null=True)
    promo_type = models.TextField('promo_type', max_length=100, blank=True, null=True)
    promo_name = models.TextField('promo_name', max_length=100, blank=True, null=True)
    flag = models.TextField('flag', max_length=100, blank=True, null=True)
    total_sales = models.DecimalField('total_sales', max_digits=20, decimal_places=10, default=0.0)
    total_sales_lfl = models.DecimalField('total_sales_lfl', max_digits=20, decimal_places=10, default=0.0)
    promo_sales = models.DecimalField('promo_sales', max_digits=20, decimal_places=10, default=0.0)
    promo_sales_lfl = models.DecimalField('promo_sales_lfl', max_digits=20, decimal_places=10, default=0.0)
    total_volume = models.IntegerField('total_volume', blank=True, null=True)
    total_volume_lfl = models.IntegerField('total_volume_lfl', blank=True, null=True)
    promo_volume = models.IntegerField('promo_volume', blank=True, null=True)
    promo_volume_lfl = models.IntegerField('promo_volume_lfl', blank=True, null=True)
    promo_giveaway = models.DecimalField('promo_giveaway', max_digits=20, decimal_places=10, default=0.0)
    promo_giveaway_lfl = models.DecimalField('promo_giveaway_lfl', max_digits=20, decimal_places=10, default=0.0)
    nonpromo_sales_lfl = models.DecimalField('nonpromo_sales_lfl', max_digits=20, decimal_places=10, default=0.0)
    nonpromo_volume_lfl = models.DecimalField('nonpromo_volume_lfl', max_digits=20, decimal_places=10, default=0.0)
    nonpromo_sales = models.DecimalField('nonpromo_sales', max_digits=20, decimal_places=10, default=0.0)
    nonpromo_volume = models.DecimalField('nonpromo_volume', max_digits=20, decimal_places=10, default=0.0)
    total_profit = models.DecimalField('promo_profit', max_digits=20, decimal_places=10, default=0.0)
    total_profit_lfl = models.IntegerField('total_profit_lfl', blank=True, null=True)
    promo_profit = models.IntegerField('promo_profit', blank=True, null=True)
    promo_profit_lfl = models.IntegerField('promo_profit_lfl', blank=True, null=True)
    nonpromo_profit_lfl = models.DecimalField('nonpromo_profit_lfl', max_digits=20, decimal_places=10, default=0.0)
    nonpromo_profit = models.DecimalField('nonpromo_profit', max_digits=20, decimal_places=10, default=0.0)
