from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    delivery_destination_id = fields.Many2one(
        comodel_name='sale.order.delivery.destination',
        string='Delivery Destination',
        copy=False,
        index=True,
    )
