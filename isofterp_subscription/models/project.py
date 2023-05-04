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
        # print('onchange_serial_umber')
        self.partner_id = self.x_serial_number_id.x_subscription_id.partner_id
        self.x_serial_number_street = self.x_serial_number_id.x_subscription_id.partner_id.street
        # self.x_serial_number_street2 = self.x_serial_number_id.x_subscription_id.partner_id.street2
        if self.x_serial_number_id.x_dlv_id.street and self.x_serial_number_id.x_dlv_id.street2 and self.x_serial_number_id.x_dlv_id.city:
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


class FSMProblemType(models.Model):
    _description = "FSM Problem Type"
    _name = "fsm.problem.type"
    _order = 'name'

    name = fields.Char("Problem Type")
