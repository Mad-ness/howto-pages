resource "azurerm_network_security_group" "backend" {
  name                          = "NSG-Backend"
  location                      = "${var.location}"
  resource_group_name           = "${var.resource_group_name}"
  security_rule {
    name                        = "Allow-SSH"
    priority                    = "1000"
    direction                   = "Inbound"
    access                      = "Allow"
    protocol                    = "Tcp"
    source_port_range           = "*"
    destination_port_range      = 22
    source_address_prefix       = "*"
    destination_address_prefix  = "*"
  }
  security_rule {
    name                        = "Allow-All-Outbound"
    priority                    = "2000"
    direction                   = "Outbound"
    access                      = "Allow"
    protocol                    = "*"
    source_port_range           = "*"
    destination_port_range      = "*"
    source_address_prefix       = "*"
    destination_address_prefix  = "*"
  }
  depends_on            = [ "azurerm_resource_group.development" ]
}

resource "azurerm_virtual_network" "internal" {
  name                  = "DevelopmentNetwork"
  location              = "${var.location}"
  resource_group_name   = "${var.resource_group_name}"
  address_space         = "${var.internal_address_space}"
  depends_on            = [ "azurerm_resource_group.development" ]
}

resource "azurerm_subnet" "backend" {
  name                  = "Subnet-Backend"
  resource_group_name   = "${var.resource_group_name}"
  virtual_network_name  = "${azurerm_virtual_network.internal.name}"
  address_prefix        = "${lookup(var.internal_addresses_prefixes, "cidr1")}"
}

resource "azurerm_network_interface" "bastion_nic_1" {
  name                  = "Nic1-Bastion"
  location              = "${var.location}"
  resource_group_name   = "${var.resource_group_name}"
  network_security_group_id = "${azurerm_network_security_group.backend.id}"

  ip_configuration {
    name                = "private_conf"
    subnet_id           = "${azurerm_subnet.backend.id}"
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id = "${azurerm_public_ip.bastion.id}"
  }
  tags = {
    environment         = "development"
    bastion             = "true"
  }
}


resource "azurerm_public_ip" "bastion" {
  name                  = "Bastion-External-IP"
  location              = "${var.location}"
  resource_group_name   = "${var.resource_group_name}"
  allocation_method     = "Static"
  tags = {
    environment         = "development"
    bastion             = "true"
  }
  depends_on            = [ "azurerm_resource_group.development" ]
}







resource "azurerm_network_interface" "master_nic" {
  count                 = 3
  name                  = "Nic${count.index+1}-Master"
  location              = "${var.location}"
  resource_group_name   = "${var.resource_group_name}"
  network_security_group_id = "${azurerm_network_security_group.backend.id}"
  internal_dns_name_label = "master-${count.index}"

  ip_configuration {
    name                = "private_conf"
    subnet_id           = "${azurerm_subnet.backend.id}"
    private_ip_address_allocation = "Dynamic"
    primary             = true
  }
  tags = {
    environment         = "development"
    master              = "true"
  }
  # depends_on            = [ "azurerm_lb_nat_rule.master" ]
}


## *** IP Addresses ***

resource "azurerm_public_ip" "master" {
  name                  = "Master-${count.index+1}-PublicIP"
  location              = "${var.location}"
  resource_group_name   = "${var.resource_group_name}"
  allocation_method     = "Static"
  domain_name_label     = "${var.cluster_prefix}-master"
  tags = {
    environment         = "development"
    master              = "true"
  }
  depends_on            = [ "azurerm_resource_group.development" ]
  sku                   = "Standard"
}




### Master Load Balancer

resource "azurerm_lb" "master" {
  name                  = "LB-Masters"
  location              = "${var.location}"
  resource_group_name   = "${var.resource_group_name}"
  depends_on            = [ "azurerm_public_ip.master" ]
  sku                   = "Standard"
  frontend_ip_configuration {
    name                = "Frontend-LBIP"
    public_ip_address_id = "${azurerm_public_ip.master.id}"
  }
  tags = {
    environment         = "development"
    balance_on          = "masters"
  }
}


resource "azurerm_lb_backend_address_pool" "master" {
  name                  = "Master-LBBackend-AddressPool" 
  resource_group_name   = "${var.resource_group_name}"
  loadbalancer_id       = "${azurerm_lb.master.id}"
  depends_on            = [ "azurerm_resource_group.development", "azurerm_lb.master" ]
}


resource "azurerm_lb_rule" "master_lb" {
  name                  = "LB-Master-Rule-1"
  resource_group_name   = "${var.resource_group_name}"
  loadbalancer_id       = "${azurerm_lb.master.id}"
  load_distribution     = "SourceIP"
  protocol              = "Tcp"
  frontend_port         = "80"
  backend_port          = "80"
  backend_address_pool_id = "${azurerm_lb_backend_address_pool.master.id}"
  enable_floating_ip    = false
  frontend_ip_configuration_name = "Frontend-LBIP"
  probe_id              = "${azurerm_lb_probe.probe_80_http.id}"
  depends_on            = [ "azurerm_lb.master", "azurerm_lb_probe.probe_80_http", "azurerm_lb_backend_address_pool.master" ]
}

resource "azurerm_lb_probe" "probe_80_http" {
  name                  = "LB-Probe-Port-80-Http"
  resource_group_name   = "${var.resource_group_name}"
  loadbalancer_id       = "${azurerm_lb.master.id}"
  protocol              = "Http"
  request_path          = "/"
  port                  = "80"
  interval_in_seconds   = 5
  number_of_probes      = 2
  depends_on            = [ "azurerm_lb.master" ]
}


resource "azurerm_lb_nat_rule" "master" {
  name                  = "SSH-port-${count.index + 2200}"
  resource_group_name   = "${var.resource_group_name}"
  loadbalancer_id       = "${azurerm_lb.master.id}"
  protocol              = "Tcp"
  frontend_port         = "${count.index + 2200}"
  backend_port          = "22"
  frontend_ip_configuration_name = "Frontend-LBIP"
  count                 = "${azurerm_virtual_machine.master.count}"
  depends_on            = [ "azurerm_lb.master", "azurerm_virtual_machine.master" ]
}


resource "azurerm_network_interface_nat_rule_association" "master-nic1" {
  count                 = "${azurerm_network_interface.master_nic.count}"
  network_interface_id  = "${element(azurerm_network_interface.master_nic.*.id, count.index)}"
  ip_configuration_name = "private_conf"
  nat_rule_id           = "${element(azurerm_lb_nat_rule.master.*.id, count.index)}"
}


### Outputs

#output "bastion_public_ip_address" {
#  value                 = "${data.azurerm_public_ip.bastion.ip_address}"
#}


