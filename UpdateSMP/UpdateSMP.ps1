# Define the location of the SMP file
$smpFile = "C:\Scripts\ServerManagementPlan.ps1"

# Define the location of the update file
$updateFile = "C:\Scripts\Updates.ps1"

# Load the SMP into memory
. $smpFile

# Load the update file into memory
. $updateFile

# Save the updated SMP back to the file
$executionContext.InvokeCommand.GetScriptBlock($MyInvocation.ScriptName).ToString() | Set-Content $smpFile

# Confirm that the SMP has been updated
Write-Output "The Server Management Plan has been updated with the latest changes."
