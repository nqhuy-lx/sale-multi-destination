from odoo import fields, models, api
from odoo.exceptions import ValidationError

class SaleOrderDeliveryLine(models.Model):
    _name = 'sale.order.delivery.line'
    _description = 'Sales Order Delivery Line'

    destination_id = fields.Many2one(
        comodel_name='sale.order.delivery.destination',
        string='Delivery Destination',
        required=True,
        ondelete='cascade',
    )

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales Order',
        related='destination_id.order_id',
        store=True,
        readonly=True,
    )

    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sales Order Line',
        required=True,
        ondelete='restrict'
    )

    quantity = fields.Integer(
        string='Allocated Quantity',
        required=True,
        default=1
    )

    ordered_quantity = fields.Float(
        string='Ordered Quantity',
        related='sale_line_id.product_uom_qty',
        readonly=True
    )

    remaining_quantity = fields.Float(
        string='Remaining',
        compute='_compute_remaining_quantity',
        readonly=True
    )

    @api.depends(
        'sale_line_id',
        'destination_id',
        'quantity',
        'destination_id.order_id.delivery_destination_ids.delivery_line_ids.quantity',
        'destination_id.order_id.delivery_destination_ids.delivery_line_ids.sale_line_id')
    def _compute_remaining_quantity(self):
        print("============================test")
        for line in self:
            if not line.sale_line_id or not line.destination_id:
                line.remaining_quantity = 0
                continue

            order = line.destination_id.order_id
            sale_line = line.sale_line_id

            total_allocated = sum(
                order.delivery_destination_ids
                .mapped('delivery_line_ids')
                .filtered(lambda allocation: allocation.sale_line_id == sale_line)
                .mapped('quantity')
            )

            line.remaining_quantity = (sale_line.product_uom_qty - total_allocated)

    @api.constrains('quantity')
    def _check_quantity_positive(self):
        for line in self:
            if line.quantity <= 0 or line.remaining_quantity < 0:
                raise ValidationError(
                    f"Invalid quantity in destination name: {line.destination_id.name}"
                )
