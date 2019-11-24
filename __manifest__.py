# -*- coding: utf-8 -*-
{
    'name': 'Sales Manipulation',
    'version': '1.0',
    'author': 'Maach Services',
    'description': """Sales Manipulation for odoo""",
    'summary': 'The module allows sales manager to manipulate a sale records',
    'category': 'Base',
    # 'live_test_url': "https://www.youtube.com/watch?v=KEjxieAoGeA&feature=youtu.be",

    'depends': ['base', 'account', 'sale'],
    'data': [
        'security/security_group.xml', 
        'views/sales_manipulation_view.xml',
        'security/ir.model.access.csv',
    ],
    # 'qweb': [
    #     'static/src/xml/base.xml',
    # ],
    'price': 1000.00,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
}
