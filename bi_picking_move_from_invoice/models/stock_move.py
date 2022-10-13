# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo.tools.translate import _
from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError
from itertools import groupby


class stockMove(models.Model):
	_inherit = "stock.move"

	move_id = fields.Many2one('account.move',string='Invoice')


	def _assign_picking(self):
		""" Try to assign the moves to an existing picking that has not been
		reserved yet and has the same procurement group, locations and picking
		type (moves should already have them identical). Otherwise, create a new
		picking to assign them to. """
		if self._context.get('stock_move')==True:
			Picking = self.env['stock.picking']
			grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]), key=lambda m: [m._key_assign_picking()])
			for group, moves in grouped_moves:
				moves = self.env['stock.move'].concat(*list(moves))
				new_picking = False
				# Could pass the arguments contained in group but they are the same
				# for each move that why moves[0] is acceptable

				picking = Picking.create(moves._get_new_picking_values())
				
				moves.write({'picking_id': picking.id})
				moves._assign_picking_post_process(new=new_picking)
			return True
		else:
			return super(stockMove,self)._assign_picking()