# Create data directory if it doesn't exist
$dataDir = Join-Path $PSScriptRoot '..\data' | Resolve-Path -ErrorAction SilentlyContinue
if (-not $dataDir) {
    New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot '..\data') | Out-Null
}

$files = @(
    'Température moyenne par principale station.csv',
    'Température minimum absolu par principale station.csv',
    'Température maximum absolu par principale station.csv',
    'Taux d''occupation par région touristique.csv',
    'samples.json',
    'Recettes touristiques en devises.csv',
    'Nuitées touristiques globales par nationalité.csv',
    'Nombre d’établissements touristiques.csv',
    'Nombre d''établissements par région touristique.csv',
    'Investissements touristiques.csv',
    'Indices des prix de l''immobilier par type de bien.csv',
    'Glissement annuel des indices des prix de l''immobilier par type de bien.csv',
    'Emplois touristiques directs.csv',
    'Durée moyenne de séjour (en jours).csv',
    'Capacité en lits.csv',
    'Capacité d''hébergement par région touristique.csv'
)

foreach ($f in $files) {
    $src = Join-Path $PSScriptRoot "..\$f"
    if (Test-Path $src) {
        $dest = Join-Path $PSScriptRoot "..\data\$f"
        Write-Host "Moving $f -> data/"
        Move-Item -Path $src -Destination $dest -Force
    } else {
        Write-Host "Not found: $f"
    }
}

Write-Host "Done."
