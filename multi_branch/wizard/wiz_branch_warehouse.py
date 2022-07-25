"""TransientModel Model for the create wizard from branch."""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizBranchWarehouse(models.TransientModel):
    """Wizard branch warehouse."""

    _name = "wiz.branch.warehouse"
    _description = "Wizard Branch Warehouse"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    note = fields.Text(string="Note")

    @api.constrains("code")
    def _check_code(self):
        """Check warehouse constrains."""
        wh = self.env["stock.warehouse"].search([("code", "=", self.code)])
        if wh:
            raise UserError(
                _(
                    "Warehouse with this code already available. "
                    "Warehouse code must be unique !!"
                )
            )

    def action_confirm_warehouse(self):
        """Create Warehouse from branch."""
        if self._context.get("active_id", False):
            branch = self.env["multi.branch"].browse(self._context["active_id"])
            self.env["stock.warehouse"].create(
                {
                    "name": self.name or "",
                    "branch_id": branch.id or False,
                    "code": self.code or "",
                    "company_id": branch.company_id.id or False,
                }
            )

    @api.model
    def default_get(self, fields):
        """Default get method for set name and code."""
        res = super(WizBranchWarehouse, self).default_get(fields)
        if self._context.get("active_id", False):
            branch = self.env["multi.branch"].browse(self._context["active_id"])
            branch_warehouses_recs = self.env['stock.warehouse'].search([('branch_id', '=', False)])
            note = "Warehouses available without branch information,\n" \
                   "You can update branch information directly into the below mentioned Warehouses." \
                   "(From Menu: Inventory => Configuration => Warehouses).\n"\
                   "                    OR                           \n"\
                   "You can click on confirm to create new Warehouse.\n"
            note += "------------------------------------------------\n"
            note += "                  WAREHOUSES                    \n"
            note += "------------------------------------------------\n"
            count = 1
            for wh in branch_warehouses_recs:
                note += str(count) + ') ' + wh.name + "\n"
                count += 1
            if branch_warehouses_recs:
                res.update({
                    "note": note
                })
            res.update(
                {
                    "name": branch.name,
                    "code": "".join([x[0] for x in branch.name.split()]).upper(),
                }
            )
        return res
