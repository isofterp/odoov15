# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):
    _description = "Task"
    _inherit = 'project.task'

    # @api.onchange("partner_id")
    # def check_due(self):
    #     #print(err)
    #     _logger.warning("******This line is firing")
    #     today = datetime.now().date()
    #     inv_ids = self.env['account.move'].search(['&', '&', '&', '&', ('partner_id', '=', self.partner_id.id), ('state', '=', 'posted'),
    #                            ('move_type', '=', 'out_invoice'), ('invoice_date_due', '<', today),('payment_state','=', 'not_paid')])
    #     if inv_ids:
    #         raise Warning(
    #             "You can not create invoice for this Customer. This customer already has one or more overdue invoices.")
    #     """To show the due amount and warning stage"""
        # partner = self.env['res.partner'].search([('id','=',self.partner_id.id)])
        # #print('amt due',partner.due_amount)
        # if self.partner_id and partner.total_due > partner.credit_limit:
        #     # user id has been replaced with user_ids (multiple assignees)
        #     self.user_ids = False
        #     title = ("Warning for %s") % partner.name
        #     message = "Has exceeded Credit Limit"
        #     warning = {
        #         'title': title,
        #         'message': message,
        #
        #     }
        #     return {'warning': warning}

    @api.onchange('x_serial_number_id')
    def onchange_serial_umber(self):
        #print('onchange_serial_umber')
        self.partner_id = self.x_serial_number_id.x_subscription_id.partner_id
        self.x_serial_number_street = self.x_serial_number_id.x_subscription_id.partner_id.street
        #self.x_serial_number_street2 = self.x_serial_number_id.x_subscription_id.partner_id.street2
        if self.x_serial_number_id.x_dlv_id.street and  self.x_serial_number_id.x_dlv_id.street2 and self.x_serial_number_id.x_dlv_id.city:
            self.x_serial_number_street2 = self.x_serial_number_id.x_dlv_id.street + '\n' + \
                                           self.x_serial_number_id.x_dlv_id.street2 + '\n' + \
                                           self.x_serial_number_id.x_dlv_id.city
        # self.x_serial_number_email = self.x_serial_number_id.x_subscription_id.partner_id.email
        # self.x_serial_number_phone = self.x_serial_number_id.x_subscription_id.partner_id.phone
        # self.x_serial_number_mobile = self.x_serial_number_id.x_subscription_id.partner_id.mobile
        return

    @api.onchange('x_black_copies', 'x_color_copies')
    def onchange_readings(self):
        # print('23',)
        if not self.x_serial_number_id and (self.x_black_copies or self.x_color_copies):
            raise UserError(
                _('You cannot enter Meter Readings without a Serial Number!.\nPlease enter a Serial Number first and try again'))
            return
        line_ids = self.env['sale.subscription.line'].search([('x_serial_number_id', '=', self.x_serial_number_id.id)])
        if line_ids:
            for line in line_ids:
                if line.name == 'Black copies' and self.x_black_copies > 0:
                    # if self.x_black_copies < line.x_copies_last:
                    #     raise UserError(_(
                    #         'You cannot enter Black Meter Readings less than Previous Reading'))
                    #     return
                    line.write({'x_copies_last': self.x_black_copies})
                if line.name == 'Colour copies' and self.x_color_copies > 0:
                    if self.x_color_copies < line.x_copies_last:
                        raise UserError(_(
                            'You cannot enter Colour Meter Readings less than Previous Reading'))
                        return
                    line.write({'x_copies_last': self.x_color_copies})
        return

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s (# %s)" % (record.name, record.id)))
        return result

    def _fsm_create_sale_order(self):
        """ Create the SO from the task, with the 'service product' sales line and link all timesheet to that line it """
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_('A customer should be set on the task to generate a worksheet.'))

        SaleOrder = self.env['sale.order']
        if self.user_has_groups('project.group_project_user'):
            SaleOrder = SaleOrder.sudo()

        # TDE note: normally company comes from project, user should be in same company
        # and _get_default_team_id already enforces company coherency + match
        # Sale.onchange_user_id() that also calls _get_default_team_id
        # Use the first assignee
        user_id = self.user_ids[0] if self.user_ids else self.env['res.users']
        team = self.env['crm.team'].sudo()._get_default_team_id(user_id=user_id.id, domain=None)
        sale_order = SaleOrder.create({
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'task_id': self.id,
            'analytic_account_id': self._get_task_analytic_account_id().id,
            'team_id': team.id if team else False,
            'x_lot_id': self.x_serial_number_id.id,
        })
        sale_order.onchange_partner_id()
        # invoking onchange_partner_shipping_id to update fiscal position
        sale_order.onchange_partner_shipping_id()
        # update after creation since onchange_partner_id sets the current user
        sale_order.user_id = user_id.id
        sale_order.onchange_user_id()

        self.sale_order_id = sale_order

    name = fields.Char(placeholder="Problem Details")
    x_serial_number_id = fields.Many2one('stock.production.lot', 'Serial Number')
    x_serial_number_name = fields.Char(related='x_serial_number_id.product_id.name', string='Machine Description')
    x_serial_number_dlv = fields.Many2one(related='x_serial_number_id.x_dlv_id', string='Machine Address')
    x_serial_number_street = fields.Char(related='x_serial_number_id.x_dlv_id.street')
    x_serial_number_street2 = fields.Char(related='x_serial_number_id.x_dlv_id.street2')
    x_serial_number_zip = fields.Char()
    x_serial_number_email = fields.Char()
    x_serial_number_phone = fields.Char()
    x_serial_number_mobile = fields.Char()
    x_black_copies = fields.Integer('Last Reading Black')
    x_color_copies = fields.Integer('Last Reading Color')
    x_rental_group = fields.Char(related='x_serial_number_id.x_subscription_id.x_rental_group_id.name',
                                 string="Rental Group")
    x_invoice_warn = fields.Text(related='partner_id.invoice_warn_msg', string='Warning')
    x_problem_type = fields.Many2one('fsm.problem.type', 'Problem Type')
    x_cust_rep = fields.Char('Customer Representative')
    x_project_task_template_id = fields.Many2one('project.task.template', 'Job Card Template')

    def _compute_line_data_for_template_change(self, line):
        return {
            'product_id': line.product_id.id,
            'product_qty':line.product_uom_qty,
            'product_uom': line.product_uom_id.id,
            'location_id':self.project_id.location_id.id,
            'location_dest_id': self.project_id.location_dest_id.id,
            'picking_type_id': self.project_id.picking_type_id.id,
            'name':self.name

        }
    @api.onchange('x_project_task_template_id')
    def onchange_x_project_task_template_id(self):
        logging.warning("============= RUNNING ON CHANGE")
        if not self.x_project_task_template_id:
            return

        template = self.x_project_task_template_id.with_context(lang=self.partner_id.lang)

        # --- first, process the list of products from the template
        parts_lines = [(5, 0, 0)]
        for line in template.task_template_line_ids:
            data = self._compute_line_data_for_template_change(line)

            if line.product_id:
                price = line.product_id.lst_price



                data.update({
                    'product_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,

                })

            parts_lines.append((0, 0, data))

        self.move_ids = parts_lines

class FSMProblemType(models.Model):
    _description = "FSM Problem Type"
    _name = "fsm.problem.type"
    _order = 'name'

    name = fields.Char("Problem Type")
