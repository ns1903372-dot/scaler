param(
    [Parameter(Mandatory = $true)]
    [string]$RepoId,

    [string]$HfToken = "",

    [string]$RemoteName = "hf-space",

    [switch]$ForceRemote
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[HF-DEPLOY] $Message"
}

if (-not (Test-Path ".git")) {
    throw "This script must be run from the repository root."
}

if ([string]::IsNullOrWhiteSpace($HfToken)) {
    $HfToken = $env:HF_TOKEN
}

$remoteUrl = "https://huggingface.co/spaces/$RepoId"
$existingRemote = git remote get-url $RemoteName 2>$null

if ($LASTEXITCODE -eq 0 -and $existingRemote) {
    if ($ForceRemote) {
        Write-Info "Updating existing remote '$RemoteName' to $remoteUrl"
        git remote set-url $RemoteName $remoteUrl
    }
    else {
        Write-Info "Remote '$RemoteName' already exists: $existingRemote"
    }
}
else {
    Write-Info "Adding remote '$RemoteName' -> $remoteUrl"
    git remote add $RemoteName $remoteUrl
}

Write-Info "Staging files"
git add .

Write-Info "Current status"
git status --short

try {
    git diff --cached --quiet
    $hasStagedChanges = $false
}
catch {
    $hasStagedChanges = $true
}

if ($hasStagedChanges) {
    Write-Info "Creating initial commit"
    git commit -m "Prepare OpenEnv retail ops Space deployment"
}
else {
    Write-Info "No new staged changes to commit"
}

if (-not [string]::IsNullOrWhiteSpace($HfToken)) {
    $pushUrl = "https://user:$HfToken@huggingface.co/spaces/$RepoId"
    Write-Info "Pushing to Hugging Face Space with token-authenticated URL"
    git push $pushUrl HEAD:main
}
else {
    Write-Info "Pushing to remote '$RemoteName'"
    git push $RemoteName HEAD:main
}

Write-Info "Deployment push complete"
Write-Info "Space URL: https://huggingface.co/spaces/$RepoId"
