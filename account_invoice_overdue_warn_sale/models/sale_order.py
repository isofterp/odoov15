# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import logging


class SaleOrder(models.Model):
    _inherit = "sale.order"

    overdue_invoice_count = fields.Integer(
        compute="_compute_overdue_invoice_count_amount",
        string="# of Overdue Invoices",
        compute_sudo=True,
    )
    overdue_invoice_amount = fields.Monetary(
        compute="_compute_overdue_invoice_count_amount",
        string="Overdue Invoices Residual",
        compute_sudo=True,
        currency_field="company_currency_id",
        help="Overdue invoices total residual amount of the invoicing partner "
        "in company currency.",
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, string="Company Currency"
    )
    commercial_partner_invoicing_id = fields.Many2one(
        related="partner_invoice_id.commercial_partner_id",
        string="Commercial Invoicing Partner",
    )
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('to_approve','To Approve'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    date_approve = fields.Datetime('Approval Date', readonly=1, index=True, copy=False)
    x_is_refused = fields.Boolean('Is Refused', readonly=1, copy=False)
    x_date_refused = fields.Datetime('Refused Date', readonly=1, index=True, copy=False)

    @api.depends("partner_invoice_id", "company_id")
    def _compute_overdue_invoice_count_amount(self):
        for order in self:
            count = amount = 0
            partner = order.partner_invoice_id
            if partner:
                # the use of commercial_partner is in the method below
                count, amount = partner._prepare_overdue_invoice_count_amount(
                    order.company_id.id
                )
            order.overdue_invoice_count = count
            order.overdue_invoice_amount = amount

    def jump_to_overdue_invoices(self):
        self.ensure_one()
        action = self.partner_invoice_id._prepare_jump_to_overdue_invoices(
            self.company_id.id
        )
        return action

    def _setup_fields(self):
        super(SaleOrder, self)._setup_fields()
        selection = self._fields['state'].selection
        exists = False
        for idx, (state, __) in enumerate(selection):
            if state == 'to_approve':
                exists = True
        if not exists:
            selection.insert(0, ('to_approve', _('To Approve')))

    def is_to_approve(self):
        self.ensure_one()
        #
        return self.overdue_invoice_amount > 0

    def create(self, vals):
        obj = super().create(vals)
        if obj.is_to_approve():
            obj.state = 'to_approve'

            # Notify Approvers
            msg = _(
                """<strong>Quotation Status -> :  {state}</strong>
                """.format(
                    state='To Approve',
                )
            )
            obj.message_post(body=msg)

            approval_category = self.env['approval.category'].search([('name', '=', 'Sales Order')])
            logging.warning("Category is %s", approval_category)
            approval_reason = 'Customer: ' + obj.partner_id.name + " has outstanding invoices older than 30 days amounting to " + str(
                obj.overdue_invoice_amount)

            # logging.warning("=======Checking if the cost price exceeds R5K")
            # print(err)
            # so_line_total = 0
            # for line in obj.order_line:
            #     logging.warning("=======Again Checking if the cost price exceeds R5K")
            #     if line.product_id.type == "product":
            #         so_line_total += line.price_unit
            #
            # if so_line_total > 5000 and not obj.x_is_contract_quote:
            #     approval_category = self.env['approval.category'].search([('name', '=', 'Non Contracts over R5K')])
            #     approval_reason = 'Total Non Contract Sales Value exceeds value - Approval Required'

            vals_list = {
                'name': obj.name,
                'request_owner_id': obj.user_id.id,
                'category_id': approval_category.id,
                'reason': approval_reason,
                'partner_id': obj.partner_id.id,
                'x_sales_order_id': obj.id,
            }
            approve_request = self.env['approval.request'].create(vals_list)
            approve_request.action_confirm()

        return obj

    def action_approve(self):
        self.write({'state': 'draft',
                    'date_approve' : fields.Datetime.now()})
        msg = _(
            """<strong>Quotation Approved by:  {user}</strong>
            """.format(
                user=self.env.user.name,
            )
        )
        self.message_post(body=msg)

    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel', 'sent'])
        if orders.is_to_approve():
            return orders.write({
                'state': 'to_approve',
                'signature': False,
                'signed_by': False,
                'signed_on': False,
            })
        else:
            return orders.write({
                'state': 'draft',
                'signature': False,
                'signed_by': False,
                'signed_on': False,
            })

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        for order in self:
            if order.state not in ('draft', 'cancel', 'to_approve'):
                raise UserError(
                    _('You can not delete a sent quotation or a confirmed sales order. You must first cancel it.'))