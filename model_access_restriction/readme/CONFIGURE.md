To configure this module, you need to:

- Go to Settings / Technical / Security / Model Access Restrictions
- Create a new access restriction
- Select the model to restrict the access
- Select the operations the rule applies to. If the operation is not selected the restriction won't apply to that operation which means users will access the model as always.
- Select the groups that will have access to the model. The rest of groups will have the access disabled.


**Interaction between access records**

Normal access records give permissions. Access restriction records remove permissions. If a user does not have one group of a restriction, the access will be forbidden.

Detailed algorithm:

1. Normal access records are combined together with a logical OR operator. If a user has the group of an access record, access will be granted.
2. Access restriction records are applied before normal access, and combined together with a logical AND operator. If a restriction is not met, the access is forbidden.
3. A restriction is not met if the user does not belong to any of the allowed groups.

Example:
`ACCESS_1 OR ACCESS_2 AND (ACCESS_RESTRICTION_1 AND ACCESS_RESTRICTION_2)`

- ACCESS_1: Group: Internal Users  
- ACCESS_2 Group: Administrator  
- ****: Allowed Groups: Internal Users  
- ACCESS_RESTRICTION_2 Allowed Groups: Administrator  

An internal user won't have access in this example because they do not meet the requirement of ACCESS_RESTRICTION_2.  
`TRUE OR FALSE AND (TRUE AND FALSE) = TRUE AND (FALSE) = FALSE`
