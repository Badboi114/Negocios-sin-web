#!/usr/bin/env python3
# ============================================================
#  main.py — SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB
# ============================================================
#  100% AUTOMÁTICO — sin confirmaciones interactivas.
#  Busca negocios sin web en toda Bolivia, genera mensajes
#  personalizados, y envía por WhatsApp Web.
#
#  Meta: que cada negocio en el mundo tenga su página web.
# ============================================================

import os
import sys
import time
import random
import socket
import subprocess
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Módulos propios
from scraper_maps import buscar_negocios
from generador_mensajes import procesar_prospectos
from exportador import exportar_csv, exportar_excel, mostrar_resumen
from whatsapp_sender import iniciar_envio_masivo
from gestor_contactados import (
    filtrar_nuevos_prospectos,
    marcar_como_contactados,
    obtener_estadisticas,
    obtener_categorias_pendientes,
    marcar_categoria_buscada,
    calcular_faltantes_hoy,
    contar_enviados_hoy,
)
import config

console = Console()

# ── Banner ──────────────────────────────────────────────────
BANNER = """
[bold cyan]
 ╔══════════════════════════════════════════════════════════════╗
 ║                                                              ║
 ║   🌍  SISTEMA AUTOMÁTICO DE PROSPECCIÓN SIN WEB  🌍         ║
 ║                                                              ║
 ║   ✅ Busca CUALQUIER negocio en Google Maps                  ║
 ║   ✅ Filtra los que NO tienen página web                     ║
 ║   ✅ Genera mensajes personalizados                          ║
 ║   ✅ Nunca contacta el mismo negocio dos veces              ║
 ║   ✅ 100% AUTOMÁTICO — meta: 20 mensajes diarios            ║
 ║   ✅ Multi-ciudad: toda Bolivia                              ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝
[/bold cyan]
"""


def _run_git(args: list[str], timeout: int = 30) -> bool:
    """Ejecuta un comando git en el directorio del proyecto."""
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True
        console.print(f"[yellow]⚠ git {' '.join(args)}: {result.stderr.strip()}[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]⚠ No se pudo ejecutar git: {e}[/yellow]")
        return False


