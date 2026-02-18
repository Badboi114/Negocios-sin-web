# ============================================================
# exportador.py — Exporta los prospectos a CSV y Excel
# ============================================================

import pandas as pd
from rich.console import Console
from rich.table import Table

import config

console = Console()


def exportar_csv(prospectos: list[dict]) -> str:
    """
    Exporta la lista de prospectos a un archivo CSV.
    
    Returns:
        Ruta del archivo generado.
    """
    if not prospectos:
        console.print("[yellow]⚠ No hay prospectos para exportar.[/yellow]")
        return ""

    df = pd.DataFrame(prospectos)
    
    ruta = config.ARCHIVO_CSV
    df.to_csv(ruta, index=False, encoding='utf-8-sig')
    console.print(f"[green]📁 CSV guardado: {ruta}[/green]")
    return ruta


def exportar_excel(prospectos: list[dict]) -> str:
    """
    Exporta la lista de prospectos a un archivo Excel
    con formato y columnas ajustadas.
    
    Returns:
        Ruta del archivo generado.
    """
    if not prospectos:
        console.print("[yellow]⚠ No hay prospectos para exportar.[/yellow]")
        return ""

    df = pd.DataFrame(prospectos)
    
    ruta = config.ARCHIVO_EXCEL
    
    with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Prospectos')
        
        # Ajustar ancho de columnas
        worksheet = writer.sheets['Prospectos']
        for i, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(col)
            )
            # Limitar ancho máximo a 60 caracteres
            worksheet.column_dimensions[chr(65 + i)].width = min(max_len + 2, 60)

    console.print(f"[green]📁 Excel guardado: {ruta}[/green]")
    return ruta


def mostrar_resumen(prospectos: list[dict]):
    """
    Muestra un resumen bonito en consola con los prospectos.
    """
    if not prospectos:
        return

    table = Table(title="📊 Resumen de Prospectos", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Nombre", style="cyan", min_width=20)
    table.add_column("Teléfono", style="green", min_width=15)
    table.add_column("Categoría", style="yellow", min_width=15)
    table.add_column("Estado", style="magenta", min_width=10)

    for i, p in enumerate(prospectos, 1):
        table.add_row(
            str(i),
            p.get("Nombre", ""),
            p.get("Telefono_Limpio", ""),
            p.get("Categoria", ""),
            p.get("Estado", "Pendiente"),
        )

    console.print(table)


# --- Para pruebas directas ---
if __name__ == "__main__":
    ejemplo = [{
        "Nombre": "Pizzería Don Mario",
        "Categoria": "Pizzería",
        "Direccion": "Av. América 123",
        "Telefono_Original": "+591 70123456",
        "Telefono_Limpio": "59170123456",
        "Link_Maps": "https://maps.google.com/example",
        "Mensaje": "Hola Pizzería Don Mario...",
        "Link_WhatsApp": "https://wa.me/59170123456?text=Hola",
        "Estado": "Pendiente",
    }]
    
    mostrar_resumen(ejemplo)
    exportar_csv(ejemplo)
    exportar_excel(ejemplo)
