# Threads auto-post (PowerShell, pool-based)
# Run by Windows Task Scheduler at 6am/12pm/6pm JST

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$LogFile = Join-Path $BaseDir "scripts\threads-post.log"
$PoolFile = Join-Path $BaseDir "scripts\posts-pool.md"
$UsedFile = Join-Path $BaseDir "scripts\posts-used.log"

function Load-Env {
    $envMap = @{}
    $envFile = Join-Path $BaseDir ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile -Encoding UTF8 | ForEach-Object {
            if ($_ -match '^([^#=]+)=(.*)$') {
                $envMap[$matches[1].Trim()] = $matches[2].Trim()
            }
        }
    }
    return $envMap
}

function Get-Section {
    $hour = (Get-Date).Hour
    if ($hour -ge 4 -and $hour -lt 10) {
        return "morning"
    } elseif ($hour -ge 10 -and $hour -lt 16) {
        return "noon"
    } else {
        return "evening"
    }
}

function Get-PostsFromPool {
    param($sectionName)

    if (-not (Test-Path $PoolFile)) {
        throw "Pool file not found: $PoolFile"
    }

    $content = Get-Content $PoolFile -Raw -Encoding UTF8
    $pattern = '## ' + [regex]::Escape($sectionName) + '[^\n]*\n([\s\S]*?)(?=\n## |\z)'
    $m = [regex]::Match($content, $pattern)
    if (-not $m.Success) {
        throw "Section not found: $sectionName"
    }
    $sectionContent = $m.Groups[1].Value

    $sep = "`n---`n"
    $blocks = $sectionContent -split '(?m)^---\s*$'
    $posts = @()
    foreach ($b in $blocks) {
        $t = $b.Trim()
        if ($t.Length -gt 20) { $posts += $t }
    }
    return $posts
}

function Get-Hash {
    param($text)
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
    $sha = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
    return [BitConverter]::ToString($sha).Replace("-", "").Substring(0, 16)
}

function Pick-Post {
    param($posts)

    $used = @{}
    if (Test-Path $UsedFile) {
        Get-Content $UsedFile -Encoding UTF8 | ForEach-Object { $used[$_] = $true }
    }

    $unused = @()
    foreach ($p in $posts) {
        $h = Get-Hash -text $p
        if (-not $used.ContainsKey($h)) { $unused += $p }
    }

    if ($unused.Count -eq 0) {
        Set-Content -Path $UsedFile -Value "" -Encoding UTF8
        $unused = $posts
    }

    $pick = $unused | Get-Random
    $pickHash = Get-Hash -text $pick
    Add-Content -Path $UsedFile -Value $pickHash -Encoding UTF8

    return $pick
}

function Post-ToThreads {
    param($userId, $token, $text)

    $r1 = Invoke-RestMethod -Uri "https://graph.threads.net/v1.0/$userId/threads" -Method Post -Body @{
        media_type = "TEXT"
        text = $text
        access_token = $token
    }
    if (-not $r1.id) { return @{ error = $r1 } }

    Start-Sleep -Seconds 3

    $r2 = Invoke-RestMethod -Uri "https://graph.threads.net/v1.0/$userId/threads_publish" -Method Post -Body @{
        creation_id = $r1.id
        access_token = $token
    }
    return $r2
}

# Main
$now = Get-Date -Format "yyyy-MM-dd HH:mm"
try {
    $envMap = Load-Env
    $token = $envMap["THREADS_ACCESS_TOKEN"]
    $userId = $envMap["THREADS_USER_ID"]

    if (-not $token -or $token -eq "your_token_here") {
        Add-Content -Path $LogFile -Value "[$now] ERROR: token not set`n" -Encoding UTF8
        exit 1
    }

    $section = Get-Section
    $posts = Get-PostsFromPool -sectionName $section
    $text = Pick-Post -posts $posts

    $result = Post-ToThreads -userId $userId -token $token -text $text

    if ($result.id) {
        $status = "OK post_id=$($result.id)"
    } else {
        $status = "ERROR: $($result | ConvertTo-Json -Compress)"
    }

    Add-Content -Path $LogFile -Value "[$now] $status (section: $section)`n$text`n`n" -Encoding UTF8
    Write-Host $status
    Write-Host $text
}
catch {
    Add-Content -Path $LogFile -Value "[$now] EXCEPTION: $_`n" -Encoding UTF8
    Write-Host "EXCEPTION: $_"
    exit 1
}
