/** @odoo-module */
/* eslint-disable no-undef */

import {useComponent, useEffect} from "@odoo/owl";

// Utility function to convert string to title case
function toTitleCase(str) {
    return str
        .replaceAll(".", " ")
        .replace(
            /\w\S*/g,
            (txt) => `${txt.charAt(0).toUpperCase()}${txt.substr(1).toLowerCase()}`
        );
}

// Function to enrich DOM elements with action links
function enrich(component, targetElement, selector, isIFrame = false) {
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
            wrapper.addEventListener("click", (ev) => {
                ev.preventDefault();
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

// Hook to enrich elements with action links
export function useEnrichWithActionLinks(ref, selector = null) {
    const comp = useComponent();
    useEffect(
        (element) => {
            if (element.matches("iframe")) {
                element.addEventListener("load", () =>
                    enrich(comp, element, selector, true)
                );
            } else {
                enrich(comp, element, selector);
            }
        },
        () => [ref.el]
    );
}
