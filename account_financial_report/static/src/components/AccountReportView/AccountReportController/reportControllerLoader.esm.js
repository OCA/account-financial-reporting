// Copyright 2026 Tecnativa - Adasat Torres
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import {accountReportControllerRegistry} from "./registry.esm";

export function getReportController(reportType, datas, params = {}) {
    const Controller = accountReportControllerRegistry.get(reportType);
    if (!Controller) {
        throw new Error(`No controller registered for report type: ${reportType}`);
    }
    return new Controller(datas, params);
}
