import logging

from odoo import api, fields, models, _
_logger = logging.getLogger(__name__)


class productTemplate(models.Model):
    _inherit = "product.template"

    x_machine_charge_ids  = fields.One2many('subscription.machine.charge', 'product_key','Master Charges')
    x_optional_component_ids = fields.Many2many(
        'product.template', 'product_component_rel', 'src_id', 'dest_id',
        string='Optional Products', help="Optional Components are suggested .", check_company=True)

    def collected_ids(self):
        print('here we are',self)


class Task(models.Model):
    _inherit = "project.task"

    x_sale_subscription_id = fields.Many2one('sale_subscription', 'Enter Serial Number')