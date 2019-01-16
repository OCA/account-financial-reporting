# Copyright  2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class VATReport(models.TransientModel):
    _name = "report_vat_report"
    _inherit = 'account_financial_report_abstract'
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * VATReport
    ** VATReportTaxTags
    *** VATReportTax
    """

    # Filters fields, used for data computation
    company_id = fields.Many2one(comodel_name='res.company')
    date_from = fields.Date()
    date_to = fields.Date()
    based_on = fields.Selection([('taxtags', 'Tax Tags'),
                                 ('taxgroups', 'Tax Groups')],
                                string='Based On',
                                required=True,
                                default='taxtags')
    tax_detail = fields.Boolean('Tax Detail')

    # Data fields, used to browse report data
    taxtags_ids = fields.One2many(
        comodel_name='report_vat_report_taxtag',
        inverse_name='report_id'
    )


class VATReportTaxTags(models.TransientModel):
    _name = 'report_vat_report_taxtag'
    _inherit = 'account_financial_report_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_vat_report',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    taxtag_id = fields.Many2one(
        'account.account.tag',
        index=True
    )
    taxgroup_id = fields.Many2one(
        'account.tax.group',
        index=True
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    tax_ids = fields.One2many(
        comodel_name='report_vat_report_tax',
        inverse_name='report_tax_id',
        string='Taxes'
    )


class VATReportTax(models.TransientModel):
    _name = 'report_vat_report_tax'
    _inherit = 'account_financial_report_abstract'
    _order = 'name ASC'

    report_tax_id = fields.Many2one(
        comodel_name='report_vat_report_taxtag',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    tax_id = fields.Many2one(
        'account.tax',
        index=True,
        string='Tax ID',
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    net = fields.Float(digits=(16, 2))
    tax = fields.Float(digits=(16, 2))


class VATReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_vat_report'

    @api.multi
    def print_report(self, report_type='qweb'):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'a_f_r.report_vat_report_xlsx'
        else:
            report_name = 'account_financial_report.report_vat_report_qweb'
        context = dict(self.env.context)
        action = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', report_type)], limit=1)
        return action.with_context(context).report_action(self, config=False)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report.report_vat_report').render(
                    rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self.with_context(given_context)._get_html()

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute report data
        if self.based_on == 'taxtags':
            self._inject_taxtags_values()
            self._inject_tax_taxtags_values()
        elif self.based_on == 'taxgroups':
            self._inject_taxgroups_values()
            self._inject_tax_taxgroups_values()
        # Refresh cache because all data are computed with SQL requests
        self.refresh()

    def _inject_taxtags_values(self):
        """Inject report values for report_vat_report_taxtags."""
        query_inject_taxtags = """
