param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('validate','import','export','summary')]
    [string]$Command,
    [string]$Path,
    [string]$Target = 'data/manual_import/sample_prices.csv'
)

$ErrorActionPreference = 'Stop'
$argsList = @('-m', 'app.scripts.import_csv', '--target', $Target, $Command)
if ($Path) { $argsList += $Path }
& .\.venv\Scripts\python.exe @argsList
exit $LASTEXITCODE
