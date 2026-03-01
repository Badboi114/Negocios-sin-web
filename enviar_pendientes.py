#!/usr/bin/env python3
# ============================================================
#  enviar_pendientes.py — Envía los prospectos pendientes
#                         del CSV sin hacer nueva búsqueda
# ============================================================

import pandas as pd
from rich.console import Console
from rich.panel import Panel

from whatsapp_sender import iniciar_envio_masivo
from gestor_contactados import marcar_como_contactados
from exportador import exportar_csv, exportar_excel
import config

console = Console()


def main():
    # Sincronizar desde remoto antes de cargar datos
    from main import sincronizar_desde_remoto, subir_contactados_a_remoto
    sincronizar_desde_remoto()

    # Cargar prospectos pendientes
    try:
        df = pd.read_csv(config.ARCHIVO_CSV)
    except FileNotFoundError:
        console.print("[red]❌ No se encontró prospectos.csv[/red]")
        return

    pendientes = df[df["Estado"] == "Pendiente"].to_dict("records")

    if not pendientes:
        console.print("[yellow]⚠ No hay prospectos pendientes en prospectos.csv[/yellow]")
        return

    console.print(Panel(
        f"[bold cyan]📋 PROSPECTOS PENDIENTES EN CSV[/bold cyan]\n\n"
        + "\n".join(
            f"  {i+1}. {p['Nombre']} — {p['Telefono_Limpio']}"
            for i, p in enumerate(pendientes)
        ),
        border_style="cyan",
    ))

    # Cargar todos para actualizar estados al final
    todos = df.to_dict("records")

    # Enviar solo los pendientes
    pendientes_enviados = iniciar_envio_masivo(pendientes) or pendientes

    # Actualizar estados en la lista completa
    estado_por_tel = {p["Telefono_Limpio"]: p for p in pendientes_enviados}
    for registro in todos:
        tel = registro.get("Telefono_Limpio")
        if tel in estado_por_tel:
            p_enviado = estado_por_tel[tel]
            registro["Estado"] = p_enviado.get("Estado", registro["Estado"])
            if p_enviado.get("Fecha_Envio"):
                registro["Fecha_Envio"] = p_enviado["Fecha_Envio"]

    # Guardar contactados
    console.print("\n[cyan]📋 Registrando negocios contactados...[/cyan]")
    marcar_como_contactados(pendientes_enviados)

    # Actualizar CSV y Excel
    exportar_csv(todos)
    exportar_excel(todos)

    # Subir al repositorio
    subir_contactados_a_remoto()

    enviados = len([p for p in pendientes_enviados if p.get("Estado") == "Enviado"])
    fallidos = len([p for p in pendientes_enviados if str(p.get("Estado", "")).startswith("Fallido")])

    console.print(Panel(
        f"[bold green]🎉 ENVÍO COMPLETADO[/bold green]\n\n"
        f"✅ Enviados: {enviados}\n"
        f"❌ Fallidos: {fallidos}",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
