# ============================================================
# generador_mensajes.py — Genera mensajes personalizados
#                         y links directos de WhatsApp
# ============================================================

import urllib.parse
from rich.console import Console

import config

console = Console()


def generar_mensaje(nombre_negocio: str, link_maps: str) -> str:
    """
    Genera el mensaje personalizado usando la plantilla de config.py
    
    Args:
        nombre_negocio: Nombre del negocio encontrado.
        link_maps: URL de Google Maps del negocio.
    
    Returns:
        Mensaje de texto personalizado.
    """
    return config.PLANTILLA_MENSAJE.format(
        nombre_negocio=nombre_negocio,
        link_maps=link_maps,
    )


def generar_link_whatsapp(telefono_limpio: str, mensaje: str) -> str:
    """
    Genera un enlace wa.me con el mensaje ya codificado.
    
    Args:
        telefono_limpio: Número solo con dígitos y código de país.
        mensaje: Texto del mensaje (sin codificar).
    
    Returns:
        URL de wa.me lista para abrir.
    """
    mensaje_codificado = urllib.parse.quote(mensaje, safe='')
    return f"https://wa.me/{telefono_limpio}?text={mensaje_codificado}"


def procesar_prospectos(negocios: list[dict]) -> list[dict]:
    """
    Toma la lista de negocios del scraper y le agrega:
    - Mensaje personalizado
    - Link directo de WhatsApp
    - Estado = 'Pendiente'
    
    Args:
        negocios: Lista de diccionarios del scraper.
    
    Returns:
        Lista enriquecida con mensaje y link de WhatsApp.
    """
    prospectos = []

    console.print("\n[bold cyan]✉️  Generando mensajes personalizados...[/bold cyan]\n")

    for negocio in negocios:
        nombre = negocio.get("nombre", "")
        telefono = negocio.get("telefono_limpio", "")
        link_maps = negocio.get("link_maps", "")

        if not nombre or not telefono:
            continue

        # Generar mensaje
        mensaje = generar_mensaje(nombre, link_maps)

        # Generar link de WhatsApp
        link_wa = generar_link_whatsapp(telefono, mensaje)

        prospecto = {
            "Nombre": nombre,
            "Categoria": negocio.get("categoria", ""),
            "Direccion": negocio.get("direccion", ""),
            "Telefono_Original": negocio.get("telefono_original", ""),
            "Telefono_Limpio": telefono,
            "Link_Maps": link_maps,
            "Mensaje": mensaje,
            "Link_WhatsApp": link_wa,
            "Estado": "Pendiente",
        }

        prospectos.append(prospecto)
        console.print(f"  [green]✓[/green] Mensaje generado para: [bold]{nombre}[/bold]")

    console.print(f"\n[bold green]✅ {len(prospectos)} mensajes generados correctamente.[/bold green]\n")
    return prospectos


# --- Para pruebas directas ---
if __name__ == "__main__":
    # Ejemplo de uso
    ejemplo = [{
        "nombre": "Pizzería Don Mario",
        "telefono_original": "+591 70123456",
        "telefono_limpio": "59170123456",
        "categoria": "Pizzería",
        "direccion": "Av. América 123",
        "link_maps": "https://www.google.com/maps/place/Pizzeria+Don+Mario",
        "tiene_web": False,
    }]
    
    resultado = procesar_prospectos(ejemplo)
    for r in resultado:
        console.print(r)
        console.print(f"\n[cyan]Link WhatsApp:[/cyan]\n{r['Link_WhatsApp']}")
