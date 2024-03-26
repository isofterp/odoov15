#!/usr/bin/env python
from odoo import api, fields, models, _
import logging


class Partner(models.Model):
    _inherit = "res.partner"

    # @api.model_create_multi
    # def create(self, vals_list):
    #     partners = super(Partner, self).create(vals_list)
    #     for vals in vals_list:
    #         is_company = vals.get('company_type')
    #         account_no = vals.get('x_account_number')
    #     # Create an Analytic Account for this Customer
    #     if is_company == 'company':
    #         analytic = self.env['account.analytic.account'].create(
    #             {'name': account_no, 'partner_id': partners.id, 'group_id': 1})
    #     return partners

    def _get_subscrptions(self):
        for rec in self:
            subs = self.env['sale.subscription'].search([('partner_id','=', rec.id),
                                                         ('recurring_total','>', 0)])
            rec.subs_count = len(subs)

    x_account_number = fields.Char('Account Number', index=True, required='Yes')
    x_fax = fields.Char('Fax Number')
    x_company_reg_no = fields.Char('Company reg no')
    subs_count = fields.Integer(string='Subscription Count', compute='_get_subscrptions', readonly=True)
    x_equipment_ids = fields.One2many('stock.production.lot', 'last_delivery_partner_id', string='Equipment')

    def set_sales_team_on_users(self):
        users = self.env['res.users'].search([('share','!=', True),
                                              ('id','not in', [1,2,57]),
                                              ('active','=', True)])
        for user in users:

            crm_team = self.env['crm.team'].search([('name','=', user.partner_id.name)])
            if crm_team:
                #logging.warning("User is %s", user.partner_id.name)
                #logging.warning("Setting Sales person and Team for user %s to %s", user.partner_id.name, crm_team.name)
                user.partner_id.user_id = user.id
                user.partner_id.team_id = crm_team.id

    def set_sales_team(self):
        partners = self.env['res.partner'].search([('company_id','!=',1 ),
                                                   ('user_id','=',False),
                                                   ('parent_id','!=', '')])

        for partner in partners:

            partner.user_id = partner.parent_id.user_id.id
            partner.team_id = partner.parent_id.team_id.id
            # crm_team = self.env['crm.team'].search([('name','=',partner.user_id.name )])
            # if not crm_team:
            #     crm_team = {
            #         'name': partner.user_id.name,
            #         'user_id': partner.user_id.id,
            #
            #     }
            #     team = self.env['crm.team'].create(crm_team)
            #     if team:
            #         # Set member of the team = user_id
            #         logging.warning("Created Team %s", team.name)
            #         team_member = {
            #             'crm_team_id': team.id,
            #             'user_id': partner.user_id.id,
            #         }
            #         team_member = self.env['crm.team.member'].create(team_member)
            #         if team_member:
            #             logging.warning("Created Team member %s %s",team_member.crm_team_id.name,
            #                             team_member.user_id.name)
            #         else:
            #             logging.warning("Could not assigned team member to team %s %s",
            #                             partner.user_id.name, team.name)
            #
            #     else:
            #         logging.warning("Could not create team for some or other reason")
            # else:
            #     #Assign sales team to contact
            #     partner.team_id = crm_team.id


    def show_subscriptions(self):

        try:
            sub_ids = self.env['subscription.line.combined'].search([('cust','=', self.name)])
            form_view_id = self.env.ref("isofterp_subscription.sale_subscription_line_combined_tree").id
            return {
                'type': 'ir.actions.act_window',
                'name': 'Subscriptions',
                'view_mode': 'tree',
                'res_model': 'subscription.line.combined',
                'views': [[form_view_id, 'tree']],
                'domain': [('id', 'in', sub_ids.ids)],
                'target': 'current',
                'view_id': False,
            }
        except Exception as e:
            form_view_id = False



