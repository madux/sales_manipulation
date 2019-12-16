# -*- coding: utf-8 -*-
{
    'name': 'Sales Manipulation',
    'version': '1.0',
    'author': 'Maach Services',
    'description': """Sales Manipulation for odoo""",
    'summary': 'The module allows sales manager to manipulate a sale records',
    'category': 'Base',
    # 'live_test_url': "https://www.youtube.com/watch?v=KEjxieAoGeA&feature=youtu.be" om_account_accountant,

    'depends': ['base','purchase','stock', 'account','sale_management', 'om_account_accountant', 'l10n_uk'],
    'data': [
        
        'security/security_group.xml', 
        # 'views/account_common_report.xml',
        'security/ir.model.access.csv',
        'report/sales_report.xml',
        'report/sale_paper_report.xml',
        'wizard/sales_wizard_view.xml',
        'views/expenses_sm.xml',
        
        'views/sales_manipulation_view.xml',
    ],
    # 'qweb': [
    #     'static/src/xml/base.xml',
    # ],
    'price': 1000.00,
    'sequence': 2,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
