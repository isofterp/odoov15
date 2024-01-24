import logging


from odoo import api, fields, models, _
from collections import defaultdict
_logger = logging.getLogger(__name__)


class productTemplate(models.Model):
    _inherit = "product.template"

    x_machine_charge_ids  = fields.One2many('subscription.machine.charge', 'product_key','Master Charges')
    x_optional_component_ids = fields.Many2many(
        'product.template', 'product_component_rel', 'src_id', 'dest_id',
        string='Optional Products', help="Optional Components are suggested .", check_company=True)
    x_alternate_product_ids = fields.Many2many(
        'product.template', 'product_alternate_rel', 'src_id', 'dest_id',
        string='Alnternate Products', help="Alternate Products .", check_company=True)
    x_invoice_ok = fields.Boolean(string="Cannot be Invoiced", help='If set the product will not be Invoiced')
    x_kit = fields.Boolean(string="KIT")
    x_kit_quantity = fields.Integer(string="How many quantities of an item to make up a kit")

class Task(models.Model):
    _inherit = "project.task"

    x_sale_subscription_id = fields.Many2one('sale_subscription', 'Enter Serial Number')

# Function is used to add serial number to the sales quotation when selecting a product
# Do I need to worry if it already exist on the quotation? Don't think so
class ProductProduct(models.Model):
    _inherit = "product.product"


    def _inverse_fsm_quantity(self):
        task = self._get_contextual_fsm_task()
        if task:
            SaleOrderLine_sudo = self.env['sale.order.line'].sudo()
            sale_lines_read_group = SaleOrderLine_sudo.read_group([
                ('order_id', '=', task.sale_order_id.id),
                ('product_id', 'in', self.ids),
                ('task_id', '=', task.id)],
                ['product_id', 'sequence', 'ids:array_agg(id)'],
                ['product_id', 'sequence'],
                lazy=False)
            sale_lines_per_product = defaultdict(lambda: self.env['sale.order.line'])
            for sol in sale_lines_read_group:
                sale_lines_per_product[sol['product_id'][0]] |= SaleOrderLine_sudo.browse(sol['ids'])
            for product in self:
                sale_lines = sale_lines_per_product.get(product.id, self.env['sale.order.line'])
                all_editable_lines = sale_lines.filtered(
                    lambda l: l.qty_delivered == 0 or l.qty_delivered_method == 'manual' or l.state != 'done')
                diff_qty = product.fsm_quantity - sum(sale_lines.mapped('product_uom_qty'))
                if all_editable_lines:  # existing line: change ordered qty (and delivered, if delivered method)
                    if diff_qty > 0:
                        vals = {
                            'product_uom_qty': all_editable_lines[0].product_uom_qty + diff_qty,
                        }
                        if all_editable_lines[0].qty_delivered_method == 'manual':
                            vals['qty_delivered'] = all_editable_lines[0].product_uom_qty + diff_qty
                        all_editable_lines[0].with_context(fsm_no_message_post=True).write(vals)
                        all_editable_lines[0].product_uom_change()
                        continue
                    # diff_qty is negative, we remove the quantities from existing editable lines:
                    for line in all_editable_lines:
                        new_line_qty = max(0, line.product_uom_qty + diff_qty)
                        diff_qty += line.product_uom_qty - new_line_qty
                        if line.product_uom_qty != new_line_qty:
                            vals = {
                                'product_uom_qty': new_line_qty
                            }
                            if line.qty_delivered_method == 'manual':
                                vals['qty_delivered'] = new_line_qty
                            line.with_context(fsm_no_message_post=True).write(vals)
                            line.product_uom_change()
                        if diff_qty == 0:
                            break
                elif diff_qty > 0:  # create new SOL
                    vals = {
                        'order_id': task.sale_order_id.id,
                        'product_id': product.id,
                        'product_uom_qty': diff_qty,
                        'product_uom': product.uom_id.id,
                        'task_id': task.id,
                    }
                    if product.service_type == 'manual':
                        vals['qty_delivered'] = diff_qty

                    if task.sale_order_id.pricelist_id.discount_policy == 'without_discount':
                        sol = SaleOrderLine_sudo.new(vals)
                        sol._onchange_discount()
                        vals.update({'discount': sol.discount or 0.0})
                    _logger.warning("**************** Calling this function")
                    sale_line = SaleOrderLine_sudo.create(vals)
                    logging.warning("sale Line order id is %s", task.sale_order_id.name)
                    #sale_line.order_id.x_lot_id = task.x_serial_number_id.id
                    ana_id = self.env['account.analytic.account'].search([('name', '=', task.x_serial_number_id.name)]).id
                    task.sale_order_id.write({'x_lot_id': task.x_serial_number_id.id,
                                              'analytic_account_id':ana_id })

                    if not sale_line.qty_delivered_method == 'manual':
                        sale_line.qty_delivered = 0
