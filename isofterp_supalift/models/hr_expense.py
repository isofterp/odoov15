from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    def action_sheet_move_create(self):
        #print("@8 in in action_sheet_move_create")
        total_amount = 0
        total_amount_currency = 0

        task_obj = self.env['project.task']
        for rec in self.expense_line_ids:
            logging.warning("The unit amount is %s %s", rec.name, rec.unit_amount)
            company_currency = rec.company_id.currency_id
            taxes = rec.tax_ids.with_context(round=True).compute_all(rec.unit_amount, rec.currency_id,
                                                                         rec.quantity, rec.product_id)
            account_date = rec.sheet_id.accounting_date or rec.date or fields.Date.context_today(rec)
            balance = rec.currency_id._convert(taxes['total_excluded'], company_currency, rec.company_id,
                                                   account_date)
            amount_currency = taxes['total_excluded']
            total_amount -= balance
            total_amount_currency -= amount_currency
            logging.warning("balance, amount_currency total_amount  %s %s %s",
                            balance,total_amount, total_amount_currency )
            #raise UserError("Not going further")



            task = task_obj.browse([rec.x_task_id.id])
            vals = {
                'task_id': task.id,
                'product_id': rec.product_id.id,
                'product_uom': rec.product_uom_id.id,
                'qty': rec.quantity,
                'total_cost': balance,
                'price':balance,
                'purchase_price': balance / rec.quantity,
                'unit_price': balance / rec.quantity,
                # 'markup_amt': 0,                   #  rec.unit_amount * rec.quantity * -1,
                # 'markup_percent':0,
                'actual_qty': rec.quantity,
                'actual_cost': balance,
                'actual_price': balance,
                'actual_profit': balance * -1,
                'notes': rec.name,
                'expense_id': rec.id,
                'branch_id': rec.branch_id.id,
                'name': task.code,
                'project_id':task.project_id.id,

            }
            #print("@24 in hr_expense",vals)

            logging.warning("======The expense vals are %s", vals)
            line = self.env['task.custom.lines'].create(vals)
            line.update_selling_from_other_source()
            line._calculate_unit_price()
            #print("@27 in hr_expense",line)
            task.task_custom_line_ids = [(4, line.id)]
            new_stage = self.env['project.task.type'].search([('name', '=', 'WIP')])
            if task.stage_id.sequence < new_stage.sequence:
                task.stage_id = new_stage.id

        return super(HrExpenseSheet, self).action_sheet_move_create()

    def action_submit_sheet(self):
        super(HrExpenseSheet, self).action_submit_sheet()
        task = "[" + self.expense_line_ids.x_task_id.code + " ] " + self.expense_line_ids.x_task_id.name
        msg = _(
            """Expense record for <strong>{task}</strong>
            submitted for Approval: <br/>
            <strong>Expense Description</strong>: {expense} <br/>
            <strong>Equipment</strong>: {equipment} <br/>
            <strong>Notes</strong>: {notes} <br/>
            <strong>User</strong>: {user}
            """.format(
                expense=self.expense_line_ids.name,
                task=task,
                equipment=self.expense_line_ids.x_task_id.project_id.x_equipment_id.name,
                user=self.expense_line_ids.employee_id.name,
                notes=self.expense_line_ids.description,
            )
        )
        logging.warning("Submitted message is %s", msg)
        self.expense_line_ids.x_task_id.sudo().message_post(body=msg)

    def approve_expense_sheets(self):
        super(HrExpenseSheet, self).approve_expense_sheets()
        task = "[" + self.expense_line_ids.x_task_id.code + " ] " + self.expense_line_ids.x_task_id.name
        msg = _(
            """Expense record for <strong>{task}</strong>
            approved: <br/>
            <strong>Expense Description</strong>: {expense} <br/>
            <strong>Equipment</strong>: {equipment} <br/>
            <strong>Notes</strong>: {notes} <br/>
            <strong>User</strong>: {user} <br/>
            """.format(
                expense=self.expense_line_ids.name,
                task=task,
                equipment=self.expense_line_ids.x_task_id.project_id.x_equipment_id.name,
                user=self.expense_line_ids.employee_id.name,
                notes=self.expense_line_ids.description,
            )
        )
        logging.warning("Approved message is %s", msg)
        self.expense_line_ids.x_task_id.sudo().message_post(body=msg)
        self.expense_line_ids.sudo().message_post(body=msg)


    def refuse_sheet(self, reason):
        super(HrExpenseSheet, self).refuse_sheet(reason)
        task = "[" + self.expense_line_ids.x_task_id.code + " ] " + self.expense_line_ids.x_task_id.name
        msg = _(
            """Expense record for <strong>{task}</strong>
            refused: <br/>
            <strong>Expense Description</strong>: {expense} <br/>
            <strong>Equipment</strong>: {equipment} <br/>
            <strong>Notes</strong>: {notes} <br/>
            <strong>User</strong>: {user} <br/>
            <strong>Reason</strong>: {reason} <br/>
            """.format(
                expense=self.expense_line_ids.name,
                task=task,
                equipment=self.expense_line_ids.x_task_id.project_id.x_equipment_id.name,
                user=self.expense_line_ids.employee_id.name,
                notes=self.expense_line_ids.description,
                reason=reason,
            )
        )
        logging.warning("Refused message is %s", msg)
        self.expense_line_ids.x_task_id.sudo().message_post(body=msg)
        self.expense_line_ids.sudo().message_post(body=msg)



