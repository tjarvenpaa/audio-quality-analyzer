# Git-alustus ja ensimmäinen push GitHubiin (Windows PowerShell)
# Käyttö: .\git-init.ps1 -Username your-github-username

param(
    [Parameter(Mandatory=$true)]
    [string]$Username
)

Write-Host "🚀 Initializing Git repository..." -ForegroundColor Green

# Alusta Git
git init

# Lisää kaikki tiedostot
Write-Host "`n📦 Adding files to Git..." -ForegroundColor Cyan
git add .

# Ensimmäinen commit
Write-Host "`n💾 Creating initial commit..." -ForegroundColor Cyan
git commit -m @"
Initial commit: GPU-accelerated audio quality analyzer

Features:
- Docker deployment with NVIDIA GPU support (CUDA 11.8)
- 7 quality aspects analysis (Clarity, Noise, Frequency, Dynamic Range, Stereo, Loudness, Production Quality)
- DSP analysis with librosa (30+ metrics per file)
- AI quality assessment with PyTorch Transformer model
- LLM explanations with Ollama Phi (3GB model)
- Automatic issue detection and prioritized recommendations
- Multi-format reports: Excel, detailed text, visualizations (PNG)
- Batch processing for multiple files
- Watch mode for continuous monitoring
- Debug logging for LLM execution monitoring

Tech stack:
- Python 3.10+ with PyTorch CUDA 11.8
- Docker + Docker Compose with GPU passthrough
- Ollama (local LLM) with Phi model
- Librosa, PyLoudnorm, Pandas, OpenPyXL, Matplotlib

Requirements:
- NVIDIA GPU with CUDA support
- Docker Desktop + NVIDIA Container Toolkit
- 8GB+ RAM, 4GB+ GPU VRAM
"@

# Lisää remote
Write-Host "`n🔗 Adding GitHub remote..." -ForegroundColor Cyan
git remote add origin "https://github.com/$Username/audio-quality-analyzer.git"

# Aseta main branch
git branch -M main

Write-Host "`n✅ Git repository initialized!" -ForegroundColor Green
Write-Host "`n📌 Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Create a new repository on GitHub:"
Write-Host "   https://github.com/new" -ForegroundColor Blue
Write-Host "   - Name: audio-quality-analyzer"
Write-Host "   - Don't initialize with README, .gitignore or LICENSE"
Write-Host ""
Write-Host "2. Push to GitHub:"
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Set repository description:"
Write-Host "   🎙️ GPU-accelerated audio quality analyzer with AI and LLM explanations."
Write-Host ""
Write-Host "4. Add topics:"
Write-Host "   audio-analysis, audio-quality, gpu-acceleration, pytorch, docker, ollama, llm, python"
Write-Host ""
