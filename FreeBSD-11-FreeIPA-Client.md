# FreeBSD 11 as a FreeIPA client configuration

This article describes how to configure FreeBSD 11 as a FreeIPA client. Not all functions were tested so if you need something special you are welcome to investrigate and configure it further.

Some instructions were taken from here https://abbra.fedorapeople.org/.paste/freeipa-freebsd.odt.


## Common plan of actions

- Compilation some packages with building a binary repository
- Installation packages
- Adjusting configuration files
- Testing


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

Actually last step is not necessary since initial values will be filled when lanch next command:

    poudriere options -j freeipa_11-0x64 -p RELEASE -f /usr/local/etc/poudriere.d/port-list    

configure the packages with the options as below:

    bind99: DLZ_LDAP, GSSAPI_MIT
    opeldap-sasl-client: FETCH, GSSAPI
    krb5: DNS_FOR_REALM, LDAP
    sssd: SMB
    sudo: SSSD

for other packages either leave the option values as is or set them respectively as above.


### Making ports sudo-sssd and sssd-smb4

Besides standard packages we need to separate the sudo port and a port which is built with sssd support and same thing for sssd package built with SMB support. SMB option is required to add IPA support in sssd. These packages will call sudo-sssd and sssd-smb4, such names are given to avoid conflicts with standard packages assembled without required options. But there is an disadvantage of such approarch - the new ports should be supported by you. 


## Make sudo-sssd port

Duplicate sudo port package to sudo-sssd:

    cd /usr/local/poudriere/ports/RELEASE/security
    cp -a sudo sudo-sssd

and edit sudo-sssd, vi sudo-sssd/Makefile:

    PKGNAMESUFFIX=      -sssd
    COMMENT=            Allow others to run commands as root with activated SSSD and LDAP options
    OPTIONS_DEFAULT=	AUDIT SSSD LDAP
    SSSD_RUN_DEPENDS=	sssd:security/sssd-smb4

Option PKGNAMESUFFIX does not exist initially so add this after PORTNAME or next to it. Here we change port name to sudo-sssd and change a dependence security/sssd to security-sssd-smb4. OPTIONS\_DEFAULT we also set within required values although it could be done previously while executing 'poudriere options' command.


## Make sssd-smb4 port

As previously, duplicate sssd port sssd-smb4:

    PKGNAMESUFFIX=      -smb4
    OPTIONS_DEFAULT=    SMB
    COMMENT=	System Security Services Daemon with SMB enabled option

Here we also make a new package name sssd-smb4 so it will not conflict with original port and add an option as default SMB.

In both cases sudo-sssd and sssd-smb4 you must youself sync new packages with its masters when the ports tree is updated.



