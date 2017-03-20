# Unattended PXE Installation of FreeBSD 11
The guide describes what and how to configure in order to get the FreeBSD 11 OS installed over PXE. This should also work on FreeBSD 10 and 9.


## Prerequisites

- ISC DHCP server
- in.tftp software - simple file transfer protocol service
- any Unix/Linux server with configured NFS server
- downloaded ISO image FreeBSD-11.0-RELEASE-amd64-disc1.iso (~700Mb)
- a physical or virtual machine (my case) for testing
- some patience


## Software settings

### ISC DHCP service

Since I already have syslinux/PXE configured in my environment then only minimal changes were made. For full config options check in the file pxe-dhcpd.conf. Special settings mentioned below.

We need to pass to each FreeBSD client option root-path. It also could be globally defined if it doesn't conflict with requirements for other systems running over PXE:

    host freebsd-pxetest {
        hardware ethernet 52:54:00:b9:f0:48;
        filename "images/freebsd/fbsd11rel/boot/pxeboot";
        option root-path "192.168.168.105:/tftp/tftpboot/images/freebsd/fbsd11rel/";
    }

Put in the hardware ethernet parameter the MAC address of the virtual machine is used for tests.

In my case I had some problems with duplicating ip addresses so the FreeBSD loader could not recognize a single boot as complete session and it did a lot of DHCP queries, next global option has fixed the trouble:

    ignore-client-uids on;

I don't know this is an error either of the FreeBSD loader, or a virtual machine (run on top of KVM on a linux) used for tests, or an OpenVSwitch bridge worked between the physical linux host and the virtual machine. The proble was recognized when FreeBSD loader tried to mount an NFS share during booting and stopped there with loading the VM's cpu up to 100%.

See remain settings in the pxe-dhcpd.conf file but in general there is no FreeBSD specifics.


### TFTP - in.tftpd service

This service is run by xinet service when an incoming packet identified at a specific port. But it doesn't matter how it is run. The config is as following:

    service tftp
    {
    	disable         = no
    	socket_type     = dgram
    	protocol        = udp
    	wait            = yes
    	user            = root
    	server          = /usr/sbin/in.tftpd
    	server_args     = -vv -R 4096:32767 -s /tftp/tftpboot
    }


### Syslinux configuration

There is no special configuration made for syslinux because syslinux is not used at all. Just keep the same directory structure as described in the dhcpd.conf file:

    /tftp/
         tftpboot/
             images/
                 freebsd/
                    fbsd11rel/
                        ... files unpacked out of ISO ...

### Setup files and NFS service

- Mount the ISO FreeBSD-11.0-RELEASE-amd64-disc1.iso and copy its content into /tftp/tftpboot/images/freebsd/fbsd11rel/ directory.
- Share directory /tftp/tftpboot/ or /tftp/tftpboot/images/freebsd/fbsd11rel/ path over NFS and make sure the virtual machine will have necessary permissions to mount it in the read-only mode.


## PXE booting process

Now just configure the virtual machine to boot from PXE. It should request IP address from DHCP service and receive parameters for loading such as pxeboot loader and root-path which to be shared by NFS protocol.

If everything did right the virtual machine should start booting from PXE and run bsdinstall program and it is possible to install FreeBSD manually. That's not our way, we need the automation. Go ahead.


## Automated (unattended) installation

The interesting file the investigation should be started from is /etc/rc.local (/tftp/tftpboot/images/freebsd/fbsd11rel/etc/rc.local), it contains some checks and instructions. It checks whether the file /etc/installerconfig presented. If yes, it runs bsdinstall program and launch the installation procedure. Besides it this file contains instructions and settings for the bsdinstall program.
At the beginning there are defined some variables used by bsdinstall and after #!/bin/sh line follows the script which will be executed after the install process completes. The file was taken here https://github.com/joyent/mi-freebsd-10/blob/master/installerconfig and slightly modified.

