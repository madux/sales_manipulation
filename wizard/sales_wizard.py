# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SalesfakeWizard(models.TransientModel):
    _name = "sakefake.wizardho"
    _description = "Sales print wizard"
    
    salesperson_id = fields.Many2one('res.users', string='User', required=False, default=lambda self: self.env.uid)
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date')
    
    # @api.multi
    # def check_report(self):
    #     data = {}
    #     data['form'] = self.read([])[0]
    #     return self._print_report(data)

    # def _print_report(self, data):
    #     data['form'].update(self.read([])[0])
    #     return self.env['report'].get_action(self, 'sales_manipulation.sale_order_print_fake', data=data)
    @api.multi
    def get_report(self):
        """Call when button 'Get Report' clicked.
        """
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.date_start,
                'date_end': self.date_end,
            },
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `_get_report_values()` and pass `data` automatically.
        return self.env.ref('sales_manipulation.recap_report_sales').report_action(self, data=data)
