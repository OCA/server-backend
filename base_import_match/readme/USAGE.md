To use this module, you need to:

1.  Go to any list or kanban view.
2.  Go to *Action \> Import records* and upload your file.
3.  In the import preview, check **Match** on the fields you want to use as matching
    keys (e.g. name, email, VAT). These fields will be used to find existing records
    but will not be written.
4.  Proceed with the import as usual. If any row cannot be matched to exactly one
    existing record, the import will be blocked and error messages will indicate
    which rows had zero or multiple matches.

If Import Match rules are configured for the model, their fields will be pre-checked
automatically.
