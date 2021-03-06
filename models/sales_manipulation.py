

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
# from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from dateutil.parser import parse
from collections import Counter
sales_lister = []

class productTemplate(models.Model):
    _inherit = "product.template"
    _order = "id desc"

    service_to_purchase = fields.Boolean(
        'Service to -purchase', default=False,)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _order = "id desc"

    cost_price = fields.Float('All Location Stock')


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _order = "id desc"

     
    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if self.order_line:
            for lines in self.order_line:
                self.product_id.standard_price = lines.price_unit
                product = self.env['product.product'].search([('id','=',lines.product_id.id)])
                product.write({'standard_price': lines.price_unit})
        self.action_rfq_send()
        self.Account_Move()
        
    def Account_Move(self):
        journal = self.env['account.journal'].search([('type', 'in', ['purchase'])], limit=1)
        acm = self.env['account.payment.method'].create(
                {'payment_type': 'outbound', 'name': 'Payment For '+self.name, 'code': str(self.name) + str(self.id)})
        payment_data = {
            'amount': self.amount_total, 
            'payment_date': fields.Date.today(),
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,  
            'narration': "SO - For" + self.name,
            'communication': str(self.name), 
            'payment_method_id': acm.id, 
                        }
        payment_model = self.env['account.payment'].create(payment_data).post()
        
    # @api.multi
    # def button_print_purchases(self):
    #     return self.env['report'].get_action(self, 'ikoyi_module.purchase_order_prints')

class SaleOrdersLine(models.Model):
    _inherit = "sale.order.line"
    _order = "id desc"
    
    difference = fields.Float('Difference', store=True)
    preview_total = fields.Float('Preview Total')
    preview_new_qty = fields.Float('Previewed Qty', store=True)
    preview_price = fields.Float('Preview Unit Price')
    manipulate_id = fields.Many2one('sale_fake.wizards', string= 'Manipulated ref')
    fake_field = fields.Boolean('Null', default=False)
    active = fields.Boolean('Active', default=True)
    tampered = fields.Boolean('None', default=False)
    stock_qty = fields.Float('All Location Stock')
    cost_price = fields.Float('All Location Stock', related="product_id.standard_price")

    
    @api.onchange('price_unit')
    def check_validity(self):
        if self.price_unit:
            if self.price_unit < self.product_id.standard_price:
                raise ValidationError('You are trying to sell a %s below your cost Price. \
                    Kindly increase the Unit price' %self.product_id.name)
    
    @api.onchange('product_id')
    def get_stock(self):
        if self.product_id:
            total = 0
            quant = self.env['stock.quant'].search([('product_id','=', self.product_id.id)])
            
            for rec in quant:
                total += rec.quantity
            self.stock_qty = total
            
    @api.multi
    def button_print_sales(self):
        return self.env['report'].get_action(self, 'sales_manipulation.sale_order_print_fake')


