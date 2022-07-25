# See LICENSE file for full copyright and licensing details.
"""Account Bank Statement."""
from odoo import api, fields, models


class AccountBankStatement(models.Model):
    """Account Bank Statement."""

    _inherit = "account.bank.statement"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    @api.onchange("journal_id")
    def onchange_journal_id(self):
        """Overridden Onchange Method."""
        super(AccountBankStatement, self).onchange_journal_id()
        self.branch_id = (
            self.journal_id
            and self.journal_id.branch_id
            and self.journal_id.branch_id.id
            or False
        )


class AccountBankStatementLine(models.Model):
    """Account Bank Statement Line."""

    _inherit = "account.bank.statement.line"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")

    def _prepare_move_line_default_vals(self, counterpart_account_id=None):

        result = super(AccountBankStatementLine, self)._prepare_move_line_default_vals()
        move_obj = self.env["account.move"]
        for line in result:
            line.update({"branch_id": self.branch_id and self.branch_id.id or False})
            move_rec = move_obj.browse(line["move_id"])
            if not move_rec.branch_id:
                move_rec.write(
                    {"branch_id": self.branch_id and self.branch_id.id or False}
                )
        return result


class AccountJournal(models.Model):
    """Account Journal."""

    _inherit = "account.journal"

    branch_id = fields.Many2one("multi.branch", string="Branch Name")
