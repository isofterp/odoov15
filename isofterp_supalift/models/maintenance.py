# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _

from odoo.exceptions import UserError
import logging

class MaintenanceEquipment(models.Model):
    _description = 'Maintenance Equipment'
    _inherit = 'maintenance.equipment'

    # Change standard technician_user_id from res_user to hr_employee
    #technician_user_id = fields.Many2one('hr.employee', 'Technician', tracking=True)
    partner_id = fields.Many2one('res.partner', 'Client', domain=[('is_company', '=', True)], required=True)
    x_meter_reading = fields.Float('Last Meter Reading')
    x_make = fields.Char('Make')
    x_engine_no = fields.Char('Engine Number')
    x_diff_no = fields.Char('Diff Number')
    x_transmission_number = fields.Char('Transmission Number')
    model = fields.Char('Model', required=True)
    x_meter_ids = fields.One2many('meter.reading', 'x_equipment_id', string='Meter Readings')
    job_type_ids = fields.Many2many('equipment.job.template')


    # @api.onchange('category_id')
    # def _onchange_category_id(self):
    #     # RL removed this because we changed technitian to point to hr instead or res-user
    #     # self.technician_user_id = self.category_id.technician_user_id
    #     return

    # def unlink(self):
    #     task_ids = self.env['project.project'].search([('name','=', self.name)]).task_ids
    #     if task_ids:
    #         raise UserError(_('Equipment cannot be deleted which has job activities created.'))
    #     self.unlink()

    def name_get(self):
        result = []
        for record in self:
            # if record.name and record.serial_no:
            #     result.append((record.id, record.name + '/' + record.serial_no))
            # if record.name and not record.serial_no:
            #     result.append((record.id, record.name))
            result.append((record.id, record.name))
        return result

    @api.model
    def create(self, vals):
        logging.warning("Equipment is %s", vals)
        res = super(MaintenanceEquipment, self).create(vals)

        # Create a new project, set customer and possible equipment
        # The stock parameters need to be set for this project

        src_loc = self.env['stock.warehouse'].search([('branch_id','=',res.branch_id.id)]).lot_stock_id.id
        prod_loc = self.env['stock.location'].search([('name','=', 'Production')]).id
        wip_src_loc = prod_loc
        wip_dst_loc = src_loc

        print(src_loc, prod_loc)
        #print(err)
        project_id = self.env['project.project'].search([('name', '=', res.name)])
        if not project_id:
            vals = {
                'name': res.name,
                'partner_id': res.partner_id.id,
                'x_equipment_id': res.id,
                'branch_id': res.branch_id.id,
                'location_source_id': src_loc,
                'location_dest_id': prod_loc,
                'location_wip_source_id': prod_loc,
                'location_wip_dest_id': src_loc,
            }
            self.env['project.project'].create(vals)
        else:
            raise UserError(_('A Project already exist for the equipment.'))
        return res