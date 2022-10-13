# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

class ProjectTask(models.Model):
    _inherit = 'project.task'

    def _get_expensed(self):
        for task in self:
            expenses = self.env['hr.expense'].search([('x_task_id','=', task.id)])
            task.expense_count = len(expenses)

    def _get_bills(self):
        bill_count = 0
        bills = []
        for task in self:
            bill_lines = self.env['account.move.line'].search([('x_task_id','=', task.id)])
            for bill_line in bill_lines:
                if bill_line.move_id.move_type == 'in_invoice':
                    bill = self.env['account.move'].search([('move_type','=', 'in_invoice'), ('id','=',bill_line.move_id.id)])
                    bills.append(bill.id)
                    bills = list( dict.fromkeys(bills) )
            bill_count += len(bills)
            task.bills_count = len(bills)

    def _get_sales(self):
        for task in self:
            sales = self.env['sale.order'].search([('task_custom_id','=', task.id)])
            task.sales_count = len(sales)

    def _get_invoices(self):
        for task in self:
            invoices = self.env['account.move'].search([('x_task_id','=', task.id),
                                                     ('move_type','=', 'out_invoice')])
            task.invoice_count = len(invoices)

    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist', check_company=True,
        required=True,
        help="If you change the pricelist, only newly added lines will be affected.")
    x_project_task_template_id = fields.Many2one('project.task.template', 'Job Card Template')
    expense_count = fields.Integer(string='Expense Count', compute='_get_expensed', readonly=True)
    bills_count = fields.Integer(string='Vendor Bill Count', compute='_get_bills', readonly=True)
    sales_count = fields.Integer(string='Sales Count', compute='_get_sales', readonly=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_get_invoices', readonly=True)
    x_po_no = fields.Char(related='sale_order_id.client_order_ref', readonly=True, string="Purchase Order")


    task_custom_line_ids = fields.One2many(
       'task.custom.lines',
       'task_custom_id',
       string="Quotation Product Lines",
       copy=True,
    )
    task_profitability = fields.Float(compute='_get_task_profitability', string='Profitability %')

    def _get_task_profitability(self):
        profit = 0
        price = 0
        cost = 0
        for rec in self:
            for line in rec.task_custom_line_ids:
                price += line.price
                if line.actual_cost > 0:
                    cost += line.actual_cost
                else:
                    cost += line.total_cost
            if not rec.task_profitability:
                try:
                    rec.task_profitability = (price - cost) / price * 100
                except ZeroDivisionError:
                    rec.task_profitability = 0
            #rec.task_profitability = (price - cost) / price * 100

    def show_quotation(self):
        self.ensure_one()
        res = self.env.ref('sale.action_quotations')
        res = res.sudo().read()[0]
        res['domain'] = str([('task_custom_id','=', self.id)])
        return res

    def show_expenses(self):
        res = self.env.ref('hr_expense.hr_expense_actions_my_all')
        res = res.sudo().read()[0]
        res['domain'] = str([('x_task_id', '=', self.id)])
        return res

    def create_expense(self):
        context = self._context.copy()
        context.update({'default_x_project_id': self.project_id.id,
                        'default_x_task_id': self.id,
                        'default_x_readonly': True},
                       )
        return {
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref("hr_expense.hr_expense_view_form").id,
            'target': 'new',
            'context':context,
        }

    def show_bills(self):
        res = self.env.ref('account.action_move_in_invoice_type')
        res = res.sudo().read()[0]
        bills = []
        bill_lines = self.env['account.move.line'].search([('x_task_id', '=', self.id)])
        for bill_line in bill_lines:
            if bill_line.move_id.move_type == 'in_invoice':
                bill = self.env['account.move'].search(
                    [('move_type', '=', 'in_invoice'),
                     ('id', '=', bill_line.move_id.id)])
                logging.warning("Bill name and type is %s %s", bill.name, bill.move_type)
                if bill.name:
                    bills.append(bill.id)
        logging.warning("bills are %s", bills)
        res['domain'] = str([('id', 'in', bills)])
        return res

    def show_invoices(self):
        res = self.env.ref('account.action_move_out_invoice_type')
        res = res.sudo().read()[0]
        invoices = []
        invoice_lines = self.env['account.move'].search([('x_task_id', '=', self.id),
                                                         ('move_type','=', 'out_invoice')])
        res['domain'] = str([('x_task_id', '=', self.id)])
        return res