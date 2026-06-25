- Add a setting to throw an error when multiple matches are found during
  programmatic imports, instead of falling back to creation of new record.
  (UI-driven imports already block on zero or multiple matches.)
- Support matching on child record fields (one2many subfields) in the import preview.
  Currently, matching only works for direct fields of the imported model.
