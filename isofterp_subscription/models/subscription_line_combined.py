
from odoo import fields, models, tools

class subscription_line_combined(models.Model):
    _name = "subscription.line.combined"
    _description = "Subscription Lines Combined"
    #_order = 'contract desc'
    _auto = False

    contract = fields.Char('Contract', readonly=True)
    cust = fields.Char('Customer', readonly=True)
    start_date = fields.Date('Start Date', readonly=True)
    end_date = fields.Date('End Date', readonly=True)
    serial = fields.Char('Serial', readonly=True)
    product = fields.Char('Product', readonly=True)
    main = fields.Boolean('Main', readonly=True)
    type = fields.Char('Type', readonly=True)
    bill = fields.Boolean('Bill', readonly=True)
    reading = fields.Integer('End reading', readonly=True)
    price = fields.Float('Price', readonly=True)
    average_quantity = fields.Integer('Ave qty', readonly=True)
    average_value = fields.Float('Ave val', readonly=True)
    esc_date = fields.Char('Esc date', readonly=True)
    esc_percent = fields.Float('Esc ', readonly=True)
    esc_price = fields.Float('New price', readonly=True)
    bank = fields.Char('Bank', readonly=True)
    area_code = fields.Char('Area Code', readonly=True)

    def _select(self):
        select_str = """
             SELECT min(l.id) as id,
                    sub.name as contract,
                    partner.name as cust,
                    l.x_start_date1 as start_date,
                    l.x_end_date1 as end_date,
                    lot.name as serial,
                    prod.name as product,
                    lot.x_main_product as main,
                    l.name as type,
                    l.x_start_date1_billable as bill,
                    l.x_copies_last as reading,
                    l.price_unit as price,
                    l.x_average_quantity as average_quantity,
                    l.x_average_value as average_value,

                    CASE
                        WHEN l.name = 'Monthly Service' THEN lot.x_increase_service_date
                        WHEN l.name = 'Monthly Rental' THEN lot.x_increase_rental_date
                    END as esc_date,
                    CASE
                        WHEN l.name = 'Monthly Service' THEN lot.x_increase_service_percent
                        WHEN l.name = 'Monthly Rental' THEN lot.x_increase_rental_percent
                    END as esc_percent,
                    CASE
                        WHEN l.name = 'Monthly Service' THEN l.price_unit * lot.x_increase_service_percent /100 + l.price_unit
                        WHEN l.name = 'Monthly Rental' THEN l.price_unit * lot.x_increase_rental_percent /100 + l.price_unit
                    END as esc_price,
                    sub.x_bank_name as bank,
                    ar.name as area_code
        """
        return select_str

    def _from(self):
        from_str = """
                    sale_subscription sub
                    join sale_subscription_line l on sub.id = l.analytic_account_id
                    join res_partner partner on sub.partner_id = partner.id  
                    left join stock_production_lot lot on l.x_serial_number_id = lot.id  
                    left join product_template prod on prod.id = lot.product_id   
                    left join area_codes ar on sub.x_area_code = ar.id  
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.product_id,
                    sub.name,
                    lot.name,
                    l.name ,
                    partner.name,
                    l.x_start_date1 ,
                    l.x_end_date1 ,
                    prod.name ,
                    lot.ref ,
                    l.x_start_date1_billable,
                    l.x_copies_last ,
                    l.price_unit ,
                    l.x_average_quantity,
                    l.x_average_value,
                    lot.x_main_product,
                    lot.x_increase_rental_date ,
                    lot.x_increase_service_date ,
                    lot.x_increase_rental_percent ,
                    lot.x_increase_service_percent ,
                    sub.x_bank_name,
                    area_code 
                    
        """
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s 
            )""" % (self._table, self._select(), self._from(), self._group_by()))






