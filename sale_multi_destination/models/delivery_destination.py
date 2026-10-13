from odoo import fields, models


class SaleOrderDeliveryDestination(models.Model):
    _name = 'sale.order.delivery.destination'
    _description = 'Sales Order Delivery Destination'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales Order',
        required=True,
        ondelete='cascade',
    )

    order_partner_id = fields.Many2one(
        comodel_name='res.partner',
        related='order_id.partner_id',
        string='Customer',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Delivery Address',
        required=True,
        domain="[('type', '=', 'delivery'), ('parent_id', '=', order_partner_id)]",
    )

    name = fields.Char(
        string='Destination Name',
        required=True,
    )

    delivery_line_ids = fields.One2many(
        comodel_name='sale.order.delivery.line',
        inverse_name='destination_id',
        string='Products',
    )




