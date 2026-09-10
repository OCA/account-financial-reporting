// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
export class AccountReportController {
    constructor(datas, params = {}) {
        this.datas = datas;
        this.params = params;
    }

    async adapt() {
        return {
            ...this.extraData(),
            header: this.getHeader(),
            columns: this.getColumns(),
            rows: this.getRows(),
            filters: this.getFilters(),
        };
    }

    getHeader() {
        throw new Error("ReportAdapter.getHeader() must be implemented");
    }

    getColumns() {
        throw new Error("ReportAdapter.getColumns() must be implemented");
    }

    getRows() {
        throw new Error("ReportAdapter.getRows() must be implemented");
    }

    getFilters() {
        throw new Error("ReportAdapter.getFilters() must be implemented");
    }

    extraData() {
        return {};
    }
}
