#!/usr/bin/env bash
# Git-alustus ja ensimmäinen push GitHubiin
# Käyttö: bash git-init.sh <your-github-username>

set -e

USERNAME=$1

if [ -z "$USERNAME" ]; then
    echo "❌ Error: GitHub username required"
    echo "Usage: bash git-init.sh <your-github-username>"
    exit 1
fi

echo "🚀 Initializing Git repository..."

# Alusta Git
git init

# Lisää kaikki tiedostot
echo "📦 Adding files to Git..."
git add .

# Ensimmäinen commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: GPU-accelerated audio quality analyzer

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
- 8GB+ RAM, 4GB+ GPU VRAM"

# Lisää remote
echo "🔗 Adding GitHub remote..."
git remote add origin "https://github.com/$USERNAME/audio-quality-analyzer.git"

# Aseta main branch
git branch -M main

echo ""
echo "✅ Git repository initialized!"
echo ""
echo "📌 Next steps:"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo "   - Name: audio-quality-analyzer"
echo "   - Don't initialize with README, .gitignore or LICENSE"
echo ""
echo "2. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. Set repository description:"
echo "   🎙️ GPU-accelerated audio quality analyzer with AI and LLM explanations. Analyze podcasts, recordings & music with 7 quality aspects + actionable recommendations."
echo ""
echo "4. Add topics:"
echo "   audio-analysis, audio-quality, gpu-acceleration, pytorch, docker, ollama, llm, python, audio-processing, podcast-analysis, machine-learning, nvidia-cuda"
echo ""
