# -*- coding: utf-8 -*-
# © 2016 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import timedelta, date, datetime as dtm
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from odoo.tools import float_is_zero

from odoo import models, fields, api, _


class OpenItemsReport(models.TransientModel):
    """ Here, we just define class fields.
    For methods, go more bottom at this file.

    The class hierarchy is :
    * OpenItemsReport
    ** OpenItemsReportAccount
    *** OpenItemsReportPartner
    **** OpenItemsReportMoveLine
    """

    _name = 'report_open_items_qweb'
    _inherit = 'report_qweb_abstract'

    # Filters fields, used for data computation
    date_at = fields.Date()
    only_posted_moves = fields.Boolean()
    hide_account_at_0 = fields.Boolean()
    foreign_currency = fields.Boolean()
    company_id = fields.Many2one(comodel_name='res.company')
    filter_account_ids = fields.Many2many(comodel_name='account.account')
    filter_partner_ids = fields.Many2many(comodel_name='res.partner')

    # Data fields, used to browse report data
    account_ids = fields.One2many(
        comodel_name='report_open_items_qweb_account',
        inverse_name='report_id'
    )


class OpenItemsReportAccount(models.TransientModel):

    _name = 'report_open_items_qweb_account'
    _inherit = 'report_qweb_abstract'
    _order = 'code ASC'

    report_id = fields.Many2one(
        comodel_name='report_open_items_qweb',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    account_id = fields.Many2one(
        'account.account',
        index=True
    )

    # Data fields, used for report display
    code = fields.Char()
    name = fields.Char()
    currency_id = fields.Many2one(comodel_name='res.currency')
    final_amount_residual = fields.Float(digits=(16, 2))
    final_amount_total_due = fields.Float(digits=(16, 2))
    final_amount_residual_currency = fields.Float(digits=(16, 2))
    final_amount_total_due_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    partner_ids = fields.One2many(
        comodel_name='report_open_items_qweb_partner',
        inverse_name='report_account_id'
    )


class OpenItemsReportPartner(models.TransientModel):

    _name = 'report_open_items_qweb_partner'
    _inherit = 'report_qweb_abstract'

    report_account_id = fields.Many2one(
        comodel_name='report_open_items_qweb_account',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    partner_id = fields.Many2one(
        'res.partner',
        index=True
    )

    # Data fields, used for report display
    name = fields.Char()
    currency_id = fields.Many2one(comodel_name='res.currency')
    final_amount_residual = fields.Float(digits=(16, 2))
    final_amount_total_due = fields.Float(digits=(16, 2))
    final_amount_residual_currency = fields.Float(digits=(16, 2))
    final_amount_total_due_currency = fields.Float(digits=(16, 2))

    # Data fields, used to browse report data
    move_line_ids = fields.One2many(
        comodel_name='report_open_items_qweb_move_line',
        inverse_name='report_partner_id'
    )

    @api.model
    def _generate_order_by(self, order_spec, query):
        """Custom order to display "No partner allocated" at last position."""
        return """
ORDER BY
    CASE
        WHEN "report_open_items_qweb_partner"."partner_id" IS NOT NULL
        THEN 0
        ELSE 1
    END,
    "report_open_items_qweb_partner"."name"
        """


class OpenItemsReportMoveLine(models.TransientModel):

    _name = 'report_open_items_qweb_move_line'
    _inherit = 'report_qweb_abstract'

    report_partner_id = fields.Many2one(
        comodel_name='report_open_items_qweb_partner',
        ondelete='cascade',
        index=True
    )

    # Data fields, used to keep link with real object
    move_line_id = fields.Many2one('account.move.line')

    # Data fields, used for report display
    date = fields.Date()
    date_due = fields.Date()
    entry = fields.Char()
    journal = fields.Char()
    account = fields.Char()
    partner = fields.Char()
    label = fields.Char()
    amount_total_due = fields.Float(digits=(16, 2))
    amount_residual = fields.Float(digits=(16, 2))
    currency_id = fields.Many2one(comodel_name='res.currency')
    amount_total_due_currency = fields.Float(digits=(16, 2))
    amount_residual_currency = fields.Float(digits=(16, 2))


class OpenItemsReportCompute(models.TransientModel):
    """ Here, we just define methods.
    For class fields, go more top at this file.
    """

    _inherit = 'report_open_items_qweb'

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type == 'xlsx':
            report_name = 'account_financial_report_qweb.' \
                          'report_open_items_xlsx'
        else:
            report_name = 'account_financial_report_qweb.' \
                          'report_open_items_qweb'
        return self.env['report'].get_action(docids=self.ids,
                                             report_name=report_name)

    def _get_html(self):
        result = {}
        rcontext = {}
        context = dict(self.env.context)
        report = self.browse(context.get('active_id'))
        if report:
            rcontext['o'] = report
            result['html'] = self.env.ref(
                'account_financial_report_qweb.'
                'report_open_items_html').render(rcontext)
        return result

    @api.model
    def get_html(self, given_context=None):
        return self._get_html()

    @api.model
    def _get_move_lines_domain(self, company_id, account_ids, partner_ids,
                               target_move, date_from):
        domain = [('account_id', 'in', account_ids),
                  ('company_id', '=', company_id),
                  ('reconciled', '=', False)]
        if partner_ids:
            domain += [('partner_id', 'in', partner_ids)]
        if target_move == 'posted':
            domain += [('move_id.state', '=', 'posted')]
        if date_from:
            domain += [('date', '>', date_from)]
        return domain

    def _recalculate_move_lines(self, move_lines, debit_ids, credit_ids,
                                debit_amount, credit_amount, ml_ids,
                                account_ids, company_id, partner_ids,
                                target_moves):
        debit_ids = set(debit_ids)
        credit_ids = set(credit_ids)
        in_credit_but_not_in_debit = credit_ids - debit_ids
        reconciled_ids = list(debit_ids) + list(in_credit_but_not_in_debit)
        reconciled_ids = set(reconciled_ids)
        ml_ids = set(ml_ids)
        new_ml_ids = reconciled_ids - ml_ids
        new_ml_ids = list(new_ml_ids)
        new_domain = self._get_new_move_lines_domain(new_ml_ids, account_ids,
                                                     company_id, partner_ids,
                                                     target_moves)
        ml_fields = [
            'id', 'name', 'date', 'move_id', 'journal_id', 'account_id',
            'partner_id', 'amount_residual', 'date_maturity', 'ref',
            'debit', 'credit', 'balance', 'reconciled', 'currency_id', 'amount_currency',
            'amount_residual_currency']
        new_move_lines = self.env['account.move.line'].search_read(
            domain=new_domain, fields=ml_fields
        )
        move_lines = move_lines + new_move_lines
        for move_line in move_lines:
            ml_id = move_line['id']
            if ml_id in debit_ids:
                move_line['amount_residual'] += debit_amount[ml_id]
            if ml_id in credit_ids:
                move_line['amount_residual'] -= credit_amount[ml_id]
        return move_lines
        
    def _get_data(
            self, account_ids, partner_ids, date_at_object,
            target_move, company_id, date_from):
        domain = self._get_move_lines_domain(company_id, account_ids,
                                             partner_ids, target_move,
                                             date_from)
        ml_fields = [
            'id', 'name', 'date', 'move_id', 'journal_id', 'account_id',
            'partner_id', 'amount_residual', 'date_maturity', 'ref',
            'debit', 'credit', 'balance', 'reconciled', 'currency_id', 'amount_currency',
            'amount_residual_currency']
        move_lines = self.env['account.move.line'].search_read(
            domain=domain, fields=ml_fields
        )
        journals_ids = set()
        partners_ids = set()
        partners_data = {}
        date_at_object = dtm.strptime(date_at_object, DT).date()
        if date_at_object < date.today():
            acc_partial_rec, debit_amount, credit_amount = \
                self._get_account_partial_reconciled(company_id,
                                                     date_at_object)
            if acc_partial_rec:
                ml_ids = list(map(operator.itemgetter('id'), move_lines))
                debit_ids = list(map(operator.itemgetter('debit_move_id'),
                                     acc_partial_rec))
                credit_ids = list(map(operator.itemgetter('credit_move_id'),
                                      acc_partial_rec))
                move_lines = self._recalculate_move_lines(
                    move_lines, debit_ids, credit_ids,
                    debit_amount, credit_amount, ml_ids, account_ids,
                    company_id, partner_ids, target_move
                )
        move_lines = [move_line for move_line in move_lines if
                      dtm.strptime(move_line['date'], DT).date() <= date_at_object and not
                      float_is_zero(move_line['amount_residual'],
                                    precision_digits=2)]

        open_items_move_lines_data = {}
        for move_line in move_lines:
            journals_ids.add(move_line['journal_id'][0])
            acc_id = move_line['account_id'][0]
            # Partners data
            if move_line['partner_id']:
                prt_id = move_line['partner_id'][0]
                prt_name = move_line['partner_id'][1]
            else:
                prt_id = 0
                prt_name = "Missing Partner"
            if prt_id not in partners_ids:
                partners_data.update({
                    prt_id: {'id': prt_id, 'name': prt_name}
                })
                partners_ids.add(prt_id)

            # Move line update
            original = 0

            if not float_is_zero(move_line['credit'], precision_digits=2):
                original = move_line['credit']*(-1)
            if not float_is_zero(move_line['debit'], precision_digits=2):
                original = move_line['debit']

            if move_line['ref'] == move_line['name']:
                if move_line['ref']:
                    ref_label = move_line['ref']
                else:
                    ref_label = ''
            elif not move_line['ref']:
                ref_label = move_line['name']
            elif not move_line['name']:
                ref_label = move_line['ref']
            else:
                ref_label = move_line['ref'] + str(' - ') + move_line['name']

            move_line.update({
                'date': move_line['date'],
                'date_maturity': move_line["date_maturity"],
                'original': original,
                'partner_id': prt_id,
                'partner_name': prt_name,
                'ref_label': ref_label,
                'journal_id': move_line['journal_id'][0],
                'move_name': move_line['move_id'][1],
                'currency_id': move_line['currency_id'][0]
                if move_line['currency_id'] else False,
                'currency_name': move_line['currency_id'][1]
                if move_line['currency_id'] else False,
            })

            # Open Items Move Lines Data
            if acc_id not in open_items_move_lines_data.keys():
                open_items_move_lines_data[acc_id] = {prt_id: [move_line]}
            else:
                if prt_id not in open_items_move_lines_data[acc_id].keys():
                    open_items_move_lines_data[acc_id][prt_id] = [move_line]
                else:
                    open_items_move_lines_data[acc_id][prt_id].append(move_line)
        journals_data = self._get_journals_data(list(journals_ids))
        accounts_data = self._get_accounts_data(
            open_items_move_lines_data.keys())
        return move_lines, partners_data, journals_data, accounts_data, \
            open_items_move_lines_data

    def _get_journals_data(self, journals_ids):
        journals = self.env['account.journal'].browse(journals_ids)
        journals_data = {}
        for journal in journals:
            journals_data.update({journal.id: {'id': journal.id,
                                               'code': journal.code}})
        return journals_data

    def _get_accounts_data(self, accounts_ids):
        accounts = self.env['account.account'].browse(accounts_ids)
        accounts_data = {}
        for account in accounts:
            accounts_data.update({account.id: {
                'id': account.id,
                'code': account.code,
                'name': account.name,
                'hide_account': False,
                'currency_id': account.currency_id or False,
                'currency_name': account.currency_id.name}
            })
        return accounts_data

    @api.model
    def _calculate_amounts(self, open_items_move_lines_data):
        total_amount = {}
        for account_id in open_items_move_lines_data.keys():
            total_amount[account_id] = {}
            total_amount[account_id]['residual'] = 0.0
            for partner_id in open_items_move_lines_data[account_id].keys():
                total_amount[account_id][partner_id] = {}
                total_amount[account_id][partner_id]['residual'] = 0.0
                for move_line in open_items_move_lines_data[account_id][
                        partner_id]:
                    total_amount[account_id][partner_id]['residual'] += \
                        move_line['amount_residual']
                    total_amount[account_id]['residual'] += move_line[
                        'amount_residual']
        return total_amount

    @api.model
    def _order_open_items_by_date(
            self, open_items_move_lines_data):
        new_open_items = {}
        for acc_id in open_items_move_lines_data.keys():
            new_open_items[acc_id] = {}
            move_lines = []
            for prt_id in open_items_move_lines_data[acc_id]:
                for move_line in open_items_move_lines_data[acc_id][prt_id]:
                    move_lines += [move_line]
            move_lines = sorted(move_lines, key=lambda k: (k['date']))
            new_open_items[acc_id] = move_lines
        else:
            for acc_id in open_items_move_lines_data.keys():
                new_open_items[acc_id] = {}
                for prt_id in open_items_move_lines_data[acc_id]:
                    new_open_items[acc_id][prt_id] = {}
                    move_lines = []
                    for move_line in open_items_move_lines_data[acc_id][prt_id]:
                        move_lines += [move_line]
                    move_lines = sorted(move_lines, key=lambda k: (k['date']))
                    new_open_items[acc_id][prt_id] = move_lines
        return new_open_items

    def _insert_line_info(self, line_data):
        # partner may be undefined but there is a record in the table report_xxx_partner
        partner_id = line_data.get('partner_id', 0)
        if partner_id and isinstance(partner_id, list):
            partner_id = partner_id[0]
        elif partner_id:
            pass
        else:
            partner_id = False
        report_partner_id = self.env['report_open_items_qweb_partner'].search([('partner_id', '=', partner_id)])[-1].id
        create_uid = 1
        create_date = line_data.get('date', dtm.strftime(dtm.now(), DT))
        move_line_id = line_data.get('id', 0)
        date = line_data.get('create_date', dtm.strftime(dtm.now(), DT))
        date_due = line_data.get('date_maturity', date)
        entry = line_data.get('move_name', "Undefined")
        journal_id = line_data.get('journal_id', 0)
        if journal_id == 0:
            journal = "Undefined"
        else:
            journal = self.env['account.journal'].browse(journal_id).name
        account_id = line_data.get('account_id', 0)
        if account_id:
            account = self.env['account.account'].browse(account_id[0]).code
        else:
            account_id = 0
        if not partner_id:
            partner = "Undefined"
        else:
            # partners with apostrophe
            partner = self.env['res.partner'].browse(partner_id).display_name.replace("'", " ")
        label = line_data.get('ref_label', "Undefined")
        amount_total_due = line_data.get('balance', 0)
        amount_residual = line_data.get('amount_residual', 0)
        currency_id = line_data.get('currency_id', 0)
        amount_total_due_currency = line_data.get('amount_currency', 0)
        amount_residual_currency = line_data.get('amount_residual_currency', 0)
        insert_query = """
            INSERT INTO report_open_items_qweb_move_line
                (
                report_partner_id,
                create_uid,
                create_date,
                move_line_id,
                date,
                date_due,
                entry,
                journal,
                account,
                partner,
                label,
                amount_total_due,
                amount_residual,
                currency_id,
                amount_total_due_currency,
                amount_residual_currency
            )
            VALUES
            (%s,
            %s,
            '%s',
            %s,
            '%s',
            '%s',
            '%s',
            '%s',
            %s,
            '%s',
            '%s',
            %s,
            %s,
            %s,
            %s,
            '%s'
            )
        """ % (
            report_partner_id or "null",
            create_uid,
            create_date,
            move_line_id,
            date,
            date_due,
            entry,
            journal,
            account,
            partner,
            label,
            amount_total_due,
            amount_residual,
            currency_id or "null",
            amount_total_due_currency,
            amount_residual_currency
        )
        self.env.cr.execute(insert_query)


    def _insert_partner_info(self, line_data):
        account_id = line_data.get('account_id', 0)
        if account_id:
            account_id = account_id[0]
            report_account_id = self.env['report_open_items_qweb_account'].search([('account_id', '=', account_id)])[-1].id
        else:
            report_account_id = 0

        partner_id = line_data.get('partner_id', 0)
        create_uid = 1
        create_date = line_data.get('date', dtm.strftime(dtm.now(), DT))
        if partner_id == 0:
            name = "Undefined"
        else:
            name = self.env['res.partner'].browse(partner_id).display_name.replace("'", " ")

        insert_query = """
            INSERT INTO
                report_open_items_qweb_partner
                (
                report_account_id,
                create_uid,
                create_date,
                partner_id,
                name
                )
            VALUES
            (%s,
            %s,
            '%s',
            %s,
            '%s'
            )
        """ % (
            report_account_id or "null",
            create_uid,
            create_date,
            partner_id or "null",
            name
        )
        self.env.cr.execute(insert_query)

    def _insert_account_info(self, line_data):
        # taking the last report
        report_id = self.env['report_open_items_qweb'].search([], order="id desc", limit=1).id
        create_uid = 1
        create_date = line_data.get('date', dtm.strftime(dtm.now(), DT))
        account_id = line_data.get('account_id', 0)
        if account_id:
            code = account_id[0]
        else:
            code = "Undefined"
        currency_id = line_data.get('currency_id', 0)
        if currency_id:
            currency_id = currency_id[0]            
        if account_id == 0:
            name = "Undefined"
            account = 0
        else:
            name = self.env['account.account'].browse(account_id[0]).display_name
            account = account_id[0]

        insert_query = """
            INSERT INTO
                report_open_items_qweb_account
                (
                report_id,
                create_uid,
                create_date,
                account_id,
                currency_id,
                code,
                name
                )
            VALUES
            (%s,
            %s,
            '%s',
            %s,
            %s,
            '%s',
            '%s'
            )
        """ % (
            report_id or "null",
            create_uid,
            create_date,
            account or "null",
            currency_id or "null",
            code,
            name
        )
        self.env.cr.execute(insert_query)

    def _inject_line_values_from_open_items_move_lines_data(self, open_items_move_lines_data):
        for account_id in open_items_move_lines_data.keys():
            # For each account
            if open_items_move_lines_data[account_id]:
                for partner_id in open_items_move_lines_data[account_id]:
                    # Display account move lines
                    for line in open_items_move_lines_data[account_id][partner_id]:
                        self._insert_line_info(line)

    @api.multi
    def compute_data_for_report(self):
        self.ensure_one()
        # Compute report data
        self._inject_account_values()
        self._inject_partner_values()
        # backport for open items refactor v12
        move_lines_data, partners_data, journals_data, accounts_data, \
            open_items_move_lines_data = self._get_data(
                self.filter_account_ids.ids, self.filter_partner_ids.ids, self.date_at,
                self.only_posted_moves, self.company_id.id, False)
        total_amount = self._calculate_amounts(open_items_move_lines_data)
        open_items_move_lines_data = self._order_open_items_by_date(
            open_items_move_lines_data
        )
        self._inject_line_values_from_open_items_move_lines_data(open_items_move_lines_data)        
        self._clean_partners_and_accounts()
        self._compute_partners_and_accounts_cumul()
        if self.hide_account_at_0:
            self._clean_partners_and_accounts(
                only_delete_account_balance_at_0=True
            )
        # Refresh cache because all data are computed with SQL requests
        self.invalidate_cache()

    def _inject_account_values(self):
        """Inject report values for report_open_items_qweb_account."""
        query_inject_account = """
WITH
    accounts AS
        (
            SELECT
                a.id,
                a.code,
                a.name,
                a.user_type_id,
                c.id as currency_id
            FROM
                account_account a
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id AND ml.date <= %s
            LEFT JOIN
                res_currency c ON a.currency_id = c.id
            """
        if self.filter_partner_ids:
            query_inject_account += """
            INNER JOIN
                res_partner p ON ml.partner_id = p.id
            """
        if self.only_posted_moves:
            query_inject_account += """
            INNER JOIN
                account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        query_inject_account += """
            WHERE
                a.company_id = %s
            AND a.reconcile IS true
            """
        if self.filter_account_ids:
            query_inject_account += """
            AND
                a.id IN %s
            """
        if self.filter_partner_ids:
            query_inject_account += """
            AND
                p.id IN %s
            """
        query_inject_account += """
            GROUP BY
                a.id, c.id
        )
INSERT INTO
    report_open_items_qweb_account
    (
    report_id,
    create_uid,
    create_date,
    account_id,
    currency_id,
    code,
    name
    )
SELECT
    %s AS report_id,
    %s AS create_uid,
    NOW() AS create_date,
    a.id AS account_id,
    a.currency_id,
    a.code,
    a.name
FROM
    accounts a
        """
        query_inject_account_params = (
            self.date_at,
            self.company_id.id,
        )
        if self.filter_account_ids:
            query_inject_account_params += (
                tuple(self.filter_account_ids.ids),
            )
        if self.filter_partner_ids:
            query_inject_account_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_account_params += (
            self.id,
            self.env.uid,
        )
        self.env.cr.execute(query_inject_account, query_inject_account_params)

    def _inject_partner_values(self):
        """ Inject report values for report_open_items_qweb_partner. """
        # pylint: disable=sql-injection
        query_inject_partner = """
WITH
    accounts_partners AS
        (
            SELECT
                ra.id AS report_account_id,
                a.id AS account_id,
                at.include_initial_balance AS include_initial_balance,
                p.id AS partner_id,
                COALESCE(
                    CASE
                        WHEN
                            NULLIF(p.name, '') IS NOT NULL
                            AND NULLIF(p.ref, '') IS NOT NULL
                        THEN p.name || ' (' || p.ref || ')'
                        ELSE p.name
                    END,
                    '""" + _('No partner allocated') + """'
                ) AS partner_name
            FROM
                report_open_items_qweb_account ra
            INNER JOIN
                account_account a ON ra.account_id = a.id
            INNER JOIN
                account_account_type at ON a.user_type_id = at.id
            INNER JOIN
                account_move_line ml ON a.id = ml.account_id AND ml.date <= %s
        """
        if self.only_posted_moves:
            query_inject_partner += """
            INNER JOIN
                account_move m ON ml.move_id = m.id AND m.state = 'posted'
            """
        query_inject_partner += """
            LEFT JOIN
                res_partner p ON ml.partner_id = p.id
            WHERE
                ra.report_id = %s
                        """
        if self.filter_partner_ids:
            query_inject_partner += """
            AND
                p.id IN %s
            """
        query_inject_partner += """
            GROUP BY
                ra.id,
                a.id,
                p.id,
                at.include_initial_balance
        )
INSERT INTO
    report_open_items_qweb_partner
    (
    report_account_id,
    create_uid,
    create_date,
    partner_id,
    name
    )
SELECT
    ap.report_account_id,
    %s AS create_uid,
    NOW() AS create_date,
    ap.partner_id,
    ap.partner_name
FROM
    accounts_partners ap
        """
        query_inject_partner_params = (
            self.date_at,
            self.id,
        )
        if self.filter_partner_ids:
            query_inject_partner_params += (
                tuple(self.filter_partner_ids.ids),
            )
        query_inject_partner_params += (
            self.env.uid,
        )
        self.env.cr.execute(query_inject_partner, query_inject_partner_params)

    def _compute_partners_and_accounts_cumul(self):
        """ Compute cumulative amount for
        report_open_items_qweb_partner and report_open_items_qweb_account.
        """
        self._compute_partner_cumul()
        self._compute_account_cumul()

    def _compute_partner_cumul(self):
        # pylint: disable=sql-injection
        where_condition_partner_by_account = """
WHERE
    id IN
        (
            SELECT
                rp.id
            FROM
                report_open_items_qweb_account ra
            INNER JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s
        )"""
        query_computer_partner_residual_cumul = """
UPDATE
    report_open_items_qweb_partner
SET
    final_amount_residual =
        (
            SELECT
                SUM(rml.amount_residual) AS final_amount_residual
            FROM
                report_open_items_qweb_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_qweb_partner.id
        )
""" + where_condition_partner_by_account
        params_compute_partners_residual_cumul = (self.id,)
        self.env.cr.execute(query_computer_partner_residual_cumul,
                            params_compute_partners_residual_cumul)

        query_compute_partners_due_cumul = """
UPDATE
    report_open_items_qweb_partner
SET
    final_amount_total_due =
        (
            SELECT
                SUM(rml.amount_total_due) AS final_amount_total_due
            FROM
                report_open_items_qweb_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_qweb_partner.id
        )
""" + where_condition_partner_by_account
        params_compute_partner_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_due_cumul,
                            params_compute_partner_due_cumul)

        # Manage currency in partner
        where_condition_partner_by_account_cur = """
WHERE
    id IN
        (
            SELECT
                rp.id
            FROM
                report_open_items_qweb_account ra
            INNER JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s AND ra.currency_id IS NOT NULL
        )
        """
        query_compute_partners_cur_id_cumul = """
UPDATE
    report_open_items_qweb_partner
SET
    currency_id =
        (
            SELECT
                MAX(currency_id) as currency_id
            FROM
                report_open_items_qweb_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_qweb_partner.id
        )
""" + where_condition_partner_by_account_cur
        params_compute_partners_cur_id_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cur_id_cumul,
                            params_compute_partners_cur_id_cumul)

        query_compute_partners_cur_residual_cumul = """
UPDATE
    report_open_items_qweb_partner
SET
    final_amount_residual_currency =
        (
            SELECT
                SUM(rml.amount_residual_currency)
                    AS final_amount_residual_currency
            FROM
                report_open_items_qweb_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_qweb_partner.id
        )
""" + where_condition_partner_by_account_cur
        params_compute_partners_cur_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cur_residual_cumul,
                            params_compute_partners_cur_residual_cumul)

        query_compute_partners_cur_due_cumul = """
UPDATE
    report_open_items_qweb_partner
SET
    final_amount_total_due_currency =
        (
            SELECT
                SUM(rml.amount_total_due_currency)
                    AS final_amount_total_due_currency
            FROM
                report_open_items_qweb_move_line rml
            WHERE
                rml.report_partner_id = report_open_items_qweb_partner.id
        )
""" + where_condition_partner_by_account_cur
        params_compute_partners_cur_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_partners_cur_due_cumul,
                            params_compute_partners_cur_due_cumul)

    def _compute_account_cumul(self):
        query_compute_accounts_residual_cumul = """
UPDATE
    report_open_items_qweb_account
SET
    final_amount_residual =
        (
            SELECT
                SUM(rp.final_amount_residual) AS final_amount_residual
            FROM
                report_open_items_qweb_partner rp
            WHERE
                rp.report_account_id = report_open_items_qweb_account.id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_residual_cumul,
                            params_compute_accounts_residual_cumul)

        query_compute_accounts_cur_residual_cumul = """
UPDATE
    report_open_items_qweb_account
SET
    final_amount_residual_currency =
        (
            SELECT
                SUM(rp.final_amount_residual_currency)
                    AS final_amount_residual_currency
            FROM
                report_open_items_qweb_partner rp
            WHERE
                rp.report_account_id = report_open_items_qweb_account.id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_cur_residual_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cur_residual_cumul,
                            params_compute_accounts_cur_residual_cumul)

        query_compute_accounts_due_cumul = """
UPDATE
    report_open_items_qweb_account
SET
    final_amount_total_due =
        (
            SELECT
                SUM(rp.final_amount_total_due) AS final_amount_total_due
            FROM
                report_open_items_qweb_partner rp
            WHERE
                rp.report_account_id = report_open_items_qweb_account.id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_due_cumul,
                            params_compute_accounts_due_cumul)

        query_compute_accounts_cur_due_cumul = """
UPDATE
    report_open_items_qweb_account
SET
    final_amount_total_due_currency =
        (
            SELECT
                SUM(rp.final_amount_total_due_currency)
                    AS final_amount_total_due_currency
            FROM
                report_open_items_qweb_partner rp
            WHERE
                rp.report_account_id = report_open_items_qweb_account.id
        )
WHERE
    report_id  = %s
        """
        params_compute_accounts_cur_due_cumul = (self.id,)
        self.env.cr.execute(query_compute_accounts_cur_due_cumul,
                            params_compute_accounts_cur_due_cumul)

    def _clean_partners_and_accounts(self,
                                     only_delete_account_balance_at_0=False):
        """ Delete empty data for
        report_open_items_qweb_partner and report_open_items_qweb_account.

        The "only_delete_account_balance_at_0" value is used
        to delete also the data with cumulative amounts at 0.
        """
        query_clean_partners = """
DELETE FROM
    report_open_items_qweb_partner
WHERE
    id IN
        (
            SELECT
                DISTINCT rp.id
            FROM
                report_open_items_qweb_account ra
            INNER JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            LEFT JOIN
                report_open_items_qweb_move_line rml
                    ON rp.id = rml.report_partner_id
            WHERE
                ra.report_id = %s
        """
        if not only_delete_account_balance_at_0:
            query_clean_partners += """
            AND rml.id IS NULL
            """
        elif only_delete_account_balance_at_0:
            query_clean_partners += """
            AND (
                rp.final_amount_residual IS NULL
                OR rp.final_amount_residual = 0
                )
            """
        query_clean_partners += """
        )
        """
        params_clean_partners = (self.id,)
        self.env.cr.execute(query_clean_partners, params_clean_partners)
        query_clean_accounts = """
DELETE FROM
    report_open_items_qweb_account
WHERE
    id IN
        (
            SELECT
                DISTINCT ra.id
            FROM
                report_open_items_qweb_account ra
            LEFT JOIN
                report_open_items_qweb_partner rp
                    ON ra.id = rp.report_account_id
            WHERE
                ra.report_id = %s
        """
        if not only_delete_account_balance_at_0:
            query_clean_accounts += """
            AND rp.id IS NULL
            """
        elif only_delete_account_balance_at_0:
            query_clean_accounts += """
            AND (
                ra.final_amount_residual IS NULL
                OR ra.final_amount_residual = 0
                )
            """
        query_clean_accounts += """
        )
        """
        params_clean_accounts = (self.id,)
        self.env.cr.execute(query_clean_accounts, params_clean_accounts)