Full listing of (tftroot)/../etc/installerconfig file:
    
    #PARTITIONS=vtbd0       # uncomment this and comment in zfs related exports to switch on UFS file system
    export ZFSBOOT_DISKS=vtbd0
    #export ZFSBOOT_DATASETS=" # default filesets will be applied, see the link below.
    #    /ROOT                mountpoint=none
    #    /ROOT/default        mountpoint=/
    #
    #    /tmp                 mountpoint=/tmp,exec=on,setuid=off
    #    /usr                 mountpoint=/usr,canmount=off
    #    /var                 mountpoint=/var,canmount=off
    #"
    export nonInteractive="YES"
    DISTRIBUTIONS="kernel.txz base.txz"
    
    #!/bin/sh
    
    set -o xtrace
    echo "==> Running installerconfig"
    
    # Enable serial and internal consoles
    echo "==> Enabling serial and internal consoles"
    # echo "-Dh" > /boot.config
    echo "cuau0   \"/usr/libexec/getty std.38400\"  xterm   on  secure" >> /etc/ttys
    
    echo "==> Setting autoboot delay to 5 seconds. Default is 10"
    echo "autoboot_delay=\"5\"" >> /boot/loader.conf
    
    echo "==> Setting up rc.conf"
    cat > /etc/rc.conf << RC_CONF
    fsck_y_enable="YES"
    dumpdev="AUTO"
    
    # Enable SmartDataCenter support. Do not remove.
    smartdc_enable="YES"
    ifconfig_vtnet0="DHCP"  # vtnet0 is the network card name
    zfs_enable="YES"
    sshd_enable="YES"
    ntpd_enable="YES"
    ntpd_sync_on_start="YES"
    
    RC_CONF
    
    # Set Time Zone to UTC
    echo "==> Setting Time Zone to UTC"
    /bin/cp /usr/share/zoneinfo/UTC /etc/localtime
    /usr/bin/touch /etc/wall_cmos_clock
    /sbin/adjkerntz -a
    
    # Fetch and install binary updates. Ensures we have the latest security fixes.
    echo "==> Running freebsd-update fetch and freebsd-update install"
    # Remove src from update since it's not installed
    # See https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=198030
    sed -i.bak -e s/Components\ src\ world\ kernel/Components\ world\ kernel/g /etc/freebsd-update.conf
    
    # env PAGER=cat freebsd-update fetch
    ### freebsd-update install ### I don't it now
    
    echo "==> Installing packages"
    # env ASSUME_ALWAYS_YES=YES pkg update -f
    # env ASSUME_ALWAYS_YES=YES pkg install -y bash curl node npm vim wget
    
    echo "== Enable root login via ssh"
    sed -i.bak -e s/#PermitRootLogin\ no/PermitRootLogin\ without-password/g /etc/ssh/sshd_config
    
    ## Build date used for motd and product file
    BUILDDATE=$(date +%Y%m%d)
    RELEASE="11.0-RELEASE"
    DOC_URL="https://docs.joyent.com/images/freebsd"
    
    
    echo "Cleaning up"
    # rm -rf /tmp/installscript
    cp /tmp/installscript /var/log/installscript
    
    echo "End of installerconfig"
    
    # Shutdown/Poweroff
    # poweroff
    reboot

Other bsdinstall variables and much more might be found here https://github.com/freebsd/freebsd/blob/master/usr.sbin/bsdinstall/scripts/zfsboot.

So in order to make unattended installation of FreeBSD just place this file on the NFS directory where ISO content is copied and start VM booting from PXE.

## Profit
    
That's all.

## Issues

There is a requirement is to be known the name of root device. So, it is possible to put some shell code for the disks detection in /etc/rc.local which will tell the right device name and same thing to be done for the interface name.

## Integrating FreeBSD installation into Syslinux boot menu

If it is required to run FreeBSD installation via syslinux, then add the next menu item for that:

    LABEL freebsd-11-release-amd64
        MENU LABEL FreeBSD 11 RELEASE amd64
        pxe images/freebsd/fbsd11rel/boot/pxeboot

As we remember the root directory is /tftp/tftpboot and the pxe parameter points out at the FreeBSD loader. But some inconvinience is still kept - the option root-path should be passed over DHCP so far.
Note: I couldn't get correctly working configuration in that case, the FreeBSD kernel stopped booting. Hope this is because of the virtual machine wasn't working best way.


