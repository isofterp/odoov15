# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo.tools.translate import _
from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError

class AccountInvoice(models.Model):
    _inherit= 'account.move'
    
    picking_count = fields.Integer(string="Count", copy=False)
    move_count = fields.Integer(string="Count" ,copy=False)
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id", copy=False)
    invoice_move_ids = fields.One2many('stock.move', 'move_id',string="Move Id")
    

    def button_cancel(self):
        if self.invoice_move_ids:
            self.invoice_move_ids._action_cancel()
        if self.invoice_picking_id:
            self.invoice_picking_id.action_cancel()

        return super(AccountInvoice,self).button_cancel()

    def button_draft(self):

        if self.invoice_move_ids:
            self.invoice_move_ids._action_cancel()
        if self.invoice_picking_id:
            self.invoice_picking_id.action_cancel()

        return super(AccountInvoice,self).button_draft()

    def action_stock_receive(self):
        move_list = []
        for invoice in self:
            if not invoice.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))

            invoice._create_stock_moves()

    def action_stock_picking(self):
        warehouse_obj = self.env['stock.warehouse']
        company_id = self.env.company
        ware_ids = self.env.company.warehouse_id
        if not ware_ids:
            raise Warning('You cannot  create picking because you not have not slected a warehouse!')

        for invoice in self:
            if invoice.move_type == 'in_invoice':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'incoming'), ('warehouse_id', '=', ware_ids.id) 
                        ], limit=1)
                pick_name = picking_type_id.sequence_id.next_by_id()
                location = invoice.partner_id.property_stock_supplier.id
                des_location = picking_type_id.default_location_dest_id.id
                picking_type = picking_type_id.id
            elif invoice.move_type == 'out_invoice':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'outgoing'), ('warehouse_id', '=', ware_ids.id) 
                        ], limit=1)
                pick_name = picking_type_id.sequence_id.next_by_id()
                location = picking_type_id.default_location_src_id.id
                des_location = invoice.partner_id.property_stock_customer.id
                picking_type = picking_type_id.id
            elif invoice.move_type == 'in_refund':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'incoming'), ('warehouse_id', '=', ware_ids.id) 
                        ], limit=1).return_picking_type_id
                pick_name = picking_type_id.sequence_id.next_by_id()
                location = picking_type_id.default_location_src_id.id
                des_location = invoice.partner_id.property_stock_supplier.id
                picking_type = picking_type_id.id
            elif invoice.move_type == 'out_refund':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'outgoing'), ('warehouse_id', '=', ware_ids.id) 
                        ], limit=1).return_picking_type_id
                pick_name = picking_type_id.sequence_id.next_by_id()
                location = invoice.partner_id.property_stock_customer.id
                des_location = picking_type_id.default_location_dest_id.id
                picking_type = picking_type_id.id
            else:
                raise UserError(_('Invalid Stock Operation !!!'))

            picking = self.env['stock.picking']

            picking_vals = {
                'partner_id':invoice.partner_id.id,
                'name': pick_name,
                'origin': invoice.name,
                'picking_type_id': picking_type,
                'state': 'draft',
                'move_type': 'direct',
                'note': invoice.narration,
                'company_id': invoice.company_id.id,
                'location_id': location,
                'location_dest_id': des_location,
            }

            picking_id = picking.create(picking_vals)
            picking_id.write({'origin': invoice.name})

            invoice.write({
                'invoice_picking_id' : picking_id.id,
                'picking_count' : len(picking_id)
            })

            moves = invoice._create_stock_moves_transfer(picking_id)

            for move in moves:
                move_ids = move._action_confirm()
                move_ids._action_assign()
            picking_id.write({'origin': invoice.name})
            

    def _create_stock_moves(self):
        moves = self.env['stock.move']
        done = []
        ware_id = self.env.company.warehouse_id
        for line in self.invoice_line_ids:
            price_unit = line.price_unit
            if self.move_type == 'out_invoice':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'outgoing'), ('warehouse_id', '=', ware_id.id) 
                        ], limit=1)
                pick = picking_type_id.id
                location = picking_type_id.default_location_src_id.id
                des_location = self.partner_id.property_stock_customer.id
            elif self.move_type == 'in_invoice':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'incoming'), ('warehouse_id', '=', ware_id.id) 
                        ], limit=1)
                pick = picking_type_id.id
                des_location = picking_type_id.default_location_dest_id.id
                location = self.partner_id.property_stock_supplier.id
            elif self.move_type == 'in_refund':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'incoming'), ('warehouse_id', '=', ware_id.id) 
                        ], limit=1).return_picking_type_id
                pick = picking_type_id.id
                des_location = self.partner_id.property_stock_supplier.id 
                location =  picking_type_id.default_location_src_id.id
            elif self.move_type == 'out_refund':
                picking_type_id = self.env['stock.picking.type'].search([
                            ('code', '=', 'outgoing'), ('warehouse_id', '=', ware_id.id) 
                        ], limit=1).return_picking_type_id
                pick = picking_type_id.id
                des_location = picking_type_id.default_location_dest_id.id
                location = self.partner_id.property_stock_customer.id
            if line.product_id:

                template = {
                    'name': _('New Move:') + (line.product_id.display_name or line.name),
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': location,
                    'location_dest_id': des_location,
                    'state': 'draft',
                    'move_id':self.id,
                    'company_id': self.company_id.id,
                    'price_unit': price_unit,
                    'picking_type_id': pick,
                    'route_ids': 1 and [
                        (6, 0, [x.id for x in self.env['stock.location.route'].search([('warehouse_ids', 'in', (picking_type_id.warehouse_id.id))])])] or [],
                    'warehouse_id': ware_id.id,
                }
            else:
                raise UserError(_('In order to create picking/stock move, you have to select product on invoice line'))

            diff_quantity = line.quantity

            template['product_uom_qty'] = diff_quantity

            move_id = moves.with_context(stock_move=True).create(template)
            m = move_id._action_confirm()
            m.write({'move_id':self.id,'product_uom_qty': line.quantity})

            m._action_assign()
            m.picking_id.button_validate()
            m.picking_id._action_done()
            m.write({'quantity_done':line.quantity,'state':'done'})


            self.move_count = self.move_count+ 1 
            
        return done


    def _create_stock_moves_transfer(self, picking):
        moves = self.env['stock.move']
        done = []

        for line in self.invoice_line_ids:

            price_unit = line.price_unit
            if line.move_id.move_type == 'out_invoice':
                pick = picking.picking_type_id.id
                location = picking.picking_type_id.default_location_src_id.id
                des_location = self.partner_id.property_stock_customer.id
            elif line.move_id.move_type == 'in_invoice':
                pick = picking.picking_type_id.id
                des_location = picking.picking_type_id.default_location_dest_id.id
                location = self.partner_id.property_stock_supplier.id
            elif line.move_id.move_type == 'in_refund':
                pick = picking.picking_type_id.id
                des_location =self.partner_id.property_stock_supplier.id 
                location = picking.picking_type_id.default_location_src_id.id
            elif line.move_id.move_type == 'out_refund':
                pick = picking.picking_type_id.id
                des_location = picking.picking_type_id.default_location_dest_id.id
                location = self.partner_id.property_stock_customer.id   
            if line.product_id:
                template = {
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'location_id': location,
                    'location_dest_id': des_location,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'company_id': self.company_id.id,
                    'price_unit': price_unit,
                    'picking_type_id': picking.picking_type_id.id,
                    'route_ids': 1 and [
                        (6, 0, [x.id for x in self.env['stock.location.route'].search([('warehouse_ids', 'in', (picking.picking_type_id.warehouse_id.id))])])] or [],
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }
            else:
                raise UserError(_('In order to create picking/stock move, you have to select product on invoice line'))

            diff_quantity = line.quantity

            template['product_uom_qty'] = diff_quantity

            move_id = moves.create(template)
            done.append(move_id)
        return done



    def action_post(self):
        print(self)
        for move in self:
            if move.move_type not in  ('in_invoice', 'out_refund'):
                if any(line.product_id and line.product_id.qty_available <= 0.0 for line in move.invoice_line_ids):
                    raise UserError(_('Product is not available in stock!'))
        res = super(AccountInvoice, self).action_post()
        if not self.invoice_cash_rounding_id:

            if self.env.company.create_move_from_invoice == True and self.env.company.create_move_picking == 'create_move' :

                self.action_stock_receive()
            if self.env.company.create_move_from_invoice == True and self.env.company.create_move_picking == 'create_picking' :

                self.action_stock_picking()
            return res
        else:
            return res

            

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', '=', self.invoice_picking_id.id)]
        pick_ids = sum([self.invoice_picking_id.id])
        if pick_ids:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids or False
        return result

    
    def action_view_move(self):
        action = self.env.ref('stock.stock_move_action')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('move_id', '=', self.id)]
        move_ids = list(map(int,self.invoice_move_ids))
        tree_view_id = self.env.ref('stock.view_move_tree', False)
        form_view_id = self.env.ref('stock.view_move_form', False)
        result['views'] = [(tree_view_id and tree_view_id.id or False, 'tree'),(form_view_id and form_view_id.id or False, 'form')]
        return result

