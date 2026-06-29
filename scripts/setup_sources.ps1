#Requires -Version 5.1
<#
.SYNOPSIS
    Clone Godot documentation and demo projects for rebuilding the RAG index.

.DESCRIPTION
    The pre-built vector index in data/chroma/ works without these repos.
    Clone them only when you need to re-chunk docs or demos.

    Repositories:
      - https://github.com/godotengine/godot-docs  (branch: master)
      - https://github.com/godotengine/godot-demo-projects
#>
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
Set-Location $Root

function Clone-IfMissing {
    param([string]$Name, [string]$Url, [string]$Branch = $null)
    $dest = Join-Path $Root $Name
    if (Test-Path $dest) {
        Write-Host "  $Name/ already exists — skipping"
        return
    }
    Write-Host "  Cloning $Name ..."
    if ($Branch) {
        git clone --depth 1 --branch $Branch $Url $dest
    } else {
        git clone --depth 1 $Url $dest
    }
}

Write-Host "Setting up Godot source corpora in $Root"
Clone-IfMissing -Name "godot-docs" -Url "https://github.com/godotengine/godot-docs.git" -Branch "master"
Clone-IfMissing -Name "godot-demo-projects" -Url "https://github.com/godotengine/godot-demo-projects.git"
Write-Host "Done."
