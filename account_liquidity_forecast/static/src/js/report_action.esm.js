import {ReportAction} from "@web/webclient/actions/reports/report_action";
import {enrichWithActionLinks} from "./report.esm";
import {patch} from "@web/core/utils/patch";

const MODULE_NAME = "account_liquidity_forecast";

patch(ReportAction.prototype, {
    setup() {
        super.setup(...arguments);
        this.isLiquidityForecastReport = this.props.report_name.startsWith(
            `${MODULE_NAME}.`
        );
    },

    /**
     * Add the drill-down links of the report lines once the iframe is loaded.
     *
     * @param {Event & { currentTarget: HTMLIFrameElement }} ev
     */
    onIframeLoaded(ev) {
        super.onIframeLoaded(ev);
        if (this.isLiquidityForecastReport) {
            enrichWithActionLinks(this, ev.currentTarget, null, true);
        }
    },
});
