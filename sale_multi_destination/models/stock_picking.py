from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_destination_id = fields.Many2one(
        comodel_name='sale.order.delivery.destination',
        string='Delivery Destination',
        copy=False,
    )
