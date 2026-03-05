# ============================================================
# gestor_contactados.py — Gestiona la lista de negocios
#                         ya contactados (anti-duplicados)
# ============================================================
# REGLA DE ORO: Un número se guarda en contactados.csv
# INMEDIATAMENTE después de enviarle mensaje exitosamente.
# Nunca se espera al final del proceso.
# ============================================================

import os
import pandas as pd
from datetime import datetime
from rich.console import Console

import config

console = Console()

# Cache en memoria para no leer el archivo cada vez
_cache_contactados: set | None = None


def cargar_contactados(silencioso: bool = False) -> set:
    """
    Carga la lista de teléfonos ya contactados.
    Usa cache en memoria para evitar lecturas repetidas.
    
    Returns:
        Set con los teléfonos que YA fueron contactados.
    """
    global _cache_contactados
    
    if _cache_contactados is not None:
        return _cache_contactados
    
    if not os.path.exists(config.ARCHIVO_CONTACTADOS):
        _cache_contactados = set()
        return _cache_contactados
    
    try:
        df = pd.read_csv(config.ARCHIVO_CONTACTADOS, encoding='utf-8-sig')
        _cache_contactados = set(df['Telefono_Limpio'].astype(str).str.strip())
        if not silencioso:
            console.print(f"[cyan]📋 {len(_cache_contactados)} negocios ya contactados (historial cargado)[/cyan]")
        return _cache_contactados
    except Exception as e:
        console.print(f"[yellow]⚠ Error cargando historial: {e}[/yellow]")
        _cache_contactados = set()
        return _cache_contactados


def numero_ya_contactado(telefono: str) -> bool:
    """
    Verifica si un número ya fue contactado.
    """
    contactados = cargar_contactados(silencioso=True)
    return str(telefono).strip() in contactados


def filtrar_nuevos_prospectos(prospectos: list[dict]) -> list[dict]:
    """
    Filtra los prospectos para excluir los que YA fueron contactados.
    Filtra por teléfono Y por nombre para mayor seguridad.
    """
    contactados = cargar_contactados()
    
    # También cargar nombres ya contactados
    nombres_contactados = set()
    if os.path.exists(config.ARCHIVO_CONTACTADOS):
        try:
            df = pd.read_csv(config.ARCHIVO_CONTACTADOS, encoding='utf-8-sig')
            nombres_contactados = set(df['Nombre'].astype(str).str.strip().str.lower())
        except Exception:
            pass
    
    nuevos = []
    duplicados = 0
    telefonos_en_lote = set()  # Para evitar duplicados dentro del mismo lote
    
    for p in prospectos:
        tel = str(p.get("Telefono_Limpio", "")).strip()
        nombre = str(p.get("Nombre", "")).strip().lower()
        
        # Verificar: teléfono ya contactado, nombre ya contactado, o duplicado en este lote
        if tel in contactados:
            duplicados += 1
        elif tel in telefonos_en_lote:
            duplicados += 1
        elif nombre and nombre in nombres_contactados:
            duplicados += 1
        else:
            nuevos.append(p)
            telefonos_en_lote.add(tel)
    
    if duplicados > 0:
        console.print(f"[yellow]⚠ {duplicados} prospectos descartados (ya contactados)[/yellow]")
    
    return nuevos


