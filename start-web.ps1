# Käynnistä äänenlaatuanalysaattori web-käyttöliittymällä
# Usage: .\start-web.ps1

Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║" -NoNewline -ForegroundColor Cyan
Write-Host "   🎙️ Äänenlaatuanalysaattori Web-käyttöliittymä         " -NoNewline -ForegroundColor White
Write-Host "║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n📦 Käynnistetään Docker-kontit...`n" -ForegroundColor Yellow

# Build and start containers
docker compose -f docker-compose.gpu.yml up -d --build

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Kontit käynnistetty!`n" -ForegroundColor Green
    
    # Wait for Ollama to be ready
    Write-Host "⏳ Odotetaan Ollaman käynnistymistä..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Pull Phi model if not exists
    Write-Host "`n📥 Tarkistetaan LLM-malli..." -ForegroundColor Yellow
    $models = docker exec audio-quality-ollama-gpu ollama list 2>$null
    if ($models -notmatch "phi") {
        Write-Host "📥 Ladataan Phi-malli (3GB, voi kestää muutaman minuutin)..." -ForegroundColor Cyan
        docker exec audio-quality-ollama-gpu ollama pull phi
    } else {
        Write-Host "✓ Phi-malli jo ladattu" -ForegroundColor Green
    }
    
    Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║" -NoNewline -ForegroundColor Green
    Write-Host "   ✅ VALMIS! Web-käyttöliittymä käynnissä                " -NoNewline -ForegroundColor White
    Write-Host "║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    
    Write-Host "`n🌐 Avaa selaimessa: " -NoNewline -ForegroundColor Cyan
    Write-Host "http://localhost:5000" -ForegroundColor White
    
    Write-Host "`n📊 Ohjeet:" -ForegroundColor Yellow
    Write-Host "   1. Kopioi äänitiedostoja input_folder/-kansioon"
    Write-Host "   2. Avaa http://localhost:5000 selaimessa"
    Write-Host "   3. Valitse analysoitavat tiedostot"
    Write-Host "   4. Klikkaa 'Käynnistä analyysi'"
    Write-Host "   5. Seuraa reaaliaikaista edistymistä"
    Write-Host "   6. Tarkastele raportteja selaimessa"
    
    Write-Host "`n🔧 Docker-komennot:" -ForegroundColor Yellow
    Write-Host "   • Pysäytä:  docker compose -f docker-compose.gpu.yml down"
    Write-Host "   • Lokit:    docker compose -f docker-compose.gpu.yml logs -f web"
    Write-Host "   • Uudelleen: docker compose -f docker-compose.gpu.yml restart web"
    
    Write-Host "`n🚀 Avataanko selain nyt? (Y/N): " -NoNewline -ForegroundColor Green
    $answer = Read-Host
    if ($answer -eq "Y" -or $answer -eq "y" -or $answer -eq "") {
        Start-Process "http://localhost:5000"
    }
    
} else {
    Write-Host "`n❌ Virhe konttien käynnistyksessä!" -ForegroundColor Red
    Write-Host "Tarkista lokit: docker compose -f docker-compose.gpu.yml logs`n" -ForegroundColor Yellow
}
