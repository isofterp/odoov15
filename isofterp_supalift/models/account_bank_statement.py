from odoo import api, fields, models, _

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    x_task_id = fields.Many2one('project.task', 'Job Card')
    x_task_assigned_to_id = fields.Many2one('hr.employee',related="x_task_id.x_assigned_to_id")

    # @api.onchange('x_task_id','sequence')
    # def onchange_task_id(self):
    #     task = self.env['project.task'].browse([self.x_task_id.id])
    #     product = self.env['product.template'].search([('name','=','Expenses')])
    #     print("onchange_task_id", task)
    #     vals = {
    #         'task_id': task.id,
    #         'product_id': product.id,
    #         'actual_cost': self.amount,
    #         'price': 0,
    #         'sub_total': 0,
    #         'sub_total_cost': self.amount,
    #         'purchase_price':self.amount,
    #         'margin': self.amount * -1,
    #         'actual_profit': self.amount * -1,
    #     }
    #     line = self.env['task.custom.lines'].create(vals)
    #     print(line)
    #     task.task_custom_line_ids = [(4,line.id)]