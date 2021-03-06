# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Partner Statement",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "OCA Financial Reports",
    "author": "AKTIV SOFTWARE",
    "website": "http://www.aktivsoftware.com",
    "license": "AGPL-3",
    "depends": ["account"],
    "external_dependencies": {"python": ["dateutil"]} ,
    "data": [
        "security/statement_security.xml",
        "security/ir.model.access.csv",
        "views/activity_statement.xml",
        "views/outstanding_statement.xml",
        #"views/assets.xml",
        "views/aging_buckets.xml",
        "views/res_config_settings.xml",
        "wizard/statement_wizard.xml",
        "data/account_email_template_data.xml",
    ],
    "installable": True,
    "application": False,
}
