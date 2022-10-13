# Copyright 2015 Tecnativa - Sergio Teruel
# Copyright 2015 Tecnativa - Carlos Dauden
# Copyright 2016-2017 Tecnativa - Vicent Cubells
# Copyright 2019 Valentin Vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    consume_material = fields.Boolean(
        help="If you mark this check, when a task goes to this state, "
             "it will consume the associated materials",
    )

    wip_to_cust_material = fields.Boolean(
        help="If you mark this check, when a task goes to this state, "
             "it will move material from consume to customer",
    )


class Task(models.Model):
    _inherit = "project.task"

    @api.depends('material_ids.stock_move_id')
    def _compute_stock_move(self):
        for task in self:
            task.stock_move_ids = task.mapped('material_ids.stock_move_id')

    @api.depends('material_ids.analytic_line_id')
    def _compute_analytic_line(self):
        for task in self:
            task.analytic_line_ids = task.mapped(
                'material_ids.analytic_line_id')

    @api.depends('stock_move_ids.state')
    def _compute_stock_state(self):
        for task in self:
            if not task.stock_move_ids:
                task.stock_state = 'pending'
            else:
                states = task.mapped("stock_move_ids.state")
                for state in ("confirmed", "assigned", "done"):
                    if state in states:
                        task.stock_state = state
                        break

    picking_id = fields.Many2one(
        "stock.picking",
        related="stock_move_ids.picking_id",
    )
    stock_move_ids = fields.Many2many(
        comodel_name='stock.move',
        compute='_compute_stock_move',
        string='Stock Moves',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Move Analytic Account',
        help='Move created will be assigned to this analytic account',
    )
    analytic_line_ids = fields.Many2many(
        comodel_name='account.analytic.line',
        compute='_compute_analytic_line',
        string='Analytic Lines',
    )

    consume_material = fields.Boolean(
        related='stage_id.consume_material',
    )

    wip_to_cust_material = fields.Boolean(
        related='stage_id.wip_to_cust_material',
    )

    stock_state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('assigned', 'Assigned'),
            ('done', 'Done')],
        compute='_compute_stock_state',
    )
    location_source_id = fields.Many2one(
        comodel_name='stock.location',
        string='Source Location',
        index=True,
        help='Keep this field empty to use the default value from'
        ' the project.',
    )
    location_dest_id = fields.Many2one(
        comodel_name='stock.location',
        string='Destination Location',
        index=True,
        help='Keep this field empty to use the default value from'
        ' the project.'
    )

    def unlink_stock_move(self):
        res = False
        moves = self.mapped('stock_move_ids')
        moves_done = moves.filtered(lambda r: r.state == 'done')
        if not moves_done:
            moves.filtered(lambda r: r.state == 'assigned')._do_unreserve()
            moves.filtered(
                lambda r: r.state in {'waiting', 'confirmed', 'assigned'}
            ).write({'state': 'draft'})
            res = moves.unlink()
        return res

    def write(self, vals):
        res = super(Task, self).write(vals)
        logging.warning("====In write statement - vals is %s", vals)
        for task in self:
            # Trying to consume material



            if 'stage_id' in vals or 'material_ids' in vals:
                _logger.warning("Stage ID or materials were passed !!!")
                logging.warning("Trying to consume material======== %s", vals)
                if task.consume_material:
                    logging.warning("====How many times am I running this!!!!")
                    todo_lines = task.material_ids.filtered(
                        lambda m: not m.stock_move_id
                    )
                    if todo_lines:
                        todo_lines.create_stock_move()
                        #todo_lines.create_analytic_line()

                # Edgar - This is firing - we dont want analytic lines anyway
                # else:
                #     logging.warning("=======When is this fired!!!!!!!!!")
                #     if task.unlink_stock_move() and task.material_ids.mapped(
                #             'analytic_line_id'):
                #         raise exceptions.Warning(
                #             _("You can't move to a not consume stage if "
                #               "there are already analytic lines")
                #         )
                #     task.material_ids.mapped('analytic_line_id').unlink()
                if task.wip_to_cust_material and task.stage_id.name == "Done":
                    logging.warning("====Doing WIP to Stock ")
                    todo_lines = task.material_ids.filtered(
                        lambda m: m.stock_move_id
                    )
                    if todo_lines:
                        logging.warning("======The to do lines are %s", todo_lines)
                        #raise UserError(_('We have the to do lines for WIP to STOCK '))
                        todo_lines.create_stock_move_from_wip()
                        #todo_lines.create_stock_move_to_cust()
            else:
                _logger.warning("NEITHER stage or material_ids were passed!!!")
                #print(err)

        #print(err)
        return res

    def unlink(self):
        self.mapped('stock_move_ids').unlink()
        self.mapped('analytic_line_ids').unlink()
        return super(Task, self).unlink()

    def action_assign(self):
        self.mapped('stock_move_ids')._action_assign()

    def action_done(self):
        for move in self.mapped('stock_move_ids'):
            move.quantity_done = move.product_uom_qty
        self.mapped('stock_move_ids')._action_done()


