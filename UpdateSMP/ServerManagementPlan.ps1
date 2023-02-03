# Define the target server to manage
$server = "server1.example.com"

# Establish a remote connection to the server
Enter-PSSession -ComputerName $server

# Perform management tasks
Get-Service | Where-Object {$_.StartType -eq "Automatic"} | Start-Service
Get-EventLog -LogName System -Newest 100 | Where-Object {$_.EntryType -eq "Error"} | Select-Object -Property TimeGenerated,EntryType,Source,Message

# Disconnect from the remote server
Exit-PSSession
