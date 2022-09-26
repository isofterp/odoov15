from odoo import api, fields, models, tools, _

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    x_invoice_warn = fields.Text(related='partner_id.invoice_warn_msg', store='yes',string='Customer Warning')
    x_customer_rank = fields.Integer(related='partner_id.customer_rank', store='yes', string='Customer Ranking')