// Copyright 2026 Quartile (https://www.quartile.co)
// License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import {BaseImportModel} from "@base_import/import_model";
import {patch} from "@web/core/utils/patch";

patch(BaseImportModel.prototype, {
    _onLoadSuccess(res) {
        this.matchFieldDefaults = {};
        for (const name of res.match_fields || []) {
            this.matchFieldDefaults[name] = true;
        }
        super._onLoadSuccess(res);
        const hasId = this.columns.some(
            (c) => c.fieldInfo && ["id", ".id"].includes(c.fieldInfo.fieldPath)
        );
        for (const column of this.columns) {
            const fieldName = column.fieldInfo && column.fieldInfo.name;
            column.matchOnly = hasId
                ? false
                : Boolean(this.matchFieldDefaults[fieldName]);
        }
    },

    setColumnField(column, fieldInfo) {
        super.setColumnField(column, fieldInfo);
        const fieldPath = fieldInfo && fieldInfo.fieldPath;
        if (["id", ".id"].includes(fieldPath)) {
            for (const col of this.columns) {
                col.matchOnly = false;
            }
        } else if (fieldPath && fieldPath.includes("/")) {
            column.matchOnly = false;
        } else {
            column.matchOnly = Boolean(
                this.matchFieldDefaults[fieldInfo && fieldInfo.name]
            );
        }
    },

    get formattedImportOptions() {
        const options = super.formattedImportOptions;
        options.import_match_only_fields = this.columns
            .filter((col) => col.matchOnly && col.fieldInfo)
            .map((col) => col.fieldInfo.fieldPath);
        return options;
    },
});
