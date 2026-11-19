# One-line installer (Windows PowerShell):
#   irm https://raw.githubusercontent.com/acikyol/agent-cad-skill/main/install.ps1 | iex
# With arguments:
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/acikyol/agent-cad-skill/main/install.ps1))) --project C:\path\to\project --vendor
# Clones or updates the skill in %USERPROFILE%\.agent-cad-skill, then runs install.py (default: --global).
$ErrorActionPreference = "Stop"
$Repo = if ($env:AGENT_CAD_SKILL_REPO) { $env:AGENT_CAD_SKILL_REPO } else { "https://github.com/acikyol/agent-cad-skill.git" }
$Dest = if ($env:AGENT_CAD_SKILL_HOME) { $env:AGENT_CAD_SKILL_HOME } else { Join-Path $HOME ".agent-cad-skill" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "git is required" }
$Py = Get-Command py -ErrorAction SilentlyContinue      # Windows Python launcher
if (-not $Py) { $Py = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Py) { throw "Python 3.10+ is required" }        # (no '??' operator: keeps Windows PowerShell 5.1 working)

if (Test-Path (Join-Path $Dest ".git")) { git -C $Dest pull --ff-only -q }
else { git clone -q --depth 1 $Repo $Dest }

$argsList = if ($args.Count -gt 0) { $args } else { @("--global") }
& $Py.Source (Join-Path $Dest "install.py") @argsList
