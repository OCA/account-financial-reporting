import {registry} from "@web/core/registry";

const pickDateRange = () => [
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
];

const tickCheckbox = (name) => ({
    content: `Tick ${name}`,
    trigger: `.o_field_widget[name=${name}] input`,
    run: "click",
});

const openReport = () => [
    {
        content: "Open the HTML report from the wizard",
        trigger: "button[name=button_export_html]",
        run: "click",
    },
    {
        content: "The report table is rendered in the iframe",
        trigger: ":iframe .act_as_table",
    },
];

const checkLinksAndExport = () => [
    {
        content: "Core links the rows to their form",
        trigger: ":iframe a > [res-id][res-model][view-type]",
    },
    {
        content: "The module links the amounts to the journal items",
        trigger: ":iframe a > [res-model][domain]",
    },
    {
        content: "Export button added by the module",
        trigger: ".o_action button:contains(Export)",
        run: "click",
    },
    {
        content: "No error dialog after the export",
        trigger: "body:not(:has(.o_error_dialog))",
    },
];

const openJournalItems = () => [
    {
        content: "Open the journal items behind an amount",
        trigger: ":iframe a > [res-model][domain]",
        run: "click",
    },
    {
        content: "Journal items list is open",
        trigger: ".o_list_view",
    },
];

const addTour = (name, steps) =>
    registry
        .category("web_tour.tours")
        .add(`account_financial_report_${name}`, {steps: () => steps});

addTour("trial_balance_html", [
    ...pickDateRange(),
    tickCheckbox("show_hierarchy"),
    ...openReport(),
    ...checkLinksAndExport(),
    ...openJournalItems(),
]);

addTour("trial_balance_analytic_html", [
    ...pickDateRange(),
    {
        content: "Open the grouping choices",
        trigger: ".o_field_widget[name=grouped_by] input.o_select_menu_toggler",
        run: "click",
    },
    {
        content: "Group the trial balance by analytic account",
        trigger: ".o_select_menu_item:contains(Analytic Account)",
        run: "click",
    },
    ...openReport(),
    {
        content: "The analytic account is a section of the report",
        trigger: ":iframe span:contains(Tour analytic)",
    },
    {
        content: "Export button added by the module",
        trigger: ".o_action button:contains(Export)",
        run: "click",
    },
    {
        content: "No error dialog after the export",
        trigger: "body:not(:has(.o_error_dialog))",
    },
]);

addTour("general_ledger_html", [
    ...openReport(),
    ...checkLinksAndExport(),
    ...openJournalItems(),
]);

addTour("journal_ledger_html", [
    ...pickDateRange(),
    ...openReport(),
    {
        content: "Export button added by the module",
        trigger: ".o_action button:contains(Export)",
        run: "click",
    },
    {
        content: "No error dialog after the export",
        trigger: "body:not(:has(.o_error_dialog))",
    },
]);

addTour("open_items_html", [
    tickCheckbox("receivable_accounts_only"),
    ...openReport(),
    {
        content: "Core links the rows to their form",
        trigger: ":iframe a > [res-id][res-model][view-type]",
    },
    {
        content: "Open the form behind a row",
        trigger: ":iframe a > [res-id][res-model][view-type]",
        run: "click",
    },
    {
        content: "The form opens",
        trigger: ".o_form_view",
    },
]);

addTour("aged_partner_balance_html", [
    tickCheckbox("receivable_accounts_only"),
    tickCheckbox("show_move_line_details"),
    ...openReport(),
    ...checkLinksAndExport(),
    ...openJournalItems(),
]);

addTour("vat_report_html", [
    ...pickDateRange(),
    tickCheckbox("tax_detail"),
    ...openReport(),
    {
        content: "Export button added by the module",
        trigger: ".o_action button:contains(Export)",
        run: "click",
    },
    {
        content: "No error dialog after the export",
        trigger: "body:not(:has(.o_error_dialog))",
    },
]);

addTour("vat_report_taxgroups_html", [
    ...pickDateRange(),
    {
        content: "Base the report on the tax groups",
        trigger: ".o_field_widget[name=based_on] input[data-value=taxgroups]",
        run: "click",
    },
    tickCheckbox("tax_detail"),
    ...openReport(),
    {
        content: "The module links the tax amounts to the journal items",
        trigger: ":iframe a > [res-model='account.move.line'][domain]",
    },
    ...openJournalItems(),
]);

addTour("age_report_configuration", [
    {
        content: "The aged partner configuration list opens",
        trigger: ".o_list_view",
    },
    {
        content: "Create a configuration",
        trigger:
            ".o_list_button_add, .o_control_panel_main_buttons button:contains(New)",
        run: "click",
    },
    {
        content: "The configuration form opens",
        trigger: ".o_form_view",
    },
]);
