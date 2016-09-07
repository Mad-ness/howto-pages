# Install of a physical server using Cobbler


## Requirements

- Web access to Cobbler
- Access in to iLO of a physical server (for configuring PXE boot)
- SSH access to Cobbler server


## Configuring PXE boot

When a new server is mounted and should be deployed there are actions to be taken first.

- configured a network device being bootable always as a first device


## Configuring Cobbler

Cobbler is up and running and not required additional configuring. 

Start Cobbler services:

    systemctl enable cobblerd httpd
    systemctl start cobblerd httpd


## Cobbler web interface

Cobbler has a web interface available at standard Apache port (usually 80). Just type in your browser
    
    http://cobbler-server/cobbler_web (use cobbler/cobbler for access)


## Adding a server into Cobbler

There are two ways of how server could be added into Cobbler:

- create a new server profile
- clone an existing server profile

In most cases the second option is more preferrable.

Note: Every server must be added into Cobbler before it can be start used.


## Use cases

There are two common cases are going to be used:

- installation of a new server
- reinstalling of existed server


### Installation of a new server

- configure a server as mentioned in the [Configuring PXE boot](#configuring-pxe-boot) section
- run a new power cycle
- once installing is started, uncheck the netboot option

Last action helps to avoid the reinstalling of a server on next booting.


### Reinstalling of existed server

- mark a server within the netboot option and start a new boot cycle
- once installing is started, uncheck the netboot option


## Known bugs

- Last volume in the disk layout is stretched out up to all free space of a volume group it hosts on.
  So there is a rootvg/dummy file system that can be destroyed at any time
- IP addresses that allocated for servers are not hardcoded so to know an ip address of the installed server is need to check DHCP logs 
  and find out IP address allocated to server's MAC address


## To be acknowleged

- Because of every node of the infrastructure is used almost looking same template but with different disk layout. I guess it is possible to use the same a single template and do just includings of required disk layout depending on a server type. So it is good to find out how to use a single overall template and include templates with disk layouts.

