# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import ValidationError


class ReportSaleeFaker(models.AbstractModel):
    _name = 'report.sales_manipulation.sale_order_print_fake'

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        sales_records = []
        orders = self.env['sale.order.line'].search([('fake_field', '=', True)])
        if docs.date_from and docs.date_to:
            for order in orders:
                if parse(docs.date_from) <= parse(order.create_date) and parse(docs.date_to) >= parse(order.create_date):
                    sales_records.append(order);
        else:
            raise ValidationError("Please enter duration")
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'orders': sales_records
        }
        return self.env['report'].render('sales_manipulation.sale_order_print_fake', docargs)
