from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_destination_ids = fields.One2many(
        comodel_name='sale.order.delivery.destination',
        inverse_name='order_id',
        string='Delivery Destinations',
    )

    def _split_pickings_by_destination(self):
        for order in self:
            allocations = order.delivery_destination_ids.mapped(
                'delivery_line_ids'
            )

            pickings = order.picking_ids.filtered(
                lambda p: (
                        p.picking_type_id.code == 'outgoing'
                        and p.state not in ('done', 'cancel')
                        and not p.delivery_destination_id
                )
            )

            for picking in pickings:
                moves = picking.move_ids.filtered(
                    lambda m: (
                            m.sale_line_id
                            and m.state not in ('done', 'cancel')
                    )
                )

                move_allocations = {}
                for move in moves:
                    lines = allocations.filtered(
                        lambda a: a.sale_line_id == move.sale_line_id
                    )
                    if lines:
                        move_allocations[move.id] = (move, lines)

                if not move_allocations:
                    continue

                destinations = self.env[
                    'sale.order.delivery.destination'
                ]

                for move, lines in move_allocations.values():
                    destinations |= lines.mapped('destination_id')

                destinations = destinations.sorted('id')

                # Dùng picking hiện tại cho địa chỉ đầu tiên.
                picking.write({
                    'delivery_destination_id': destinations[0].id,
                    'partner_id': destinations[0].partner_id.id,
                })

                destination_pickings = {
                    destinations[0].id: picking,
                }

                # Tạo thêm picking cho các địa chỉ còn lại.
                for destination in destinations[1:]:
                    new_picking = picking.copy({
                        'name': '/',
                        'move_ids': [],
                        'partner_id': destination.partner_id.id,
                        'delivery_destination_id': destination.id,
                    })
                    destination_pickings[destination.id] = new_picking

                new_moves = self.env['stock.move']

                for move, lines in move_allocations.values():
                    lines = lines.sorted(
                        key=lambda a: a.destination_id.id
                    )

                    for index, allocation in enumerate(lines):
                        quantity = allocation.sale_line_id.product_uom._compute_quantity(
                            allocation.quantity,
                            move.product_uom,
                            round=False,
                        )

                        target_picking = destination_pickings[
                            allocation.destination_id.id
                        ]

                        if index == 0:
                            # Tái sử dụng move hiện tại, không tạo trùng.
                            move.write({
                                'picking_id': target_picking.id,
                                'product_uom_qty': quantity,
                                'delivery_destination_id': (
                                    allocation.destination_id.id
                                ),
                            })
                        else:
                            # Tạo move cho phần phân bổ còn lại.
                            new_move = move.copy({
                                'picking_id': target_picking.id,
                                'product_uom_qty': quantity,
                                'delivery_destination_id': (
                                    allocation.destination_id.id
                                ),
                                'move_line_ids': [(5, 0, 0)],
                            })
                            new_moves |= new_move

                if new_moves:
                    new_moves._action_confirm(merge=False)

    def action_confirm(self):
        Allocation = self.env['sale.order.delivery.line']

        for order in self:
            if not order.delivery_destination_ids:
                raise ValidationError(
                    "Please add at least one delivery destination before confirming."
                )

            order_lines = order.order_line.filtered(
                lambda line: not line.display_type # các dòng tiêu đề và ghi chú có display_type nên not thì lọc đc sp
            )

            for sale_line in order_lines: # lặp qua từng sp đã lọc đc ở trên
                allocations = Allocation.search([
                    ('sale_line_id', '=', sale_line.id),
                    ('destination_id.order_id', '=', order.id),
                ])

                allocated_quantity = sum(
                    allocations.mapped('quantity')
                )

                ordered_quantity = sale_line.product_uom_qty

                if float_compare(
                        allocated_quantity,
                        ordered_quantity,
                        precision_rounding=sale_line.product_uom.rounding,
                ) != 0:
                    raise ValidationError(
                        f"Product: {sale_line.product_id.display_name}\n"
                        f"Ordered quantity: {ordered_quantity}\n"
                        f"Allocated quantity: {allocated_quantity}\n"
                        "The allocated quantity must equal the ordered quantity."
                    )

        result = super().action_confirm()
        self._split_pickings_by_destination()
        return result
