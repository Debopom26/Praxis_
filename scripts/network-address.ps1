# Return usable private IPv4 addresses on active physical LAN interfaces.
$candidates = foreach ($adapter in [System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces()) {
    if ($adapter.OperationalStatus -ne [System.Net.NetworkInformation.OperationalStatus]::Up) { continue }
    if ($adapter.NetworkInterfaceType -notin @(
        [System.Net.NetworkInformation.NetworkInterfaceType]::Wireless80211,
        [System.Net.NetworkInformation.NetworkInterfaceType]::Ethernet)) { continue }
    if ($adapter.Name -match '(?i)virtual|vEthernet|WSL|Docker|VPN|TAP|TUN') { continue }
    $properties = $adapter.GetIPProperties()
    $hasGateway = @($properties.GatewayAddresses | Where-Object {
        $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and
        $_.Address.IPAddressToString -ne '0.0.0.0'
    }).Count -gt 0
    foreach ($entry in $properties.UnicastAddresses) {
        if ($entry.Address.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) { continue }
        $bytes = $entry.Address.GetAddressBytes()
        if (-not ($bytes[0] -eq 10 -or
            ($bytes[0] -eq 172 -and $bytes[1] -ge 16 -and $bytes[1] -le 31) -or
            ($bytes[0] -eq 192 -and $bytes[1] -eq 168))) { continue }
        [pscustomobject]@{
            Address = $entry.Address.IPAddressToString
            Gateway = [int]$hasGateway
            Wireless = [int]($adapter.NetworkInterfaceType -eq [System.Net.NetworkInformation.NetworkInterfaceType]::Wireless80211)
        }
    }
}
$candidates | Sort-Object -Property @{ Expression = 'Gateway'; Descending = $true },
    @{ Expression = 'Wireless'; Descending = $true }, Address -Unique |
    ForEach-Object { $_.Address }
