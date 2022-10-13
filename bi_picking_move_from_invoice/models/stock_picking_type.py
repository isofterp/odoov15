# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo.tools.translate import _
from odoo import api, fields, models, _
from odoo.exceptions import Warning,UserError


class StockPickingTypein(models.Model):
    _inherit = 'stock.picking.type'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('type'):
            if self._context.get('type') in ['out_invoice','in_refund']:
                args += [('code', '=', 'outgoing')]
                return super(StockPickingTypein, self).name_search(name, args, operator, limit)
            elif self._context.get('type') in ['in_invoice','out_refund']:
                args += [('code', '=', 'incoming')]
                return super(StockPickingTypein, self).name_search(name, args, operator, limit)
            else:
                return super(StockPickingTypein, self).name_search(name, args, operator, limit)
        return super(StockPickingTypein, self).name_search(name, args, operator, limit)
