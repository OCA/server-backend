// Copyright 2026 Quartile (https://www.quartile.co)
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {ImportDataContent} from "@base_import/import_data_content/import_data_content";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(ImportDataContent.prototype, {
    onMatchOnlyChanged: (column, ev) => (column.matchOnly = ev.target.checked),
    get matchColumnTooltip() {
        return _t(
            "Use this field to find existing records without updating its value."
        );
    },
    get hasIdColumn() {
        return this.props.columns.some(
            (c) => c.fieldInfo && ["id", ".id"].includes(c.fieldInfo.fieldPath)
        );
    },
});
