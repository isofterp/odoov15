# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_view_partner_equipment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("maintenance.hr_equipment_action")
        action['domain'] = [
            # ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.id),
        ]
        # action['context'] = {'default_move_type':'out_invoice',
        # 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_unpaid': 1}
        return action
