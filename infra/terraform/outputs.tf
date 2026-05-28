output "public_ip" {
  value = azurerm_public_ip.public_ip.ip_address
}

output "web_url" {
  value = "http://${azurerm_public_ip.public_ip.ip_address}:5000"
}

output "grafana_url" {
  value = "http://${azurerm_public_ip.public_ip.ip_address}:3000"
}

output "prometheus_url" {
  value = "http://${azurerm_public_ip.public_ip.ip_address}:9090"
}