class SaleOrders(models.Model):
    _inherit = "sale.order"
    _order = "id desc"
    
    fake_field = fields.Boolean('Null', default=False)
    active = fields.Boolean('Active', default=True)
    manipulate_id = fields.Many2one('sale_fake.wizards', string= 'Manipulated ref')
    tampered = fields.Boolean('None', default=False)
     
    def _default_partner(self):
        lists=[]
        partner_obj = self.env['res.partner']
        partner = partner_obj.search([('name','=', 'Random Customer')])
        if partner:
            lists.append(partner.id)
        else:
            part = partner_obj.create({'supplier':True, 'name':'Random Customer'})
            lists.append(part.id)
        return partner_obj.search(
            [('name', '=', 'Random Customer')], limit=1)
    
    partner_id = fields.Many2one('res.partner', string='Customer', default=_default_partner, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always', track_sequence=1, help="You can find a customer by its Name, TIN, Email or Internal Reference.")
           
    @api.multi
    def action_confirm(self):
        res = super(SaleOrders, self).action_confirm() 
        self.Account_Move()
        return res

    @api.multi
    def button_print_sales(self):
        return self.env['report'].get_action(self, 'sales_manipulation.report_print_sale_order_sm')

    def Account_Move(self):
        journal = self.env['account.journal'].search([('type', 'in', ['sale'])], limit=1)
        acm = self.env['account.payment.method'].create(
                {'payment_type': 'inbound', 'name': 'Payment For '+self.name, 'code': str(self.name) + str(self.id)})
        payment_data = {
            'amount': self.amount_total, 
            'payment_date': fields.Date.today(),
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,  
            'narration': "SO - For" + self.name,
            'communication': str(self.name), 
            'payment_method_id': acm.id, 
                        }
        payment_model = self.env['account.payment'].create(payment_data).post()
             
        # sale_name = str(self.name)
        # partner = self.partner_id.id
        # date = fields.Date.today()
        # narration = "SO - For" + sale_name
        # amount = self.amount_total 
        # move_id = self.env['account.move'].create({'journal_id': journal.id,  
        #                                            'ref': sale_name,
        #                                            'date': date,
        #                                            'narration': narration, 
        #                                            })
        # # create account.move.line for both debit and credit
        # acc_move_line = self.env['account.move.line']
        # line_id_dr = acc_move_line.with_context(check_move_validity=False)\
        #     .with_context(check_move_validity=False).create({
        #                                 'move_id': move_id.id,
        #                                 'ref': sale_name,
        #                                 'name': narration,
        #                                 'partner_id': partner,
        #                                 'account_id': journal.default_debit_account_id.id, 
        #                                 'debit': amount,
        #                                 # 'analytic_account_id': if any?
        #                 })

        # line_id_cr = self.env['account.move.line'].with_context(check_move_validity=False).create({
        #                                 'move_id': move_id.id,
        #                                 'ref': sale_name,
        #                                 'name': narration,
        #                                 'partner_id': partner,
        #                                 'account_id': journal.default_credit_account_id.id,
        #                                 'credit': amount,
        #                 })


class CommissionWizard(models.Model):
    _name = "sale_fake.wizards"
    _rec_name = "id"

    start = fields.Datetime('Start Date', required=True)
    end = fields.Datetime('End Date', required=True)
    amount = fields.Float('Amount Above', store=True)
    value = fields.Integer('Value(%)', required=True,
                           default=1,
                           help="Computed based on the run type selected") 
    original_sales_order = fields.Many2many('sale.order', 
                                            string='Original Sale orders')
    sale_ordes = fields.Many2many('sale.order', string='Order IDs')
    sales_fake_line = fields.One2many('sale.order.line', 'manipulate_id',
                                      string='Order Lines')
    run_type = fields.Selection([
        ('percent', 'Run by Percentage'),
        ('fix', 'Fixed Amount'),
        ], string='Run Type', readonly=False, copy=False,
                                index=True,
                                track_visibility='onchange',
                                default='percent')
    state = fields.Selection([
        ('trigger', 'Modified'),
        ('done', 'done'),
        ], string='Run Type', readonly=False, copy=False,
                                index=True,
                                track_visibility='onchange',
                                default='trigger')

    overall_operation = fields.Boolean('Overall Trigger', default=True)

    """If the user checks overall trigger, it will run based on the
     percent or fixed amount: 
     This will affect the price_unit of each sale order lines"""

    @api.one
    def trigger_preview_changes(self):
        g = []
        line_ids = []
        orders = self.env['sale.order'].search([('state', '=', 'sale')])
        if orders:
            for rec in orders:
                if (self.start <= rec.date_order) and (self.end >= rec.date_order):# and (self.amount < rec.amount_total):   
                    g.append(rec.id)
                    self.write({'original_sales_order': [(4, rec.id)]})
                    for line in rec.order_line:
                        line_ids.append(line.id)
                    self.sales_fake_line = [(6, 0, line_ids)]
                    self.state = "done"
    
    @api.one
    def reset_back(self):
        self.value = 0
        for order_line in self.sales_fake_line:
            order_line.update({'preview_new_qty': order_line.product_uom_qty})

    @api.onchange('value')
    def preview_percentage(self):
        percent_amount = 0
        value = 0
        for order_line in self.sales_fake_line:
            if self.overall_operation == True:
                if self.run_type == "percent":
                    if (self.value) > 100 or (self.value < 0):
                        raise ValidationError('The value must be between the range 0 - 100')
                    if self.value > 0:
                        percent_qty = (self.value * order_line.product_uom_qty) / 100
                        deducted_qty = order_line.product_uom_qty - percent_qty
                        new_qty_unit = deducted_qty
                        order_line.update({'preview_new_qty': round(new_qty_unit), 
                                           'preview_total': new_qty_unit * order_line.price_unit,
                                           'tax_id': False})
                    elif self.value == 0:
                        order_line.update({'preview_new_qty': round(order_line.product_uom_qty), 
                                           'preview_total': order_line.product_uom_qty * order_line.price_unit,
                                           'tax_id': False})
                        
    @api.one
    def trigger_changes(self):
        percent_amount = 0
        value = 0
        for order_line in self.sales_fake_line:
            if self.overall_operation == True:
                order_line.update({'product_uom_qty': round(order_line.preview_new_qty)})

    # def create_fake_sales(self):
    #     sales_obj = self.env['sale.order']
    #     sales_line = self.env['sale.order.line']
    #     line_values = {}
    #     sale_dict = {}
    #     line_ids = []
    #     if self.original_sales_order:
    #         for sale in self.original_sales_order:
    #             sales_id = sales_obj.create({
    #                                         'partner_id': sale.partner_id.id,
    #                                         'date_order': sale.date_order,
    #                                         'payment_term_id': sale.payment_term_id.id,
    #                                         'fake_field': True,
    #                                         })
    #             for s_line in sale.order_line:
    #                 line_values['product_id'] = s_line.product_id.id
    #                 line_values['product_uom_qty'] = s_line.product_uom_qty
    #                 line_values['price_unit'] = s_line.price_unit
    #                 line_values['preview_price'] = s_line.price_unit
    #                 line_values['preview_total'] = s_line.price_total
    #                 line_values['name'] = s_line.name
    #                 line_values['tax_id'] = False
    #                 line_values['order_id'] = sales_id.id
    #                 line_values['fake_field'] = True
    #                 line_values['tampered'] = True
    #                 sol = sales_line.create(line_values)
    #                 line_ids.append(sol.id)
    #         self.sales_fake_line = [(6, 0, line_ids)]
    #         self.state = "done"
    
    # def Account_Move(self, sale_name, journal, date, narration, partner, amount):
    #     # branch = self.env.user.branch_id.id
    #     move_id = self.env['account.move'].create({'journal_id': journal.id, # bank.id,
    #                                                'ref': sale_name,
    #                                                'date': date,
    #                                                'fake_field': True,
    #                                                'narration': narration,
    #                                             #    'branch_id': branch
    #                                                })
    #     # create account.move.line for both debit and credit
    #     acc_move_line = self.env['account.move.line']
    #     line_id_dr = acc_move_line.with_context(check_move_validity=False).with_context(check_move_validity=False).create({
    #                                     'move_id': move_id.id,
    #                                     'ref': sale_name,
    #                                     'name': narration,
    #                                     'partner_id': partner,
    #                                     'account_id': journal.default_debit_account_id.id,
    #                                     # 'branch_id': branch,
    #                                     'debit': amount,
    #                                     # 'analytic_account_id': if any?
    #                     })

    #     line_id_cr = self.env['account.move.line'].with_context(check_move_validity=False).create({
    #                                     'move_id': move_id.id,
    #                                     'ref': sale_name,
    #                                     'name': narration,
    #                                     'partner_id': partner,
    #                                     'account_id': journal.default_credit_account_id.id,
    #                                     # 'branch_id': branch,
    #                                     'credit': amount,
    #                                     # 'analytic_account_id': if any ?
    #                     })
    #     """Code to push to Journal and payment follows up:
    #     Next thing is to register the payment to the respective journals,
    #     so there is need to add an optional Journal field on the wizard.
    #     If not, used the Journal type - SALE"""

    # @api.one
    # def confirm_faker(self):
    #     sale = []
    #     journal = self.env['account.journal'].search([('type', 'in', ['sale'])], limit=1)
    #     # item = sale.append(x.order_id.id for x in self.sales_fake_line)
    #     for rec in self.sales_fake_line:
    #         sale.append(rec.order_id.id) 

    #     sorted_item = [it for it, count in Counter(sale).items() if count > 1]
    #     for each in sorted_item:
    #         sale_order = self.env['sale.order'].browse([each])
    #         sale_name = str(sale_order.name)
    #         partner = sale_order.partner_id.id
    #         date = sale_order.date_order
    #         narration = "SM"
    #         amount = sale_order.amount_total
    #         '''each sales append the order_id, pick the total amount and create move'''
    #         self.Account_Move(sale_name, journal, date, narration, partner, amount)
        
    #     for original in self.original_sales_order:
    #         original.write({'tampered': True, 'active':False})
    #         for original_line in original:
    #             original.write({'active':False})
                
        
class AcocuntPaymentFake(models.Model):
    _inherit = "account.payment"

    fake_field = fields.Boolean('Null', default=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    fake_field = fields.Boolean('Null', default=False)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    fake_field = fields.Boolean('Null', default=False)


class AccountInvoiceFake(models.Model):
    _inherit = "account.invoice"

    fake_field = fields.Boolean('Null', default=False)

    """
    Format for account transaction
        incoming 500 ==> original 500 + (incoming 500 - incoming500) = 500
    """


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    fake_field = fields.Boolean('Apply Restrict', default=True)
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True, 
                                   default=lambda self: self.env['account.journal'].search([('fake_field', '=', True)])\
                                        if self.fake_field == True else self.env['account.journal'].search([]))
    target_move = fields.Selection([('posted', 'Entries'),
                                    ('all', 'All Entries'),
                                    ('draft', 'All Posted'),
                                    ], string='Target Moves', required=True, default='draft')

    def _build_contexts(self, data):
        result = super(AccountCommonReport, self)._build_contexts(data)
        data = {}
        data['form'] = self.read(['fake_field'])[0]
        result['fake_field'] = 'fake_field' in data['form'] and data['form']['fake_field'] or False
        return result
 
    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'fake_field'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
        return self._print_report(data)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
