from odoo import api, fields, models, _, osv
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
#from odoo import exceptions
from odoo.exceptions import ValidationError



_logger = logging.getLogger(__name__)

class Lead(models.Model):
    _inherit = "crm.lead"

    name_seq = fields.Char(string="CRM Number", readonly=True, required=True, copy=False, default='New')

    @api.model_create_multi
    def create(self, vals_list):
        _logger.warning("vals list %s", vals_list)
        if isinstance(vals_list,dict):
                vals_list['name_seq'] = self.env['ir.sequence'].next_by_code('crm.lead.sequence') or 'New'
        if isinstance(vals_list, list):
            if vals_list[0].get('type') == 'opportunity':
                vals_list[0]['name_seq'] = self.env['ir.sequence'].next_by_code('crm.lead.sequence') or 'New'
        _logger.warning("vals list %s", vals_list)
        result = super(Lead, self).create(vals_list)
        return result

    def convert_opportunity(self, partner_id, user_ids=False, team_id=False):
        customer = False
        if partner_id:
            customer = self.env['res.partner'].browse(partner_id)
        for lead in self:
            if not lead.active or lead.probability == 100:
                continue
            vals = lead._convert_opportunity_data(customer, team_id)
            _logger.warning("convert_opportunity %s ", vals)
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('crm.lead.sequence') or 'New'
            lead.write(vals)

        if user_ids or team_id:
            self._handle_salesmen_assignment(user_ids=user_ids, team_id=team_id)

        return True










    




