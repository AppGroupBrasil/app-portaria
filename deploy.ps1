# ============================================
# Deploy Script - App Portaria → Hetzner
# Servidor: 46.225.191.114
# Caminho remoto: /root/projetos/condominio_info
# ============================================

$SERVER = "root@46.225.191.114"
$SSH_KEY = "$HOME\.ssh\hetzner_key"
$REMOTE_DIR = "/root/projetos/condominio_info"
$LOCAL_DIR = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOY - App Portaria → Hetzner" -ForegroundColor Cyan
Write-Host "  Servidor: 46.225.191.114" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Step 1: Enviar arquivos via SCP ---
Write-Host "[1/4] Enviando código-fonte..." -ForegroundColor Yellow

# Arquivos e pastas principais (exclui venv, __pycache__, db local, media_cdn)
$filesToSync = @(
    "manage.py",
    "settings.ini",
    "requirements.txt",
    "requirements-vps.txt",
    "condominio_info",
    "info",
    "static",
    "server_configs"
)

foreach ($item in $filesToSync) {
    $localPath = Join-Path $LOCAL_DIR $item
    if (Test-Path $localPath) {
        Write-Host "  → Enviando $item ..." -ForegroundColor Gray
        scp -i $SSH_KEY -r "$localPath" "${SERVER}:${REMOTE_DIR}/"
    } else {
        Write-Host "  ⚠ $item não encontrado, pulando..." -ForegroundColor DarkYellow
    }
}

Write-Host ""
Write-Host "[2/4] Executando comandos no servidor..." -ForegroundColor Yellow

# --- Step 2: Instalar dependências + collectstatic + migrate + restart ---
ssh -i $SSH_KEY $SERVER "cd $REMOTE_DIR && source venv/bin/activate && pip install -r requirements-vps.txt -q && python manage.py migrate --noinput && python manage.py collectstatic --noinput && sudo systemctl restart gunicorn && sudo systemctl restart nginx && echo 'Deploy concluido com sucesso!'"

Write-Host ""
Write-Host "[3/4] Verificando se o site está online..." -ForegroundColor Yellow
ssh -i $SSH_KEY $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/ || echo 'Verificando via gunicorn sock...'; curl -s -o /dev/null -w '%{http_code}' --unix-socket /run/gunicorn.sock http://localhost/"

Write-Host ""
Write-Host "[4/4] Deploy finalizado!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Site: https://appportaria.com" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
