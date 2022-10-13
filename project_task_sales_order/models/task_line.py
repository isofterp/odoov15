# -*- coding: utf-8 -*

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging
_logger = logging.getLogger(__name__)

class TaskCustomLines(models.Model):
    _name = 'task.custom.lines'
    _description = "Task Custom Lines"


    task_custom_id = fields.Many2one(
        'project.task',
        string="Task"
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product",
        required=True
    )
    project_id = fields.Many2one(
        'project.project',
        string="Equipment",
        required=False
    )
    task_id = fields.Many2one(
        'project.task',
        string="Task",
        required=False
    )
    qty = fields.Float(
        string="Qty",
        default=1.0,
        required=True
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string="UOM",
        required=False
    )
    price = fields.Float(
        string="Q Tot-Price",
        required=True
    )
    unit_price = fields.Float(
        string="Q Unit-Price",
        required=True
    )

    total_cost = fields.Float(
        string="Total cost",
        required=True
    )
    purchase_price = fields.Float(
        string="Cost Price",
        required=True
    )
    actual_qty = fields.Float(
        string="Actual Qty",
        default=0,
        required=False
    )

    actual_cost = fields.Float(
        string="Actual Cost",
        required=False
    )
    actual_price = fields.Float(
        string="Actual Price",
        required=False
    )
    actual_profit = fields.Float(
        string="Actual Profit",
        required=False
    )
    markup_percent = fields.Float(
        string="Mark Up %",
        default=40.0,
        required=True
    )
    markup_percent_skip = fields.Boolean(string='skip markup percent')


    markup_amt = fields.Float(
        string="Q Profit",
    )
    markup_amt_skip = fields.Boolean(string='Skip markup amt')

    margin_percent = fields.Float(
        string="Margin %",

    )
    notes = fields.Text(
        string="Description",
    )
    is_so_line_created = fields.Boolean(
        string='Not Quoted',
    )

    name = fields.Char('Job Number')
    branch_id = fields.Many2one('res.branch', string="Branch")
    expense_id = fields.Many2one('hr.expense', string='Expense')
    x_job_type = fields.Char("Job Type")


    def populate_project_id(self):
        for rec in self.search([]):
            print ("Task Code - Project", rec.task_id.code, rec.task_custom_id.id, rec.task_id.project_id.name)
            rec.name = rec.task_custom_id.code
            rec.project_id = rec.task_custom_id.project_id.id


    def create(self, vals):
        """Overridden create method to create a Material record."""
        res = super(TaskCustomLines, self).create(vals)

        if "branch_id" not in vals:
            res.branch_id = res.task_custom_id.branch_id.id
        if "project_id" not in vals:
            res.project_id = res.task_custom_id.project_id.id
        if "name" not in vals:
            res.name = res.task_custom_id.code

        if "name" not in vals:
            res.x_job_type = res.task_custom_id.x_job_type.name

        if isinstance(vals, list):
            for rec in res:
                if rec.product_id.type == 'product':

                    vals = {
                        'task_id': rec.task_custom_id.id,
                        'product_id': rec.product_id.id,
                        'quantity': rec.qty,
                        'description': rec.notes,
                        'product_uom_id': 1,
                        'price_unit': rec.total_cost,

                    }
                    # print('vals in task_line - about to create', vals)
                    new_line = self.env['project.task.material'].create(vals)

        return res


    def _calculate_unit_price(self):
        for rec in self:
            if rec.product_id.product_tmpl_id.name == "Consumables":
                return
            if rec.product_id.categ_id.name == "Labour" or "Travel":
                pricelist_id = self.env['product.pricelist'].browse([self.task_custom_id.pricelist_id]).id
                pricelist_price = self.env['product.pricelist.item'].search(
                    [('pricelist_id', '=', pricelist_id.id), ('product_tmpl_id', '=', rec.product_id.name)])
                rec.unit_price = pricelist_price.fixed_price

            if not rec.unit_price:
                try:
                    rec.unit_price = rec.price / rec.qty
                except ZeroDivisionError:
                    rec.unit_price = 0

    def _lookup_pricelist(self, product_name):
        pricelist_id = self.env['product.pricelist'].browse([self.task_custom_id.pricelist_id]).id
        pricelist_price = self.env['product.pricelist.item'].search(
            [('pricelist_id', '=', pricelist_id.id), ('product_tmpl_id.name', '=', product_name)])
        return pricelist_price.fixed_price

    def _get_cost_price(self):
        if self.product_id:
            cost_price = self.product_id.product_tmpl_id.standard_price
            # print('cost_price @116=', cost_price)
            # The Cost price is normally obtained from the Product Master.
            # However, the user can also enter the Cost price and then we do not use the Product Cost Price
            if cost_price != self.purchase_price and self.purchase_price != 0:
                cost_price = self.purchase_price
            if self.product_id.can_be_expensed:
                cost_price = self.actual_cost
            # set the margin % back to what it was
            if self._origin.margin_percent:
                self.margin_percent = self._origin.margin_percent
            #print('on leaving _get_cost_price cost_price  =', cost_price)


            return cost_price

    def _calculate_markup_percent(self):
        if self.total_cost != 0:
            self.markup_percent = (self.markup_amt * 100) / self.total_cost

    def _get_actual_profit(self):
        if self.actual_cost:
            self.actual_profit = self.price - self.actual_cost
        else:
            self.actual_profit = self.price - self.total_cost
            # if self.product_id.name == 'Consumables' or self.product_id.name == 'Travel':
            #     self.actual_profit = self.price - self.total_cost
            # else:
            #     self.actual_profit = self.price - self.total_cost

        return self.actual_profit

    def _calculate_markup(self):
        # print("@176 ",self.qty * self.price, self.qty , self.price)
        if self.product_id:
            # self.price = self.qty * self.price
            # self.total_cost = self.qty * self._get_cost_price()

            self.markup_amt = self.price - self.total_cost
            self._get_actual_profit()

            #print("On leaving calcutale_margin price =", self.price, 'total cost = ', self.total_cost)

    def _recalculate_line_values(self):
        global global_vars
        if self.product_id:
            #print('in recalculate_line_values', self.qty)
            if self.product_id.name == 'Consumables':
                self.markup_percent = 7.5
                self._calculate_consumables()
                return
            if self.product_id.can_be_expensed:
                return

            cost_price = self._get_cost_price()
            self.total_cost = self.qty * cost_price # This is correct



            if self.product_id.categ_id.name == 'Labour' or self.product_id.name == 'Travel':
                self.price = self._lookup_pricelist(self.product_id.name) * self.qty
                #self.price = self._lookup_pricelist(self.product_id.name)
            else:
                # print("@133",cost_price,self.markup_percent,cost_price * self.markup_percent / 100)
                self.price = cost_price + (cost_price * self.markup_percent / 100)
                self._calculate_unit_price()

            self.purchase_price = cost_price
            #print("on leaving recalculate_line_values cost price =", cost_price, "sell price = ", self.price)
            self._calculate_markup()
            self._calculate_markup_percent()
            self.actual_profit = self._get_actual_profit()

            #print("************* self.actual_profit self.unit_price", self.actual_profit, self.unit_price)
            if self.product_id.categ_id.name == 'Labour':
                vals = {
                    'labour_price': self.price,
                    'labour_cost': self.total_cost,
                    'labour_qty': self.qty
                }
                return vals

    def _recalculate_line_values_for_unit_price(self):
        global global_vars
        if self.product_id:
            #print('in recalculate_line_values', self.qty)
            if self.product_id.name == 'Consumables':
                self.markup_percent = 7.5
                self._calculate_consumables()
                return
            if self.product_id.can_be_expensed:
                return

            cost_price = self._get_cost_price()
            self.total_cost = self.qty * cost_price

            if self.product_id.categ_id.name == 'Labour' or self.product_id.name == 'Travel':
                self.price = self._lookup_pricelist(self.product_id.name) * self.qty

                #self.price = self._lookup_pricelist(self.product_id.name)
            else:
                # print("@133",cost_price,self.markup_percent,cost_price * self.markup_percent / 100)
                self.price = cost_price + (cost_price * self.markup_percent / 100)
                self.price = self.qty * self.unit_price
                #self._calculate_unit_price()

            self.purchase_price = cost_price
            #print("on leaving recalculate_line_values cost price =", cost_price, "sell price = ", self.price)
            self._calculate_markup()
            self._calculate_markup_percent()
            self.actual_profit = self._get_actual_profit()

            #print("************* self.actual_profit self.unit_price", self.actual_profit, self.unit_price)
            if self.product_id.categ_id.name == 'Labour':
                vals = {
                    'labour_price': self.price,
                    'labour_cost': self.total_cost,
                    'labour_qty': self.qty
                }
                return vals

    def _calculate_consumables(self):
        labour_qty = 0
        labour_lines = self.search([('task_custom_id', '=', self.env.context.get('default_task_id')),
                              ('product_id.categ_id.name', '=', 'Labour')])
        if not labour_lines:
            raise Warning(_('Please load and Save a Labour record before adding a Consumable Line.'))
        for labour in labour_lines:
            # calculate  total hours for labour and get Standard Labour cost and selling price
            labour_qty += labour.qty
        #standard_labour_cost = self.env['product.template'].search([('name', '=', 'Labour Standard')]).standard_price
        standard_labour_cost = self.env['product.template'].search([('name', '=', 'Labour - Standard')]).standard_price

        if not standard_labour_cost:
            raise Warning(_('Please load a Product "Labour Standard" before continuing.'))
        standard_labour_price = self._lookup_pricelist('Labour - Standard')

        # print('labour price %s  total cost= %s' % (labour.unit_price, labour.total_cost))
        self.qty = labour_qty
        self.unit_price = (standard_labour_price * 7.5) / 100
        #print("self.unit_price= %s * 7.5/100 = %s" % (self.unit_price,standard_labour_price * 7.5 / 100))

        self.price = self.unit_price * labour_qty
        self.purchase_price = standard_labour_cost * 7.5 / 100  # this must be 7.5% of total cost price og Standard labour
        self.total_cost = self.purchase_price * self.qty
        self.markup_amt = self.price - self.total_cost
        # print("@ 218 in _calculate_consumables   self.price = %s  self.total_cost= %s diff = %s" %(self.price,self.total_cost,self.price - self.total_cost))
        self.actual_profit = self._get_actual_profit()
        self.markup_percent = self.purchase_price / standard_labour_cost * 100
        print("@ 230 price=",self.price ,  " purchase_rice=",  self.purchase_price,  "total_cost",  self.total_cost )

    def _check_is_so_line_created(self):
        if self.is_so_line_created:
            raise Warning(_('This line is on a Quotation and cannot be amended.'))

    # Check if line is quoted, can't update quoted costs, just actuals
    def _check_is_so_line_created_2(self):
        if self.is_so_line_created:
            return True
        else:
            return False

    @api.onchange('price')
    def change_price(self):
        self._check_is_so_line_created()

    @api.onchange('product_id')
    def product_id_change(self):
        global global_vars
        if self.product_id:
            #print('in onchange product_id', self.product_id.name)
            self.notes = self.product_id.code or self.product_id.name
            if self.product_id.name == 'Consumables':
                self._calculate_consumables()
                print('@ 248 on leaving self.unit_price =', self.unit_price, self.price)
            else:

                self.product_uom = self.product_id.uom_id.id
                self._recalculate_line_values()

    @api.onchange('markup_percent','purchase_price')
    def change_markup_percent(self):
        self._check_is_so_line_created()

        #if self.product_id.name == 'Consumables': return
        if self.product_id.name == 'Consumables': return
        self.price = (self.purchase_price + (self.purchase_price * self.markup_percent / 100)) * self.qty
        self.total_cost = self.purchase_price * self.qty
        self._calculate_unit_price()
        self.markup_amt_skip = True
        self.markup_percent_skip = True
        self.markup_amt = (self.price - self.total_cost)

        self.actual_profit = self._get_actual_profit()

        #print('==> Enter change_markup_percent',self.price,self.total_cost)

    @api.onchange('qty')
    def change_qty(self):

        if self.product_id.name == 'Consumables':
            return
        self._check_is_so_line_created()
        global global_vars
        global_vars = 'labour'
        self.product_id = self.product_id
        self.markup_amt_skip = True
        self.markup_percent_skip = True
        #print('########### entering onchange_qty', self.price, self.qty)
        self.total_cost = self.purchase_price * self.qty
        self.price = (self.purchase_price * self.markup_percent / 100 + self.purchase_price) * self.qty
        self._calculate_unit_price()
        self.markup_amt = self.price - self.total_cost
        self.actual_profit = self._get_actual_profit()

        # Labout values have changed so need to update Consumables
        #print("@@@@ 256",self.product_id.categ_id.name)
        if self.product_id.categ_id.name == 'Labour':
            # Find the Consumable record if it exists
            domain = [('task_custom_id', '=', self.env.context.get('default_task_id')), ('notes', 'ilike', 'Consum')]
            consumable_line = self.search(domain)
            #print("consumeable line ", consumable_line, domain)
            if consumable_line:
                #consumable_line.unit_price = self.price * 7.5 / 100
                consumable_line.purchase_price = self.total_cost * 7.5  / 100  # this must be 7.5% of total cost price of labour_task_line
                consumable_line.total_cost = consumable_line.purchase_price
                consumable_line.price =  consumable_line.unit_price * self.qty
                consumable_line.markup_amt = consumable_line.price - consumable_line.total_cost
                consumable_line.actual_profit =  consumable_line.markup_amt

                #print(" @131 We have updated the consumabe record")




            # domain = [('task_custom_id', '=', self.env.context.get('default_task_id')), ('product_id.name','=','Consumables')]
            # labour_task_line = self.search(domain)
            # if labour_task_line:
            #
            #     self = labour_task_line
            #     print("**** going to re calcutale Consumables")
            #     self.calculate_consumables()

    @api.onchange('markup_amt')
    def update_markup_amt(self):
        self._check_is_so_line_created()
        if self.markup_amt_skip:
            self.markup_amt_skip = False
        else:
            #print('in onchage markup_amt self.unit_price =', self.unit_price, self.markup_amt_skip, self.markup_amt)
            if self.product_id.name == "Consumables": return
            self.price = (self.purchase_price + self.markup_amt) * self.qty
            self.actual_profit = self._get_actual_profit()
        if self.markup_percent_skip:
            self.markup_percent_skip = False
        else:
            self._calculate_markup_percent()

    @api.onchange('actual_qty')
    def onchange_qty(self):
        self._check_is_so_line_created()
        if self.product_id.categ_id.name == "Travel":
            self.actual_cost = self.actual_qty * self.purchase_price


    @api.onchange('actual_cost')
    def onchange_cost(self):
        self._check_is_so_line_created()
        #print('in onchange_cost ', self.actual_cost)
        self.actual_profit = self._get_actual_profit()

    @api.onchange('unit_price')
    def onchange_unit_price(self):
        self._check_is_so_line_created()
        self._recalculate_line_values_for_unit_price()

    # Added by Edgar
    def update_selling_from_other_source(self):
        self.price = self.purchase_price + (self.purchase_price * self.markup_percent / 100)
        self.calculate_margin()

    def calculate_margin(self):
        # print("@176 ",self.qty * self.price, self.qty , self.price)
        self.price = self.qty * self.price
        # print("@187",self.qty , self.purchase_price)
        self.total_cost = self.qty * self.purchase_price
        if self.product_id.categ_id.name == 'Labour':
            self.markup_amt = self.price - self.total_cost
            # self.markup_amt = self.price - self.total_cost
        else:
            self.markup_amt = self.price - self.total_cost
        if self.total_cost != 0:
            self.markup_percent = (self.markup_amt * 100) / self.total_cost
            # self.margin_percent = (self.markup_amt * 100) / self.total_cost

        if self.actual_cost:
            self.actual_profit = self.price - self.actual_cost
        else:
            self.actual_profit = self.markup_amt

    def calculate_labour_margin(self):
        # print("@176 ",self.qty * self.price, self.qty , self.price)
        self.price = self.qty * self.price
        # print("@187",self.qty , self.purchase_price)
        self.total_cost = self.qty * self.purchase_price
        if self.product_id.categ_id.name == 'Labour':
            self.markup_amt = self.price + self.total_cost
            # self.markup_amt = self.price - self.total_cost
        else:
            self.markup_amt = self.price - self.total_cost
        if self.total_cost != 0:
            self.markup_percent = (self.markup_amt * 100) / self.total_cost
            # self.margin_percent = (self.markup_amt * 100) / self.total_cost

        if self.actual_cost:
            self.actual_profit = self.price - self.actual_cost
        else:
            self.actual_profit = self.markup_amt