# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)

class Processor():
    """Class container for processing stuff."""

    _counter = 0

    def addcounter(self):
        """Increment the counter."""
        # Some code here ...
        self._counter += 1


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _timesheet_postprocess(self, values):

        _logger.warning("Getting in here %s", self.env.context)
        res = super(AccountAnalyticLine, self)._timesheet_postprocess_values(values)
        if 'out_invoice' not in self.env.context.values():
            if self.task_id:
                # print("@16 values=",values['product_id'])
                # print(err)
                proc = Processor()
                proc.addcounter()
                #_logger.warning("Counter is %s", proc._counter)
                #print(self.product_id)
                custom_line_obj = self.env['task.custom.lines']
                for rec in self.task_id:
                    #_logger.warning("rec is %s ",rec.name)
                    task_line = custom_line_obj.search([('task_custom_id', '=', rec.id), ('product_id', '=', self.product_id.id)])

                tot_unit = tot_amount = 0
                for timesheet in self.search([('task_id', '=', self.task_id.id)]):
                    cost = timesheet.employee_id.timesheet_cost or 0.0
                    tot_amount += -timesheet.unit_amount * cost
                    tot_unit += timesheet.unit_amount

                pricelist_id = self.env['product.pricelist'].browse([self.task_id.pricelist_id]).id
                pricelist_price = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', pricelist_id.id), ('product_tmpl_id', '=', self.product_id.id)])

                if task_line:
                    # If the task line exist, lookup all the timesheet records for the given product type
                    # accumulate all the timesheet hours
                    # We must also check if any of the lines being amended is already quoted.
                    # If quoted, only the actuals must change however if not, all the line values must change
                    # and must match up to the actuals. Quotes values == actual values

                    timesheets = self.env['account.analytic.line'].search([('task_id','=', self.task_id.id),('product_id','=',self.product_id.id )], order='create_date asc')
                    tot_time = 0
                    descr_line = []
                    descr = ''

                    # This is crazy difficult to concatenate

                    for tm in timesheets:
                        _logger.warning("The timesheet entries are %s %s %s %s", tm.employee_id.name, tm.unit_amount, tm.date, tm.name)
                        tot_time += tm.unit_amount
                        if tm.name != "/" and len(tm.name) > 1:
                            descr_line.append(tm.name)
                            #descr += tm.name + "\n"

                    logging.warning("Description List is %s", descr_line)
                    for note in descr_line:
                        logging.warning("Note is %s", note)
                        if note != "/":
                            descr += note + '\n'
                    if len(descr) == 0:
                        descr = task_line.notes

                    _logger.warning("Total hours already for this job card is %s", descr)

                    # Update existing Labour task line with newly Calculated timesheet records
                    if not task_line._check_is_so_line_created_2():
                        logging.warning("Line is not quoted - so update quoted values")
                        # Update all line values
                        task_line.qty = tot_time
                        task_line.total_cost = tot_time * task_line.purchase_price
                        task_line.price = tot_time * pricelist_price.fixed_price
                        task_line.markup_amt = (tot_time * pricelist_price.fixed_price) - (task_line.purchase_price * tot_time)

                    task_line.actual_qty = tot_time # This is not a fix at all
                    task_line.actual_cost = tot_time * task_line.purchase_price
                    #_logger.warning("1. The task line values now is %s %s %s %s", task_line.price, task_line.actual_cost, task_line.actual_qty,
                    #               task_line.actual_profit)
                    task_line.actual_profit = task_line.price - task_line.actual_cost
                    task_line.notes = descr
                    #_logger.warning("2. The task line values now is %s %s %s %s", task_line.price, task_line.actual_cost, task_line.actual_qty,task_line.actual_profit)
                    # task_line.actual_qty = tot_unit
                    # task_line.actual_cost = tot_amount * -1
                    # task_line.actual_profit = task_line.price - task_line.actual_cost
                else:
                    # Create a new Labour task line
                    _logger.warning("Create timesheet entry!!!!!!")
                    product = self.env['product.product'].search([('id','=', self.product_id.id)])
                    # ###### Need to lookup price via the Price List

                    # rec.unit_price = pricelist_price.fixed_price

                    logging.warning("Labour name is %s", len(self.name))
                    if len(self.name) == 1:
                        notes = product.name
                    else:
                        notes = str(self.date) + "-" + self.name
                    vals = {
                        'notes': notes,
                        'task_id': self.task_id.id,
                        'task_custom_id': self.task_id.id,
                        'product_id': product.id,
                        'actual_qty': self.unit_amount,
                        'actual_cost': self.unit_amount * product.standard_price,
                        'qty': self.unit_amount,
                        #'markup_percent': 0,
                        'purchase_price': product.standard_price,
                        'total_cost': product.standard_price * self.unit_amount,
                        'unit_price': pricelist_price.fixed_price,
                        'price': self.unit_amount * pricelist_price.fixed_price,
                        #'actual_profit': task_line.price - task_line.actual_cost,
                        'actual_profit': (self.unit_amount * pricelist_price.fixed_price) - (product.standard_price * self.unit_amount),
                        'markup_amt': (self.unit_amount * pricelist_price.fixed_price) - (product.standard_price * self.unit_amount),
                        #'markup_percent': (self.markup_amt * 100) / self.total_cost,
                        'markup_percent': ((self.unit_amount * pricelist_price.fixed_price) -
                                           (product.standard_price * self.unit_amount)) * 100 /
                                          (product.standard_price * self.unit_amount),
                    }
                    logging.warning("Vals is %s %s", vals.get('qty'), vals.get('actual_qty'))
                    line = custom_line_obj.create(vals)
                    #line.calculate_labour_margin()
                # Update the job stage
                new_stage = self.env['project.task.type'].search([('name', '=', 'WIP')])
                if self.task_id.stage_id.sequence < new_stage.sequence:
                    self.task_id.stage_id = new_stage.id
        return res

