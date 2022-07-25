# See LICENSE file for full copyright and licensing details.
"""Res Users Model."""


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MultiBranch(models.Model):
    """Multi Branch Model."""

    _name = "multi.branch"
    _description = "Multi Branch"

    @api.model
    def default_get(self, fields):
        """Method to set default company in branch."""
        result = super(MultiBranch, self).default_get(fields)
        company = (
            self.env.company.id or False
        )
        if self._context and self._context.get("allowed_company_ids", []):
            company = self._context["allowed_company_ids"][0]
        if company:
            result.update({"company_id": company})
        return result

    name = fields.Char(related="partner_id.name", string="Branch Name", store=True)
    logo = fields.Binary(
        related="partner_id.image_1920", string="Company Logo", store=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company Name",
        default=lambda self: self.env.company.id,
    )
    partner_id = fields.Many2one("res.partner", string="Partner")
    street = fields.Char(compute="_compute_address", inverse="_inverse_street")
    street2 = fields.Char(compute="_compute_address", inverse="_inverse_street2")
    zip = fields.Char(compute="_compute_address", inverse="_inverse_zip")
    city = fields.Char(compute="_compute_address", inverse="_inverse_city")
    state_id = fields.Many2one(
        "res.country.state",
        compute="_compute_address",
        inverse="_inverse_state",
        string="Fed. State",
    )
    country_id = fields.Many2one(
        "res.country",
        compute="_compute_address",
        inverse="_inverse_country",
        string="Country",
    )
    email = fields.Char(related="partner_id.email", store=True)
    phone = fields.Char(related="partner_id.phone", store=True)
    website = fields.Char(related="partner_id.website")
    # wh_available = fields.Integer(
    #     compute="_compute_wh_available", string="Warehouse Available with this branch ?"
    # )

    def _compute_wh_available(self):
        for branch in self:
            branch.wh_available = self.env["stock.warehouse"].search_count(
                [("branch_id", "=", branch.id)]
            )

    def _get_branch_address_fields(self, partner):
        return {
            "street": partner.street,
            "street2": partner.street2,
            "city": partner.city,
            "zip": partner.zip,
            "state_id": partner.state_id,
            "country_id": partner.country_id,
        }

    def _compute_address(self):
        for branch in self.filtered(lambda branch: branch.partner_id):
            address_data = branch.partner_id.sudo().address_get(adr_pref=["contact"])
            if address_data["contact"]:
                partner = branch.partner_id.browse(address_data["contact"]).sudo()
                branch.update(branch._get_branch_address_fields(partner))

    def _inverse_street(self):
        for branch in self:
            branch.partner_id.street = branch.street

    def _inverse_street2(self):
        for branch in self:
            branch.partner_id.street2 = branch.street2

    def _inverse_zip(self):
        for branch in self:
            branch.partner_id.zip = branch.zip

    def _inverse_city(self):
        for branch in self:
            branch.partner_id.city = branch.city

    def _inverse_state(self):
        for branch in self:
            branch.partner_id.state_id = branch.state_id

    def _inverse_country(self):
        for branch in self:
            branch.partner_id.country_id = branch.country_id

    @api.returns("self", lambda value: value.id)
    def copy(self):
        """Overridden copy method to restrict all users."""
        super(MultiBranch, self).copy()
        raise ValidationError(
            _(
                "User can not Duplicate the branch ! "
                " Instead of duplicate, Create a New Branch."
            )
        )

    @api.model
    def create(self, vals):
        """Create Method to add the partner."""
        partner_obj = self.env["res.partner"]
        if not vals.get("name", False) or vals.get("partner_id", False):
            self.clear_caches()
            return super(MultiBranch, self).create(vals)
        partner = partner_obj.create(
            {
                "name": vals["name"],
                "is_company": True,
                "image_1920": vals.get("logo"),
                "email": vals.get("email"),
                "phone": vals.get("phone"),
                "website": vals.get("website"),
            }
        )
        vals["partner_id"] = partner.id
        self.clear_caches()
        new_branch = super(MultiBranch, self).create(vals)
        # The write is made on the user to set it automatically in the multi
        # branch group.
        self.env.user.write({"branch_ids": [(4, new_branch.id)]})
        #partner.write({"branch_id": new_branch.id})

        # Make sure that the selected currency is enabled
        if vals.get("currency_id"):
            currency = self.env["res.currency"].browse(vals["currency_id"])
            if not currency.active:
                currency.write({"active": True})
        return new_branch

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Method to select filtered branch id for different model."""
        domain = args
        branch_obj = self.env["multi.branch"]
        if (
            self._context
            and self._context.get("branch_filter", False)
            and self._context.get("uid", False)
        ):
            user = self.env["res.users"].browse(self._context["uid"])
            branch_ids = []
            if self._context.get("filter_company_id", False):
                allow_branches = user.branch_ids
                allow_branches |= user.branch_id
                domain += [("company_id", "=", self._context["filter_company_id"])]
                if allow_branches:
                    domain += [("id", "in", allow_branches.ids)]
                branch_ids = branch_obj.search(domain)
            if not branch_ids:
                branch_ids = user.branch_ids
                branch_ids |= user.branch_id
                domain += [("id", "in", branch_ids and branch_ids.ids or args)]
                if self._context.get("filter_company_id", False):
                    domain += [("company_id", "=", self._context["filter_company_id"])]
                branch_ids = branch_obj.search(domain)
            domain += [("id", "in", branch_ids and branch_ids.ids or args)]
        return self._search(domain, limit=limit, access_rights_uid=name_get_uid)

    @api.constrains("name")
    def _check_branch_name(self):
        if self.search_count([("name", "=", self.name)]) > 1:
            raise ValidationError(_("Branch Name must be unique!!"))
