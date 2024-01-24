from odoo import api, fields, models, tools, _

class AreaCodes(models.Model):
    _name = 'area.codes'
    _description = "Area Codes"

    name = fields.Char(string="Name", required=True, index=True)