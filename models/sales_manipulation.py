

'''
Wizard pop up to select all the records filtered based on the added amount
- Add A fake boolean field on sales order
- Add a button to filter the selected sales order between selected month and amount inputed
- Add the many2many field to wizard,  referencing sales.order
- Add a button to apply the filter records on the many2many field
- Add Fake field to the journal,
- On the print wizard, add a selection button to choose or default to Fake report
- On click on button it will automatically create invoice, register payment and post payments to journal
- 
- Add a menu to only display the Fake sales records
'''

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, ValidationError
from odoo.tools import misc, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import time
import datetime
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from dateutil.parser import parse


class SaleOrdersLine(models.Model):
    _inherit = "sale.order.line"
    
    difference = fields.Float('Difference', 
                              store=True) 
                              # compute="Compute_manipulated_changes") # This will apply when manipulation discount take effect


class SaleOrders(models.Model):
    _inherit = "sale.order"
    
    fake_field = fields.Boolean('Apply Fake', default=False)
    active = fields.Boolean('Active', default=True)
    
    manipulate_id = fields.Many2one('sale_fake.wizards', string= 'Manipulated ref')
    # update_amount = fields.Float('Update Amount(%)') 
    # difference_amount = fields.Float('Price Difference', compute="Get_difference", store=True)

    # @api.depends('update_amount')
    # def Get_difference(self):
    #     if self.update_amount:
    #         diff = self.amount_total - self.update_amount
    #         self.difference_amount = diff
    
    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrders, self)._prepare_invoice()
        # commission_obj = self.env['commission.model']
        if self.fake_field == True:
            vals.update({'fake_field': True})
        return vals


class CommissionWizard(models.Model):
    _name ="sale_fake.wizards"
    _rec_name = "id"

    start = fields.Datetime('Start Date', required=True)
    end = fields.Datetime('End Date', required=True)
    amount = fields.Float('Amount range', store=True)
    value = fields.Float('Value', required=True, default=1, help="Computed based on the run type selected")
    mani_sales_order = fields.Many2many('sale.order', string = 'Manipulated Sale orders')
    original_sales_order = fields.Many2many('sale.order', string = 'Original Sale orders')
    
    run_type = fields.Selection([
        ('percent', 'Run by Percentage'),
        ('fix', 'Fixed Amount'),
        ], string='Run Type', readonly=False, copy=False, 
                                index=True, 
                                track_visibility='onchange', 
                                default='fix')

    overall_operation = fields.Boolean('Overall Trigger', default=True)

    '''If the user checks overall trigger, it will run based on the percent or fixed amount:
     This will affect the price_unit of each sale order lines'''

    @api.one
    def preview_changes(self): 
        orders = self.env['sale.order'].search([('state', 'not in', ['draft','open'])])  
        item = []
        original_item = [] 
        value = 0
        for rec in orders:
            if parse(self.start) <= parse(rec.date_order) and parse(self.end) >= parse(rec.date_order) and self.amount < rec.amount_total:
                original_item.append(rec.id)
                self.write({'original_sales_order': [(4, original_item)]})
                copy_sales = rec.copy({'state':'draft', 'fake_field': True})
                item.append(copy_sales.id) 
                self.write({'mani_sales_order': [(4, item)]})
         
            
    @api.one
    def trigger_changes(self):
        percent_amount = 0 
        value = 0
        value_amount = 0
         
        for sales in self.mani_sales_order:
            if self.overall_operation == True:
                if self.run_type == "percent":
                    if self.value < 0:
                        raise ValidationError('Please enter Value greater than 0')
                        '''For each of the manipulate sales_orders, go into the orderlines
                        and change the items by the enter percentage value'''
                    else:
                        for order_line in sales.order_line:
                            percent_amount = (order_line.price_unit *  value) / 100
                            diff = order_line.price_unit - percent_amount
                            order_line.update({'difference': diff, 'price_unit': percent_amount})
    
                else:
                    for order_line in sales.order_line:
                        value_amount = (order_line.price_unit - value)
                        diff = order_line.price_unit - value_amount
                        order_line.update({'difference': diff, 'price_unit': value_amount})
            else:
                pass

    @api.multi
    def confirm_faker(self):
        for original in self.original_sales_order:
            original.write({'active': False})
        for sales in self.mani_sales_order:    
            confirm_sale = sales.action_confirm()
        # invoice = confirm_sale._prepare_invoice()
            invoice_id = confirm_sale.action_invoice_create()
            find_invoice_id = self.env['account.invoice'].search([('id','=',invoice_id)])
            find_invoice_id.update({'fake_field': True}) 
            '''Next thing is to register the payment to the respective journals, 
            so there is need to add an optional Journal field on the wizard. 
            If not, used the Journal type - SALE'''
                 
                
class AcocuntPaymentFake(models.Model):
    _inherit = "account.payment"

    fake_field = fields.Boolean('Apply Fake', default=False)

                 
class AccountInvoiceFake(models.Model):
    _inherit = "account.invoice"
          
    fake_field = fields.Boolean('Apply Fake', default=False)
          
                 
                 
                 
                 
                  