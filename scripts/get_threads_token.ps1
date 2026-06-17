# Threads アクセストークン取得（PowerShell版）
# 期限切れ時に実行してトークンを再取得・.env更新する

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$EnvFile = Join-Path $BaseDir ".env"

$APP_ID = Read-Host "App ID を入力 (デフォルト 886961687735504、Enter で確定)"
if (-not $APP_ID) { $APP_ID = "886961687735504" }

$APP_SECRET = Read-Host "App Secret を入力（Meta for Developers で確認）" -AsSecureString
$APP_SECRET_PLAIN = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($APP_SECRET)
)

$REDIRECT_URI = "https://www.facebook.com"
$encodedRedirect = [System.Uri]::EscapeDataString($REDIRECT_URI)

$AUTH_URL = "https://threads.net/oauth/authorize?client_id=$APP_ID&redirect_uri=$encodedRedirect&scope=threads_basic,threads_content_publish&response_type=code"

Write-Host ""
Write-Host "=== Step 1: ブラウザで認証 ===" -ForegroundColor Yellow
Write-Host "下記URLをブラウザで開いて、Threadsアカウントでログイン:"
Write-Host ""
Write-Host $AUTH_URL -ForegroundColor Cyan
Write-Host ""
Start-Process $AUTH_URL

Write-Host "=== Step 2: 認可コード貼り付け ===" -ForegroundColor Yellow
Write-Host "認証後 facebook.com にリダイレクトされる。"
Write-Host "URLバーの ?code=XXXXX#_ の XXXXX 部分（=より後、#より前）をコピー"
Write-Host ""
$rawCode = Read-Host "コードを貼り付け"
$authCode = ($rawCode -split "#")[0].Trim()

# 短期トークン取得
Write-Host ""
Write-Host "短期トークン取得中..." -ForegroundColor Yellow
$shortResp = Invoke-RestMethod -Uri "https://graph.threads.net/oauth/access_token" -Method Post -Body @{
    client_id = $APP_ID
    client_secret = $APP_SECRET_PLAIN
    code = $authCode
    grant_type = "authorization_code"
    redirect_uri = $REDIRECT_URI
}
$shortToken = $shortResp.access_token
$userId = $shortResp.user_id
Write-Host "短期トークン取得 OK (user_id=$userId)" -ForegroundColor Green

# 長期トークン交換
Write-Host "長期トークン交換中..." -ForegroundColor Yellow
$longResp = Invoke-RestMethod -Uri "https://graph.threads.net/access_token" -Body @{
    grant_type = "th_exchange_token"
    client_secret = $APP_SECRET_PLAIN
    access_token = $shortToken
}
$longToken = $longResp.access_token
$expiresDays = [Math]::Round($longResp.expires_in / 86400, 0)
Write-Host "長期トークン取得 OK (有効期限: $expiresDays 日)" -ForegroundColor Green

# .env 更新
$lines = if (Test-Path $EnvFile) { Get-Content $EnvFile } else { @() }

function Upsert-EnvLine {
    param([string[]]$lines, [string]$key, [string]$value)
    $found = $false
    $result = @()
    foreach ($l in $lines) {
        if ($l -match "^$key=") {
            $result += "$key=$value"
            $found = $true
        } else {
            $result += $l
        }
    }
    if (-not $found) { $result += "$key=$value" }
    return $result
}

$lines = Upsert-EnvLine -lines $lines -key "THREADS_ACCESS_TOKEN" -value $longToken
$lines = Upsert-EnvLine -lines $lines -key "THREADS_USER_ID" -value $userId
Set-Content -Path $EnvFile -Value $lines -Encoding UTF8

Write-Host ""
Write-Host ".env 更新完了 ✓" -ForegroundColor Green
Write-Host "  THREADS_USER_ID = $userId"
Write-Host "  THREADS_ACCESS_TOKEN = $($longToken.Substring(0,20))..."
Write-Host ""
Write-Host "テスト投稿は post_threads.ps1 を直接実行で確認できます。"
