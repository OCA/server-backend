This module extends the `base_user_role` module to enforce strict
role-based access control.

It overrides the access rights evaluation to ensure that for model
access rights, Odoo ignores standard user group assignments and
considers only those groups associated with the user's active, enabled
roles.

This ensures a robust separation of concerns where role configurations
supersede implicit or overlapping group permissions.

> **⚠️ Important Installation Note**
> 
> Installing this module will **recursively add all inherited model accesses to the role's associated group access rights**, even for the **existing roles** already present in the system. This means it might grant new access permissions to those existing roles based on their assigned groups' inheritance.
> 
> **Example:**
> If you have an existing role "Sales Manager" that includes the standard group "Sales / Manager", and that standard group inherits from "Sales / User", installing this module will automatically copy all the model access rights from *both* "Sales / Manager" and "Sales / User" directly onto the role's associated group. If the role was previously missing some of these inherited permissions, it will now possess them.
