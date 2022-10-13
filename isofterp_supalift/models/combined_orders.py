from odoo import api, fields, tools, models, _


class CombinedOrders(models.Model):
    _name = "combined.orders"
    _description = "PO and VO Report"
    _auto = False

    id = fields.Char('ID', readonly=True)
    partner = fields.Many2one('res.partner','Partner', readonly=True)
    product = fields.Many2one('product.product',string='Product M2O')
    product_name = fields.Char('Product Name', readonly=True)
    reference = fields.Char('Reference Number', readonly=True)
    create_date = fields.Date('Date', readonly='True')
    price = fields.Monetary('Price', readonly=True)
    qty = fields.Float('Quantity', readonly=True)
    currency_id = fields.Many2one('res.currency')
    movetype = fields.Char('Type')

    def _select(self, product_search):
        return str(
            self._cr.mogrify(
                """
                SELECT       po.id as id,
                       po.partner_id as partner,
                       po.currency_id as currency_id,
                       ol.product_id as product,
                       po.date_order as create_date,
                       ol.product_qty as qty,
                       ol.price_total  as price,
                       'PO' as movetype,
                       po.name as reference,
                       tmpl.name as product_name
               from purchase_order as po
               join purchase_order_line as ol on po.id = ol.order_id
               join product_template tmpl on tmpl.id = ol.product_id
               where tmpl.type = 'product'
               AND ol.product_id = %(product_search)s
               UNION
               SELECT   m.id as id,
                       m.partner_id as partner,
                       m.currency_id as currency_id,
                       l.product_id as product,
                       m.date as create_date,
                       l.quantity as qty,
                       l.price_subtotal as price,
                       'Bill' as movetype,
                       m.name as reference,
                       tmpl.name as product_name
               from account_move m
                     join account_move_line as l on  m.id = l.move_id
                     join product_template tmpl on tmpl.id = l.product_id
                where m.move_type = 'in_invoice'
                     AND tmpl.type = 'product'
                    AND l.product_id = %(product_search)s
           """,
                locals(),
            ),
            "utf-8",
        )

    def my_init(self,product_search):
            tools.drop_view_if_exists(self.env.cr, self._table)
            self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
                %s
                )""" % (self._table, self._select(product_search)))

