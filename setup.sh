#!/bin/bash
# ============================================================
# setup.sh — Script de instalación del sistema
# ============================================================
# Ejecuta: chmod +x setup.sh && ./setup.sh
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   🔧 INSTALACIÓN — Sistema de Prospección           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Verificar Python
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado."
    echo "   Instálalo con: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION encontrado"

# Crear entorno virtual
echo ""
echo "📦 Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
echo ""
echo "📥 Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Instalar navegadores de Playwright
echo ""
echo "🌐 Instalando navegadores para Playwright..."
echo "   (Esto puede tardar unos minutos la primera vez)"
playwright install chromium
playwright install-deps chromium

# Verificar instalación
echo ""
echo "✅ Verificando instalación..."
python3 -c "
from playwright.sync_api import sync_playwright
import pandas as pd
from rich.console import Console
print('✅ Playwright — OK')
print('✅ Pandas — OK')
print('✅ Rich — OK')
print()
print('🎉 ¡Todo instalado correctamente!')
"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ INSTALACIÓN COMPLETA                           ║"
echo "║                                                      ║"
echo "║   Para ejecutar:                                     ║"
echo "║   source venv/bin/activate                           ║"
echo "║   python3 main.py                                    ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
