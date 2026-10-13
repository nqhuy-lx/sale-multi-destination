{
    'name': 'Sales Multi-Destination Delivery',
    'version': '18.0.1.0.0',
    'summary': 'Deliver one sales order to multiple destinations',
    'depends': [
        'sale_stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
}