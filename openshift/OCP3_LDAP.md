# OpenShift 3.x LDAP Integration

Integration Openshift Container Platform 3.x with FreeIPA.

This integration allows FreeIPA users to authenticate in Openshift platform.

## Prerequisites

* Openshift and Freeipa are configured and work.
* FreeIPA settings:
  * domain name `example.com`
  * server address `ldaps://idm.example.com`
  * SSL enabled


## Updating /etc/origin/master/master-config.yaml
Update the file on all masters as shown below and restart __API__ service `master-restart api api`
```yaml
...
oauthConfig:
  ...
  identityProviders:
### Provider specific configuration
  - name: freeipa
    challenge: true
    mappingMethod: claim
    login: true
    provider:
      kind: LDAPPasswordIdentityProvider
      apiVersion: v1
      attributes:
        id: [ 'dn' ]
        email: [ 'mail' ]
        name: [ 'cn' ]
        preferredUsername: [ 'uid' ]
      insecure: false
      ca: /etc/origin/master/freeipa-ca.crt
      bindDN: 'uid=openshift_bind,cn=users,cn=accounts,dc=example,dc=com'
      bindPassword: '***********'
      url: 'ldaps://idm.example.com/cn=users,cn=accounts,dc=example,dc=com?uid'
### end
...
```
Certificate `freeipa-ca.crt` is taken from __FreeIPA__ server.

## LDAP Groups

By default any valid (enabled) account can log in to Openshift. In order to map FreeIPA groups and their members to OpenShift,
some actions need to be taken.

* Create file `sync-ldap.yaml`
```yaml
$ cat sync-ldap.yaml
kind: LDAPSyncConfig
apiVersion: v1
url: 'ldaps://idm.example.com'
bindDN: 'uid=openshift_bind,cn=users,cn=accounts,dc=example,dc=com'
bindPassword: '***********'
insecure: false
ca: freeipa-ca.crt

rfc2307:
  groupsQuery:
    baseDN: 'cn=groups,cn=accounts,dc=example,dc=com'
    scope: sub
    derefAliases: never
    timeout: 0
    filter: '(&(objectClass=posixGroup)(|(cn=openshift_admins)(cn=openshift_users)))'
    pageSize: 0
  groupUIDAttribute: dn
  groupNameAttributes: [ cn ]
  userNameAttributes: [ uid ]
  groupMembershipAttributes: [ member ]
  usersQuery:
    baseDN: "cn=users,cn=accounts,dc=example,dc=com"
    scope: sub
    derefAliases: never
    pageSize: 0
  userUIDAttribute: dn
  userNameAttribute: [ mail ]
  tolerateMemberNotFoundErrors: false
  tolerrateMemberOutOfScopeErrors: false
```
    - *the filter limits synchronization only specific groups __openshift_admins__ and __openshift_users__*
    - *CA certificate freeipa-ca.crt should be taken from FreeIPA server*

* Use this command to run synchronization:
```
$ oc adm groups sync --sync-config=sync-ldap.yaml --confirm
```
This commands creates the groups and adds to these groups its members.

Use the synchronization for any changes in the groups to reflect them on to Openshift.

* Verification

Make sure that the needed groups and users are there (providing that _admin_ is a member of group *openshift_admins* and users *ocp_testuser1* and *ocp_testuser2* are the members of group _openshit_users_ in FreeIPA).
```
$ oc get groups
NAME               USERS
openshift_admins   admin
openshift_users    ocp_testuser1, ocp_testuser2
```
Also check the output of `oc get users` and `oc get identities`.

## Give permissions

Assign the needed roles to the groups

```
$ oc adm policy add-cluster-role-to-group cluster-admin openshift_admins
$ oc adm policy add-cluster-role-to-group basic-user openshift_users
```



