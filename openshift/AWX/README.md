# Creating and Using Templates

In this work you need to create a template and run **AWX** application from this. This application is a main stream project for **Red Hat Ansible Tower**. It consists of a few microservices and fits very good for this lab.


## YAML Files

There are given a number of YAML files from which you need to create a template. These files can be run separately and used independently but some of them depends on the other ones.

This directory also contains a final template `awx-template.yaml`. Try to not use this and create your own one.

### List of YAML files

- `configmap.rabbitmq-config.yaml` - configuration files for **RabbitMQ**
- `configmap.awx-config.yaml` - configuration files for **AWX**
- `secret.awx-secrets.yaml` - configuration files and some variables with *secret* data
- `deploymentconfig.postgresql.yaml` - deployment config and a service for a *PostgreSQL* database
- `statefulset.awx-rabbitmq.yaml` - statefulset and a service for *RabbitMQ* messaging bus
- `statefulset.awx-task.yaml` - includes a service account `awx`, a statefulset, and a service for running *AWX-Task* service
- `statefulset.awx-web.yaml` defines a statefulset, a service, and a route for *AWX Web* service
- `statefulset.awx-memcached.yaml` includes a statefulset and a service for *MemCached* service



### Dependencies


The config maps and the secret should be created first because they are used by RabbitMQ, PostgreSQL. Services 
*RabbitMQ*, *MemCached*, and *PostgreSQL* might be created afterwards. 
Then, AWX-Task and AWX-Web. Initialization of AWX-Task takes some time since it populates the database records.


### Special Actions

AWX-Task requires advanced permissions. This is why there is a creating of `awx` service account. 
You need to have cluster-admin privileges to give this account needed permissions. Once you are ready do this:

    oc adm policy add-scc-to-user privileged -z awx -n <project>


## Creating the Objects

Create the needed instances in the mentioned order and make sure everything is running successfully.


## What to Improve

* Passwords, logins, hostnames for RabbitMQ, PostgreSQL, and MemCached mentioned in a few places. Ideally it should be mentioned only one time.
* Scalability have not been tested and it should not work out of box.
* Username and Password for AWX's admin user is hardcoded
* PostgreSQL database does not have a permanent storage
* Limits cannot be adjusted without modifying the resources in the template
* Versions of images are hardcoded in the template

### Ldap Authentication

This work has been checked on FreeIPA.

Put the file `ldap.py` to `/etc/tower/conf.d/ldap.py` into  **AWX-Web** container to enable LDAP authentication. 

This file also requires some environment variables to be provided:

- *LDAP_BASE_DN* - base DN, ex. `cn=accounts,dc=example,dc=com`
- *LDAP_BIND_DN* - bind DN, ex. `uid=tower_bind,cn=users,cn=accounts,dc=example,dc=com`
- *LDAP_BIND_PASSWORD* - bind DN password
- *LDAP_URI* - ldap host, ex. `ldap://example.com`


This file could look like

```python
import os
import ldap
from django_auth_ldap.config import LDAPSearch
from django_auth_ldap.config import GroupOfNamesType

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

base_dn = os.environ.get("LDAP_BASE_DN").strip()
bind_username = os.environ.get("LDAP_BIND_DN")
bind_password = os.environ.get("LDAP_BIND_PASSWORD")
ldap_host = os.environ.get("LDAP_URI")

AUTH_LDAP_BIND_DN = bind_username
AUTH_LDAP_USER_DN_TEMPLATE = "uid=%(user)s,cn=users,{0}".format(base_dn)
AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()
AUTH_LDAP_BIND_PASSWORD = bind_password

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_superuser": [ "cn=toweradmins,cn=groups,{0}".format(base_dn) ],
    "is_system_auditor": [ "cn=towerauditors,cn=groups,{0}".format(base_dn) ]
}

AUTH_LDAP_USER_ATTR_MAP = { "first_name": "givenName", "last_name": "sn", "email": "mail" }
AUTH_LDAP_SERVER_URI = ldap_host
AUTH_LDAP_START_TLS = True

AUTH_LDAP_GROUP_TYPE_PARAMS = {}

AUTH_LDAP_USER_SEARCH = LDAPSearch(
  "cn=users,{0}".format(base_dn), # Base DN
  ldap.SCOPE_SUBTREE,
  "(uid=%(user)s)", # Query
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
  "cn=groups,{0}".format(base_dn), # Base DN
  ldap.SCOPE_SUBTREE, # SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE
  '(&(objectClass=groupOfNames)(|(cn=towerusers)(cn=toweradmins)(cn=towerauditors)))', # Query
)
```
In order to save flexibility further configuring of organizations and teams might be done in the UI. 
Or, if you still need to have those settings hardcoded, the above python script could be extended with this configuration

```python
AUTH_LDAP_ORGANIZATION_MAP = {
  "Demo Company (LDAP)": {
    "admins": "cn=toweradmins,cn=groups,{0}".format(base_dn),
    "users": [
      "cn=towerusers,cn=groups,{0}".format(base_dn),
      "cn=towerusers_demo_admins,cn=groups,{0}".format(base_dn),
      "cn=towerusers_demo_operators,cn=groups,{0}".format(base_dn),
      "cn=towerusers_demo_users,cn=groups,{0}".format(base_dn)
    ],
    "remove_users": True,
    "remove_admins": True,
    "users": True
  }
}

AUTH_LDAP_TEAM_MAP = {
  "Administrators": {
    "organization": "Demo Company (LDAP)",
    "users": "cn=towerusers_demo_admins,cn=groups,{0}".format(base_dn),
    "remove": True
  },
  "Engineering": {
    "organization": "Demo Company (LDAP)",
    "users": "cn=towerusers_demo_operators,cn=groups,{0}".format(base_dn),
    "remove": True
  },
  "Users": {
    "organization": "Demo Company (LDAP)",
    "users": "cn=towerusers_demo_users,cn=groups,{0}".format(base_dn),
    "remove": True
  }
}
```


## Authors

* Dmitrii Mostovshchikov <dmadm2008@gmail.com>


