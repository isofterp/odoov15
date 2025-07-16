# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    x_mrp_rm_perc = fields.Char('RM%')

class StockMove(models.Model):
    _inherit = 'stock.move'

    x_mrp_rm_perc = fields.Char('RM%')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    x_yield_perc = fields.Char('Yield%')

    @api.onchange('bom_id', 'product_id', 'product_qty', 'product_uom_id')
    def _onchange_move_raw(self):
        if not self.bom_id and not self._origin.product_id:
            return
        _logger.warning("--------Firing this----------")

        # Clear move raws if we are changing the product. In case of creation (self._origin is empty),
        # we need to avoid keeping incorrect lines, so clearing is necessary too.
        if self.product_id != self._origin.product_id:
            self.move_raw_ids = [(5,)]
        if self.bom_id and self.product_id and self.product_qty > 0:
            # keep manual entries
            list_move_raw = [(4, move.id) for move in self.move_raw_ids.filtered(lambda m: not m.bom_line_id)]
            moves_raw_values = self._get_moves_raw_values()
            move_raw_dict = {move.bom_line_id.id: move for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)}
            for move_raw_values in moves_raw_values:
                if move_raw_values['bom_line_id'] in move_raw_dict:
                    _logger.warning("**--------Firing this %s", move_raw_values)


                    # update existing entries
                    list_move_raw += [(1, move_raw_dict[move_raw_values['bom_line_id']].id, move_raw_values)]
                else:
                    # add new entries
                    _logger.warning("**+++--------Firing this %s", move_raw_values)
                    # FInd the bom line id and get the RM% value
                    bom_line_tmp = self.env['mrp.bom.line'].search([('id', '=',move_raw_values.get('bom_line_id'))])
                    move_raw_values['x_mrp_rm_perc'] = bom_line_tmp.x_mrp_rm_perc or False
                    list_move_raw += [(0, 0, move_raw_values)]
            self.move_raw_ids = list_move_raw
            _logger.warning("*******Firing this %s", list_move_raw)
        else:
            self.move_raw_ids = [(2, move.id) for move in self.move_raw_ids.filtered(lambda m: m.bom_line_id)]
            _logger.warning("*******If statement not firing")

