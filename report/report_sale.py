# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import ValidationError
from datetime import datetime
 
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT




class ReportSaleeFaker(models.AbstractModel):
    _name = 'report.sales_manipulation.sale_order_print_fake'

    # @api.model
    # def render_html(self, docids, data=None):
    #     self.model = self.env.context.get('active_model')
    #     docs = self.env[self.model].browse(self.env.context.get('active_id'))
    #     sales_records = []
    #     orders = self.env['sale.order.line'].search([('fake_field', '=', True)])
    #     if docs.date_from and docs.date_to:
    #         for order in orders:
    #             if parse(docs.date_from) <= parse(order.create_date) and parse(docs.date_to) >= parse(order.create_date):
    #                 sales_records.append(order);
    #     else:
    #         raise ValidationError("Please enter duration")
        
    #     docargs = {
    #         'doc_ids': self.ids,
    #         'doc_model': self.model,
    #         'docs': docs,
    #         'time': time,
    #         'orders': sales_records
    #     }
    #     return self.env['report'].render('sales_manipulation.sale_order_print_fake', docargs)


    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        date_diff = (date_end_obj - date_start_obj).days + 1

        docs = []
        sales_records = []
        orders = self.env['sale.order.line'].search([(date_start <= date_start_obj.strftime(DATETIME_FORMAT)),(date_end_obj.strftime(DATETIME_FORMAT) >= order.create_date)])
                                                  
        for order in orders:
                # if (date_start <= date_start_obj.strftime(DATETIME_FORMAT)) and (date_end_obj.strftime(DATETIME_FORMAT) >= order.create_date):
                # if parse(docs.date_from) <= parse(order.create_date) and parse(docs.date_to) >= parse(order.create_date):
            sales_records.append(order)
            docs.append({
                        'order_name': order.order_id.name,
                        'partner': order.order_partner_id.name,
                        'product': order.product_id.name,
                        'qty': order.product_uom_qty,
                        'unit_price': order.price_unit,
                        'total': order.price_total,
                        })

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start,
            'date_end': date_end,
            'docs': docs,
        }