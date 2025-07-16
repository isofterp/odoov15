# -*- coding: utf-8 -*-
# Copyright 2020-2022 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import threading
import logging
_logger = logging.getLogger(__name__)

class FinanceCharge(models.TransientModel):
    _name = 'finance.charge'
    _description = 'Finance Charge'

    due_date_prior_to = fields.Date(required=True)

    def create_finance_charge_invoices(self, partner=False, invoice_ids=None):
        invoice_ref = []
        amount_due = 0
        payment_param = self.env['ir.config_parameter'].sudo().get_param('finance_charge.payment_term_id')
        product_param = self.env['ir.config_parameter'].sudo().get_param('finance_charge.product_id')
        finance_param = self.env['ir.config_parameter'].sudo().get_param('finance_charge.finance_percent')
        finance_threshold = self.env['ir.config_parameter'].sudo().get_param('finance_charge.finance_threshold')
        if not all([payment_param, product_param, finance_param]):
            raise UserError('Please add finance charge configuration to proceed!')
        if not invoice_ids:
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('partner_id', '=', partner.id),
                ('invoice_date_due', '<', self.due_date_prior_to),
                ('invoice_finance_charges', '=', False),
                ]
            invoice_ids = self.env['account.move'].search(domain)
        for invoice in invoice_ids:
            payment_vals = invoice.sudo()._get_reconciled_info_JSON_values()
            paid_amt_after_date = payment_vals and sum([payment.get('amount') for payment in payment_vals if payment['date'] >= self.due_date_prior_to]) or 0
            if invoice.payment_state != 'not_paid':
                if paid_amt_after_date or invoice.amount_residual:
                    amount_due += invoice.amount_residual + paid_amt_after_date
                    invoice_ref.append(invoice.name)
            else:
                amount_due += invoice.amount_residual + paid_amt_after_date
                invoice_ref.append(invoice.name)
        if amount_due:
            finance_threshold = not finance_threshold and 0 or float(finance_threshold)
            finance_charge_amount = round((amount_due * float(finance_param)) / 100, 2)
            if finance_charge_amount >= finance_threshold:
                product = self.env['product.product'].browse(int(product_param))
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'partner_id': partner.id,
                    'invoice_date': fields.Date.today(),
                    'invoice_payment_term_id': int(payment_param),
                    'ref': 'Finance charge - {} for invoices {}'.format((self.due_date_prior_to - relativedelta(months=1)).strftime('%B %Y'), ', '.join(invoice_ref)),
                    'invoice_finance_charges': True,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': int(product_param),
                        'name' : product.display_name,
                        'product_uom_id' : product.uom_id.id,
                        'quantity' : 1,
                        'price_unit' : finance_charge_amount,
                    })]
                    }
                self.env['account.move'].create(invoice_vals)

    def create_finance_charge_invoices_for_all(self):
        payment_param = self.env['ir.config_parameter'].sudo().get_param('finance_charge.payment_term_id')
        product_param = self.env['ir.config_parameter'].sudo().get_param('finance_charge.product_id')
        finance_param = self.env['ir.config_parameter'].sudo().get_param('finance_charge.finance_percent')
        finance_threshold = self.env['ir.config_parameter'].sudo().get_param('finance_charge.finance_threshold')
        if not all([payment_param, product_param, finance_param]):
            raise UserError('Please add finance charge configuration to proceed!')
        query = """
            SELECT partner_id,
                   Jsonb_agg(DISTINCT ref) AS ref,
                   SUM(amount) amount_due
            FROM   (SELECT am.partner_id,
                           ARRAY_AGG(DISTINCT am.name) AS ref,
                           SUM(am.amount_residual) AS amount
                    FROM   account_move am
                           JOIN res_partner part
                             ON part.id = am.partner_id
                    WHERE  amount_residual > 0
                           AND am.state = 'posted'
                           AND am.invoice_date_due < %s
                           AND am.move_type = 'out_invoice'
                           AND part.finance_charges = True
                           AND am.invoice_finance_charges = False
                    GROUP  BY am.partner_id
                    UNION ALL
                    SELECT invoice.partner_id,
                        ARRAY_AGG(DISTINCT invoice.NAME) AS ref,
                        CASE
                            WHEN SUM(part.debit_amount_currency) > 0
                                THEN SUM(part.debit_amount_currency)
                            ELSE
                                SUM(part.credit_amount_currency)
                        End AS amount
                    FROM   account_payment payment
                           JOIN account_move move
                             ON move.id = payment.move_id
                           JOIN account_move_line line
                             ON line.move_id = move.id
                           JOIN account_partial_reconcile part
                             ON part.debit_move_id = line.id
                                 OR part.credit_move_id = line.id
                           JOIN account_move_line counterpart_line
                             ON part.debit_move_id = counterpart_line.id
                                 OR part.credit_move_id = counterpart_line.id
                           JOIN account_move invoice
                             ON invoice.id = counterpart_line.move_id
                           JOIN account_account account
                             ON account.id = line.account_id
                           JOIN res_partner partn
                             ON partn.id = move.partner_id
                    WHERE  account.internal_type = 'receivable'
                           AND line.id != counterpart_line.id
                           AND invoice.move_type = 'out_invoice'
                           AND invoice.invoice_finance_charges = False
                           AND payment.partner_type = 'customer'
                           AND payment.payment_type = 'inbound'
                           AND move.date >= %s
                           AND partn.finance_charges = True
                           AND invoice.invoice_date_due < %s
                    GROUP  BY invoice.partner_id) s
            GROUP  BY partner_id
        """

        self._cr.execute(query, [self.due_date_prior_to,self.due_date_prior_to,self.due_date_prior_to])
        results = self._cr.dictfetchall()
        finance_threshold = not finance_threshold and 0 or float(finance_threshold)
        for result in results:
            invoice_ref = []
            invoice_ref.extend(inv_ref for inv_lst in result.get('ref') for inv_ref in inv_lst if inv_ref not in invoice_ref)
            if result.get('amount_due') > 0:
                finance_charge_amount = round((result.get('amount_due') * float(finance_param)) / 100, 2)
                if finance_charge_amount >= finance_threshold:
                    product = self.env['product.product'].browse(int(product_param))
                    invoice_vals = {
                        'move_type': 'out_invoice',
                        'partner_id': result.get('partner_id'),
                        'invoice_date': fields.Date.today(),
                        'invoice_payment_term_id': int(payment_param),
                        'ref': 'Finance charge - {} for invoices {}'.format((self.due_date_prior_to - relativedelta(months=1)).strftime('%B %Y'), ', '.join(invoice_ref)),
                        'invoice_finance_charges': True,
                        'invoice_line_ids': [(0, 0, {
                            'product_id': int(product_param),
                            'name' : product.display_name,
                            'product_uom_id' : product.uom_id.id,
                            'quantity' : 1,
                            'price_unit' : finance_charge_amount,
                        })]
                        }
                    self.env['account.move'].create(invoice_vals)

    def process_finance_charge_invoices(self):
        _logger.info("Finance Charge process started.")
        partners = self.env['res.partner']
        partner_inv_dict = {}
        domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('invoice_date_due', '<', self.due_date_prior_to),
                ('invoice_finance_charges', '=', False)]
        if self.env.context.get('active_model', False) == 'account.move' and self.env.context.get('active_ids', False):
            domain.append(('id', 'in', self.env.context.get('active_ids')))
            invoice_ids = self.env['account.move'].search(domain)

            for invoice_id in invoice_ids:
                if invoice_id.partner_id in partner_inv_dict:
                    partner_inv_dict.update({invoice_id.partner_id: partner_inv_dict.get(invoice_id.partner_id) + invoice_id})
                else:
                    partner_inv_dict.update({invoice_id.partner_id:invoice_id})
            for partner, invoice_ids  in partner_inv_dict.items():
                self.create_finance_charge_invoices(partner=partner, invoice_ids=invoice_ids)
        elif self.env.context.get('active_model', False) == 'res.partner' and self.env.context.get('active_ids', False):
            partners = partners.browse(self._context.get('active_ids')).filtered(lambda p:p.finance_charges)
        else:
            self.create_finance_charge_invoices_for_all()
        for partner in partners:
            self.create_finance_charge_invoices(partner=partner)
        _logger.info("Finance Charge process ends.")

    def _process_create_finance_charge(self):
        new_cr = self.pool.cursor()
        self = self.with_env(self.env(cr=new_cr))
        self.process_finance_charge_invoices()
        self._cr.commit()
        new_cr.close()
        return {}

    def process_create_finance_charge_invoices(self):
        threaded_calculation = threading.Thread(target=self._process_create_finance_charge, args=())
        threaded_calculation.start()
        return {'type': 'ir.actions.act_window_close'}
