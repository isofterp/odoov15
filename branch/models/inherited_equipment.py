# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    @api.model
    def default_get(self, default_fields):
        res = super(MaintenanceEquipment, self).default_get(default_fields)
        #if self.env.user.branch_id:
        if self.partner_id.branch_id:
            res.update({
                'branch_id' : self.partner_id.branch_id.id or False
            })
        _logger.warning("Default get returned %s", res)
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        _logger.warning("On change Customer running!!!!")
        if self.partner_id.branch_id:
            self.branch_id = self.partner_id.branch_id

    branch_id = fields.Many2one('res.branch', string="Branch", ondelete="restrict")