def hay_internet() -> bool:
    """Verifica si hay conexión a internet intentando conectar a DNS de Google."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False


def esperar_conexion(intervalo: int = 30, max_espera: int = 3600):
    """
    Si no hay internet, espera hasta que vuelva la conexión.
    Reintenta cada `intervalo` segundos, hasta `max_espera` segundos total.
    Retorna True si la conexión volvió, False si se agotó el tiempo.
    """
    if hay_internet():
        return True

    console.print(Panel(
        "[bold red]🔌 SIN CONEXIÓN A INTERNET[/bold red]\n\n"
        f"Reintentando cada {intervalo} segundos...\n"
        f"Tiempo máximo de espera: {max_espera // 60} minutos",
        border_style="red",
    ))

    inicio = time.time()
    intentos = 0
    while time.time() - inicio < max_espera:
        intentos += 1
        time.sleep(intervalo)
        if hay_internet():
            console.print(f"[green]✅ Conexión restaurada (después de {intentos * intervalo}s)[/green]\n")
            return True
        minutos = int((time.time() - inicio) / 60)
        console.print(f"[yellow]⏳ Sin internet... ({minutos}min transcurridos)[/yellow]")

    console.print("[red]❌ No se pudo restaurar la conexión. Abortando.[/red]")
    return False


def sincronizar_desde_remoto():
    """Descarga los últimos cambios del repositorio remoto."""
    console.print("[cyan]🔄 Sincronizando desde el repositorio remoto...[/cyan]")
    _run_git(["stash", "--include-untracked"])
    ok = _run_git(["pull", "--rebase", "origin", "main"], timeout=60)
    _run_git(["stash", "pop"])
    if ok:
        console.print("[green]✅ Sincronizado.[/green]")
    else:
        console.print("[yellow]⚠ No se pudo sincronizar — se usará historial local.[/yellow]")


def subir_contactados_a_remoto():
    """Sube archivos de contactados al repositorio remoto."""
    archivos = [config.ARCHIVO_CONTACTADOS, config.ARCHIVO_HISTORICO, config.ARCHIVO_CATEGORIAS_BUSCADAS]
    existentes = [f for f in archivos if os.path.exists(f)]
    if not existentes:
        return

    console.print("\n[cyan]☁️  Subiendo al repositorio remoto...[/cyan]")
    _run_git(["add"] + existentes)
    fecha = time.strftime("%Y-%m-%d %H:%M")
    _run_git(["commit", "-m", f"chore: actualizar contactados [{fecha}]"])
    ok = _run_git(["push", "origin", "main"], timeout=60)

    if ok:
        console.print("[green]✅ Historial subido al repositorio.[/green]")
    else:
        console.print("[yellow]⚠ No se pudo subir (se intentará la próxima vez).[/yellow]")


def elegir_ciudad() -> str:
    """
    Elige automáticamente la siguiente ciudad para buscar.
    Rota entre las ciudades de Bolivia basándose en la fecha
    para distribuir equitativamente.
    """
    dia_del_ano = datetime.now().timetuple().tm_yday
    hora = datetime.now().hour
    idx = (dia_del_ano * 3 + hora // 8) % len(config.CIUDADES_BOLIVIA)
    return config.CIUDADES_BOLIVIA[idx]


def mostrar_config(ciudad: str, faltantes: int):
    """Muestra la configuración actual."""
    stats = obtener_estadisticas()
    categorias_pendientes = obtener_categorias_pendientes()
    total_cats = len(config.CATEGORIAS_NEGOCIOS)
    cats_pendientes = len(categorias_pendientes)

    console.print(Panel(
        f"[cyan]📍 Ciudad:[/cyan] [bold]{ciudad}[/bold]\n"
        f"[cyan]🌐 Código de país:[/cyan] [bold]+{config.CODIGO_PAIS}[/bold]\n"
        f"[cyan]📊 Meta diaria:[/cyan] [bold]{config.MENSAJES_DIARIOS_META}[/bold]\n"
        f"[cyan]✅ Enviados hoy:[/cyan] [bold]{stats['enviados_hoy']}[/bold]\n"
        f"[cyan]📤 Faltan hoy:[/cyan] [bold]{faltantes}[/bold]\n"
        f"[cyan]📂 Categorías pendientes:[/cyan] [bold]{cats_pendientes}/{total_cats}[/bold]\n"
        f"[cyan]📋 Total contactados:[/cyan] [bold]{stats['total_contactados']}[/bold]\n"
        f"[cyan]🏙️  Ciudades disponibles:[/cyan] [bold]{len(config.CIUDADES_BOLIVIA)}[/bold]",
        title="⚙️ Configuración",
        border_style="cyan",
    ))


def busqueda_automatica(ciudad: str, limite: int) -> list[dict]:
    """
    Busca negocios SIN web hasta alcanzar el límite.
    Multi-ciudad, aleatoriza categorías, salta agotadas.
    """
    todos_los_prospectos = []

    categorias = obtener_categorias_pendientes()
    if not categorias:
        console.print("[yellow]⚠ Todas las categorías buscadas. Reiniciando...[/yellow]")
        categorias = list(config.CATEGORIAS_NEGOCIOS)

    random.shuffle(categorias)
    total_categorias = len(categorias)

    console.print(f"\n[bold yellow]🚀 BÚSQUEDA AUTOMÁTICA: {limite} negocios en {ciudad}[/bold yellow]")
    console.print(f"[cyan]   {total_categorias} categorías disponibles[/cyan]\n")

    categoria_idx = 0
    while len(todos_los_prospectos) < limite and categoria_idx < total_categorias:
        categoria = categorias[categoria_idx]
        termino = f"{categoria} en {ciudad}"

        console.print(Panel(
            f"[bold cyan]🔍 [{categoria_idx + 1}/{total_categorias}] {termino}[/bold cyan]\n"
            f"[dim]Encontrados: {len(todos_los_prospectos)}/{limite}[/dim]",
            border_style="cyan",
        ))

        try:
            faltantes = limite - len(todos_los_prospectos)
            cantidad_a_buscar = min(config.CANTIDAD_POR_CATEGORIA, faltantes + 5)

            negocios = buscar_negocios(termino, cantidad_a_buscar)

            if negocios:
                prospectos = procesar_prospectos(negocios)
                prospectos_nuevos = filtrar_nuevos_prospectos(prospectos)

                if prospectos_nuevos:
                    telefonos_sesion = {p["Telefono_Limpio"] for p in todos_los_prospectos}
                    prospectos_nuevos = [
                        p for p in prospectos_nuevos
                        if p["Telefono_Limpio"] not in telefonos_sesion
                    ]

                if prospectos_nuevos:
                    todos_los_prospectos.extend(prospectos_nuevos)
                    console.print(f"[green]✅ {len(prospectos_nuevos)} NUEVOS "
                                  f"— Total: {len(todos_los_prospectos)}/{limite}[/green]\n")
                else:
                    console.print(f"[yellow]⚠ Categoría agotada[/yellow]\n")
                    marcar_categoria_buscada(categoria)
            else:
                console.print(f"[yellow]⚠ Sin resultados[/yellow]\n")
                marcar_categoria_buscada(categoria)

        except KeyboardInterrupt:
            console.print(f"\n[yellow]⚠ Búsqueda interrumpida[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]\n")

        if len(todos_los_prospectos) >= limite:
            console.print(f"\n[green]✅ Meta alcanzada: {limite} negocios[/green]")
            break

        categoria_idx += 1

        if categoria_idx < total_categorias:
            pausa = random.uniform(5, 10)
            time.sleep(pausa)

    todos_los_prospectos = todos_los_prospectos[:limite]
    return todos_los_prospectos


def main():
    """Flujo principal 100% automático con loop hasta completar la meta."""
    console.print(BANNER)

    # ── Verificar internet antes de empezar ──
    if not esperar_conexion():
        return

    # ── Sincronizar ──
    sincronizar_desde_remoto()

    # ── Calcular cuántos faltan hoy ──
    faltantes = calcular_faltantes_hoy()
    enviados_hoy = contar_enviados_hoy()

    # ── Elegir ciudad automáticamente ──
    ciudad = elegir_ciudad()

    mostrar_config(ciudad, faltantes)

    if faltantes == 0:
        console.print(Panel(
            f"[bold green]🎉 META DIARIA COMPLETADA[/bold green]\n\n"
            f"Ya se enviaron [bold]{enviados_hoy}/{config.MENSAJES_DIARIOS_META}[/bold] "
            f"mensajes hoy.\n\n"
            f"Ejecuta mañana para continuar.",
            border_style="green",
        ))
        return

    # ── LOOP: Buscar → Enviar → Repetir hasta completar la meta ──
    MAX_RONDAS = 10  # Evitar loop infinito si no hay negocios
    total_enviados_sesion = 0
    total_fallidos_sesion = 0
    ronda = 0

    while faltantes > 0 and ronda < MAX_RONDAS:
        ronda += 1

        # Verificar internet antes de cada ronda
        if not esperar_conexion():
            console.print("[red]❌ Sin internet. Guardando progreso...[/red]")
            subir_contactados_a_remoto()
            break

        # Buscar un extra para compensar fallos (~40% fallan por no tener WhatsApp)
        buscar_cantidad = min(faltantes * 2, faltantes + 10)

        console.print(Panel(
            f"[bold green]🔍 RONDA {ronda} — BÚSQUEDA AUTOMÁTICA[/bold green]\n\n"
            f"Enviados hoy: [bold]{contar_enviados_hoy()}[/bold]\n"
            f"Faltan: [bold]{faltantes}[/bold] para completar la meta de "
            f"[bold]{config.MENSAJES_DIARIOS_META}[/bold]\n"
            f"Buscando: [bold]{buscar_cantidad}[/bold] negocios (extra para compensar fallos)\n"
            f"Ciudad: [bold]{ciudad}[/bold]",
            border_style="green",
        ))

        # ── Buscar ──
        nuevos = busqueda_automatica(ciudad, buscar_cantidad)

        if not nuevos:
            console.print(Panel(
                "[bold yellow]⚠️ NO SE ENCONTRARON NEGOCIOS NUEVOS[/bold yellow]\n\n"
                "Cambiando de ciudad para la siguiente ronda...",
                border_style="yellow",
            ))
            # Cambiar a otra ciudad si esta se agotó
            idx_actual = config.CIUDADES_BOLIVIA.index(ciudad) if ciudad in config.CIUDADES_BOLIVIA else 0
            ciudad = config.CIUDADES_BOLIVIA[(idx_actual + 1) % len(config.CIUDADES_BOLIVIA)]
            continue

        # ── Guardar prospectos ──
        exportar_csv(nuevos)
        exportar_excel(nuevos)

        console.print(Panel(
            f"[bold green]📊 {len(nuevos)} NEGOCIOS ENCONTRADOS[/bold green]\n"
            f"Ciudad: [bold]{ciudad}[/bold]",
            border_style="green",
        ))
        mostrar_resumen(nuevos)

        # ── Enviar por WhatsApp (automático) ──
        console.print(Panel(
            f"[bold cyan]📤 ENVIANDO {len(nuevos)} MENSAJES POR WHATSAPP[/bold cyan]\n\n"
            f"100% automático. Si no hay sesión activa,\n"
            f"escanea el QR cuando aparezca en el navegador.",
            border_style="cyan",
        ))

        nuevos = iniciar_envio_masivo(nuevos) or nuevos

        # ── Guardar contactados ──
        console.print("\n[cyan]📋 Registrando contactados...[/cyan]")
        marcar_como_contactados(nuevos)
        exportar_csv(nuevos)
        exportar_excel(nuevos)

        # ── Contar resultados de esta ronda ──
        enviados_ronda = len([p for p in nuevos if p.get("Estado") == "Enviado"])
        fallidos_ronda = len([p for p in nuevos if str(p.get("Estado", "")).startswith("Fallido")])
        total_enviados_sesion += enviados_ronda
        total_fallidos_sesion += fallidos_ronda

        console.print(Panel(
            f"[cyan]📊 RONDA {ronda} COMPLETADA[/cyan]\n\n"
            f"✅ Enviados esta ronda: {enviados_ronda}\n"
            f"❌ Fallidos esta ronda: {fallidos_ronda}",
            border_style="cyan",
        ))

        # ── Subir al repositorio después de cada ronda ──
        subir_contactados_a_remoto()

        # ── Recalcular faltantes ──
        faltantes = calcular_faltantes_hoy()

        if faltantes > 0:
            console.print(f"\n[yellow]⏳ Faltan {faltantes} mensajes. "
                          f"Iniciando nueva ronda de búsqueda...[/yellow]\n")
            pausa = random.uniform(10, 20)
            console.print(f"[dim]Pausa de {pausa:.0f}s antes de la siguiente ronda...[/dim]")
            time.sleep(pausa)

    # ── Resumen final ──
    total_hoy = contar_enviados_hoy()

    if faltantes == 0:
        estado_msg = f"[bold green]🎉 META DIARIA COMPLETADA — {total_hoy}/{config.MENSAJES_DIARIOS_META}[/bold green]"
    else:
        estado_msg = (f"[bold yellow]⚠ Meta parcial: {total_hoy}/{config.MENSAJES_DIARIOS_META}[/bold yellow]\n"
                      f"Se completaron {MAX_RONDAS} rondas. Ejecuta de nuevo si es necesario.")

    console.print(Panel(
        f"{estado_msg}\n\n"
        f"✅ Enviados esta sesión: {total_enviados_sesion}\n"
        f"❌ Fallidos esta sesión: {total_fallidos_sesion}\n"
        f"🔄 Rondas ejecutadas: {ronda}\n"
        f"🏙️  Ciudad: {ciudad}\n"
        f"📁 Archivos: {config.ARCHIVO_CSV}, {config.ARCHIVO_HISTORICO}",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