class ProjectTaskMaterial(models.Model):
    _inherit = "project.task.material"

    stock_move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Stock Move',
    )
    analytic_line_id = fields.Many2one(
        comodel_name='account.analytic.line',
        string='Analytic Line',
    )
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        oldname="product_uom",
        string='Unit of Measure',
    )
    product_id = fields.Many2one(
        domain="[('type', 'in', ('consu', 'product'))]"
    )
    ticked = fields.Boolean('To Consume')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id.id
        return {'domain': {'product_uom_id': [
            ('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    def _prepare_stock_move(self, source_loc, dest_loc):
        logging.warning("Preparing stock move records")
        product = self.product_id
        #source_loc = self.env['stock.warehouse'].search([('branch_id','=', self.task_id.branch_id.id)]).lot_stock_id.id
        logging.warning("Source location is %s and dest %s", source_loc, dest_loc)
        #source_loc = pick_type.default_location_src_id.id
        #est_loc = pick_type.default_location_dest_id.id
        res = {
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': self.product_uom_id.id or product.uom_id.id,
            'product_uom_qty': self.quantity,
            'origin': self.task_id.name,
            'location_id':source_loc,
            # 'location_dest_id':
            #     self.task_id.location_dest_id.id or
            #     self.task_id.project_id.location_dest_id.id or
            #     self.env.ref('stock.stock_location_customers').id,
            'location_dest_id': dest_loc,
            'branch_id': self.task_id.branch_id.id,
            'x_project_id': self.task_id.project_id.id,
            'x_task_id': self.task_id.id,
            'price_unit': self.price_unit,
        }
        logging.warning("====RES is %s", res)


        return res

    def create_stock_move(self):
        logging.warning("Creating stock move records!!!!")
        task = self[0].task_id
        task_custom_line_obj = self.env['task.custom.lines']

        if task.consume_material and not task.wip_to_cust_material:
            source_loc = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.task_id.branch_id.id)]).lot_stock_id.id

            source_wh = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.task_id.branch_id.id)]).id
            # pick_type = self.env.ref(
            #     'project_task_material_stock.project_task_material_picking_type')
            pick_type = self.env['stock.picking.type'].search(
                [('warehouse_id' ,'=', source_wh),
                 ('default_location_src_id', '=', source_loc),
                 ('default_location_dest_id','=', task.project_id.location_dest_id.id),
                 ('code', '=', 'internal')])

            # logging.warning("The Pick type is %s %s", source_wh, pick_type.name)
            # if task.picking_id:
            #     raise UserError(_('====A picking already exist for this line '))

            # There is a problem with the below code - here are the reasons
            # For starters we cater for individual lines to be ticked
            # However on the first write, a stock picking record is created
            # picking_id is false as there are no stock_move records created yet.
            # See how the picking_id field is created in project.task
            # On the second write, when the lines are ticked, it creates the valid stock picking
            # record with the move lines.
            # This code must be adjusted not to create stock picking records
            # Need to sort this out later

            picking_id = task.picking_id or self.env['stock.picking'].create({
                'origin': "{}/{}".format(task.project_id.name, task.name),
                'partner_id': task.partner_id.id,
                'picking_type_id': pick_type.id,
                'location_id': source_loc,
                'location_dest_id': pick_type.default_location_dest_id.id,
                'branch_id': task.branch_id.id,
            })

            for line in self:
                if line.ticked:
                    # Search for any previous moves for this product having the same characteristics
                    has_move = self.env['stock.move'].search([('origin', '=', task.name),
                                                              ('location_id', '=', source_loc),
                                                              ('branch_id', '=', self.task_id.branch_id.id),
                                                              ('product_id', '=', line.product_id.id)])
                    if has_move:
                        raise UserError(_('A consumption already exist for this job and product %s %s', task.name,
                                          line.product_id.name))

                    move_vals = line._prepare_stock_move(source_loc,pick_type.default_location_dest_id.id)
                    move_vals.update({'picking_id': picking_id.id or False})
                    move_id = self.env['stock.move'].create(move_vals)
                    line.stock_move_id = move_id.id

                    # set actuals to standrd if not already set
                    custom_line = task_custom_line_obj.search(
                        [('task_custom_id', '=', task.id), ('product_id', '=', move_vals['product_id'])])
                    if custom_line.actual_qty == 0:
                        custom_line.actual_qty = custom_line.qty
                    if custom_line.actual_cost == 0:
                        custom_line.actual_cost = custom_line.total_cost

        if  task.wip_to_cust_material:

            source_loc = task.project_id.location_wip_source_id.id

            source_wh = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.task_id.branch_id.id)]).id
            pick_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', source_wh),
                 ('default_location_src_id', '=', source_loc),
                 ('default_location_dest_id', '=', task.project_id.location_wip_dest_id.id),
                 ('code', '=', 'internal')])

            logging.warning("The Pick type for stock return from WIP is %s %s %s %s", source_loc, source_wh,task.project_id.location_wip_dest_id.id, pick_type.name)
            picking_id = task.picking_id or self.env['stock.picking'].create({
                'origin': "{}/{}".format(task.project_id.name, task.name),
                'partner_id': task.partner_id.id,
                'picking_type_id': pick_type.id,
                'location_id': source_loc,
                'location_dest_id': pick_type.default_location_dest_id.id,
                'branch_id': task.branch_id.id,
            })
            for line in self:

                # Search for any previous moves for this product having the same characteristics
                has_move = self.env['stock.move'].search([('origin', '=', task.name),
                                                          ('location_id', '=', source_loc),
                                                          ('branch_id', '=', self.task_id.branch_id.id),
                                                          ('product_id', '=', line.product_id.id),
                                                          ('x_project_id','=', task.project_id.id),
                                                          ('x_task_id','=', task.id),
                                                          ('picking_type_id', '=', pick_type.id)])
                if has_move:
                    raise UserError(_('A return from WIP already exist for this job and product %s %s', task.name,
                                      line.product_id.name))

                move_vals = line._prepare_stock_move(source_loc, pick_type.default_location_dest_id.id)
                logging.warning("Move vals are %s", move_vals)
                # raise UserError(_('You are about to return this item from WIP  product '))
                move_vals.update({'picking_id': picking_id.id or False})
                move_id = self.env['stock.move'].create(move_vals)
                #line.stock_move_id = move_id.id




        #pick_type = self.env['stock.picking.type'].search([('default_location_src_id','=',source_loc ),('code','=','outgoing')])

    def create_stock_move_from_wip(self):
        logging.warning("=======Creating stock move records from WIP to Stock!!!!")
        task = self[0].task_id
        if task.wip_to_cust_material:

            source_loc = task.project_id.location_wip_source_id.id
            source_wh = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.task_id.branch_id.id)]).id
            pick_type = self.env['stock.picking.type'].search(
                [('warehouse_id', '=', source_wh),
                 ('default_location_src_id', '=', source_loc),
                 ('default_location_dest_id', '=', task.project_id.location_wip_dest_id.id),
                 ('code', '=', 'internal')])

            logging.warning("The Pick type for stock return from WIP is %s %s %s %s", source_loc, source_wh,task.project_id.location_wip_dest_id.id, pick_type.name)

            picking_id = self.env['stock.picking'].create({
                'origin': "{}/{}".format(task.project_id.name, task.name),
                'partner_id': task.partner_id.id,
                'picking_type_id': pick_type.id,
                'location_id': source_loc,
                'location_dest_id': pick_type.default_location_dest_id.id,
                'branch_id': task.branch_id.id,
            })
            if picking_id:
                logging.warning("The picking id is %s", picking_id.id)
            #raise UserError(_('You are about to return this item from WIP  product '))
            for line in self:

                # Search for any previous moves for this product having the same characteristics
                # I think there is a better way of checking this
                has_move = self.env['stock.move'].search([('origin', '=', task.name),
                                                          ('location_id', '=', source_loc),
                                                          ('branch_id', '=', self.task_id.branch_id.id),
                                                          ('product_id', '=', line.product_id.id),
                                                          ('x_project_id','=', task.project_id.id),
                                                          ('x_task_id','=', task.id),
                                                          ('picking_type_id', '=', pick_type.id)])
                if has_move:
                    raise UserError(_('A return from WIP already exist for this job and product %s %s %s', task.name,
                                      line.product_id.name,pick_type.name ))
                # else:
                #     raise UserError(_('A return from WIP does not exist for this job and product %s %s %s', task.name,
                #                       line.product_id.name, pick_type.name))

                move_vals = line._prepare_stock_move(source_loc, pick_type.default_location_dest_id.id)
                logging.warning("Move vals are %s", move_vals)
                # raise UserError(_('You are about to return this item from WIP  product '))
                move_vals.update({'picking_id': picking_id.id or False})
                move_id = self.env['stock.move'].create(move_vals)
                move_id._action_assign()
                logging.warning("-====move id is %s", move_id)
                for mv_line in move_id.move_line_ids:
                    mv_line.qty_done = move_vals.get('product_uom_qty')
                    logging.warning("Line is %s %s %s", mv_line.picking_id.name, mv_line.move_id.reference, mv_line.qty_done)

                #move_id._action_done()
                #line.stock_move_id = move_id.id
            #picking_id._action_done()
            picking_id.button_validate()
            #picking_id.action_confirm()






        #pick_type = self.env['stock.picking.type'].search([('default_location_src_id','=',source_loc ),('code','=','outgoing')])

    def create_stock_move_to_cust(self):
        logging.warning("=======Creating stock move records from Stock to Customer From WIP!!!!")
        task = self[0].task_id
        if task.wip_to_cust_material:

            source_loc = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.task_id.branch_id.id)]).lot_stock_id.id
            pick_type = self.env['stock.picking.type'].search(
                [('default_location_src_id', '=', source_loc), ('code', '=', 'outgoing')])
            # source_wh = self.env['stock.warehouse'].search(
            #     [('branch_id', '=', self.task_id.branch_id.id)]).id
            # pick_type = self.env['stock.picking.type'].search(
            #     [('warehouse_id', '=', source_wh),
            #      ('default_location_src_id', '=', source_loc),
            #      ('default_location_dest_id', '=', task.project_id.location_wip_dest_id.id),
            #      ('code', '=', 'internal')])

            logging.warning("The Pick type for stock to CUST is is %s %s %s %s", source_loc,pick_type.name)

            picking_id = self.env['stock.picking'].create({
                'origin': "{}/{}".format(task.project_id.name, task.name),
                'partner_id': task.partner_id.id,
                'picking_type_id': pick_type.id,
                'location_id': source_loc,
                'location_dest_id': pick_type.default_location_dest_id.id,
                'branch_id': task.branch_id.id,
            })
            if picking_id:
                logging.warning("The picking id is %s", picking_id.id)
            #raise UserError(_('You are about to return this item from WIP  product '))
            for line in self:

                # Search for any previous moves for this product having the same characteristics
                # I think there is a better way of checking this
                has_move = self.env['stock.move'].search([('origin', '=', task.name),
                                                          ('location_id', '=', source_loc),
                                                          ('branch_id', '=', self.task_id.branch_id.id),
                                                          ('product_id', '=', line.product_id.id),
                                                          ('x_project_id','=', task.project_id.id),
                                                          ('x_task_id','=', task.id),
                                                          ('picking_type_id', '=', pick_type.id)])
                if has_move:
                    raise UserError(_('An issue to CUST already exist for this job and product %s %s %s', task.name,
                                      line.product_id.name,pick_type.name ))
                # else:
                #     raise UserError(_('A return from WIP does not exist for this job and product %s %s %s', task.name,
                #                       line.product_id.name, pick_type.name))

                move_vals = line._prepare_stock_move(source_loc, pick_type.default_location_dest_id.id)
                logging.warning("Move vals are %s", move_vals)
                # raise UserError(_('You are about to return this item from WIP  product '))
                move_vals.update({'picking_id': picking_id.id or False})
                move_id = self.env['stock.move'].create(move_vals)
                move_id._action_assign()
                logging.warning("-====move id is %s", move_id)
                for mv_line in move_id.move_line_ids:
                    mv_line.qty_done = move_vals.get('product_uom_qty')
                    logging.warning("Line is %s %s %s", mv_line.picking_id.name, mv_line.move_id.reference, mv_line.qty_done)

                #move_id._action_done()
                #line.stock_move_id = move_id.id
            #picking_id._action_done()
            picking_id.button_validate()
            #picking_id.action_confirm()






        #pick_type = self.env['stock.picking.type'].search([('default_location_src_id','=',source_loc ),('code','=','outgoing')])



    def _prepare_analytic_line(self):
        product = self.product_id
        company_id = self.env['res.company']._company_default_get(
            'account.analytic.line')
        analytic_account = getattr(self.task_id, 'analytic_account_id', False)\
            or getattr(self.task_id.project_id, 'analytic_account_id', False)
        if not analytic_account:
            raise exceptions.Warning(
                _("You must assign an analytic account for this task/project.")
            )
        res = {
            'name': self.task_id.name + ': ' + product.name,
            'ref': self.task_id.name,
            'product_id': product.id,
            'unit_amount': self.quantity,
            'account_id': analytic_account.id,
            'user_id': self._uid,
            'product_uom_id': self.product_uom_id.id,
            'company_id': analytic_account.company_id.id or
            self.env.user.company_id.id,
            'partner_id': self.task_id.partner_id.id or
            self.task_id.project_id.partner_id.id or None,
            'task_material_id': [(6, 0, [self.id])],
        }
        amount_unit = \
            self.product_id.standard_price
        amount = amount_unit * self.quantity or 0.0
        result = round(amount, company_id.currency_id.decimal_places) * -1
        vals = {'amount': result}
        if 'employee_id' in self.env['account.analytic.line']._fields:
            vals['employee_id'] = \
                self.env['hr.employee'].search([
                    ('user_id', '=', self.task_id.user_id.id)
                ], limit=1).id
        res.update(vals)
        return res

    def create_analytic_line(self):
        for line in self:
            if line.ticked:
                self.env['account.analytic.line'].create(
                    line._prepare_analytic_line())

    def unlink_stock_move(self):
        if not self.stock_move_id.state == 'done':
            if self.stock_move_id.state == 'assigned':
                self.stock_move_id._do_unreserve()
            if self.stock_move_id.state in (
               'waiting', 'confirmed', 'assigned'):
                self.stock_move_id.write({'state': 'draft'})
            picking_id = self.stock_move_id.picking_id
            self.stock_move_id.unlink()
            if not picking_id.move_line_ids_without_package and \
               picking_id.state == 'draft':
                picking_id.unlink()

    def _update_unit_amount(self):
        # The analytical amount is updated with the value of the
        # stock movement, because if the product has a tracking by
        # lot / serial number, the cost when creating the
        # analytical line is not correct.

        # Commented the below function as v14 does not have a value field on the stock move table
        # I assume at this stage the price_unit field is the one to use
        # for sel in self.filtered(lambda x: x.stock_move_id.state == 'done' and
        #                          x.analytic_line_id.amount !=
        #                          x.stock_move_id.value):
        #     sel.analytic_line_id.amount = sel.stock_move_id.value

        for sel in self.filtered(lambda x: x.stock_move_id.state == 'done' and
                                 x.analytic_line_id.amount !=
                                 x.stock_move_id.price_unit):
            sel.analytic_line_id.amount = sel.stock_move_id.price_unit

    def unlink(self):
        self.unlink_stock_move()
        if self.stock_move_id:
            raise exceptions.Warning(
                _("You can't delete a consumed material if already "
                  "have stock movements done.")
            )
        self.analytic_line_id.unlink()
        return super(ProjectTaskMaterial, self).unlink()
