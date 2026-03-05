#!/usr/bin/env python3
# ============================================================
#  enviar_ahora.py — SOLO ENVÍO MASIVO POR WHATSAPP
# ============================================================
#  Carga los prospectos del CSV ya existente y los envía
#  directo por WhatsApp Web. Sin volver a buscar.
# ============================================================

import os
import sys
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from whatsapp_sender import iniciar_envio_masivo
from gestor_contactados import guardar_contactados_lote, filtrar_nuevos_prospectos
from exportador import exportar_csv, exportar_excel
import config

console = Console()

CSV_PATH = os.path.join(os.path.dirname(__file__), "prospectos.csv")

def main():
    console.print(Panel(
        "[bold cyan]📤 ENVÍO MASIVO POR WHATSAPP WEB[/bold cyan]\n\n"
        "Este script carga los prospectos ya encontrados\n"
        "y los envía directamente por WhatsApp Web.\n\n"
        "[bold]Se abrirá un navegador para escanear el QR.[/bold]",
        border_style="cyan",
    ))

    # Cargar CSV
    if not os.path.exists(CSV_PATH):
        console.print(f"[red]❌ No se encontró el archivo: {CSV_PATH}[/red]")
        return

    df = pd.read_csv(CSV_PATH)
    prospectos = df.to_dict('records')

    # FILTRAR: excluir ya contactados por teléfono y nombre
    prospectos = filtrar_nuevos_prospectos(prospectos)

    # Filtrar solo pendientes
    pendientes = [p for p in prospectos if p.get("Estado") == "Pendiente"]

    console.print(f"\n[green]📋 Prospectos cargados: {len(prospectos)}[/green]")
    console.print(f"[yellow]⏳ Pendientes de envío: {len(pendientes)}[/yellow]\n")

    if not pendientes:
        console.print("[yellow]⚠ No hay prospectos pendientes para enviar.[/yellow]")
        return

    # Mostrar lista rápida
    for i, p in enumerate(pendientes, 1):
        console.print(f"  {i}. {p.get('Nombre', '?')} — {p.get('Telefono_Limpio', '?')}")

    console.print()

    if not Confirm.ask("¿Enviar ahora por WhatsApp?", default=True):
        console.print("[yellow]Cancelado.[/yellow]")
        return

    # ENVIAR
    resultado = iniciar_envio_masivo(prospectos)
    if resultado is not None:
        prospectos = resultado

    # Registrar contactados
    console.print("\n[cyan]📋 Registrando negocios contactados...[/cyan]")
    guardar_contactados_lote(prospectos)

    # Guardar resultado
    exportar_csv(prospectos)
    exportar_excel(prospectos)

    enviados = len([p for p in prospectos if p.get("Estado") == "Enviado"])
    fallidos = len([p for p in prospectos if str(p.get("Estado", "")).startswith("Fallido")])

    console.print(Panel(
        f"[bold green]🎉 ENVÍO COMPLETADO[/bold green]\n\n"
        f"✅ Enviados: {enviados}\n"
        f"❌ Fallidos: {fallidos}\n"
        f"📁 Archivo: {config.ARCHIVO_CSV}",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
