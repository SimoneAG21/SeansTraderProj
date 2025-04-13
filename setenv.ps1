# setenv.ps1

param (
    [switch]$Refresh = $false
)

# Define the Python path to add
$pythonPath = "C:\pyver\py312"

# Add the Python path to the current session's PATH environment variable
$env:PATH = "$pythonPath;" + $env:PATH

# Verify that Python is accessible
Write-Host "Python path added: $pythonPath"
Write-Host "Current Python version:"
python --version


# Define the virtual environment path
$venvPath = "P:\DynaPOD\proj\trader\venv"



# Activate the virtual environment
$activateScript = Join-Path -Path $venvPath -ChildPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment at $venvPath"
    & $activateScript
} else {
    Write-Host "Error: Virtual environment activation script not found at $activateScript"
    exit
}
# Confirm activation
Write-Host "Active Python path after venv activation:"
(Get-Command python).Path

# If -Refresh is specified, update pip and requirements