class HrExpense(models.Model):
    _inherit = "hr.expense"

    # branch_id = fields.Many2one("multi.branch",  default=lambda self: self.env.user.branch_id,string="Branch Names")
    x_project_id = fields.Many2one('project.project', 'Equipment')
    x_task_id = fields.Many2one('project.task', 'Job Card', required=True)
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"),("company_account", "Company")], default='company_account', tracking=True,
            states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]},
            string="Paid By")
    x_readonly = fields.Boolean(String="read only", default=False)

    @api.onchange('x_project_id')
    def onchange_x_project_id(self):
        #print("@47",self.x_project_id.name)
        if self.x_project_id:
            analytic_account = self.env["account.analytic.account"].search([("name", "=", self.x_project_id.name)])
            if analytic_account:
                self.analytic_account_id = analytic_account.id

    def _send_message(self, expense_rec):
        task = "[" + expense_rec.x_task_id.code + " ] " + expense_rec.x_task_id.name
        channel_odoo_bot_users = '%s' % ('Field Service')
        channel_obj = self.env['mail.channel']
        channel_id = channel_obj.search([('name', 'like', channel_odoo_bot_users)])

        if not channel_id:
            channel_id = channel_obj.create({
                'name': channel_odoo_bot_users,
                'email_send': False,
                'channel_type': 'channel',
                'public': 'private',
                'channel_partner_ids': [(4, odoo_bot.partner_id.id), (4, employee.user_id.partner_id.id)]
            })
        try:

            channel_id.sudo().message_post(
                subject="Expense Record created for Job " + task,
                body="Expense Record created for Job " + task,
                message_type='comment',
                subtype_id=1,
            )
        except Exception as e:
            print('ERROR in _send_message')

        msg = _(
            """Expense record for <strong>{task}</strong>
            created: <br/>
            <strong>Expense Description</strong>: {expense} <br/>
            <strong>Equipment</strong>: {equipment} <br/>
            <strong>Notes</strong>: {notes} <br/>
            <strong>User</strong>: {user}
            """.format(
                expense=expense_rec.name,
                task=task,
                equipment=expense_rec.x_task_id.project_id.x_equipment_id.name,
                user=expense_rec.employee_id.name,
                notes=expense_rec.description
            )
        )
        expense_rec.x_task_id.sudo().message_post(body=msg)
        expense_rec.sudo().message_post(body=msg)

    @api.model
    def create(self, vals):
        logging.warning("Calling this method........")
        rec = super(HrExpense, self).create(vals)
        job_card = "[" + rec.x_task_id.code + " ] " + rec.x_task_id.name
        rec.x_readonly = False
        self._send_message(rec)
        return rec

