# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
import json

from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    def _compute_last_meter_reading(self):

        for rec in self:
            cur_reading = self.env['meter.reading'].search([('x_equipment_id','=',rec.x_equipment_id.id)], limit=1, order='x_reading_date desc')
            if cur_reading:
                logging.warning("Meter reading")
                logging.warning("Meter reading is %s", cur_reading.name)
                rec.x_meter_reading = cur_reading.name
            else:
                rec.x_meter_reading = 0

    x_equipment_id = fields.Many2one('maintenance.equipment', 'Equipment')
    x_meter_reading = fields.Float('Latest Meter Reading', compute="_compute_last_meter_reading")
    x_branch_id = fields.Integer('Old Branch')

    @api.onchange("x_equipment_id")
    def populate_equipment_fields(self):
        if self.x_equipment_id:
            self.name = self.x_equipment_id.name + " " + self.x_equipment_id.model


class Task(models.Model):
    _inherit = 'project.task'
    _order = 'create_date desc'

    def write(self, vals):
        logging.warning("Vals write is %s", vals)
        # If the stage id is changed for this task several checks need to be performed
        # Setting a task to:
        # draft state
        # - If the task has already been in any other state, i.e. WIP it cannot be moved back to draft
        # if you are manually trying to move a job to WIP
        # 1. A timesheet record needs to exist or
        # 2. A vendor bill needs to exist or
        # 3. An expense needs to exist
        # 4. An actual travel value needs to exist
        if 'stage_id' in vals:
            new_stage = self.env['project.task.type'].search([('id', '=', vals.get('stage_id'))])
            _logger.warning("Setting the current stage %s with sequence %s to %s with sequence %s",
                            self._origin.stage_id.name,
                            self._origin.stage_id.sequence,
                            new_stage.name,
                            new_stage.sequence)
            if new_stage.name == 'Draft' and self._origin.stage_id.sequence > new_stage.sequence:
                raise UserError(
                    _("You cannot move the job from %s to %s") % (self._origin.stage_id.name, new_stage.name))
            if new_stage.name == 'WIP' and (self._origin.stage_id.sequence < new_stage.sequence):
                time_move = expense_move = bill_move = po_move = travel_move = False
                logging.warning("Conext in write is %s", self._context)
                travel = self._context.get('travel_move') or None
                if travel:
                    travel_move = travel

                #logging.warning("Can travel is %s", travel_move)

                if not self.timesheet_ids and not self.x_po_no and self.bills_count < 1 and self.expense_count < 1 and not travel_move:
                    raise UserError(_(
                        "All of the following conditions have not been met: \n1. No Timesheets \n2. No PO Number \n3. No Bills \n4. No actual Expenses"))

                if self.timesheet_ids:
                    time_move = True
                if self.expense_count > 0:
                    expense_move = True
                if self.bills_count > 0:
                    bill_move = True
                if self.x_po_no:
                    po_move = True

                if not time_move and not expense_move and not bill_move and not po_move and not travel_move:
                    raise UserError(_("This job cannot move to WIP - No actuals for any line is available"))

                # When job is moved to WIP state, auto-consume product lines which has an actual qty
                # How

            # else:
            #     raise UserError(
            #         _("You cannot move the job from %s to %s") % (self._origin.stage_id.name, new_stage.name))

            if new_stage.name == 'Quoted':
                if not self.sale_order_id:
                    raise UserError(_("There is no quotation associated with this Job"))
                if self.sale_order_id and self.sale_order_id.state in ['draft', 'cancel']:
                    raise UserError(_("The Sales Order %s has not been sent or has been cancelled - State is %s") %
                                    (self.sale_order_id.name, self.sale_order_id.state))

            # This is based on an entered meter reading and the sales order having been quoted or confirmed
            if new_stage.name == 'Awaiting PO':
                # if not self.sale_order_id:
                #     raise UserError(_("There is no quotation associated with this Job"))
                # If the quote is sent and meter reading is entered for this job - Awaiting PO
                if self.sale_order_id and self.sale_order_id.state in ['draft', 'cancel']:
                    raise UserError(_("The Sales Order %s has not been sent or has been cancelled - State is %s") %
                                    (self.sale_order_id.name, self.sale_order_id.state))

            # raise UserError(_(
            #     "State is in the vals list"))

        res = super(Task, self).write(vals)
        _logger.warning("===IN WRITE STATEMENT")
        context = self._context.copy()
        context.update({'default_task_id': self.id, })

        for line in self.task_custom_line_ids:
            # line.with_context(context).product_id_change()
            # line.with_context(context).calc_template_labour()
            ##line.with_context(context)._recalculate_line_values()
            # line.with_context(context).update_selling_from_other_source()
            ##line.with_context(context)._calculate_unit_price()

            _logger.warning("@34 - IN write statement For line in line %s", line.price)
        return res

    @api.model
    def create(self, vals):

        # vals.update({'branch_id': self.env.user.branch_id.id})
        # logging.warning("Vals is %s", vals)
        rec = super(Task, self).create(vals)

        partner_id = rec.project_id.partner_id
        pricelist = partner_id.property_product_pricelist
        rec.write({'pricelist_id': rec.project_id.partner_id.property_product_pricelist})
        # print('RE=', rec, rec.name, rec.project_id)

        # tag_vals = {
        #     'name': rec.name,
        #     'active_analytic_distribution': 1,
        # }
        # new_tag = self.env['account.analytic.tag'].create(tag_vals)
        # distribution_vals = {
        #     'tag_id': new_tag.id,
        #     'account_id': rec.project_id.id,
        #     'percentage': 100,
        # }
        # self.env['account.analytic.distribution'].create(distribution_vals)

        # Send message to users inbox of new task
        _logger.warning("====Sending inbox message to user")
        val_list = {
            'Project': rec.project_id.name,
            'Job Card': rec.code + " " + rec.name + " has been assigned to you",
            'Created': rec.create_date,

        }
        partners_to_message = []
        for user in self.env['res.users'].search([('id', '=', rec.user_id.id)]):
            partners_to_message.append(user.partner_id.id)
        for partner in partners_to_message:
            notification_ids = [(0, 0, {
                'res_partner_id': partner,
                'notification_type': 'inbox'})]
            rec.message_post(body=val_list['Job Card'], notification_ids=notification_ids)

        return rec

    @api.onchange("partner_id")
    def populate_pricelist(self):
        self.pricelist_id = self.partner_id.property_product_pricelist

    @api.onchange("x_equipment_id")
    def populate_equipment(self):
        # This will populate the Customer and Sale Order with equipment id and meter reading
        # Need to discuss if these updates are needed

        self.partner_id = self.x_equipment_id.partner_id.id
        self.sale_order_id.x_equipment_id = self.x_equipment_id.id
        self.sale_order_id.x_meter_reading = self.x_meter_reading

    # A write function is required to update the meter reading if it has been populated
    # There must also be a check i.e if task moved to done state to check that a meter reading has been filled in

    @api.onchange("x_meter_reading")
    def update_meter_readng(self):
        if self.x_equipment_id.x_meter_reading < self.x_meter_reading:
            self.x_equipment_id.x_meter_reading = self.x_meter_reading
            if self.parent_id:
                self.parent_id.x_meter_reading = self.x_meter_reading

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        new_task = super(Task, self).copy(default)
        for task_line in new_task.task_custom_line_ids:
            task_line.actual_qty = 0
            task_line.actual_cost = 0
            task_line.is_so_line_created = False
            task_line.actual_profit = task_line.markup_amt
        return new_task

    @api.depends('project_id')
    def _compute_job_template_id_domain(self):
        job_list = []
        if len(self.project_id.x_equipment_id.job_type_ids) > 0:
            for rec in self.project_id.x_equipment_id.job_type_ids:
                job_list.append(rec.id)
                self.x_job_template_domain = json.dumps(
                    [('id', 'in', job_list)]

                )
        else:
            self.x_job_template_domain = json.dumps(
                [('id', 'in', [0])])

    def _compute_last_meter_reading(self):
        for rec in self:
            cur_reading = self.env['meter.reading'].search([('x_task_id', '=', self.id)], limit=1, order='id desc')
            if cur_reading:
                logging.warning("Meter reading")
                logging.warning("Meter reading is %s", cur_reading.name)
                rec.x_meter_reading = cur_reading.name
            else:
                rec.x_meter_reading = 0

    x_assigned_to_id = fields.Many2one('hr.employee', 'Technician')
    x_equipment_id = fields.Many2one('maintenance.equipment', related="project_id.x_equipment_id")
    x_meter_reading = fields.Float(related='project_id.x_meter_reading', readonly=True, string='Job Card Meter Reading')
    project_task_template_id = fields.Many2one('project.task.template', 'Quotation Template')
    x_branch_id = fields.Integer('Old Branch')
    x_job_template_domain = fields.Char(string="Filtered job types",
                                        compute="_compute_job_template_id_domain",
                                        readonly=True,
                                        store=False)
    x_job_template = fields.Many2one('equipment.job.template', string="Job Template")
    x_job_type = fields.Many2one('job.card.types', string="Job Type")

    def _compute_line_data_for_template_change(self, line):
        return {
            'name': line.name,
            'product_id': line.product_id,
            'qty': line.product_uom_qty,
        }

    @api.onchange("x_job_template")
    def create_task_lines(self):
        # self.task_custom_line_ids.unlink()

        vals = {}
        template = self.x_job_template.with_context(lang=self.partner_id.lang)
        # _logger.warning("===Creating task lines %s", template)
        quote_lines = [(5, 0, 0)]
        for template_line in template.task_template_line_ids:
            tmp_price = 0
            data = self._compute_line_data_for_template_change(template_line)

            # _logger.warning("The data is %s", data)
            pricelist_id = self.env['product.pricelist'].browse([self.pricelist_id]).id
            pricelist_price = self.env['product.pricelist.item'].search(
                [('pricelist_id', '=', pricelist_id.id), ('product_tmpl_id', '=', data.get('product_id').id)])
            if pricelist_price:
                tmp_price = pricelist_price.fixed_price
            # else:
            #     tmp_price = data.get('product_id').list_price

            _logger.warning("the Tmp price for %s is %s %s", data.get('product_id').name, tmp_price, data.get('qty'))

            data.update({
                'purchase_price': data.get('product_id').standard_price,
                'unit_price': tmp_price,
                'total_cost': data.get('qty') * data.get('product_id').standard_price,
                'notes': data.get('name'),
                'branch_id': self.branch_id.id,
                'project_id': self.project_id.id,
                'qty': data.get('qty'),
                'price': data.get('qty') * tmp_price,

            })
            quote_lines.append((0, 0, data))
            self.task_custom_line_ids = quote_lines
            # context = self._context.copy()
            # context.update({'default_create_task_lines': 'create_task_lines',}
            #                )
            # for line in self.task_custom_line_ids:
            #     _logger.warning("For linr in line %s %s", context, line.task_custom_id)
            #     line.with_context(context).product_id_change()

    # @api.onchange('project_task_template_id')
    # def project_task_template_id_change(self):
    #     logging.warning("--------project_task_template_id is running!!!!")
    #     template = self.project_task_template_id.with_context(lang=self.partner_id.lang)
    #     quote_lines = [(5, 0, 0)]
    #     for line in template.task_template_line_ids:
    #         data = self._compute_line_data_for_template_change(line)
    #         if line.product_id:
    #             price = line.product_id.product_tmpl_id.standard_price
    #             # if self.pricelist_id:
    #             #     pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(
    #             #         line.product_id, 1, False)
    #             #
    #             #     if self.pricelist_id.discount_policy == 'without_discount' and price:
    #             #         discount = max(0, (price - pricelist_price) * 100 / price)
    #             #     else:
    #             #         price = pricelist_price
    #
    #             data.update({
    #                 'purchase_price': price,
    #                 'product_id': line.product_id.id,
    #                 'product_uom': line.product_uom_id.id,
    #                 'notes': line.product_id.name,
    #                 'qty': line.product_uom_qty,
    #
    #             })
    #         quote_lines.append((0, 0, data))
    #     self.task_custom_line_ids = quote_lines
