variable "resource_group_name" {
  default             = "Development"
}

variable "cluster_prefix" {
  default             = "local"
}

variable "location" {
  default             = "East US"
}

variable "master_vm_size" {
  default             = "Standard_B1ls"
}

variable "internal_address_space" {
  type                = "list"
  default             = [ "10.0.0.0/16" ]
}

variable "internal_addresses_prefixes" {
  type                = "map"
  default = {
    cidr1             = "10.0.1.0/24"
    cidr2             = "10.0.2.0/24" 
  }
}

variable "vm_sizes" {
  type                = "map"
  default = {
    bastion           = "Standard_B1ls"
    master            = "Standard_B1ls"
    infra             = "Standard_B1ls"
    compute           = "Standard_B1ls"
  }
}

variable "image_master" {
  type                = "map"
  default = {
    publisher         = "OpenLogic"
    offer             = "CentOS"
    sku               = "7.6"
    version           = "7.6.20190402"
  }
}

variable "image_bastion" {
  type                = "map"
  default = {
    publisher         = "Canonical"
    offer             = "UbuntuServer"
    sku               = "18.04-LTS"
    version           = "latest"
  }
}

variable "creds" {
  type                = "map"
  default = {
    bastion_username  = "ubuntu"
    bastion_password  = "Password123@"
    master_username   = "ubuntu"
    master_password   = "Password123@"
  }
}

