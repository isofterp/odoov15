# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta
import logging
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    branch_id = fields.Many2one(
        "res.branch",
        string="Branch Name",
        #default=lambda self: self.env.user.branch_id,
        ondelete="restrict",
    )

    @api.model
    def next_by_code(self, sequence_code, sequence_date=None):
        """ Draw an interpolated string using a sequence with the requested code.
            If several sequences with the correct code are available to the user
            (multi-company cases), the one from the user's current company will
            be used.

            :param dict context: context dictionary may contain a
                ``force_company`` key with the ID of the company to
                use instead of the user's current company for the
                sequence selection. A matching sequence for that
                specific company will get higher priority.
        """
        self.check_access_rights('read')
        force_company = self._context.get('force_company')
        _logger.warning("#########The sequence code is %s", self._context)
        branch_id = self.env.user.branch_id
        _logger.warning("#########The branch is  code is %s", branch_id)
        if not force_company:
            force_company = self.env.company.id

        if sequence_code == 'project.task':
            seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [force_company, False]),
                                   ('branch_id', '=', branch_id.id)],
                                  order='branch_id')
            _logger.warning("The new sequence is %s", seq_ids[0])
        else:
            seq_ids = self.search([('code', '=', sequence_code), ('company_id', 'in', [force_company, False])],
                                  order='company_id')
        if not seq_ids:
            _logger.debug(
                "No ir.sequence has been found for code '%s'. Please make sure a sequence is set for current branch." % sequence_code)
            return False
        seq_id = seq_ids[0]
        _logger.warning("The new sequence returned is %s", seq_id)
        return seq_id._next(sequence_date=sequence_date)
