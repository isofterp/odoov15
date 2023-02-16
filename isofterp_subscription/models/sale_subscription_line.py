from odoo import api, fields, models, _
import logging
from datetime import datetime, timedelta
_logger = logging.getLogger(__name__)

class sale_subscription_line(models.Model):
    _inherit = 'sale.subscription.line'
    #_inherit = ['mail.thread', 'mail.activity.mixin','sale.subscription.line']  need this for tracking - not working

    # @api.model
    # def name_get(self):
    #     print('name_get in custom sub_line')
    #     result = []
    #     for record in self:
    #         name = str(record.x_serial_number_id.name) + " " + record.name
    #         result.append((record.id, name))
    #     return result
    #
    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike',
    #                  limit=100, name_get_uid=None):
    #     args = [] if args is None else args.copy()
    #     print('args',args)
    #     if not (name == '' and operator == 'ilike'):
    #         args += ['|', '|',
    #                  ('x_serial_number_id', operator, name),
    #                  ('analytic_account_id', operator, name),
    #                  ('analytic_account_id.partner_id.x_account_number', operator, name)
    #                  ]
    #     return super(sale_subscription_line, self)._name_search(name='', args=args, operator='ilike',limit=limit, name_get_uid=name_get_uid)
    #

    specific_price = fields.Float(string='Specific Price',digits = (7,4))
    quantity = fields.Integer(compute='_new_qty',store='yes',string='Quantity',default=1)
    x_serial_number_id = fields.Many2one('stock.production.lot', 'Serial Number' )
    x_product_id = fields.Many2one('product.product',related='x_serial_number_id.product_id',string='Machine')
    x_partner_id = fields.Many2one('res.partner',related='analytic_account_id.partner_id',string='Customer')
    #x_machine_master_id = fields.Char( string='Machine Master', ondelete='cascade')

    x_copies_show = fields.Boolean('Show copies')
    x_copies_free = fields.Integer('Free Copies')
    x_copies_minimum = fields.Float('Minimum Charge',help='This is the minimum amount in Rands to bill')
    x_email_count = fields.Integer('Email Count')


    x_copies_previous = fields.Integer('Previous Reading')
    x_copies_last = fields.Integer('Last Reading',tracking=True)
    x_start_date1 = fields.Date('Start Date', default=datetime.today())  # default=datetime.today()
    x_start_date1_billable = fields.Boolean('Bill',tracking=True,default='1' )
    x_end_date1 = fields.Date('End Date')

    #x_charges_type1_id = fields.Many2one('subscription.charges.type', 'Type 1')  # Not sure we need this ?
    #x_start_date2 = fields.Date('Start 2')
    #x_end_date2 = fields.Date('End 2')
    #x_charges_type2_id = fields.Many2one('contract.charges.type', 'Type 2')
    #x_start_date2_billable = fields.Boolean('Bill 2')

    x_copies_vol_1 = fields.Integer('Volume 1')
    x_copies_price_1 = fields.Float('Charge 1',digits = (3,4) )
    x_copies_vol_2 = fields.Integer('Volume 2')
    x_copies_price_2 = fields.Float('Charge 2',digits = (3,4))
    x_copies_vol_3 = fields.Integer('Volume 3')
    x_copies_price_3 = fields.Float('Charge 3',digits = (3,4))
    x_average_quantity = fields.Integer('Average Qty',compute='_average_quantity',store=True)
    #x_average_quantity = fields.Integer('Ave Qty', default=1)
    x_average_value = fields.Float('Ave Val',digits = (3,4))
    x_average_months = fields.Integer('Average Months', default=1,help="Set the average number of months to use")
    x_billing_frequency = fields.Integer("Billing Frequency", default=1)
    x_billing_hold = fields.Integer("Billing Hold")

    _defaults = {
        'uom_id': 1,
    }

    @api.depends('x_copies_last')
    def _new_qty(self):
        for rec in self:
            if rec.x_copies_last == 0 and rec.x_copies_previous == 0:
                rec.quantity = 1
            else:
                rec.quantity = rec.x_copies_last - rec.x_copies_previous

    """ This might need to run as a cron monthly to calculate and store values"""
    @api.depends('quantity')
    def _average_quantity(self):
        self.ensure_one()
        now = datetime.now()
        date_N_months_ago = now - timedelta(days=self.x_average_months * 30)
        sortBy = "create_date desc"
        print (self.create_date," ",date_N_months_ago)
        trx = self.env['account.move.line'].search([('subscription_id','=',self.id),
                                                       ('product_id','=', self.product_id.id ),
                                                       ('create_date', '>=' , str(date_N_months_ago))])
        tot = 0
        for rec in self:
            for record in trx:
                #print ('found record',record.create_date)
                tot += record.quantity

            rec.x_average_quantity = tot / self.x_average_months
            #rec.x_average_quantity = rec.quantity
            rec.x_average_value = rec.quantity * rec.x_copies_price_1

        return













    

   
 
