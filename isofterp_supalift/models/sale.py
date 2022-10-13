from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
import logging
_logger = logging.getLogger(__name__)



class SaleOrderExt(models.Model):
    _inherit = 'sale.order'

    # x_equipment_id = fields.Many2one(related='task_id.x_equipment_id', string='Equipment')
    x_equipment_id = fields.Many2one('maintenance.equipment', 'Equipment',
                                     domain="[('partner_id','=', partner_id)]")
    x_meter_reading = fields.Integer('Meter Reading')
    x_branch_id = fields.Integer('Old Branch')

    # If the Sales Order is linked to a job card, change the state of the job card to quoted
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
            # If the task is in a completed state and being quoted, change state to "Awaiting PO"
            # else its quoted
            if self.task_custom_id.stage_id.name == "Completed":
                new_stage = self.env['project.task.type'].search([('name', '=', 'Awaiting PO')])
            else:
                new_stage = self.env['project.task.type'].search([('name', '=', 'Quoted')])
            #if self.task_custom_id.stage_id.sequence < new_stage.sequence:
            self.task_custom_id.stage_id = new_stage.id
            #print("**kwargs", kwargs)
            #_logger.warning("The SO is %s", stage_id.name)
            self.task_custom_id.message_post(**kwargs)
            #raise UserError(_('STOP HERE QUICK '))
        return super(SaleOrderExt, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def action_confirm(self):
        if not self.client_order_ref:
            raise UserError(_(
                "You cannot confirm the Sales Order without a valid Client Purchase Order."))
        else:
            # The below code has been commented on 2022-03-30
            # Christine indicated that CPT branch allows multiple jobs to be allocated to the same
            # purchase order number
            # #Perhaps we need to check if the PO number had already been allocated to another order for the same client
            # # Provided the sales order has not been cancelled
            # sales_order = self.env['sale.order'].search([('client_order_ref','=',self.client_order_ref ),
            #                                              ('state','!=', 'cancel'),
            #                                              ('partner_id', '=', self.partner_id.id),
            #                                              ('name', '!=', self.name)])
            # if sales_order:
            #     raise UserError(_(
            #         "Purchase Order already captured against Sales Order (%s) PO (%s)") % (sales_order.name, sales_order.client_order_ref))
            # else:
            res = super(SaleOrderExt, self).action_confirm()
            # if the current stage of the job is Completed and becuase an order number is entered move job to completed
            # else it will be in WIP

            # If taks was in Awaiting PO and order number is entered, and meter reading reading has been entered
            # It has to move to closing stage:


            if self.task_custom_id.stage_id.name == "Completed":
                stage_id = self.env['project.task.type'].search([('name', '=', 'Closed')])
            else:
                stage_id = self.env['project.task.type'].search([('name', '=', 'WIP')])

            if self.task_custom_id.stage_id.name == "Awaiting PO":
                stage_id = self.env['project.task.type'].search([('name', '=', 'Closed')])

            if self.task_custom_id.stage_id == stage_id.id:
                msg = _(
                    """Purchase Order Received - Job state already in WIP  <strong>{po_number}</strong>
                    """.format(
                        po_number=self.client_order_ref,
                    )
                )
            else:
                _logger.warning("The SO is %s", stage_id.name)
                msg = _(
                    """Purchase Order Received - Changing state from <strong>{cur_state} to WIP. PO Number: <strong>{po_number}</strong>
                    """.format(
                        po_number=self.client_order_ref,
                        cur_state = self.task_custom_id.stage_id.name
                    )
                )
                self.task_custom_id.stage_id = stage_id.id
            self.task_custom_id.message_post(body=msg)
            return res

    def _prepare_invoice(self):
        res = super(SaleOrderExt, self)._prepare_invoice()
        res['x_equipment_id'] = self.x_equipment_id.id
        res['x_task_id'] = self.task_custom_id.id
        return res

    def write(self,values):
        logging.warning("PO Number is %s %s", self.client_order_ref, values)
        if self.state == 'sale' and values.get('client_order_ref') == False:
            raise UserError(_(
                "Client Purchase Order has not been captured."))
        result = super(SaleOrderExt, self).write(values)
        return result



    # The below functions were all used to set certain fields on an existing database
    # These will not be needed anymore so comment them for the time being



    # def copy_branch_field_sales(self):
    #     orders = self.env['sale.order'].search([])
    #     for order in orders:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in orders:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_sales_lines(self):
    #     orders = self.env['sale.order.line'].search([])
    #     for order in orders:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in orders:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_purchase(self):
    #     orders = self.env['purchase.order'].search([])
    #     for order in orders:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in orders:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_purchase_lines(self):
    #     orders = self.env['purchase.order.line'].search([])
    #     for order in orders:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in orders:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_invoices(self):
    #     invoices = self.env['account.move'].search([])
    #     for order in invoices:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in invoices:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_invoices_lines(self):
    #     invoices = self.env['account.move.line'].search([])
    #     for order in invoices:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in invoices:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_stock_pick(self):
    #     picks = self.env['stock.picking'].search([])
    #     for order in picks:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in picks:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_stock_move(self):
    #     moves = self.env['stock.move'].search([])
    #     for order in moves:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in moves:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_projects(self):
    #     project = self.env['project.project'].search([])
    #     for order in project:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in project:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_tasks(self):
    #     task = self.env['project.task'].search([])
    #     for order in task:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in task:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_users(self):
    #     users = self.env['res.users'].search([])
    #     for order in users:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in users:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_locations(self):
    #     locations = self.env['stock.location'].search([])
    #     for order in locations:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in locations:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def copy_branch_field_warehouse(self):
    #     warehouses = self.env['stock.warehouse'].search([])
    #     for order in warehouses:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in warehouses:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)
    #
    # def set_branchon_invoices(self):
    #     invoices = self.env['account.move'].search([('branch_id', '=', 1),('move_type','=','in_invoice')])
    #     if invoices:
    #         for inv in invoices:
    #             _logger.warning("Invoice is %s %s" , inv.id, inv.name)
    #             #inv.branch_id = 2
    #             for inv_line in inv.invoice_line_ids:
    #                 inv_line.branch_id = inv.branch_id.id
    #
    # def set_branch_on_task_lines(self):
    #     task_lines = self.env['task.custom.lines'].search([])
    #     for lines in task_lines:
    #         _logger.warning("Line is %s %s", lines.task_custom_id.branch_id.name, lines.task_custom_id.name)
    #         lines.branch_id = lines.task_custom_id.branch_id.id
    # def copy_branch_field_sequence(self):
    #     sequences = self.env['ir.sequence'].search([])
    #     for order in sequences:
    #         _logger.warning("The order is {%s} and branch {%s} and ID {%s}", order.name, order.branch_id.name,
    #                         order.branch_id.id)
    #         order.branch_id = order.x_branch_id
    #     for order in sequences:
    #         _logger.warning("The order is {%s} and old-branch {%s} and new-branch {%s}", order.name, order.branch_id.id,
    #                         order.x_branch_id)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_branch_id = fields.Integer('Old Branch')

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv

        # remove the no_variant attributes that don't belong to this template
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        #vals.update(name=self.get_sale_order_line_multiline_description_sale(product))
        vals.update(name=product.code or product.name)

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
        self.update(vals)


        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s", product.name)
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result



    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        return