def guardar_contactado_individual(prospecto: dict):
    """
    Guarda UN prospecto procesado (enviado o fallido) en el historial
    para no volver a contactarlo. También agrega al archivo histórico.

    Args:
        prospecto: Diccionario con datos de un prospecto procesado.
    """
    global _cache_contactados

    # Solo guardar si fue procesado (no pendiente)
    estado = prospecto.get("Estado", "")
    if not estado or estado == "Pendiente":
        return

    telefono = str(prospecto.get("Telefono_Limpio", "")).strip()
    if not telefono:
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

    contactados_existentes.append({
        "Nombre": prospecto.get("Nombre", ""),
        "Telefono_Limpio": telefono,
        "Fecha_Contacto": prospecto.get("Fecha_Envio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "Estado": estado,
    })

    df = pd.DataFrame(contactados_existentes)
    df['Telefono_Limpio'] = df['Telefono_Limpio'].astype(str)
    df.drop_duplicates(subset=['Telefono_Limpio'], keep='first', inplace=True)
    df.to_csv(config.ARCHIVO_CONTACTADOS, index=False, encoding='utf-8-sig')

    # Actualizar cache en memoria
    if _cache_contactados is not None:
        _cache_contactados.add(telefono)

    es_enviado = estado == "Enviado"
    if es_enviado:
        console.print(f"  [green]📋 Guardado en historial: {prospecto.get('Nombre', '?')}[/green]")
    else:
        console.print(f"  [yellow]📋 Registrado como fallido: {prospecto.get('Nombre', '?')}[/yellow]")

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

    historico_existente.append({
        "Fecha_Envio": prospecto.get("Fecha_Envio", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "Nombre": prospecto.get("Nombre", ""),
        "Telefono": telefono,
        "Categoria": prospecto.get("Categoria", ""),
        "Estado": estado,
    })

    df_historico = pd.DataFrame(historico_existente)
    df_historico.drop_duplicates(subset=['Telefono'], keep='first', inplace=True)
    df_historico.to_csv(config.ARCHIVO_HISTORICO, index=False, encoding='utf-8-sig')


def guardar_contactados_lote(prospectos: list[dict]):
    """
    Guarda una lista de prospectos procesados en el historial.
    Wrapper para guardar varios de una vez.
    """
    procesados = [
        p for p in prospectos
        if p.get("Estado") and p.get("Estado") != "Pendiente"
    ]
    for p in procesados:
        guardar_contactado_individual(p)


def contar_enviados_hoy() -> int:
    """
    Cuenta cuántos mensajes se enviaron EXITOSAMENTE hoy.
    Lee el histórico y filtra por fecha de hoy y estado 'Enviado'.
    """
    if not os.path.exists(config.ARCHIVO_HISTORICO):
        return 0

    try:
        df = pd.read_csv(config.ARCHIVO_HISTORICO, encoding='utf-8-sig')
        hoy = datetime.now().strftime("%Y-%m-%d")
        # Filtrar por fecha de hoy Y estado enviado (no fallidos)
        df['Fecha_Envio'] = df['Fecha_Envio'].astype(str)
        enviados_hoy = df[
            (df['Fecha_Envio'].str.startswith(hoy)) &
            (df['Estado'].astype(str).str.startswith('Enviado'))
        ]
        return len(enviados_hoy)
    except Exception:
        return 0


def calcular_faltantes_hoy() -> int:
    """
    Calcula cuántos mensajes faltan para completar la meta diaria.
    """
    enviados = contar_enviados_hoy()
    faltantes = max(0, config.MENSAJES_DIARIOS_META - enviados)
    return faltantes


def obtener_estadisticas() -> dict:
    """
    Retorna estadísticas de contactos.
    """
    global _cache_contactados
    _cache_contactados = None  # Forzar recarga
    contactados = cargar_contactados()
    enviados_hoy = contar_enviados_hoy()
    faltantes_hoy = calcular_faltantes_hoy()

    stats = {
        "total_contactados": len(contactados),
        "enviados_hoy": enviados_hoy,
        "faltantes_hoy": faltantes_hoy,
        "meta_diaria": config.MENSAJES_DIARIOS_META,
        "archivo_contactados": config.ARCHIVO_CONTACTADOS,
        "archivo_historico": config.ARCHIVO_HISTORICO,
    }

    return stats


def cargar_categorias_buscadas() -> dict:
    """
    Carga las categorías que ya fueron completamente buscadas.

    Returns:
        Dict con {categoria: fecha_busqueda}
    """
    if not os.path.exists(config.ARCHIVO_CATEGORIAS_BUSCADAS):
        return {}

    try:
        df = pd.read_csv(config.ARCHIVO_CATEGORIAS_BUSCADAS, encoding='utf-8-sig')
        return dict(zip(df['Categoria'].astype(str), df['Fecha_Busqueda'].astype(str)))
    except Exception:
        return {}


def marcar_categoria_buscada(categoria: str):
    """
    Registra una categoría como completamente buscada (sin más resultados nuevos).
    """
    existentes = cargar_categorias_buscadas()
    existentes[categoria] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame([
        {"Categoria": k, "Fecha_Busqueda": v}
        for k, v in existentes.items()
    ])
    df.to_csv(config.ARCHIVO_CATEGORIAS_BUSCADAS, index=False, encoding='utf-8-sig')


def obtener_categorias_pendientes() -> list[str]:
    """
    Retorna las categorías que aún no han sido completamente buscadas.
    """
    buscadas = cargar_categorias_buscadas()
    pendientes = [c for c in config.CATEGORIAS_NEGOCIOS if c not in buscadas]
    return pendientes


# ── Gestión de ciudades (progreso secuencial) ──────────────────


def obtener_ciudad_actual() -> str:
    """
    Lee la ciudad en la que se está trabajando actualmente.
    Si no existe el archivo, retorna la primera ciudad de la lista.
    """
    if os.path.exists(config.ARCHIVO_CIUDAD_ACTUAL):
        try:
            with open(config.ARCHIVO_CIUDAD_ACTUAL, "r", encoding="utf-8") as f:
                ciudad = f.read().strip()
                if ciudad and ciudad in config.CIUDADES_BOLIVIA:
                    return ciudad
        except Exception:
            pass
    return config.CIUDADES_BOLIVIA[0]


def guardar_ciudad_actual(ciudad: str):
    """Guarda la ciudad actual en el archivo de progreso."""
    with open(config.ARCHIVO_CIUDAD_ACTUAL, "w", encoding="utf-8") as f:
        f.write(ciudad)


def obtener_ciudades_completadas() -> set:
    """Retorna el set de ciudades ya completadas (todas las categorías agotadas)."""
    if not os.path.exists(config.ARCHIVO_CIUDADES_COMPLETADAS):
        return set()
    try:
        df = pd.read_csv(config.ARCHIVO_CIUDADES_COMPLETADAS, encoding="utf-8-sig")
        return set(df["Ciudad"].astype(str).str.strip())
    except Exception:
        return set()


def marcar_ciudad_completada(ciudad: str):
    """Marca una ciudad como completada (todas las categorías agotadas)."""
    completadas = []
    if os.path.exists(config.ARCHIVO_CIUDADES_COMPLETADAS):
        try:
            completadas = pd.read_csv(
                config.ARCHIVO_CIUDADES_COMPLETADAS, encoding="utf-8-sig"
            ).to_dict("records")
        except Exception:
            pass

    completadas.append({
        "Ciudad": ciudad,
        "Fecha_Completada": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    df = pd.DataFrame(completadas)
    df.drop_duplicates(subset=["Ciudad"], keep="first", inplace=True)
    df.to_csv(config.ARCHIVO_CIUDADES_COMPLETADAS, index=False, encoding="utf-8-sig")
    console.print(f"[green]✅ Ciudad '{ciudad}' marcada como COMPLETADA[/green]")


def avanzar_a_siguiente_ciudad() -> str | None:
    """
    Avanza a la siguiente ciudad no completada.
    Resetea las categorías buscadas para la nueva ciudad.
    Retorna la nueva ciudad o None si TODAS están completadas.
    """
    completadas = obtener_ciudades_completadas()

    for ciudad in config.CIUDADES_BOLIVIA:
        if ciudad not in completadas:
            guardar_ciudad_actual(ciudad)
            resetear_categorias_buscadas()
            console.print(f"[bold cyan]🏙️  Avanzando a: {ciudad}[/bold cyan]")
            return ciudad

    console.print("[bold green]🎉 TODAS LAS CIUDADES DE BOLIVIA COMPLETADAS[/bold green]")
    return None


def resetear_categorias_buscadas():
    """Borra el archivo de categorías buscadas (se reinicia para la nueva ciudad)."""
    if os.path.exists(config.ARCHIVO_CATEGORIAS_BUSCADAS):
        os.remove(config.ARCHIVO_CATEGORIAS_BUSCADAS)
        console.print("[cyan]🔄 Categorías reiniciadas para nueva ciudad[/cyan]")
