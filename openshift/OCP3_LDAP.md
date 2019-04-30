# OpenShift 3.x LDAP Integration

Integration Openshift Container Platform 3.x with FreeIPA.

This integration allows FreeIPA users to authenticate in Openshift platform.

## Prerequisites

* Openshift and Freeipa are configured and work.
* FreeIPA settings:
  * domain name `example.com`
  * server address `ldaps://idm.example.com`
  * SSL enabled
* An account with the cluster-admin permissions


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

- [x] the filter limits synchronization of only specific groups __openshift_admins__ and __openshift_users__
- [x] CA certificate freeipa-ca.crt should be taken from FreeIPA server

* Use this command to run synchronization:
```
$ oc adm groups sync --sync-config=sync-ldap.yaml --confirm
```
This commands creates the groups and adds to these groups its members in OpenShift.

__Use the synchronization for any changes in the groups to reflect them on Openshift.__

## Verification

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

If you will run  `oc adm groups sync` manually or use any external tools, you may not read further.


## Making synchronization is done by OpenShift itself

Executing the synchronization is done by this command `oc adm groups sync`. I don't know whether it possible to call the same action with API (sure possible). But I found another way how to do it. I will use `CronJob` object and an image with OpenShift client tool. It will call `oc adm groups sync` command by cron.

### Prerequisites

- for OpenShift v3.11 we need an access to the image `docker.io/ebits/openshift-client:v3.11.0`
- create a project for this operation `oc new-project openshift-services` (`oc create ns openshift-service` should work)

### Creating Needed objects

There is a bunch of objects we need to create to do the work:

- kind: ClusterRole
- kind: ServiceAccount
- kind: ClusterRoleBinding
- kind: Secret
- kind: ConfigMap
- kind: CronJob

#### All resources in one file

Save this content in file and do `oc create -f <file>`.

