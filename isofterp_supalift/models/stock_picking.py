from odoo import api, fields, models
from odoo.tools import float_is_zero, OrderedSet

import logging
_logger = logging.getLogger(__name__)

class StockPick(models.Model):
    _inherit = "stock.picking"

    x_branch_id = fields.Integer('Old Branch')

    def button_validate(self):
        res = super(StockPick,self).button_validate()

        # Update job card
        task_custom_lines_obj = self.env['task.custom.lines']
        project_task_material_obj = self.env['project.task.material']

        for picking in self:
            _logger.warning("The move record is %s", picking.name)

            # Icoming Stock via Vendor bills
            if self.picking_type_id.code == 'incoming':
                for move_line in picking.move_line_ids:
                    _logger.warning("The move record is %s", move_line.qty_done)
                    # If an associated vendor bill exist, find the line matching the given line
                    # and get the value on local currency
                    #vendor_bills = self.search('account.move').mapped('picking_id.invoice_picking_id)
                    invoice = self.env['account.move'].search([('invoice_picking_id','=', picking.id)])
                    _logger.warning("The invoice is record is %s", invoice.name)
                    for invoice_line in invoice.invoice_line_ids:
                        if invoice_line.product_id == move_line.product_id:
                            _logger.warning("The product record is %s", invoice_line.product_id.name)
                            if invoice_line and move_line.qty_done > 0:
                                if invoice_line.x_task_id and invoice_line.x_project_id:
                                    _logger.warning("Invoice line status = %s",invoice_line.exclude_from_invoice_tab )
                                    if not invoice_line.exclude_from_invoice_tab:
                                        custom_line = task_custom_lines_obj.search([('product_id', 'ilike', invoice_line.product_id.id),
                                                                                    ('task_custom_id', '=', invoice_line.x_task_id.id)])
                                        if custom_line:
                                            custom_line.actual_qty += move_line.qty_done
                                            custom_line.actual_cost += invoice_line.amount_residual
                                            custom_line.actual_profit = custom_line.price - custom_line.actual_cost
                                            # custom_line.actual_profit = custom_line.quoted_price - custom_line.actual_cost

                                        else:
                                            if invoice_line.x_task_id and invoice_line.x_project_id:
                                                vals = {  # Cant find record so create a quote line
                                                    'task_custom_id': invoice_line.x_task_id.id,
                                                    'task_id': invoice_line.x_task_id.id,
                                                    'product_id': invoice_line.product_id.id,
                                                    'product_uom': invoice_line.product_uom_id.id,
                                                    'qty': move_line.qty_done,
                                                    'total_cost': move_line.qty_done * invoice_line.amount_residual,
                                                    'price': move_line.qty_done * invoice_line.amount_residual,
                                                    'purchase_price': invoice_line.amount_residual,
                                                    'unit_price': invoice_line.amount_residual,

                                                    'actual_qty': move_line.qty_done,
                                                    'actual_cost': invoice_line.amount_residual,
                                                    'actual_profit': move_line.qty_done * invoice_line.amount_residual * -1,
                                                    'notes': move_line.move_id.name,
                                                }
                                                new_line = task_custom_lines_obj.create(vals)
                                                new_line.update_selling_from_other_source()
                                                new_line._calculate_unit_price()
                                                if new_line:
                                                    print("New line created")
                                                else:
                                                    print("No task line created")
                                        # Create a Material line
                                        material = project_task_material_obj.search(
                                            [('task_id', '=', invoice_line.x_task_id.id), ('product_id', '=', move_line.product_id.id)])
                                        if material:
                                            material.quantity = custom_line.actual_qty
                                            material.ticked = True
                                        else:
                                            if invoice_line.x_task_id and invoice_line.x_project_id:
                                                logging.warning("QTY is %s", move_line.qty_done)
                                                vals = {
                                                    'task_id': invoice_line.x_task_id.id,
                                                    'product_id': move_line.product_id.id,
                                                    'description': invoice_line.name,
                                                    'quantity': move_line.qty_done,
                                                    'product_uom_id': move_line.product_uom_id.id,
                                                    'price_unit': invoice_line.amount_residual,
                                                    'ticked': True
                                                }
                                                # print(vals)
                                                _logger.warning("Creating new project task material record %s", vals)
                                                new_line = project_task_material_obj.create(vals)

                                        # Update the job stage
                                        new_stage = self.env['project.task.type'].search([('name', '=', 'WIP')])
                                        if invoice_line.x_task_id.stage_id.sequence < new_stage.sequence:
                                            invoice_line.x_task_id.stage_id = new_stage.id

        return res


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    x_branch_id = fields.Integer('Old Branch')

class StockLocation(models.Model):
    _inherit = "stock.location"

    x_branch_id = fields.Integer('Old Branch')

