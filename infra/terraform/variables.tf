variable "resource_group_name" {
  description = "Назва resource group в Azure"
  type        = string
  default     = "housing-analytics-rg"
}

variable "location" {
  description = "Регіон Azure"
  type        = string
  default     = "West Europe"
}

variable "admin_username" {
  description = "Ім'я адміністратора VM"
  type        = string
  default     = "azureuser"
}

variable "ssh_public_key" {
  description = "SSH публічний ключ для доступу до VM"
  type        = string
}
