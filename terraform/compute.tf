resource "azurerm_availability_set" "bastion" {
  name                        = "Bastion-AvailabilitySet"
  resource_group_name         = "${var.resource_group_name}"
  location                    = "${var.location}"
  platform_update_domain_count = 3
  depends_on                  = [ "azurerm_resource_group.development" ]
}


resource "azurerm_availability_set" "masters" {
  name                        = "Masters-AvailabilitySet"
  resource_group_name         = "${var.resource_group_name}"
  location                    = "${var.location}"
  platform_update_domain_count = 3
  managed                     = true
  depends_on                  = [ "azurerm_resource_group.development" ]
}

resource "azurerm_virtual_machine" "bastion" {
  name                        = "VM-Bastion"
  location                    = "${var.location}"
  resource_group_name         = "${var.resource_group_name}"
  network_interface_ids       = [ "${azurerm_network_interface.bastion_nic_1.id}" ]
  vm_size                     = "${lookup(var.vm_sizes, "bastion")}"
  delete_os_disk_on_termination = true
  delete_data_disks_on_termination = true
  tags = {
    environment               = "Development"
  }
  os_profile {
    computer_name             = "bastion-vm"
    admin_username            = "${lookup(var.creds, "bastion_username")}"
    admin_password            = "${lookup(var.creds, "bastion_password")}"
  }
  os_profile_linux_config {
    disable_password_authentication = false
    ssh_keys {
        key_data              = "${file("~/.ssh/id_rsa.pub")}" 
        path                  = "/home/${lookup(var.creds, "bastion_username")}/.ssh/authorized_keys"
    }
  }
  storage_image_reference {
    publisher                 = "${var.image_bastion["publisher"]}"
    offer                     = "${var.image_bastion["offer"]}"
    sku                       = "${var.image_bastion["sku"]}"
    version                   = "${var.image_bastion["version"]}"
  }
  storage_os_disk {
    name                      = "VM-Bastion-OS-Disk"
    caching                   = "ReadWrite"
    create_option             = "FromImage"
    disk_size_gb              = 30
  }
  depends_on                  = [ "azurerm_resource_group.development" ]
}




resource "azurerm_virtual_machine" "master" {
  count                       = 3
  name                        = "VM-Master-${count.index}"
  location                    = "${var.location}"
  resource_group_name         = "${var.resource_group_name}"
  # network_interface_ids       = [ "${azurerm_network_interface.master_nic.id}" ]
  network_interface_ids       = [ "${element(azurerm_network_interface.master_nic.*.id, count.index)}" ]
  vm_size                     = "${lookup(var.vm_sizes, "master")}"
  delete_os_disk_on_termination = true
  delete_data_disks_on_termination = true
  tags = {
    environment               = "Development"
    master                    = "true"
    name                      = "VM-Master-${count.index}"
    hostname                  = "master-${count.index}-vm"
  }
  os_profile {
    computer_name             = "master-${count.index}-vm"
    admin_username            = "${lookup(var.creds, "master_username")}"
    admin_password            = "${lookup(var.creds, "master_password")}"
  }
  os_profile_linux_config {
    disable_password_authentication = false
    ssh_keys {
        key_data              = "${file("~/.ssh/id_rsa.pub")}" 
        path                  = "/home/${lookup(var.creds, "master_username")}/.ssh/authorized_keys"
    }
  }
  storage_image_reference {
    publisher                 = "${var.image_master["publisher"]}"
    offer                     = "${var.image_master["offer"]}"
    sku                       = "${var.image_master["sku"]}"
    version                   = "${var.image_master["version"]}"
  }

  storage_os_disk {
    name                      = "VM-Master-${count.index}-OS-Disk"
    caching                   = "ReadWrite"
    create_option             = "FromImage"
    disk_size_gb              = 30
  }
  depends_on                  = [ "azurerm_resource_group.development", "azurerm_availability_set.masters" ]
  availability_set_id         = "${azurerm_availability_set.masters.id}"
}

