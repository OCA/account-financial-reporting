odoo.define("account_financial_report.report", function(require) {
    "use strict";

    require("web.dom_ready");
    const utils = require("report.utils");

    if (window.self === window.top) {
        return;
    }

    const web_base_url = $("html").attr("web-base-url");
    const trusted_host = utils.get_host_from_url(web_base_url);
    const trusted_protocol = utils.get_protocol_from_url(web_base_url);
    const trusted_origin = utils.build_origin(trusted_protocol, trusted_host);

    /**
     * Convert a model name to a capitalized title style
     * Example: account.mode.line --> Account Move Line
     *
     * @param {String} str
     * @returns {String}
     */
    function toTitleCase(str) {
        return str
            .replaceAll(".", " ")
            .replace(
                /\w\S*/g,
                txt => `${txt.charAt(0).toUpperCase()}${txt.substr(1).toLowerCase()}`
            );
    }

    // Allow sending commands to the webclient
    // `do_action` command with domain
    $("[res-model][domain]")
        .wrap("<a/>")
        .attr("href", "#")
        .on("click", function(ev) {
            ev.preventDefault();
            const res_model = $(this).attr("res-model");
            const action = {
                type: "ir.actions.act_window",
                res_model: res_model,
                domain: $(this).attr("domain"),
                name: toTitleCase(res_model),
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
            };
            window.parent.postMessage(
                {
                    message: "report:do_action",
                    action: action,
                },
                trusted_origin
            );
        });
});
