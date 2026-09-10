// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {Component, useState} from "@odoo/owl";
import {AccountReportLines} from "../AccountReportLines/accountReportLines.esm";

export class AccountReportJournalLedger extends Component {
    static template = "account_financial_report.AccountReportJournalLedger";
    static props = {env: Object};
    static components = {AccountReportLines};

    static filterRowsByAccount(rows, prefix) {
        return rows
            .map((journal) => {
                const moves = journal.moves
                    .map((move) => ({
                        ...move,
                        lines: move.lines.filter((line) =>
                            String(line.account.code).trim().startsWith(prefix)
                        ),
                    }))
                    .filter((move) => move.lines.length);
                const lines = moves.flatMap((move) => move.lines);
                const total = journal.total
                    ? {
                          ...journal.total,
                          values: journal.total.values.map((cell) => {
                              if (cell.key !== "debit" && cell.key !== "credit")
                                  return cell;
                              return {
                                  ...cell,
                                  value: lines.reduce(
                                      (amount, line) =>
                                          amount +
                                          line.values.find(
                                              (value) => value.key === cell.key
                                          ).value,
                                      0
                                  ),
                              };
                          }),
                      }
                    : undefined;
                // The fiscal summary covers the complete journal, not filtered accounts.
                return {...journal, moves, total, taxes: []};
            })
            .filter((journal) => journal.moves.length);
    }

    setup() {
        this.state = useState({collapsedMoves: {}});
    }

    isMoveOpen(move) {
        return !this.state.collapsedMoves[move.key];
    }

    toggleMove(move) {
        this.state.collapsedMoves[move.key] = this.isMoveOpen(move);
    }

    get rows() {
        return this.props.env.filteredRows;
    }

    get columns() {
        return this.props.env.columns.filter((column) => column.show);
    }

    get taxColumns() {
        return this.props.env.taxColumns;
    }
}
