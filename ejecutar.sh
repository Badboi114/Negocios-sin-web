#!/bin/bash
# ============================================================
#  ejecutar.sh — Doble clic para ejecutar el sistema
# ============================================================
#  Abre una terminal y ejecuta el sistema automáticamente.
#  Si no hay internet, espera hasta que vuelva.
# ============================================================

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================"
echo "  SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB"
echo "============================================"
echo ""

# Verificar que existe el entorno virtual
if [ ! -f "venv/bin/python3" ]; then
    echo "ERROR: No se encontró el entorno virtual (venv/)"
    echo "Ejecuta: python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    echo ""
    echo "Presiona Enter para salir..."
    read
    exit 1
fi

# Ejecutar el sistema
echo "Iniciando sistema..."
echo ""
venv/bin/python3 main.py

# Mostrar resultado y esperar
echo ""
echo "============================================"
echo "  Sistema finalizado."
echo "============================================"
echo ""
echo "Presiona Enter para cerrar..."
read
