# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):
    _description = "Task"
    _inherit = 'project.task'

    @api.model_create_multi
    def create(self, vals_list):
        logging.warning("Vals list is %s", vals_list[0])
        if vals_list[0].get('x_serial_number_id'):
            logging.warning("1-----Setting flags on this record")
            ten_days_ago = datetime.now() - timedelta(days=10)
            logging.warning("10 days ago %s %s", ten_days_ago.strftime('%Y-%m-%d'), vals_list[0].get('x_serial_number_id'))
            tickets = self.env['project.task'].search([('x_serial_number_id','=', vals_list[0].get('x_serial_number_id')),('create_date','>=',ten_days_ago)])
            if len(tickets) >= 3:
                logging.warning("2-----Setting flags on this record")
                vals_list[0]['x_flag_tickets'] = len(tickets)

            else:
                logging.warning("You DONT have tickets")

        obj = super().create(vals_list)
        logging.warning("Object is %s", obj)
        return obj
        #obj.write({'x_flag_tickets': self.x_flag_tickets})
    def _action_generate_serial_flag_wizard(self):
        logging.warning("This view must be returned but its not")
        view = self.env.ref('isofterp_subscription.view_flag_field_service_calls')
        return {
            'name': _('Flag tickets'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'project.task',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': 'None',
        }

    def _jump_to_flagged_calls(self):

        action = self.env["ir.actions.actions"]._for_xml_id(
            "isofterp_subscriptions.action_flagged_incidents"
        )
        logging.warning("Action is %s", action)

        return action

    def jump_to_flagged_calls(self):
        self.ensure_one()
        company_id = self.company_id.id or self.env.company.id
        action = self._jump_to_flagged_calls()
        return action

    def _get_problem_calls(self):
        logging.warning("====SELF is %s ", self,)
        self.x_problem_tickets = self.env['project.task'].search([('partner_id','=',9729)]).id



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
    x_serial_number_id = fields.Many2one('stock.production.lot', 'Serial Number', store=True)
    x_serial_number_name = fields.Char(related='x_serial_number_id.product_id.name', string='Machine Description', store=True)
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
    x_flag_tickets = fields.Integer('Flagged Tickets')

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