WITH
    taxtags AS
        (SELECT coalesce(regexp_replace(tag.name,
                '[^0-9\\.]+', '', 'g'), ' ') AS code,
                tag.name, tag.id,
                coalesce(sum(movetax.tax_base_amount), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax
            FROM
                account_account_tag AS tag
                INNER JOIN account_tax_account_tag AS taxtag
                    ON tag.id = taxtag.account_account_tag_id
                INNER JOIN account_tax AS tax
                    ON tax.id = taxtag.account_tax_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE tag.id is not null AND movetax.tax_exigible
                AND move.company_id = %s AND move.date >= %s
                    AND move.date <= %s AND move.state = 'posted'
            GROUP BY tag.id
            ORDER BY code, tag.name
        )
INSERT INTO
    report_vat_report_taxtag
    (
    report_id,
    create_uid,
    create_date,
    taxtag_id,
    code,
    name,
    net, tax
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    tag.id,
    tag.code,
    tag.name,
    abs(tag.net),
    abs(tag.tax)
FROM
    taxtags tag
        """
        query_inject_taxtags_params = (self.company_id.id, self.date_from,
                                       self.date_to, self.id, self.env.uid)
        self.env.cr.execute(query_inject_taxtags, query_inject_taxtags_params)

    def _inject_taxgroups_values(self):
        """Inject report values for report_vat_report_taxtags."""
        query_inject_taxgroups = """
WITH
    taxgroups AS
        (SELECT coalesce(taxgroup.sequence, 0) AS code,
                taxgroup.name, taxgroup.id,
                coalesce(sum(movetax.tax_base_amount), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax
            FROM
                account_tax_group AS taxgroup
                INNER JOIN account_tax AS tax
                    ON tax.tax_group_id = taxgroup.id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE taxgroup.id is not null AND movetax.tax_exigible
                AND move.company_id = %s AND move.date >= %s
                    AND move.date <= %s AND move.state = 'posted'
            GROUP BY taxgroup.id
            ORDER BY code, taxgroup.name
        )
INSERT INTO
    report_vat_report_taxtag
    (
    report_id,
    create_uid,
    create_date,
    taxgroup_id,
    code,
    name,
    net, tax
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    groups.id,
    groups.code,
    groups.name,
    abs(groups.net),
    abs(groups.tax)
FROM
    taxgroups groups
        """
        query_inject_taxgroups_params = (self.company_id.id, self.date_from,
                                         self.date_to, self.id, self.env.uid)
        self.env.cr.execute(query_inject_taxgroups,
                            query_inject_taxgroups_params)

    def _inject_tax_taxtags_values(self):
        """ Inject report values for report_vat_report_tax. """
        # pylint: disable=sql-injection
        query_inject_tax = """
WITH
    taxtags_tax AS
        (
            SELECT
                tag.id AS report_tax_id, ' ' AS code,
                tax.name, tax.id,
                coalesce(sum(movetax.tax_base_amount), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax
            FROM
                report_vat_report_taxtag AS tag
                INNER JOIN account_tax_account_tag AS taxtag
                    ON tag.taxtag_id = taxtag.account_account_tag_id
                INNER JOIN account_tax AS tax
                    ON tax.id = taxtag.account_tax_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE tag.id is not null AND movetax.tax_exigible
                AND tag.report_id = %s AND move.company_id = %s
                AND move.date >= %s AND move.date <= %s
                AND move.state = 'posted'
            GROUP BY tag.id, tax.id
            ORDER BY tax.name
        )
INSERT INTO
    report_vat_report_tax
    (
    report_tax_id,
    create_uid,
    create_date,
    tax_id,
    name,
    net,
    tax
    )
SELECT
    tt.report_tax_id,
    %s AS create_uid,
    NOW() AS create_date,
    tt.id,
    tt.name,
    abs(tt.net),
    abs(tt.tax)
FROM
    taxtags_tax tt
        """
        query_inject_tax_params = (self.id, self.company_id.id, self.date_from,
                                   self.date_to, self.env.uid)
        self.env.cr.execute(query_inject_tax, query_inject_tax_params)

    def _inject_tax_taxgroups_values(self):
        """ Inject report values for report_vat_report_tax. """
        # pylint: disable=sql-injection
        query_inject_tax = """
WITH
    taxtags_tax AS
        (
            SELECT
                taxtag.id AS report_tax_id, ' ' AS code,
                tax.name, tax.id,
                coalesce(sum(movetax.tax_base_amount), 0.00) AS net,
                coalesce(sum(movetax.balance), 0.00) AS tax
            FROM
                report_vat_report_taxtag AS taxtag
                INNER JOIN account_tax AS tax
                    ON tax.tax_group_id = taxtag.taxgroup_id
                INNER JOIN account_move_line AS movetax
                    ON movetax.tax_line_id = tax.id
                INNER JOIN account_move AS move
                    ON move.id = movetax.move_id
            WHERE taxtag.id is not null AND movetax.tax_exigible
                AND taxtag.report_id = %s AND move.company_id = %s
                AND move.date >= %s AND move.date <= %s
                AND move.state = 'posted'
            GROUP BY taxtag.id, tax.id
            ORDER BY tax.name
        )
INSERT INTO
    report_vat_report_tax
    (
    report_tax_id,
    create_uid,
    create_date,
    tax_id,
    name,
    net,
    tax
    )
SELECT
    tt.report_tax_id,
    %s AS create_uid,
    NOW() AS create_date,
    tt.id,
    tt.name,
    abs(tt.net),
    abs(tt.tax)
FROM
    taxtags_tax tt
        """
        query_inject_tax_params = (self.id, self.company_id.id, self.date_from,
                                   self.date_to, self.env.uid)
        self.env.cr.execute(query_inject_tax, query_inject_tax_params)