class StockMove(models.Model):
    """Inherit Stock Move."""

    _inherit = "stock.move"

    x_project_id = fields.Many2one('project.project', 'Equipment')
    x_task_id = fields.Many2one('project.task', 'Job Number')
    x_branch_id = fields.Integer('Old Branch')

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                  cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        # The cost value is taken from the stock master file which is not desireable
        # We need to take the cost value where ever the cost price is being used
        _logger.warning("==== Before - Inherited _create_account_move_line cost %s", cost)
        cost = self.price_unit
        _logger.warning("==== After - Inherited _create_account_move_line cost %s", cost)


        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            _logger.warning("==== The account move line are %s", move_lines)
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()

    def _account_entry_move(self, qty, description, svl_id, cost):
        _logger.warning("===========The cost for this accounting move is %s %s %s", description, qty, cost)
        """ Accounting Valuation Entries """
        self.ensure_one()
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return False
        if self.restrict_partner_id:
            # if the move isn't owned by the company, we don't make any valuation
            return False

        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False

        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            if self._is_returned(valued_type='in'):
                self.with_company(company_to)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty,
                                                                        description, svl_id, cost)
            else:
                self.with_company(company_to)._create_account_move_line(acc_src, acc_valuation, journal_id, qty,
                                                                        description, svl_id, cost)

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = self.price_unit
            cost = -1 * cost
            _logger.warning("====The cost in _account_entry_move is %s - cost is stil fine here", cost)
            #print(err)
            if self._is_returned(valued_type='out'):
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_src, journal_id, qty,
                                                                          description, svl_id, cost)
            else:
                self.with_company(company_from)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty,
                                                                          description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            if self._is_dropshipped():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_src, acc_valuation, journal_id,
                                                                                 qty, description, svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_dest, journal_id,
                                                                                 qty, description, svl_id, cost)
            elif self._is_dropshipped_returned():
                if cost > 0:
                    self.with_company(self.company_id)._create_account_move_line(acc_valuation, acc_src, journal_id,
                                                                                 qty, description, svl_id, cost)
                else:
                    cost = -1 * cost
                    self.with_company(self.company_id)._create_account_move_line(acc_dest, acc_valuation, journal_id,
                                                                                 qty, description, svl_id, cost)

        if self.company_id.anglo_saxon_accounting:
            # Eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
            self._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=self.product_id)

    def _create_out_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        _logger.warning("=====Inherited - _create_out_svl")
        svl_vals_list = []
        for move in self:
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done,
                                                                                     move.product_id.uom_id)
            if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
                continue
            svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)

            _logger.warning("SVL at line 227 - _prepare_out_svl_vals %s %s move.task_id", svl_vals, move.x_task_id)
            # If this move is related to a task and task custom line - get the actual cost and override what the _prepare_out_svl_vals gives
            if move.x_task_id:
                task_line = self.env['task.custom.lines'].search([('task_custom_id','=', move.x_task_id.id),
                                                                  ('product_id','=', move.product_id.id),])
                if task_line:
                    product_cost = task_line.actual_cost
                    svl_vals['value'] = -product_cost
                    svl_vals['unit_cost'] = product_cost
                # else:
                #     print("could not find the line", err)

            svl_vals.update(move._prepare_common_svl_vals())
            _logger.warning("SVL at line 191 - _prepare_common_svl_vals with out svl vals %s", svl_vals)
            #print(err)
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')
            svl_vals_list.append(svl_vals)
        return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in res:
            _logger.warning("The move is ")

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_value(self):
        """ For standard and AVCO valuation, compute the current accounting
                valuation of the quants by multiplying the quantity by
                the standard price. Instead for FIFO, use the quantity times the
                average cost (valuation layers are not manage by location so the
                average cost is the same for all location and the valuation field is
                a estimation more than a real value).
                """
        for quant in self:
            quant.currency_id = quant.company_id.currency_id
            # If the user didn't enter a location yet while enconding a quant.
            if not quant.location_id:
                quant.value = 0
                return

            if not quant.location_id._should_be_valued() or \
                    (quant.owner_id and quant.owner_id != quant.company_id.partner_id):
                quant.value = 0
                continue
            if quant.product_id.cost_method == 'fifo':
                quantity = quant.product_id.with_company(quant.company_id).quantity_svl
                if float_is_zero(quantity, precision_rounding=quant.product_id.uom_id.rounding):
                    quant.value = 0.0
                    continue
                average_cost = quant.product_id.with_company(quant.company_id).value_svl / quantity
                quant.value = quant.quantity * average_cost
            else:
                quant.value = quant.quantity * quant.product_id.with_company(quant.company_id).standard_price


