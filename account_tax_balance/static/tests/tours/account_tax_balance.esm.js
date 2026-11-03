import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("account_tax_balance_open_taxes", {
    steps: () => [
        {
            content: "Type a date range of the date_range module",
            trigger: ".o_field_widget[name=date_range_id] input",
            run: "edit Tour range",
        },
        {
            content: "Pick the date range",
            trigger: ".o-autocomplete--dropdown-item:contains(Tour range)",
            run: "click",
        },
        {
            content: "Open the taxes balance",
            trigger: "button[name=open_taxes]",
            run: "click",
        },
        {
            content: "The tax with its balance is listed",
            trigger: ".o_list_view .o_data_row td[name=balance_regular]",
        },
        {
            content: "Open the journal items of the tax",
            trigger: ".o_data_row button[name=view_tax_regular_lines]",
            run: "click",
        },
        {
            content: "The journal items are listed",
            trigger: ".o_list_view .o_data_row",
        },
    ],
});
