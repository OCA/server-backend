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
        for (const column of this.columns) {
            column.matchOnly = this._isDefaultMatchOnly(column.fieldInfo);
        }
    },

    setColumnField(column, fieldInfo) {
        super.setColumnField(column, fieldInfo);
        const fieldPath = fieldInfo && fieldInfo.fieldPath;
        if (["id", ".id"].includes(fieldPath)) {
            for (const col of this.columns) {
                col.matchOnly = false;
            }
        } else {
            column.matchOnly = this._isDefaultMatchOnly(fieldInfo);
        }
    },

    get hasIdColumn() {
        return this.columns.some(
            (c) => c.fieldInfo && ["id", ".id"].includes(c.fieldInfo.fieldPath)
        );
    },

    _isDefaultMatchOnly(fieldInfo) {
        // Records are identified by ID when an ID column is mapped (the Match
        // column is then hidden), and subfield columns (e.g. one2many lines)
        // cannot be match criteria.
        return (
            !this.hasIdColumn &&
            Boolean(fieldInfo) &&
            !fieldInfo.fieldPath.includes("/") &&
            Boolean(this.matchFieldDefaults[fieldInfo.name])
        );
    },

    get formattedImportOptions() {
        const options = super.formattedImportOptions;
        options.import_match_only_fields = this.columns
            .filter((col) => col.matchOnly && col.fieldInfo)
            .map((col) => col.fieldInfo.fieldPath);
        return options;
    },
});
