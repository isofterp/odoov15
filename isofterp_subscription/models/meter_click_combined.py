
from odoo import fields, models, tools
from datetime import datetime
import logging

class meter_click_combined(models.Model):
    _name = "meter.click.combined"
    _description = "Meter Click Report"
    _auto = False

    code = fields.Char('Code', readonly=True)
    partner = fields.Char('Partner', readonly=True)
    salesperson = fields.Char('Owner', readonly=True)
    serial = fields.Char('Serial', readonly=True)
    last_reading = fields.Integer('Last reading', readonly=True)
    previous_reading = fields.Integer('previous reading', readonly=True)
    to_bill = fields.Integer('Copies to Bill', readonly='True')
    product = fields.Char('Product', readonly=True)
    price = fields.Float('AvePrice', readonly=True)
    billamt = fields.Float('MinBilling', readonly=True)
    copytype = fields.Char('Copytype', readonly=True)

    def _select(self):
        select_str = """
             SELECT min(l.id) as id,
                    sub.code as code,
                    partner.name as partner,
                    users.login as salesperson,
                    l.name as copytype,
                    l.x_copies_last as last_reading,
                    l.x_copies_previous as previous_reading,
                    l.x_copies_last - l.x_copies_previous as to_bill,
                    lot.name as serial,
                    prod.name as product,
                    partner.x_account_number as acc,
                    partner.email as partner_email,
                    l.x_copies_price_1 as price,
                    ((l.x_copies_last - l.x_copies_previous) * l.x_copies_price_1) as billamt         
        """
        return select_str

    def _from(self):
        from_str = """
                sale_subscription sub
                join res_partner partner on sub.partner_id = partner.id    
                join sale_subscription_line l on sub.id = l.analytic_account_id
                left join stock_production_lot lot on l.x_serial_number_id = lot.id  
                left join product_template prod on prod.id = lot.product_id  
                left join res_users users on partner.user_id = users.id 
        """
        return from_str

    def _where(self):
        where_str = """
                    WHERE l.x_copies_show is True 
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                    l.product_id,
                    sub.name,
                    sub.code,
                    lot.name,
                    users.login,
                    partner.name,
                    partner.user_id ,
                    partner.x_account_number,
                    partner.email,
                    prod.name ,
                    l.name,
                    l.x_copies_last,
                    l.x_copies_last ,
                    l.x_copies_previous,
                    x_copies_price_1                   
        """
        return group_by_str

    def _sort_by(self):
        sort_by_str = """
            SORT BY 
                    billamt              
        """
        return sort_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s %s
            )""" % (self._table, self._select(), self._from(), self._where(),self._group_by()))

    def action_set_average_reading(self):
        logging.warning("======== SETTING AVERAGE QTY")
        if self.env.context.get('active_ids', False):
            for rec in self.env.context.get('active_ids', False):
                logging.warning("======== ACTIVE IDS %s",rec)
                total_readings = 0
                avg_reading = 0
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M")
                sub_line = self.env['sale.subscription.line'].search([('id', '=',rec )])
                if sub_line:
                    logging.warning("Line is %s %s", sub_line.name, sub_line.quantity)
                    # For this line get the last reading
                    # get all the readings todate from history
                    # Get the average reading over the period and set that as the new reading
                    # Update the Audit report
                    history_recs = self.env['meter.reading.history'].search([('name','=',sub_line.x_partner_id.name),
                                                    ('product_id','=',sub_line.product_id.id),
                                                    ('contract_id','=',sub_line.analytic_account_id.id),],
                                                                            limit=6)
                    if history_recs:
                        for hrec in history_recs:
                            logging.warning("The records are %s %s %s %s %s %s",
                                            hrec.create_date, hrec.name, hrec.product_id.name,
                                            hrec.contract_id.name, hrec.serial_no_id.name,
                                            hrec.no_of_copies)
                            total_readings += hrec.no_of_copies
                    if total_readings > 0:
                        avg_reading = round(total_readings / len(history_recs))
                        logging.warning("Average reading is %s", avg_reading)

                        #Create meter reading error report
                        new_reading = sub_line.x_copies_previous + avg_reading
                        message = dt_string + ' Average Reading Calculated ' + 'Serial No: ' + sub_line.x_serial_number_id.name + ' ' + sub_line.name + \
                                  ' Copies Previous = ' + str(sub_line.x_copies_last) + ' Average: ' + str(avg_reading) + ' New Reading: ' + str(new_reading)
                        self.env['meter.reading.error'].create({
                            'name': message
                        })
                        sub_line.write({
                            'x_copies_last': new_reading,
                            'x_reading_type_last': 'Average'
                        })

                        # Write a note onto the chatter of the contract
                        sub_line.analytic_account_id.sudo().message_post(body=message)






"""
-- select x_serial_number_id, name from sale_subscription_line
 SELECT 
    sub.name as contract,
    partner.x_account_number as acc,
    l.x_start_date1 as start_date,
    l.x_end_date1 as end_date,
    lot.name as serial,
    prod.name as product,
    lot.ref as main,
    l.name as trx,
    l.x_start_date1_billable as bill,
    l.x_copies_last as reading,
    l.price_unit,
    lot.x_increase_rental_date as rental_esc_date,
    lot.x_increase_rental_percent as rental_esc,
    lot.x_increase_service_percent as service_esc,
    sub.x_bank_name
                    
                    
from 
    sale_subscription sub 
    join sale_subscription_line l on sub.id = l.analytic_account_id
    join res_partner partner on sub.partner_id = partner.id    
    left join stock_production_lot lot on l.x_serial_number_id = lot.id  
    left join product_template prod on prod.id = lot.product_id 
-- where sub.name = '11105631'
where l.name <> ''
order by
    sub.name
 
-- group by
--     sub.name,
--     l.analytic_account_id,
--     
--     l.product_id,
--     l.name
--     
--     lot.name
-- """