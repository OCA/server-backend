This modules adds a new models which contains the security updates a user wants to do. Theses security updates are
then validated through a workflow. If the updates are approved, the changes are done one the users/groups.
The request must be approved twice by different users to be approved. Only users with the manager access can approve
all steps.

Lists of actions:
* add a group to a user
* remove a group from a user
* add a group to a group
* remove a group from a group

This module also makes readonly user groups views, inherited groups of a group, model access and security rules.
