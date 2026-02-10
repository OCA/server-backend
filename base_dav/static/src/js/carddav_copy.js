/** @odoo-module **/

function getValueFromContainer(container) {
    if (!container) {
        return "";
    }
    const input = container.querySelector("input, textarea");
    if (input) {
        return input.value || "";
    }
    const link = container.querySelector("a");
    if (link) {
        return (link.textContent || "").trim();
    }
    const span = container.querySelector(".o_field_widget, span");
    if (span) {
        return (span.textContent || "").trim();
    }
    return "";
}

function findFieldElement(scope, fieldName) {
    if (!fieldName) {
        return null;
    }
    return scope.querySelector(
        [
            `[name="${fieldName}"]`,
            `.o_field_widget[name="${fieldName}"]`,
            `.o_field_widget[data-name="${fieldName}"]`,
            `.o_field_widget[data-field="${fieldName}"]`,
            `[data-name="${fieldName}"]`,
            `[data-field="${fieldName}"]`,
        ].join(", ")
    );
}

function copyText(value) {
    if (!value) {
        return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(value).catch(() => {});
        return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
        document.execCommand("copy");
    } catch (err) {
        // Ignore copy errors for older browsers.
    }
    document.body.removeChild(textarea);
}

document.addEventListener("click", (event) => {
    const button = event.target.closest(".o_carddav_copy");
    if (!button) {
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    if (event.stopImmediatePropagation) {
        event.stopImmediatePropagation();
    }
    const fieldName = button.dataset.copyField;
    const scope = button.closest(".o_form_view") || document;
    const field = findFieldElement(scope, fieldName);
    const container = field || button.closest(".o_row") || button.parentElement;
    const value = getValueFromContainer(container);
    copyText(value);
});
