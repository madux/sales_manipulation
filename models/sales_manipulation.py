

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

    difference = fields.Float('Difference', store=True)
    manipulate_id = fields.Many2one('sale_fake.wizards', string= 'Manipulated ref')


class SaleOrders(models.Model):
    _inherit = "sale.order"

    fake_field = fields.Boolean('Apply Fake', default=False)
    active = fields.Boolean('Active', default=True)
    manipulate_id = fields.Many2one('sale_fake.wizards', string= 'Manipulated ref')
    @api.multi
    def _prepare_invoice(self):
        vals = super(SaleOrders, self)._prepare_invoice() 
        if self.fake_field == True:
            vals.update({'fake_field': True})
        return vals


class CommissionWizard(models.Model):
    _name = "sale_fake.wizards"
    _rec_name = "id"

    start = fields.Datetime('Start Date', required=True)
    end = fields.Datetime('End Date', required=True)
    amount = fields.Float('Amount Above', store=True)
    value = fields.Float('Value', required=True,
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

    overall_operation = fields.Boolean('Overall Trigger', default=True)

    """If the user checks overall trigger, it will run based on the
     percent or fixed amount: 
     This will affect the price_unit of each sale order lines"""

    @api.one
    def trigger_preview_changes(self): 
        orders = self.env['sale.order'].search([('state', 'not in', ['draft','open'])])  
        item = []
        original_item = [] 
        value = 0
        for rec in orders:
            if parse(self.start) <= parse(rec.date_order) and parse(self.end) >= parse(rec.date_order) and self.amount < rec.amount_total:
                original_item.append(rec.id)
                self.write({'original_sales_order': [(4, original_item)]})
        self.create_fake_sales()
                # copy_sales = rec.copy({'state':'draft', 'fake_field': True})
                # item.append(copy_sales.id)
                # self.write({'mani_sales_order': [(4, item)]})

    def create_fake_sales(self):
        sales_obj = self.env['sale.order']
        sales_line = self.env['sale.order.line']
        line_values = {}
        sale_dict = {}
        line_ids = []
        if self.original_sales_order:
            for sale in self.original_sales_order:
                sales_id = sales_obj.create({
                                            'partner_id': sale.partner_id.id,
                                            'date_order': sale.date_order,
                                            'payment': sale.payment_term_id.id,
                                            'fake_field': True,
                                            'branch_id' : self.env.user.branch_id.id
                                            })
                sale.write({'active': False})
                self.sale_ordes = [(6, 0, [sales_id.id])]
                
                for s_line in sale.order_line:
                    line_values['product_id'] = s_line.product_id.id
                    line_values['product_uom_qty'] = s_line.product_uom_qty
                    line_values['price_unit'] = s_line.price_unit
                    line_values['name'] = s_line.name
                    line_values['tax_id'] = s_line.tax_id
                    line_values['order_id'] = sales_id.id
                    sol = sales_line.create(line_values)
                    line_ids.append(sol.id) 
                    self.sales_fake_line = [(6, 0, line_ids)]

    @api.one
    def trigger_changes(self):
        percent_amount = 0
        value = 0
        for order_line in self.sales_fake_line:
            if self.overall_operation == True:
                if self.run_type == "percent":
                    if self.value < 0:
                        raise ValidationError('Please enter Value greater than 0')
                        '''For each of the manipulate sales_orders, go into the orderlines
                        and change the items by the enter percentage value'''
                    else:
                        percent_amount = (order_line.price_unit * self.value) / 100
                        amount = order_line.price_unit - percent_amount
                        order_line.update({'price_unit': amount})
                        
    def Account_Move(self, sale_name, journal, date, narration, partner, amount):
        branch = self.env.user.branch_id.id
        move_id = self.env['account.move'].create({'journal_id': journal.id, # bank.id,
                                                   'ref': sale_name,
                                                   'date': date,
                                                   'fake_field': True,
                                                   'narration': narration,
                                                   'branch_id': branch})
        # create account.move.line for both debit and credit
        acc_move_line = self.env['account.move.line']
        line_id_dr = acc_move_line.with_context(check_move_validity=False).with_context(check_move_validity=False).create({
                                        'move_id': move_id.id,
                                        'ref': sale_name,
                                        'name': narration,
                                        'partner_id': partner,
                                        'account_id': journal.default_debit_account_id.id,
                                        'branch_id': branch,
                                        'debit': amount,
                                        # 'analytic_account_id': if any?
                        })

        line_id_cr = self.env['account.move.line'].with_context(check_move_validity=False).create({
                                        'move_id': move_id.id,
                                        'ref': sale_name,
                                        'name': narration,
                                        'partner_id': partner,
                                        'account_id': journal.default_credit_account_id.id,
                                        'branch_id': branch,
                                        'credit': amount,
                                        # 'analytic_account_id': if any ?
                        })
        """Code to push to Journal and payment follows up:
        Next thing is to register the payment to the respective journals,
        so there is need to add an optional Journal field on the wizard.
        If not, used the Journal type - SALE"""

    @api.multi
    def confirm_faker(self):
        journal = self.env['account.journal'].search([('type', 'in', ['sale'])], limit=1)
        if self.sale_ordes:
            for each in self.sale_ordes:
                sale_name = str(each.name)
                partner = each.partner_id.id
                date = each.date_order
                narration = "SM"
                amount = each.amount_total
                '''each sales append the order_id, pick the total amount and create move'''
                self.Account_Move(sale_name, journal, date, narration, partner, amount)


class AcocuntPaymentFake(models.Model):
    _inherit = "account.payment"

    fake_field = fields.Boolean('Apply Fake', default=False)


class AccountMove(models.Model):
    _inherit = "account.move"

    fake_field = fields.Boolean('Apply Fake', default=False)


class AccountInvoiceFake(models.Model):
    _inherit = "account.invoice"

    fake_field = fields.Boolean('Apply Fake', default=False)

    """
    Format for account transaction
        incoming 500 ==> original 500 + (incoming 500 - incoming500) = 500
    """