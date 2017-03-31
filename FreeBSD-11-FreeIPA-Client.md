# FreeBSD 11 as a FreeIPA client configuration

This article describes how to configure FreeBSD 11 as a FreeIPA client. Not all functions were tested so if you need something special you are welcome to investrigate and configure it further.

Some instructions were taken from here https://abbra.fedorapeople.org/.paste/freeipa-freebsd.odt.


## Common plan of actions

- Compilation some packages with building a binary repository
- Connecting a new repository with binary packages
- Installing FreeIPA-client packages
- Adjusting configuration files
- Testing


## Prerequisites

Physical or virtual servers:

- Make sure that a FreeIPA server is already installed and working properly, this guide is not about this.
- One FreeBSD build machine and one more FreeBSD machine which is intended to be a FreeIPA client, actually this might a single machine.


Used software versions:

- FreeIPA server 4.4.3 running on Fedora 25
- A FreeBSD build machine and a FreeBSD FreeIPA client 11.0-RELEASE-p8
- FreeBSD packages: sudo-1.8.19p2, sssd-1.11.7\_8, krb5-1.15.1\_4, openldap-sasl-client-2.4.44, samba-4.4.12

I think this guide will also be suitable for FreeBSD 10 and maybe FreeBSD 9.


FreeIPA details:

- FreeIPA server: fedora25-freeipa.airlan.local
- FreeIPA client: freebsd-pkgtest2.airlan.local
- domain: airlan.local
- realm: AIRLAN.LOCAL
- FreeIPA server configured with no DNS support so DNS server is in other place in airlan.local domain as well as DHCP.


## Building required packages

To conform requirements we need some packages would build with options differing from default ones available in the FreeBSD repositories. Instead of building packages from ports on each FreeBSD client we will make a repository of such packages and build them once so other FreeBSD instances might use them. The package Pourdiere available in ports, it will help us in that, more details are https://www.freebsd.org/doc/handbook/ports-poudriere.html. 

### Set up poudriere environment

First of all install poudriere package the way you prefer and configure it using as an example this article https://www.digitalocean.com/community/tutorials/how-to-set-up-a-poudriere-build-system-to-create-packages-for-your-freebsd-servers or follow further this section.

#### Configuring poudriere

Update portage tree:

    portsnap fetch update


Install poudriere:

    /usr/ports/ports-mgmt/poudriere
    make install clean


Also we need Nginx web server:

    /usr/ports/www/nginx && make install clean


Create an SSL certificate and key

    mkdir -p /usr/local/etc/ssl/{keys,certs}
    chmod 0600 /usr/local/etc/ssl/keys
    openssl genrsa -out /usr/local/etc/ssl/keys/poudriere.key 4096
    openssl rsa -in /usr/local/etc/ssl/keys/poudriere.key -pubout -out /usr/local/etc/ssl/certs/poudriere.cert

Next, open the configuration file and edit it as below, vi /usr/local/etc/poudriere.conf:

    NO_ZFS=no                           # if you use ZFS
    ZPOOL=zroot                         # name of your zfs pool where jails will be placed
    ZROOTFS=/poudriere                  # there will be stored some data
    FREEBSD_HOST=ftp://ftp.freebsd.org  # closest mirror
    POUDRIERE_DATA=${BASEFS}/data
    CHECK_CHANGED_OPTIONS=verbose       # these two options are useful
    CHECK_CHANGED_DEPS=yes              
    PKG_REPO_SIGNING_KEY=/usr/local/etc/ssl/keys/poudriere.key
    URL_BASE=http://<your-repo-hostname> # it points out at the build host

Save and close the file.


#### Create build environment
    
Now we will construct a jail, there packages will be built in. It keeps the base system clean and unaffected.

    poudriere jail -c -j freeipa_11-0x64 -v 11.0-RELEASE

To check it:
    
     jail -l

The output will look like this:

    JAILNAME        VERSION         ARCH  METHOD TIMESTAMP           PATH
    freeipa-11_0x64 11.0-RELEASE-p8 amd64 ftp    2017-03-26 13:51:11 /usr/local/poudriere/jails/freeipa-11_0x64

Configure poudrier to use a port tree. The port tree is deployed inside ZROOTFS and later you can decide to use this port tree for other version of FreeBSD:
    
    poudriere ports -c -p RELEASE     

Check the result:

    poudriere ports -l


#### Create a port building list and setting port options

