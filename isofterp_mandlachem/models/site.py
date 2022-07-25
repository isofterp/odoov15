# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date
from odoo import api, fields, models, _

class SiteSite(models.Model):
    _name = 'site.site'
    _description = 'Sites'

    @api.model
    def create(self, vals):
        #print('site create', vals)
        partner = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
        branch_vals = {
            'name': vals['name'],
            'street': partner.street,
            'street2': partner.street2,
            'partner_id': partner.id,
        }
        rec = self.env['multi.branch'].create(branch_vals)
        vals['branch_id'] = rec.id
        return super(SiteSite, self).create(vals)

    name = fields.Char('Site Description', required=True)
    branch_id = fields.Many2one('multi.branch', string='Site id', required=True)
    partner_id = fields.Many2one('res.partner', "Partner")
    address = fields.Char(related='partner_id.street',string='Address')
    contact_number = fields.Char(related='partner_id.mobile',string='Contact Number')
    email = fields.Char(related='partner_id.email',string='Email')
    contact_ids = fields.One2many('res.partner','site_id',string="Contact")
    notes = fields.Char('Notes')
    technician_ids = fields.One2many('hr.employee','site_id', string='Technician')
    line_ids = fields.One2many('site.line', 'site_id', string='Lines')
    tank_ids = fields.One2many('site.tank', 'site_id', string='tank')

class SiteLine(models.Model):
    _name = 'site.line'
    _description = 'Site Lines'

    @api.model_create_multi
    def create(self,vals):
        rec = super(SiteLine, self).create(vals)
        tank_id = vals[0].get('tank_ids')[0][2]
        if tank_id:
            tank = self.env['site.tank'].search([('id','=',tank_id[0])])
            tank.line_id = rec.id
            tank.site_id = rec.site_id.id
            #print(tank.line_id,rec.id)
        return rec

    name = fields.Char("Line Name")
    site_id = fields.Many2one('site.site', string='Site')
    branch_id = fields.Many2one(related='site_id.branch_id', string="Branch",ondelete='cascade')
    employee_ids = fields.Many2many('hr.employee', string='Technician')
    contact_ids = fields.Many2many('res.partner','site_id',string="Contact")
    tank_ids = fields.Many2many('site.tank',  required=True, string='Tanks')

# class HrEmployee(models.Model):
#     _inherit = "hr.employee"
#
#     site_line_id = fields.Many2one("site.line",string="Line")



