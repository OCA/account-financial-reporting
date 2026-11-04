import {user} from "@web/core/user";

// Utility function to convert string to title case
function toTitleCase(str) {
    return str
        .replaceAll(".", " ")
        .replace(
            /\w\S*/g,
            (txt) => `${txt.charAt(0).toUpperCase()}${txt.slice(1).toLowerCase()}`
        );
}

// Function to enrich DOM elements with action links
export function enrichWithActionLinks(
    component,
    targetElement,
    selector,
    isIFrame = false
) {
    let doc = window.document;
    let contentDocument = targetElement;

    // Handle iframe case
    if (isIFrame) {
        contentDocument = targetElement.contentDocument;
        doc = contentDocument;
    }

    // Collect targets based on selector
    const targets = selector
        ? [...contentDocument.querySelectorAll(selector)]
        : [contentDocument];

    // Add action links to elements with res-model and domain attributes
    for (const currentTarget of targets) {
        const elementsToWrap = currentTarget.querySelectorAll("[res-model][domain]");
        for (const element of elementsToWrap) {
            const wrapper = doc.createElement("a");
            wrapper.setAttribute("href", "#");
            wrapper.addEventListener("click", async (ev) => {
                ev.preventDefault();
                const companyId = Number(element.getAttribute("company-id"));
                const companyIds = user.activeCompanies.map((c) => c.id);
                if (
                    companyId &&
                    !companyIds.includes(companyId) &&
                    user.allowedCompanies.some((c) => c.id === companyId)
                ) {
                    // Records of the report company are only visible when it is active
                    await user.activateCompanies([...companyIds, companyId], {
                        includeChildCompanies: false,
                        reload: false,
                    });
                }
                component.env.services.action.doAction({
                    type: "ir.actions.act_window",
                    res_model: element.getAttribute("res-model"),
                    domain: element.getAttribute("domain"),
                    name: toTitleCase(element.getAttribute("res-model")),
                    views: [
                        [false, "list"],
                        [false, "form"],
                    ],
                });
            });
            element.parentNode.insertBefore(wrapper, element);
            wrapper.appendChild(element);
        }
    }
}
