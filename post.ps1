param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Mot,

    [switch]$Cemantle
)

$origin = if ($Cemantle) { "https://cemantle.certitudes.org" } else { "https://cemantix.certitudes.org" }

# Numero du jour (meme calcul que le site)
if ($Cemantle) {
    $epoch = [datetime]::Parse("2022-04-04")
    $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Pacific Standard Time")
} else {
    $epoch = [datetime]::Parse("2022-03-02")
    $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Romance Standard Time")
}

$today = [System.TimeZoneInfo]::ConvertTimeFromUtc([datetime]::UtcNow, $tz).Date
$day = ($today - $epoch.Date).Days

$url = "$origin/score?n=$day"

$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    "Origin"     = $origin
    "Referer"    = "$origin/"
}

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body @{ word = $Mot }
}
catch {
    Write-Error "Requete echouee : $_"
    exit 1
}

$exitCode = 0

if ($response.r) {
    Write-Error "Numero de jour invalide ($day)."
    $exitCode = 1
}
elseif ($response.e) {
    Write-Error "Mot inconnu ou invalide : $Mot"
    $exitCode = 1
}
else {
    $score = [double]$response.s
    $proximite = [math]::Round($score * 100, 2)

    Write-Host "Jour #$day - mot : $Mot"
    Write-Host "Score    : $proximite"

    if ($null -ne $response.v) {
        Write-Host "Validations avant vous : $($response.v)"
    }

    if ($score -ge 1.0) {
        Write-Host "Trouve !" -ForegroundColor Green
    }
    elseif ($score -ge 0.5) {
        Write-Host "Tres chaud !" -ForegroundColor Yellow
    }
    elseif ($score -ge 0.25) {
        Write-Host "Tiede." -ForegroundColor DarkYellow
    }
    else {
        Write-Host "Froid." -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "Reponse JSON :"
$response | ConvertTo-Json -Depth 10

exit $exitCode
