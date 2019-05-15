resource "azurerm_resource_group" "development" {
  name                  = "${var.resource_group_name}"
  location              = "${var.location}"
}