Fill the file port-list with package names which you need to build customized, in a format category/portname per line. In our case the file looks like below:

    vi /usr/local/etc/poudriere.d/port-list
    security/cyrus-sasl2-gssapi
    security/pam_mkhomedir
    security/sudo-sssd
    security/sssd-smb4
    net/openldap24-sasl-client

Next, we edit make.conf file which plays the same role as /etc/make.conf file but this one will be used by a jail during the build process. Take a note that its name should conform to jail's name (jailname-make.conf):

    vi /usr/local/etc/poudriere.d/freeipa_11-0x64-make.conf

Confire this file as below:

    WANT_OPENLDAP_SASL=	yes     # probably this option is not valid more because of man make.conf doesn't know it
    OPTIONS_UNSET=		DOCS EXAMPLES DEBUG X11
    WITH_GSSAPI=		yes
    OPTIONS_UNSET+=		DBUS GSSAPI_BASE GSSAPI_HEIMDAL
    OPTIONS_SET+=		GSSAPI_MIT
    
Next, create a directory where it stores options for each of packages, its name also should contain a jail's name
    
    mkdir /usr/local/etc/poudriere.d/freeipa_11-0x64-options

And copy initial values from base system:

    cp -r /var/db/ports/* /usr/local/etc/poudriere.d/freeipa_11-0x64-options

Actually last step is not necessary since initial values will be configured later.


### Making ports sudo-sssd and sssd-smb4

Besides standard packages we need to separate the sudo port and a port which is built with sssd support and same thing for sssd package built with SMB support. SMB option is required to add IPA support in sssd. These packages will call sudo-sssd and sssd-smb4, such names are given to avoid conflicts with standard packages assembled without required options. But there is an disadvantage of such approarch - the new ports should be supported by you. 

In the two below subsections are created two additional ports but not needed to create separate ports for other modified packages because they are not installed directly but installed as depedencies. So in further you will have a choice to install standard packages from regular FreeBSD repository or with supporting special options from our repository.


#### Make sudo-sssd port

Duplicate sudo port package to sudo-sssd:

    cd /usr/local/poudriere/ports/RELEASE/security
    cp -a sudo sudo-sssd

and edit sudo-sssd, vi sudo-sssd/Makefile:

    PKGNAMESUFFIX=      -sssd
    COMMENT=            Allow others to run commands as root with activated SSSD and LDAP options
    OPTIONS_DEFAULT=	AUDIT SSSD LDAP
    SSSD_RUN_DEPENDS=	sssd:security/sssd-smb4

Option PKGNAMESUFFIX does not exist initially so add this after PORTNAME or next to it. Here we change port name to sudo-sssd and change a dependence security/sssd to security-sssd-smb4. OPTIONS\_DEFAULT we also set within required values although it could be done previously while executing 'poudriere options' command.


#### Make sssd-smb4 port

As previously, duplicate sssd port sssd-smb4:

    PKGNAMESUFFIX=      -smb4
    OPTIONS_DEFAULT=    SMB
    COMMENT=	System Security Services Daemon with SMB enabled option

Here we also make a new package called sssd-smb4 so it will not conflict with its original port. We need to have samba package enabled because it gives ipa module for sssd, however samba will not be configured at all.

In both cases sudo-sssd and sssd-smb4 you must on youself synchronize the new packages with its masters when the ports tree is refreshed.


### Configure packages options

Run this command, it configure packages like make config in a ports tree.

    poudriere options -j freeipa_11-0x64 -p RELEASE -f /usr/local/etc/poudriere.d/port-list


### Building the ports

It is always good keep the jail up-to-dated so run this to do it:

    poudriere jail -u -j freebsd_11-0x64

If you need to update the ports tree first, it could be done so way:

    poudriere ports -u -p RELEASE 

And run this command to start building the packages for our custom repository:

    poudriere bulk -j freebsd_11-0x64 -p RELEASE -f /usr/local/etc/poudriere.d/port-list

the command downloads, compiles source files and packs them into binary packages like FreeBSD maintainers do. Pressing Ctlr+T gives details about current status.


### Setting up Nginx

We need Nginx to provide access to our custom repository and as a plus Poudriere has a web interface for watching the current buildings.


Enable Nginx:
    
    echo 'nginx_enable="YES"' >> /etc/rc.conf


Edit Nginx's configuration file like so:

    vi /usr/local/etc/nginx/nginx.conf
    ...
    server {
        listen 80 default;
        server_name BuildServer_Hostname_or_IP;
        root /usr/local/share/poudriere/html;

        location /data {
            alias /usr/local/poudriere/data/logs/bulk;
            autoindex on;
        }
        location /packages {
            root /usr/local/poudriere/data;
            autoindex on;
        }
    }
    ...

And edit this file, vi /usr/local/etc/nginx/mime.types:

    text/mathml                         mml;
    text/plain                          txt log;  # Update this line
    text/vnd.sun.j2me.app-descriptor    jad;

And start it:

    service nginx configtest && service nginx start


So check how it is working: open in a webrowser:

- http://BuildServer\_Hostname\_or\_IP/data - web interface to Poudriere
- http://BuildServer\_Hostname\_or\_IP/packages - this points the built packages


## Connecting a new repository with binary packages

Since now go to the FreeBSD FreeIPA-client server and configure it to start using the custom repository


### Adding a repository to be it known the system

    mkdir -p /usr/local/etc/pkg/repos
    vi /usr/local/etc/pkg/repos/poudriere.conf

    poudriere: {
        url: "pkg+http://BuildServer\_Hostname\_or\_IP/packages/freeipa_11-0x64-RELEASE",
        mirror_type: "srv",
        signature_type: "pubkey",
        pubkey: "/usr/local/etc/ssl/certs/poudriere.cert",
        enabled: yes,
        priority: 100
    }

We give it priority 100. Having two or more repositories, the selected packages will be installed from a repository with highest priority. In our case such packages are samba4, krb5, bind99 and other.

But if it is needed you can disable FreeBSD repository:

    vi /usr/local/etc/pkg/repos/freebsd.conf
    FreeBSD: {
        enabled: no
    }   

Now inform the system to recognize the new connected repository:

    pkg update


## Installing FreeIPA-client packages

If all above have done well, now we can start working with FreeIPA related things.


### Install packages

    pkg install sssd-smb4 sudo-sssd cyrus-sasl2-client


### Configure OpenLDAP client

    vi /usr/local/etc/openldap/ldap.conf
    BASE		    dc=airlan,dc=local
    URI		        ldap://fedora25-freeipa.airlan.local
    SSL		        start_tls
    SASL_NOCANON 	on
    TLS_CACERT 	    /usr/local/etc/sssd/ip.cacert
    TLS_CACERTDIR	/usr/local/etc/sssd

Certificate /usr/local/etc/sssd/ip.cacert should be copied from IPA server, usually it installed as /root/cacert.p12.

Run openldap -x, to check the correctness of settings.


### Configure DNS

If you did not select "configure DNS" as I did then add following DNS records in airlan.local zone:

    $ORIGIN airlan.local.
    fedora25-freeipa	A	192.168.168.211
    _kerberos		    TXT	"AIRLAN.LOCAL"
    $ORIGIN _tcp.airlan.local.
    _kerberos		    SRV	0 100 88 fedora25-freeipa.airlan.local.
    _kerberos-adm		SRV	0 100 88 fedora25-freeipa.airlan.local.
    _kerberos-master	SRV	0 100 88 fedora25-freeipa.airlan.local.
    _kpasswd		    SRV	0 100 464 fedora25-freeipa.airlan.local.
    _ldap			    SRV	0 100 389 fedora25-freeipa.airlan.local.
    $ORIGIN _udp.airlan.local.
    _kerberos		    SRV	0 100 88 fedora25-freeipa.airlan.local.
    _kerberos-adm		SRV	0 100 88 fedora25-freeipa.airlan.local.
    _kerberos-master	SRV	0 100 88 fedora25-freeipa.airlan.local.
    _kpasswd		    SRV	0 100 464 fedora25-freeipa.airlan.local.
    _ntp			    SRV	0 100 123 fedora25-freeipa.airlan.local.

Actually you should be informed about this after completing deploying FreeIPA server.


### Configure Kerberos client

    vi /etc/krb5.conf
    [libdefaults]
     default_realm = AIRLAN.LOCAL
    
    [realms]
     AIRLAN.LOCAL = {
      kdc = fedora25-freeipa.airlan.local
      admin_server = fedora25-freeipa.airlan.local
     }
    
    [domain_realm]
     .airlan.local = AIRLAN.LOCAL
     airlan.local = AIRLAN.LOCAL

Run "kinit admin" and provide admin's password. If a ticket is received then it's fine.


### Configure SSSd

    vi /usr/local/etc/sssd/sssd.conf 
    [domain/airlan.local]
     cache_credential = True
     krb5_store_password_if_offline = True
     ipa_domain = airlan.local
     id_provider = ipa
     auth_provider = ipa
     access_provider = ipa
     ipa_hostname = freebsd-pkgtest2.airlan.local
     chpass_provider = ipa
     ipa_server = _srv_, fedora25-freeipa.airlan.local
     ldap_tls_cacert = /usr/local/etc/sssd/ip.cacert
     entry_cache_timeout = 5
     enumerate = True
    
    [sssd]
     config_file_version = 2
     services = nss, pam, sudo
     domains = airlan.local
    
    [nss]
     override_homedir = /usr/home/%u   # by default there is not /home directory on FreeBSD     
     override_shell = /bin/csh
    
    [pam]
    
    [sudo]

and make it secure and enable:

    chmod 0600 /usr/local/etc/sssd/sssd.conf
    echo 'sssd_enable="YES"' >> /etc/rc.conf


More details see man sssd-ipa.


### Configure /etc/nsiswitch.conf and pam files

Set options as specified

    group: files sss
    passwd: files sss
    sudoers: sss files


File /etc/pam.d/system. Pay attention that only /usr/local/lib/pam\_sss.so, pam\_krb5.so and pam\_mkhomedir.so were added.

    #
    # $FreeBSD: releng/11.0/etc/pam.d/system 197769 2009-10-05 09:28:54Z des $
    #
    # System-wide defaults
    #
    
    # auth
    auth		sufficient	pam_opie.so		no_warn no_fake_prompts
    auth		requisite	pam_opieaccess.so	no_warn allow_local
    auth		sufficient	pam_krb5.so 		no_warn try_first_pass
    #auth		sufficient	pam_ssh.so		no_warn try_first_pass
    auth		sufficient	/usr/local/lib/pam_sss.so debug use_first_pass
    auth		required	pam_unix.so		no_warn try_first_pass nullok
    
    # account
    #account	required	pam_krb5.so
    account		required	pam_login_access.so
    account		required	pam_unix.so
    account 	required 	/usr/local/lib/pam_sss.so ignore_unknown_user ignore_authinfo_unavail
    
    # session
    #session	optional	pam_ssh.so		want_agent
    session		required	pam_lastlog.so		no_fail
    session		required	/usr/local/lib/pam_mkhomedir.so
    
    # password
    #password	sufficient	pam_krb5.so		no_warn try_first_pass
    password	sufficient	/usr/local/lib/pam_sss.so use_authtok
    password	required	pam_unix.so		no_warn try_first_pass
    

and similar updates in /etc/pam.d/sshd file

    #
    # $FreeBSD: releng/11.0/etc/pam.d/sshd 197769 2009-10-05 09:28:54Z des $
    #
    # PAM configuration for the "sshd" service
    #
    
    # auth
    auth		sufficient	pam_opie.so		no_warn no_fake_prompts
    auth		requisite	pam_opieaccess.so	no_warn allow_local
    auth		sufficient	pam_krb5.so		no_warn	try_first_pass
    #auth		sufficient	pam_ssh.so		no_warn try_first_pass
    auth		sufficient	/usr/local/lib/pam_sss.so use_first_pass
    auth		required	pam_unix.so		no_warn try_first_pass
    
    # account
    account		required	pam_nologin.so
    #account	required	pam_krb5.so
    account		required	pam_login_access.so
    account		required	pam_unix.so
    account		required	/usr/local/lib/pam_sss.so ignore_unknown_user ignore_authinfo_unavail
    
    # session
    #session	optional	pam_ssh.so		want_agent
    session		required	pam_permit.so
    session		required	/usr/local/lib/pam_mkhomedir.so
    
    # password
    #password	sufficient	pam_krb5.so		no_warn try_first_pass
    password	sufficient	/usr/local/lib/pam_sss.so use_authtok
    password	required	pam_unix.so		no_warn try_first_pass


### Configure SSH service

Uncomment and enable "GSSAPIAuthentication yes" option and restart sshd service.


### Configure FreeIPA

Now switch to FreeIPA server and add the client host:

    kinit admin 

and provide admin's password on a prompt

    ipa host-add freebsd-pkgtest2.airlan.local

copy file /etc/krb5.keytab to freebsd-pkgtest2.airlan.local:/etc/krb5.keytab and check:

    ldapsearch -Y GSSAPI

output should be printed.

Now you can start sssd service, create some accounts in FreeIPA and try to login to FreeBSD client.


## Important notes

- Just created users who must reset their passwords at first login are not prompted to do it on FreeBSD clients
- Sudo rules weren't tested intensively
- Other a lot of things weren't alsot tested

