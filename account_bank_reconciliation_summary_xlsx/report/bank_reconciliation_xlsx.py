# Copyright 2017-2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BankReconciliationXlsx(models.AbstractModel):
    _name = "report.bank.reconciliation.xlsx"
    _description = "Bank Reconciliation XLSX Report"
    _inherit = "report.report_xlsx.abstract"

    def _compute_account_balance(self, journal, date, date_from=False):
        bank_account = journal.default_account_id
        # TODO: add support for bank accounts in foreign currency
        # if not o.currency_id else 'amount_currency'
        query = """
            SELECT sum(balance) FROM account_move_line
            WHERE account_id=%s AND date <= %s AND parent_state = 'posted'"""
        params = [bank_account.id, date]
        if date_from:
            query += " AND date >= %s"
            params.append(date_from)

        self.env.cr.execute(query, tuple(params))
        query_results = self.env.cr.dictfetchall()
        if query_results:
            account_bal = query_results[0].get("sum") or 0.0
        else:
            account_bal = 0.0
        return account_bal

    def _prepare_move_lines(self, journal, date, date_from=False):
        bank_account = journal.default_account_id
        domain = [
            ("account_id", "=", bank_account.id),
            ("journal_id", "=", journal.id),  # to avoid initial line
            ("date", "<=", date),
            ("move_id.state", "=", "posted"),
            "|",
            ("statement_line_date", "=", False),
            ("statement_line_date", ">", date),
        ]
        if date_from:
            domain.append(("date", ">=", date_from))

        mlines = self.env["account.move.line"].search(domain)
        res = []
        for mline in mlines:
            move = mline.move_id
            cpart = []
            for line in move.line_ids:
                if (
                    line.account_id != bank_account
                    and line.account_id.code not in cpart
                ):
                    cpart.append(line.account_id.code)
            counterpart = " ,".join(cpart)
            res.append(
                {
                    "date": mline.date,
                    "label": mline.name,
                    "ref": mline.ref or "",
                    "partner": mline.partner_id.display_name or "",
                    "amount": mline.balance,
                    "statement_line_date": mline.statement_line_date or "",
                    "move_number": move.name,
                    "counterpart": counterpart,
                }
            )
        return res

    def _prepare_draft_statement_lines(self, journal, date, date_from=False):
        domain = [
            ("is_reconciled", "=", False),
            ("journal_id", "=", journal.id),
            ("date", "<=", date),
        ]
        if date_from:
            domain.append(("date", ">=", date_from))

        blines = self.env["account.bank.statement.line"].search(domain)
        res = []
        for bline in blines:
            res.append(
                {
                    "date": bline.date,
                    "label": bline.name,
                    "ref": bline.ref or "",
                    "partner": bline.partner_id.display_name or "",
                    "amount": bline.amount,
                    "statement_ref": bline.statement_id.display_name or "",
                }
            )
        return res

    def _get_report_styles(self, workbook, journal):
        lang_code = self.env.user.lang
        lang = False
        if lang_code:
            lang = self.env["res.lang"].search([("code", "=", lang_code)])
        if not lang:
            lang = self.env["res.lang"].search([], limit=1)
        xls_date_format = (
            lang.date_format.replace("%Y", "yyyy")
            .replace("%m", "mm")
            .replace("%d", "dd")
            .replace("%y", "yy")
        )
        if "%" in xls_date_format:
            xls_date_format = "yyyy-mm-dd"

        cur_format = "#,##0.00 %s" % (
            journal.company_id.currency_id.symbol or journal.company_id.currency_id.name
        )

        styles = {
            "doc_title": workbook.add_format({"bold": True, "font_size": 16}),
            "col_title": workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#e2e2fa",
                    "text_wrap": True,
                    "font_size": 10,
                }
            ),
            "title_right": workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#e6e6fa",
                    "font_size": 10,
                    "align": "right",
                }
            ),
            "title_date": workbook.add_format(
                {
                    "bg_color": "#f6f6ff",
                    "bold": True,
                    "num_format": xls_date_format,
                    "font_size": 10,
                    "align": "left",
                }
            ),
            "label_bold": workbook.add_format(
                {"bold": True, "text_wrap": False, "font_size": 10}
            ),
            "none": workbook.add_format(
                {"bold": True, "font_size": 10, "align": "right"}
            ),
            "regular": workbook.add_format({"font_size": 10}),
            "regular_date": workbook.add_format(
                {"num_format": xls_date_format, "font_size": 10, "align": "left"}
            ),
            "regular_currency": workbook.add_format(
                {"num_format": cur_format, "font_size": 10}
            ),
            "regular_currency_bg": workbook.add_format(
                {"num_format": cur_format, "font_size": 10, "bg_color": "#f6f6ff"}
            ),
        }
        return styles

    def _write_report_header(self, sheet, journal, styles, date_from, date_dt):
        sheet.write(
            0,
            0,
            self.env._("%s - %s - Bank Reconciliation")
            % (journal.company_id.name, journal.display_name),
            styles["doc_title"],
        )
        sheet.set_row(0, 26)
        sheet.set_row(1, 25)
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 40)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 12)
        sheet.set_column(5, 5, 18)
        sheet.set_column(6, 6, 14)
        sheet.set_column(7, 7, 14)
        row = 2
        if date_from:
            sheet.write(row, 0, self.env._("Start Date:"), styles["title_right"])
            sheet.write(row, 1, date_from, styles["title_date"])
            row += 1
        sheet.write(row, 0, self.env._("End Date:"), styles["title_right"])
        sheet.write(row, 1, date_dt, styles["title_date"])
        return row + 2

    def _write_accounting_balance(self, sheet, row, journal, styles, date_from, date):
        bank_account = journal.default_account_id
        for col in range(3):
            sheet.write(row, col, "", styles["title_right"])
        sheet.write(
            row, 3, self.env._("Balance %s:") % bank_account.code, styles["title_right"]
        )
        account_bal = self._compute_account_balance(journal, date, date_from=date_from)
        sheet.write(row, 4, account_bal, styles["regular_currency_bg"])
        return account_bal

    def _write_move_lines(self, sheet, row, journal, styles, date_from, date):
        bank_account = journal.default_account_id
        sheet.write(
            row,
            0,
            self.env._(
                "Journal items of account %s not linked to a bank statement line:"
            )
            % bank_account.code,
            styles["label_bold"],
        )
        mlines = self._prepare_move_lines(journal, date, date_from=date_from)
        if not mlines:
            sheet.write(row, 4, self.env._("NONE"), styles["none"])
            return row + 2, 0, ""

        row += 1
        col_labels = [
            self.env._("Date"),
            self.env._("Label"),
            self.env._("Ref."),
            self.env._("Partner"),
            self.env._("Amount"),
            self.env._("Statement Line Date"),
            self.env._("Move Number"),
            self.env._("Counter-part"),
        ]
        for col, col_label in enumerate(col_labels):
            sheet.write(row, col, col_label, styles["col_title"])

        m_start_row = row + 1
        m_end_row = row
        total_amount = 0
        for mline in mlines:
            row += 1
            m_end_row = row
            total_amount += mline["amount"]
            sheet.write(row, 0, mline["date"], styles["regular_date"])
            sheet.write(row, 1, mline["label"], styles["regular"])
            sheet.write(row, 2, mline["ref"], styles["regular"])
            sheet.write(row, 3, mline["partner"], styles["regular"])
            sheet.write(row, 4, mline["amount"], styles["regular_currency"])
            sheet.write(row, 5, mline["statement_line_date"], styles["regular_date"])
            sheet.write(row, 6, mline["move_number"], styles["regular"])
            sheet.write(row, 7, mline["counterpart"], styles["regular"])

        formula = "-SUM(E%d:E%d)" % (m_start_row + 1, m_end_row + 1)
        return row + 2, total_amount, formula

    def _write_statement_lines(self, sheet, row, journal, styles, date_from, date):
        sheet.write(
            row, 0, self.env._("Draft bank statement lines:"), styles["label_bold"]
        )
        blines = self._prepare_draft_statement_lines(journal, date, date_from=date_from)
        if not blines:
            sheet.write(row, 4, self.env._("NONE"), styles["none"])
            return row + 2, 0, ""

        row += 1
        col_labels = [
            self.env._("Date"),
            self.env._("Label"),
            self.env._("Ref."),
            self.env._("Partner"),
            self.env._("Amount"),
            self.env._("Statement Ref."),
            "",
            "",
        ]
        for col, col_label in enumerate(col_labels):
            sheet.write(row, col, col_label, styles["col_title"])

        b_start_row = row + 1
        b_end_row = row
        total_amount = 0
        for bline in blines:
            row += 1
            b_end_row = row
            total_amount += bline["amount"]
            sheet.write(row, 0, bline["date"], styles["regular_date"])
            sheet.write(row, 1, bline["label"], styles["regular"])
            sheet.write(row, 2, bline["ref"], styles["regular"])
            sheet.write(row, 3, bline["partner"], styles["regular"])
            sheet.write(row, 4, bline["amount"], styles["regular_currency"])
            sheet.write(row, 5, bline["statement_ref"], styles["regular_currency"])

        formula = "+SUM(E%d:E%d)" % (b_start_row + 1, b_end_row + 1)
        return row + 2, total_amount, formula

    def _write_no_journal_warning(self, workbook):
        sheet = workbook.add_worksheet(self.env._("No Bank Journal"))
        sheet.set_row(0, 30)
        warn_msg = workbook.add_format(
            {"bold": True, "font_size": 16, "font_color": "#003b6f"}
        )
        sheet.write(
            0,
            0,
            self.env._(
                "No bank journal selected. This report is only for bank journals."
            ),
            warn_msg,
        )

    def generate_xlsx_report(self, workbook, data, wizard):
        date = wizard.date
        date_from = wizard.date_from
        date_dt = fields.Date.from_string(date)
        no_bank_journal = True
        for journal in wizard.journal_ids:
            no_bank_journal = False
            styles = self._get_report_styles(workbook, journal)
            sheet = workbook.add_worksheet(journal.code or journal.name)

            row = self._write_report_header(sheet, journal, styles, date_from, date_dt)

            account_bal = self._write_accounting_balance(
                sheet, row, journal, styles, date_from, date
            )
            bank_bal = account_bal
            formula = "=E%d" % (row + 1)
            row += 2

            row, m_amount, m_formula = self._write_move_lines(
                sheet, row, journal, styles, date_from, date
            )
            bank_bal -= m_amount
            formula += m_formula

            row, b_amount, b_formula = self._write_statement_lines(
                sheet, row, journal, styles, date_from, date
            )
            bank_bal += b_amount
            formula += b_formula

            # Theoretical bank account balance at the bank
            for col in range(3):
                sheet.write(row, col, "", styles["title_right"])
            sheet.write(
                row,
                3,
                self.env._("Computed Bank Account Balance at the Bank:"),
                styles["title_right"],
            )
            sheet.write_formula(
                row, 4, formula, styles["regular_currency_bg"], bank_bal
            )

        if no_bank_journal:
            self._write_no_journal_warning(workbook)
