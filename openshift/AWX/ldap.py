import os
import ldap
from django_auth_ldap.config import LDAPSearch
from django_auth_ldap.config import GroupOfNamesType

ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

base_dn = os.environ.get("LDAP_BASE_DN").strip()
bind_username = os.environ.get("LDAP_BIND_DN")
bind_password = os.environ.get("LDAP_BIND_PASSWORD")
ldap_host = os.environ.get("LDAP_URI") # ldap://example.com[:389]

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


#AUTH_LDAP_ORGANIZATION_MAP = {
#  "Demo Company (LDAP)": {
#    "admins": "cn=toweradmins,cn=groups,{0}".format(base_dn),
#    "users": [
#      "cn=towerusers,cn=groups,{0}".format(base_dn),
#      "cn=towerusers_demo_admins,cn=groups,{0}".format(base_dn),
#      "cn=towerusers_demo_operators,cn=groups,{0}".format(base_dn),
#      "cn=towerusers_demo_users,cn=groups,{0}".format(base_dn)
#    ],
#    "remove_users": True,
#    "remove_admins": True,
#    "users": True
#  }
#}
#
#AUTH_LDAP_TEAM_MAP = {
#  "Administrators": {
#    "organization": "Demo Company (LDAP)",
#    "users": "cn=towerusers_demo_admins,cn=groups,{0}".format(base_dn),
#    "remove": True
#  },
#  "Engineering": {
#    "organization": "Demo Company (LDAP)",
#    "users": "cn=towerusers_demo_operators,cn=groups,{0}".format(base_dn),
#    "remove": True
#  },
#  "Users": {
#    "organization": "Demo Company (LDAP)",
#    "users": "cn=towerusers_demo_users,cn=groups,{0}".format(base_dn),
#    "remove": True
#  }
#}

