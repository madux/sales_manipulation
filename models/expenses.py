from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
import time
import datetime


class SM_Expenses(models.Model):
    _name = "sm.expenses"
    _rec_name = "id"

    def _default_partner(self):
        lists= []
        partner_obj = self.env['res.partner']
        partner = partner_obj.search([('name','=', 'Random Customer')])
        if partner:
            lists.append(partner.id)
        else:
            part = partner_obj.create({'supplier':True, 'name':'Random Customer'})
            lists.append(part.id)
        return partner_obj.search(
            [('name', '=', 'Random Customer')], limit=1)
            
    start = fields.Datetime('Date', required=True) 
    amount = fields.Float('Amount Above', store=True)
    description = fields.Char('Item Description', required=True) 
    note = fields.Char('Notes', required=True) 
    state = fields.Selection([
        ('draft', 'New'),
        ('done', 'done'),
        ], string='State', readonly=False, copy=False,
                                index=True,
                                track_visibility='onchange',
                                default='draft')

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, 
                                  )
    partner_id = fields.Many2one('res.partner', string='Vendor', 
                              required=True, default=_default_partner)

    def Confirm_Expenses(self):
        journal = self.journal_id.id # or self.env['account.journal'].search([('type', 'in', ['purchase'])], limit=1)
        acm = self.env['account.payment.method'].create(
                {'payment_type': 'outbound', 'name': 'Payment For '+self.description, 'code': str(self.description)})
        payment_data = {
            'amount': self.amount, 
            'payment_date': fields.Date.today(),
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'journal_id': journal,  
            'narration': "EXP - For" + self.description,
            'payment_method_id': acm.id, 
                        }
        payment_model = self.env['account.payment'].create(payment_data).post()
        self.state = 'done'
    
