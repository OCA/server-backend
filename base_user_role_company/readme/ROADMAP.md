Since Odoo CE has allowed the browsing with several companies in the same session
(st at least since v16.0), this module adds a security vulnerability.
This breach allows a user to escalate its permissions between itsallowed companies,
especially when browsing on different web browser tabs or by API calls.

Steps to reproduce / example from the UI
--------

With UI:
1. Open 1st browser tab on Company A.
2. Open a 2nd browser tab and switch to Company B. Let's say the user's
   permissions are higher in the lattest Company B than the A.
3. Just go back to the 1st tab. You are browsing the Company A with
   permissions given in company B.

Example in `hr_expense`.
Trying to approve one's own expense report:
* In Company A: I am only a Team Validator. I cannot validate my own expense.
* In Company B: I am a an Expense Administrator. I can validate all expenses.
* Therefore, on step 3 (going back to my expense report, created on Company A,
  now browsing with my permissions on Company B): I can validate my own expense,
  while my permissions on Company A do not allow it.

The security risk is quite limited from the UI because:
* it is only active until the user refresh the 1st tab;
* except a few example like this one in `hr_expense`, the usually only displays
  the models and actions adapted to the user permissions

Steps to reproduce with the API
--------

The true breach happens with the API (like RPC calls). The steps can be repeatedin a
`odoo shell` session or by API calls.
Disclaimer: this § and next ones were IA-assisted and human-verified.

- Authenticate with a user allowed on Company A and B. Roles example:
  - *Account/Billing* on Company A
  - *Account/Accountant* on Company B
- Call `get_session_info` with a `cids` cookie on Company B
- Call a method you should not be allowed on Company A, but on a record you are allowed
  to view on Company A.
  - Example:  `account_move.button_draft`, which is not displayed in the UI on Company A
    because *Billing* role does not display it

Root cause
--------

In the depending module `base_user_role`, the method `res_users.set_groups_from_roles()`
updates the `res.groups` of a user according to its roles. Therefore, it
**writes the changes in the database, making them global to all user-browsing tabs**.

With the module `base_user_role_company`, the same method is called from `session_info`,
itself only called from `authenticate` so **when the whole web page is refreshed**.
Therefore, the `res_users.groups_id` written in the database depends on the last
`company_ids` found in web browser cookie `cids` on the last refresh of a browser tab.

Possible fixes (draft / to be discussed)
--------

First ideas of options to be brainstormed:
1. Call again `set_groups_from_roles()` before trying to use this exploit.
   But when? And what impact on performances?
2. Hide and block multi-companies browsing at the same time, in the UI and in the ORM.
   Example: in the UI,hide the checkboxes next to company-choosing widgetin the UI. In the ORM, allow only 1 company in `cids` cookie.
