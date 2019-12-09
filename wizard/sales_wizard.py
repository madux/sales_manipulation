# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SalesfakeWizard(models.TransientModel):
    _name = "sakefake.wizardho"
    _description = "Sales print wizard"
    
    salesperson_id = fields.Many2one('res.users', string='User', required=False, default=lambda self: self.env.uid)
    date_from = fields.Datetime(string='Start Date')
    date_to = fields.Datetime(string='End Date')
    
    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read([])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read([])[0])
        return self.env['report'].get_action(self, 'sales_manipulation.sale_order_print_fake', data=data)
 