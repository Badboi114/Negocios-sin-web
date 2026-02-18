# ============================================================
# gestor_contactados.py — Gestiona la lista de negocios
#                         ya contactados (anti-duplicados)
# ============================================================

import os
import pandas as pd
from datetime import datetime
from rich.console import Console

import config

console = Console()


def cargar_contactados() -> set:
    """
    Carga la lista de teléfonos ya contactados.
    
    Returns:
        Set con los teléfonos que YA fueron contactados.
    """
    if not os.path.exists(config.ARCHIVO_CONTACTADOS):
        return set()
    
    try:
        df = pd.read_csv(config.ARCHIVO_CONTACTADOS, encoding='utf-8-sig')
        telefónos = set(df['Telefono_Limpio'].astype(str).str.strip())
        console.print(f"[cyan]📋 {len(telefónos)} negocios ya contactados (historial cargado)[/cyan]")
        return telefónos
    except Exception as e:
        console.print(f"[yellow]⚠ Error cargando historial: {e}[/yellow]")
        return set()


def filtrar_nuevos_prospectos(prospectos: list[dict]) -> list[dict]:
    """
    Filtra los prospectos para excluir los que YA fueron contactados.
    
    Args:
        prospectos: Lista de prospectos encontrados.
    
    Returns:
        Lista de prospectos que NO han sido contactados aún.
    """
    contactados = cargar_contactados()
    
    nuevos = []
    duplicados = 0
    
    for p in prospectos:
        tel = str(p.get("Telefono_Limpio", "")).strip()
        if tel not in contactados:
            nuevos.append(p)
        else:
            duplicados += 1
    
    if duplicados > 0:
        console.print(f"[yellow]⚠ {duplicados} prospectos descartados (ya contactados)[/yellow]")
    
    return nuevos


def marcar_como_contactados(prospectos: list[dict]):
    """
    Guarda los prospectos enviados en el historial de contactados.
    También los agrega al archivo histórico para auditoría.
    
    Args:
        prospectos: Lista de prospectos que se enviaron correctamente.
    """
    enviados = [p for p in prospectos if p.get("Estado") == "Enviado"]
    
    if not enviados:
        return
    
    # 1. Agregar a CONTACTADOS (para no volver a contactar)
    contactados_existentes = []
    if os.path.exists(config.ARCHIVO_CONTACTADOS):
        try:
            contactados_existentes = pd.read_csv(
                config.ARCHIVO_CONTACTADOS,
                encoding='utf-8-sig'
            ).to_dict('records')
        except Exception:
            pass
    
    # Agregar nuevos
    for p in enviados:
        contactados_existentes.append({
            "Nombre": p.get("Nombre", ""),
            "Telefono_Limpio": p.get("Telefono_Limpio", ""),
            "Fecha_Contacto": p.get("Fecha_Envio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        })
    
    # Guardar contactados
    df = pd.DataFrame(contactados_existentes)
    df.drop_duplicates(subset=['Telefono_Limpio'], keep='first', inplace=True)
    df.to_csv(config.ARCHIVO_CONTACTADOS, index=False, encoding='utf-8-sig')
    console.print(f"[green]✅ {len(enviados)} contactos guardados en historial[/green]")
    
    # 2. Agregar al archivo histórico (auditoría)
    historico_existente = []
    if os.path.exists(config.ARCHIVO_HISTORICO):
        try:
            historico_existente = pd.read_csv(
                config.ARCHIVO_HISTORICO,
                encoding='utf-8-sig'
            ).to_dict('records')
        except Exception:
            pass
    
    for p in enviados:
        historico_existente.append({
            "Fecha_Envio": p.get("Fecha_Envio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "Nombre": p.get("Nombre", ""),
            "Telefono": p.get("Telefono_Limpio", ""),
            "Categoria": p.get("Categoria", ""),
            "Estado": "Enviado correctamente",
        })
    
    df_historico = pd.DataFrame(historico_existente)
    df_historico.to_csv(config.ARCHIVO_HISTORICO, index=False, encoding='utf-8-sig')


def obtener_estadisticas() -> dict:
    """
    Retorna estadísticas de contactos.
    """
    contactados = cargar_contactados()
    
    stats = {
        "total_contactados": len(contactados),
        "archivo_contactados": config.ARCHIVO_CONTACTADOS,
        "archivo_historico": config.ARCHIVO_HISTORICO,
    }
    
    return stats