```yaml
---
apiVersion: authorization.openshift.io/v1
kind: ClusterRole
metadata:
  name: sync-ldap-users
rules:
- apiGroups: [ "user.openshift.io" ]
  resources: [ "groups" ]
  verbs: [ "get", "update" ]


---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sync-ldap-users


---
apiVersion: authorization.openshift.io/v1
kind: ClusterRoleBinding
metadata:
  name: sync-ldap-users
roleRef:
  name: sync-ldap-users
subjects:
- kind: ServiceAccount
  name: sync-ldap-users


---
apiVersion: v1
kind: Secret
metadata:
  name: sync-ldap-users
  labels:
    app: sync-ldap-users
type: Opaque
data:
  credentials: |
    ZXhwb3J0IExEQVBfSE9TVD1sZGFwczovL2lkbS5kZW1vLmxpOS5jb20KZXhwb3J0IExEQVBfQklOREROPSJ1aWQ9b3BlbnNoaWZ0X2JpbmQsY249dXNlcnMsY249YWNjb3VudHMsZGM9ZGVtbyxkYz1saTksZGM9Y29tIgpleHBvcnQgTERBUF9CSU5ERE5fUEFTUz0iczU3cHBHdytEWndjZjJSUHJLdz0iCg==
#     export LDAP_HOST=ldaps://idm.demo.li9.com
#     export LDAP_BINDDN="uid=openshift_bind,cn=users,cn=accounts,dc=demo,dc=li9,dc=com"
#     export LDAP_BINDDN_PASS="s57ppGw+DZwcf2RPrKw="
stringData:
  filtering: |
    export LDAP_GROUPS_BASEDN="cn=groups,cn=accounts,dc=demo,dc=li9,dc=com"
    export LDAP_GROUPS_FILTER="(&(objectClass=posixGroup)(|(cn=openshift_admins)(cn=openshift_users)))"
    export LDAP_USERS_BASEDN="cn=users,cn=accounts,dc=demo,dc=li9,dc=com"


---
apiVersion: v1
kind: ConfigMap
metadata:
  name: sync-ldap-users
  labels:
    app: sync-ldap-users
data:
    freeipa-ca.crt: |
      -----BEGIN CERTIFICATE-----
      MIIDjjCCAnagAwIBAgIBATANBgkqhkiG9w0BAQsFADA3MRUwEwYDVQQKDAxERU1P
      LkxJOS5DT00xHjAcBgNVBAMMFUNlcnRpZmljYXRlIEF1dGhvcml0eTAeFw0xOTAx
      MTkwMTI0MDVaFw0zOTAxMTkwMTI0MDVaMDcxFTATBgNVBAoMDERFTU8uTEk5LkNP
      TTEeMBwGA1UEAwwVQ2VydGlmaWNhdGUgQXV0aG9yaXR5MIIBIjANBgkqhkiG9w0B
      AQEFAAOCAQ8AMIIBCgKCAQEA704KobWljBA50B6udKEkCNosLaz2dLsFlQHCKYD3
      N7b6oBCp1ClOEmU1YO5cBVRAq7fuRjxdRUpiTLKHsaH01jp/DSv2YapmfYSTbD4c
      LHa7cgVowHHY2ywv/HwebDaaiv2Fc4MeegWXSN/2Ewag8bHGWB0MHIqGU9UwZ8Xx
      U6zY8Ii7FYOM2P41AhwTr8hX7Bu29dOUIwf7h64DPuV3Uo2R/LMhGyFb3WFkwjnV
      bH5CI2KVPdKYJuTHa5tHAwtexF+sLyHBmIhx48FRMAVod7odBnuZ88NJPweO3Q1O
      Vec17VVhhB/JiQ4O4YlqSlVYjDfpYQ1enZfjT+wS0OMZIwIDAQABo4GkMIGhMB8G
      A1UdIwQYMBaAFLUSvxyD79hgpLg6Brx/+2cKD+XwMA8GA1UdEwEB/wQFMAMBAf8w
      DgYDVR0PAQH/BAQDAgHGMB0GA1UdDgQWBBS1Er8cg+/YYKS4Oga8f/tnCg/l8DA+
      BggrBgEFBQcBAQQyMDAwLgYIKwYBBQUHMAGGImh0dHA6Ly9pcGEtY2EuZGVtby5s
      aTkuY29tL2NhL29jc3AwDQYJKoZIhvcNAQELBQADggEBAK4hJYXVyy5fs5AdZfA7
      lTmhRqGJ0Ve44WVkdwZDzjMhiXSVXw868aGKW4VEGoCSWrekS5ld0x18S1zFLGql
      00z2h4NPlEnXDhN8q9ZHUB+1s5jMjxL90Hvszmvqu4bTu2P30YOMulC74JRRaEfg
      huTjY9d6pnTYtaInoxNitlj6QUBzHxP0CKMSDE0NbLfgbamwtkOxyhFl4BIZGLEu
      JyQ8kemfiTow8FYT6lGVMyALHMRPxCsc7MisgkMK7bpK3HgfiSnu8LILGmaSkcz/
      INfDgmtVLmUzgOYlc+/JtyqFUDgRXRUNb1LYQD6mXKmHJl1dNmSXIMSsFP6nqe+u
      FDM=
      -----END CERTIFICATE-----
    sync-ldap-users.sh: |
      #!/bin/sh

      YAML_CONFIG=/tmp/sync-ldap-users.yaml
      . /config/envvars/credentials
      . /config/envvars/filtering

      cat << YAML > ${YAML_CONFIG}
      kind: LDAPSyncConfig
      apiVersion: v1
      url: '${LDAP_HOST}'
      bindDN: '${LDAP_BINDDN}'
      bindPassword: '${LDAP_BINDDN_PASS}'
      insecure: false
      ca: /config/scripts/freeipa-ca.crt

      rfc2307:
        groupsQuery:
          baseDN: '${LDAP_GROUPS_BASEDN}'
          scope: sub
          derefAliases: never
          timeout: 0
          filter: '${LDAP_GROUPS_FILTER}'
          pageSize: 0
        groupUIDAttribute: dn
        groupNameAttributes: [ cn ]
        userNameAttributes: [ uid ]
        groupMembershipAttributes: [ member ]
        usersQuery:
          baseDN: '${LDAP_USERS_BASEDN}'
          scope: sub
          derefAliases: never
          pageSize: 0
        userUIDAttribute: dn
        userNameAttribute: [ mail ]
        tolerateMemberNotFoundErrors: false
        tolerrateMemberOutOfScopeErrors: false
      YAML

      # Doing the synchronization
      oc login https://kubernetes.default.svc \
        --certificate-authority /run/secrets/kubernetes.io/serviceaccount/ca.crt  \
        --token $(cat /run/secrets/kubernetes.io/serviceaccount/token)
      oc adm groups sync --sync-config=${YAML_CONFIG} --confirm


---
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: sync-ldap-users
  labels:
    app: sync-ldap-users
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: sync-ldap-users
            parent: "cronjob-sync-ldap-users"
        spec:
          restartPolicy: Never
          volumes:
          - name: envvars
            secret:
              secretName: sync-ldap-users
          - name: scripts
            configMap:
              name: sync-ldap-users
          serviceAccountName: sync-ldap-users
          containers:
          - name: sync-ldap-users
            image: "docker.io/ebits/openshift-client:v3.11.0"
            command: [ "/bin/sh" ]
            args:
              - /config/scripts/sync-ldap-users.sh
            volumeMounts:
            - name: envvars
              mountPath: /config/envvars
              readOnly: true
            - name: scripts
              mountPath: /config/scripts
```

### Verification

Run watch to check the cron
```
$ oc get cronjob -w
NAME              SCHEDULE      SUSPEND   ACTIVE    LAST SCHEDULE   AGE
sync-ldap-users   */1 * * * *   False     1         12s             11m
sync-ldap-users   */1 * * * *   False     0         16s       11m
sync-ldap-users   */1 * * * *   False     1         7s        12m
sync-ldap-users   */1 * * * *   False     0         17s       12m
sync-ldap-users   */1 * * * *   False     1         7s        13m
```

In the meantime time add and delete users in FreeIPA to groups `openshift_users` and `openshift_admins` and watch the updates `oc get groups -w`.
