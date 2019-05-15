# Example of Terraform for Azure

This shows an example of using resources and variables for creating virtual machines, networks in **Azure** using **Terraform**.


## Description

The example is doing:

- creates 1 virtual machine named `bastion` and assigns the VM a public IP address
- creates 3 virtual machines master-1, master-2, and  master-3
- creates 1 network
- creates 1 subnet in the network
- creates three network cards in the subnet and attaches to the masters VMs
- creates a security group and allows an inbound connection on `port 22/tcp`
- creates a load balancer, configures it to pass http/80 proto to the master VMs
- also the same LB is configured to pass connections to port 2200, 2201, and 2202 and pass them to master-1, master-2, and master-3 accordingly


## Files

The Terraform configuration split up into few files. There is no a special requirements which names give to files but one, all of them have to be ended on `*.tf`.

- **compute.tf** - defines compute resources to create virtual machines
- **network.tf** - defines network resources to create network things
- **resource-group.tf** - defines a single resource *resource group*
- **variables.tf** - defines variables which are used in the above `*.tf` files

Actually it is enough to describe everything in a single `*.tf` file.


