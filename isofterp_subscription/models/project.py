# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command, fields, models, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import datetime, timedelta, time
import pytz
import logging
_logger = logging.getLogger(__name__)


class Task(models.Model):
    _description = "Task"
    _inherit = 'project.task'

    @api.model_create_multi
    def create(self, vals_list):
        #logging.warning("Vals list is %s", vals_list[0])
        if vals_list[0].get('x_serial_number_id'):
            logging.warning("1-----Setting flags on this record")
            ten_days_ago = datetime.now() - timedelta(days=10)
            #logging.warning("10 days ago %s %s", ten_days_ago.strftime('%Y-%m-%d'), vals_list[0].get('x_serial_number_id'))
            tickets = self.env['project.task'].search([('x_serial_number_id','=', vals_list[0].get('x_serial_number_id')),('create_date','>=',ten_days_ago)])
            if len(tickets) >= 3:
                #logging.warning("2-----Setting flags on this record")
                vals_list[0]['x_flag_tickets'] = len(tickets)

            else:
                logging.warning("You DONT have tickets")
        project_id = self.env['project.project'].search([('id','=',vals_list[0].get('project_id'))])

        analytic_acc = self.env['account.analytic.account'].search([('name','=', project_id.name)])
        if analytic_acc:
            #logging.warning("========Analytic is %s", analytic_acc)
            vals_list[0]['analytic_account_id'] = analytic_acc.id
        else:
            logging.warning("No analytic account found")

        obj = super().create(vals_list)
        #logging.warning("Object is %s", obj)
        return obj
        #obj.write({'x_flag_tickets': self.x_flag_tickets})

    def write(self, vals):
        #The write fires twice with the stage_id in the 2nd write
        #_logger.warning("--------vals is %s", vals)


        for task in self:

            # The write gets called if a task needs to be approved and the approver
            # needs write access to approve the record
            # Check in the vals for the approval key so that we can bypass the x_to_approve

            if task.x_to_approve and 'x_is_approved' not in vals:
                raise AccessError(
                    "Access Denied - Changes not allowed on this task. Waiting on Approval!!")
            if task.sale_order_id == None:
                if 'stage_id' in vals:
                    user_list = []
                    for user in task.user_ids:
                        user_list.append(user.id)
                    _logger.warning("users and me %s %s %s", user_list, self.env.user.id, task._origin.stage_id.name)
                    if not (self.env.user.has_group('project.group_project_manager') or
                            self.env.user._is_admin() or
                            self.env.user.id in user_list):
                        raise AccessError(
                            "You can only change the state of your own tasks. Project managers and administrators can change the state of any task.")
            # Lookup the stage_id
            stage_id = self.env['project.task.type'].search([('id', '=', task._origin.stage_id.id)])
            #_logger.warning("stage is %s", stage_id.name)
            if stage_id.name == 'Done':
                logging.warning("Checking if the user can amend the record")
                if not (self.env.user.has_group('project.group_project_manager') or
                        self.env.user.has_group('isofterp_subscription.access_field_service_amend_group') or
                        self.env.user._is_admin()):
                    raise AccessError(
                        "You cannot amend a task in a Done state - Contact Project administrators for assistance!")

        return super(Task, self).write(vals)
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
        # if self.x_serial_number_id:
        #     title = 'WARNING -------> ' + self.x_serial_number_name
        #     message = self.x_serial_number_id.x_service_type_id.name
        #     if message:
        #         warning = {
        #             'title': title,
        #             'message': message,
        #         }
        #         return {'warning': warning}
        if not self.partner_id:
            self.partner_id = self.x_serial_number_id.x_subscription_id.partner_id  # Field has to be populated
        self.x_serial_number_street = self.x_serial_number_id.x_subscription_id.partner_id.street
        #self.x_serial_number_street2 = self.x_serial_number_id.x_subscription_id.partner_id.street2
        if self.x_serial_number_id.x_dlv_id.street and  self.x_serial_number_id.x_dlv_id.street2 and self.x_serial_number_id.x_dlv_id.city:
            self.x_serial_number_street2 = self.x_serial_number_id.x_dlv_id.street + '\n' + \
                                           self.x_serial_number_id.x_dlv_id.street2 + '\n' + \
                                           self.x_serial_number_id.x_dlv_id.city
        self.x_cust_rep = self.x_serial_number_id.x_dlv_id.name
        self.x_serial_number_email = self.x_serial_number_id.x_dlv_id.email
        self.x_serial_number_phone = self.x_serial_number_id.x_dlv_id.phone
        self.x_serial_number_mobile = self.x_serial_number_id.x_dlv_id.mobile
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

    @api.model
    def default_get(self, fields_list):
        #logging.warning("Runnign this!!!!!!! %s", self._context)
        result = super(Task, self).default_get(fields_list)
        is_fsm_mode = self._context.get('fsm_mode')
        if 'project_id' in fields_list and not result.get('project_id') and is_fsm_mode:
            company_id = self.env.context.get('default_company_id') or self.env.company.id
            fsm_project = self.env['project.project'].search([('is_fsm', '=', True), ('company_id', '=', company_id)],
                                                             order='sequence', limit=1)
            if fsm_project:
                result['stage_id'] = self.stage_find(fsm_project.id, [('fold', '=', False), ('is_closed', '=', False)])
            logging.warning("=====Setting the project ID to %s", fsm_project.id)
            result['project_id'] = fsm_project.id

        date_begin = result.get('planned_date_begin')
        date_end = result.get('planned_date_end')
        if is_fsm_mode and (date_begin or date_end):
            if not date_begin:
                date_begin = date_end.replace(hour=0, minute=0, second=1)
            if not date_end:
                date_end = date_begin.replace(hour=23, minute=59, second=59)
            date_diff = date_end - date_begin
            if date_diff.days > 0:
                # force today if default is more than 24 hours (for eg. "Add" button in gantt view)
                today = fields.Date.context_today(self)
                date_begin = datetime.combine(today, time(0, 0, 0))
                date_end = datetime.combine(today, time(23, 59, 59))
            if date_diff.seconds / 3600 > 23.5:
                # if the interval between both dates are more than 23 hours and 30 minutes
                # then we changes those dates to fit with the working schedule of the assigned user or the current company
                # because we assume here, the planned dates are not the ones chosen by the current user.
                user_tz = pytz.timezone(self.env.context.get('tz') or 'UTC')
                date_begin = pytz.utc.localize(date_begin).astimezone(user_tz)
                date_end = pytz.utc.localize(date_end).astimezone(user_tz)
                user_ids_list = [res[2] for res in result.get('user_ids', []) if
                                 len(res) == 3 and res[0] == Command.SET]  # user_ids = [(Command.SET, 0, <user_ids>)]
                user_ids = user_ids_list[-1] if user_ids_list else []
                users = self.env['res.users'].sudo().browse(user_ids)
                user = len(users) == 1 and users
                if user and user.employee_id:  # then the default start/end hours correspond to what is configured on the employee calendar
                    resource_calendar = user.resource_calendar_id
                else:  # Otherwise, the default start/end hours correspond to what is configured on the company calendar
                    company = self.env['res.company'].sudo().browse(result.get('company_id')) if result.get(
                        'company_id') else self.env.user.company_id
                    resource_calendar = company.resource_calendar_id
                if resource_calendar:
                    resources_work_intervals = resource_calendar._work_intervals_batch(date_begin, date_end)
                    work_intervals = [(start, stop) for start, stop, meta in resources_work_intervals[False]]
                    if work_intervals:
                        planned_date_begin = work_intervals[0][0].astimezone(pytz.utc).replace(tzinfo=None)
                        planned_date_end = work_intervals[-1][1].astimezone(pytz.utc).replace(tzinfo=None)
                        result['planned_date_begin'] = planned_date_begin
                        result['planned_date_end'] = planned_date_end
                else:
                    result['planned_date_begin'] = date_begin.replace(hour=9, minute=0, second=1).astimezone(
                        pytz.utc).replace(tzinfo=None)
                    result['planned_date_end'] = date_end.astimezone(pytz.utc).replace(tzinfo=None)
        return result

    def action_timer_start(self):
        if self.stage_id.name == 'Done':
            logging.warning("==========================Dont let the Timer start")
            raise AccessError(
                "You cannot start the timer for a task in a Done state - Contact Project administrators for assistance.")

        if self.x_to_approve == True:
            raise AccessError(
                "You cannot start the timer for a task waiting for Approval - Contact Project administrators for assistance.")

        if not self.user_timer_id.timer_start and self.display_timesheet_timer:
            super(Task, self).action_timer_start()

    @api.model
    def delete_tasks(self, rec):
        stripped_name = rec.name
        logging.warning("************The record is %s",stripped_name.rstrip())
        chk_name = rec.sale_order_id.name + ": PRODUCT RUN UP"
        logging.warning("Check name %s", len(chk_name))
        if stripped_name.rstrip() == chk_name:
            sale_line = self.env['sale.order.line'].search([('id','=', rec.sale_line_id.id)])
            sale_line.write(
                {'task_id':''}
            )
            # rec.sale_line_id.write(
            #     {'task_id',''}
            # )
            logging.warning("******Going to delete this record %s", rec.name)
            #rec.sale_order_id = ''
            #rec.sale_line_id = ''
            rec.active = False

            #rec.unlink()


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
