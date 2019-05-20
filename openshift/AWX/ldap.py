import os
import ldap
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
from django_auth_ldap.config import GroupOfNamesType, GroupOfUniqueNamesType, PosixGroupType
from django_auth_ldap.config import LDAPGroupQuery

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

# Provide these values in environment variables
base_dn = os.environ.get("LDAP_BASE_DN")
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

