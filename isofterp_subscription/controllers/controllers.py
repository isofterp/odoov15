from odoo import http
import logging
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
from odoo.http import request
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.osv.expression import AND


class ContractsPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(ContractsPortal, self)._prepare_portal_layout_values()
        domain = request.env['sale.subscription']._contract_get_portal_domain()
        values['timesheet_count'] = request.env['account.analytic.line'].sudo().search_count(domain)
        return values

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth='public', website=True,csrf='False')
    def portal_my_contracts(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kwargs):
        values = {}
        print("/my/contracts Kwargs=", kwargs)
        contracts = http.request.env['sale.subscription'].sudo().search([('name', '=', kwargs['id'])])
        for contract in contracts:
            print("Contract details are", contract.name, contract.date_start)

        grouped_contracts = [contracts]
        values.update({
            'contracts': contracts,
            'page_name': 'contracts',
            'grouped_contracts': grouped_contracts,
            'default_url': '/my/contracts',

        })
        return http.request.render('isofterp_subscription.portal_my_contracts_tmpl', values)

    @http.route(['/my/contracts/submit'], type='http', auth='public', website=True)
    def get_form_values(self, **kwargs):
        values = {}
        if request.httprequest.method == 'POST':
            #logging.warning("black copies = %s colour copies= %s", (kwargs.get('black'),kwargs.get('colour')))
            print('kwargs',kwargs)
            message_1 = message_2 = ''
            values.update({"subscription": kwargs['contract']})

            if kwargs['black']:
                line = http.request.env['sale.subscription.line'].sudo().search([('x_serial_number_id.name','=',kwargs['serial']),('product_id.name', '=', 'Black copies')])
                if line:
                    # print(line)
                    line.x_copies_last = kwargs['black']
                    message_1 = 'Thank you for submitting your readings for Serial Number ' + kwargs['serial'] + " Last meter reading for Black Copies=" + kwargs['black']
                    line.x_reading_type_last = 'Web'
                else:
                    err_message_1 = "We kave a problem - could not find a machine with Serial Number= " + kwargs['serial'] + " for" + kwargs['black'] + " Black Copies"
                    err_message_1 += "Please contact CopyType 021 559 1605"
                    values.update({"err_message_1": err_message_1})

            if kwargs['colour']:
                line = http.request.env['sale.subscription.line'].sudo().search([('x_serial_number_id.name','=',kwargs['serial']),('product_id.name', '=', 'Colour copies')])
                if line:
                    #print(line)
                    line.x_copies_last = kwargs['colour']
                    message_2 = 'Thank you for submitting your readings for Serial Number ' + kwargs['serial'] + " Last meter reading for Colour Copies=" + kwargs['colour']
                    line.x_reading_type_last = 'Web'
                else:
                    err_message_2 = "We kave a problem - could not find a machine with Serial Number " + kwargs['serial'] + " with Colour Copies"
                    err_message_2 += " Please contact CopyType 021 559 1605"
                    values.update({"err_message_2": err_message_2})

            values.update({
                'message_1': message_1,
                'message_2': message_2,
                })
            return http.request.render('isofterp_subscription.portal_meterreading_response_tmpl', values)

