# Add a new management task
Get-Service | Where-Object {$_.DisplayName -eq "SQL Server"} | Restart-Service
