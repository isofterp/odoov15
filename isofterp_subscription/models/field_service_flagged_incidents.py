from odoo import fields, models, tools
import logging


class field_service_flagged_incidents(models.Model):
    _name = "field.service.flagged.incidents"
    _description = "Field Service Flagged Report"
    _auto = False

    cur_incident = fields.Char('Current Incident')
    prev_incident = fields.Char('Prev Incident')
    cur_date = fields.Char('Current Date')
    prev_date = fields.Char('Prev Date')
    partner = fields.Many2one('res.partner', 'Customer', check_company=True,)
    prev_serial = fields.Char('Prev Serial Number', readonly=True)
    product = fields.Char('Product', readonly=True)
    serial_number = fields.Many2one('stock.production.lot', 'Serial Name', store=True)

    def _select(self):
        select2_str = """
            SELECT
                    q1.id as id,
                    q1.name as cur_incident,
                    q1.x_serial_number_id as serial_number,
                    q1.partner_id as partner,
                    q1.x_serial_number_name as product,
                    q1.create_date as cur_date,
                    q1.prev_serial_number_id as prev_serial,
                    q1.prev_create_date as prev_date,
                    q1.prev_name as prev_incident
                    
        """
        return select2_str

    def _from(self):

        from2_str = """
                ( SELECT *,
                LAG(create_date, 1) OVER(ORDER BY x_serial_number_id, create_date ASC) AS prev_create_date, 
                LAG(x_serial_number_id, 1) OVER(ORDER BY x_serial_number_id, create_date ASC) AS prev_serial_number_id,
                LAG(name, 1) OVER(ORDER BY x_serial_number_id, create_date ASC) AS prev_name
                FROM project_task ) 
                AS q1
                left join stock_production_lot lot on q1.x_serial_number_id = lot.id 
        """
        return from2_str

    def _where(self):
        where_str = """
                    WHERE pt.project_id = 4
                    AND pt.create_date >= NOW() - INTERVAL '10 DAYS' 
        """
        where2_str = """
                WHERE (q1.create_date::date - q1.prev_create_date::date) <= 10
                AND q1.x_serial_number_id = q1.prev_serial_number_id
                ORDER BY q1.x_serial_number_id, q1.create_date
        """
        return where2_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
                    %s
                    FROM  %s 
                    %s
                    )""" % (self._table, self._select(), self._from(), self._where()))
