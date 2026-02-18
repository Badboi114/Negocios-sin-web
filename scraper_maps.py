# ============================================================
# scraper_maps.py — Módulo de scraping de Google Maps
# ============================================================
# Usa Playwright para navegar Google Maps, buscar negocios,
# extraer su información y filtrar los que NO tienen sitio web.
# ============================================================

import time
import random
import re
from typing import Optional
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PwTimeout
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

import config

console = Console()


def _pausa(minimo: float = None, maximo: float = None):
    """Pausa aleatoria para simular comportamiento humano."""
    mn = minimo or config.PAUSA_MIN
    mx = maximo or config.PAUSA_MAX
    tiempo = random.uniform(mn, mx)
    time.sleep(tiempo)


def _limpiar_texto(texto: str) -> str:
    """Limpia espacios extra y caracteres no deseados."""
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()


def _extraer_telefono_limpio(telefono: str) -> str:
    """
    Limpia un número telefónico: quita espacios, guiones, paréntesis.
    Devuelve solo dígitos con código de país.
    """
    if not telefono:
        return ""
    # Quitar todo lo que no sea dígito o +
    limpio = re.sub(r'[^\d+]', '', telefono)
    # Si empieza con +, quitar el +
    if limpio.startswith('+'):
        limpio = limpio[1:]
    # Si NO empieza con código de país, agregarlo
    if not limpio.startswith(config.CODIGO_PAIS):
        # Si empieza con 0, quitarlo
        if limpio.startswith('0'):
            limpio = limpio[1:]
        limpio = config.CODIGO_PAIS + limpio
    return limpio


def _scroll_resultados(page: Page):
    """Hace scroll en el panel de resultados de Google Maps."""
    try:
        # El contenedor de resultados en Google Maps
        panel = page.locator('div[role="feed"]')
        if panel.count() > 0:
            panel.evaluate(
                'el => el.scrollTop = el.scrollHeight'
            )
        else:
            # Alternativa: buscar el panel scrolleable
            page.mouse.wheel(0, 800)
    except Exception:
        page.mouse.wheel(0, 800)


def _obtener_urls_negocios(page: Page, cantidad_deseada: int) -> list[str]:
    """
    Hace scroll en los resultados de Maps hasta obtener
    la cantidad deseada de URLs de negocios.
    """
    urls_encontradas = set()
    scrolls_sin_nuevos = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Buscando negocios..."),
        BarColumn(),
        TextColumn("[green]{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scrolling", total=cantidad_deseada)

        while len(urls_encontradas) < cantidad_deseada:
            # Obtener todos los links de negocios visibles
            links = page.locator('a[href*="/maps/place/"]').all()
            cantidad_anterior = len(urls_encontradas)

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and '/maps/place/' in href and href not in urls_encontradas:
                        urls_encontradas.add(href)
                        progress.update(task, completed=min(len(urls_encontradas), cantidad_deseada))
                        if len(urls_encontradas) >= cantidad_deseada:
                            break
                except Exception:
                    continue

            # Verificar si encontramos nuevos resultados
            if len(urls_encontradas) == cantidad_anterior:
                scrolls_sin_nuevos += 1
                if scrolls_sin_nuevos >= config.MAX_SCROLLS_SIN_RESULTADOS:
                    console.print(
                        f"\n[yellow]⚠ No se encontraron más resultados después de "
                        f"{scrolls_sin_nuevos} intentos. "
                        f"Se obtuvieron {len(urls_encontradas)} de {cantidad_deseada}.[/yellow]"
                    )
                    break
            else:
                scrolls_sin_nuevos = 0

            # Scroll para cargar más
            _scroll_resultados(page)
            _pausa(config.PAUSA_SCROLL_MIN, config.PAUSA_SCROLL_MAX)

            # Verificar si llegamos al final de resultados
            try:
                fin = page.locator('text="No hay más resultados"').or_(
                    page.locator('text="Has llegado al final de la lista"')
                ).or_(
                    page.locator('span.HlvSq')  # "No hay más resultados" en Maps
                )
                if fin.count() > 0:
                    console.print("\n[yellow]⚠ Se alcanzó el final de los resultados.[/yellow]")
                    break
            except Exception:
                pass

    return list(urls_encontradas)[:cantidad_deseada]


def _extraer_info_negocio(page: Page, url: str) -> Optional[dict]:
    """
    Navega a la página de un negocio en Maps y extrae:
    - Nombre
    - Teléfono
    - Si tiene web o no
    - Link de Maps
    """
    try:
        page.goto(url, timeout=config.TIMEOUT_PAGINA, wait_until="domcontentloaded")
        _pausa(2, 4)

        # --- NOMBRE del negocio ---
        nombre = ""
        try:
            # Selector principal del nombre
            nombre_el = page.locator('h1.DUwDvf').first
            if nombre_el.count() > 0:
                nombre = _limpiar_texto(nombre_el.inner_text())
            else:
                # Alternativa
                nombre_el = page.locator('h1').first
                nombre = _limpiar_texto(nombre_el.inner_text())
        except Exception:
            nombre = "Negocio sin nombre"

        if not nombre:
            return None

        # --- Verificar si TIENE SITIO WEB (si tiene, lo descartamos) ---
        tiene_web = False
        try:
            # Buscar botón/link de sitio web en la ficha
            web_selectors = [
                'a[data-item-id="authority"]',
                'a[aria-label*="Sitio web"]',
                'a[aria-label*="sitio web"]',
                'a[aria-label*="Website"]',
                'a[aria-label*="website"]',
                'button[data-item-id="authority"]',
                'a[data-tooltip="Abrir sitio web"]',
                'a[data-tooltip="Open website"]',
            ]
            for sel in web_selectors:
                if page.locator(sel).count() > 0:
                    tiene_web = True
                    break
        except Exception:
            pass

        if tiene_web:
            console.print(f"  [dim]✗ {nombre} — YA tiene sitio web. Ignorado.[/dim]")
            return None

        # --- TELÉFONO ---
        telefono = ""
        try:
            tel_selectors = [
                'button[data-item-id^="phone:"] .Io6YTe',
                'button[data-item-id^="phone:"]',
                'a[data-item-id^="phone:"]',
                'button[aria-label*="Teléfono"]',
                'button[aria-label*="Phone"]',
                '[data-tooltip="Copiar número de teléfono"]',
                '[data-tooltip="Copy phone number"]',
            ]
            for sel in tel_selectors:
                el = page.locator(sel).first
                if el.count() > 0:
                    # Intentar obtener el aria-label que contiene el número
                    aria = el.get_attribute('aria-label')
                    if aria:
                        # Extraer números del aria-label
                        numeros = re.findall(r'[\d\s\-\+\(\)]+', aria)
                        if numeros:
                            telefono = max(numeros, key=len).strip()
                            break
                    # Si no, intentar inner_text
                    txt = el.inner_text()
                    if txt and re.search(r'\d', txt):
                        telefono = _limpiar_texto(txt)
                        break
                    # Último intento: data-item-id
                    data_id = el.get_attribute('data-item-id')
                    if data_id and data_id.startswith('phone:'):
                        telefono = data_id.replace('phone:tel:', '').replace('phone:', '')
                        break
        except Exception:
            pass

        if not telefono:
            console.print(f"  [dim]✗ {nombre} — Sin teléfono. Ignorado.[/dim]")
            return None

        telefono_limpio = _extraer_telefono_limpio(telefono)

        if not telefono_limpio or len(telefono_limpio) < 8:
            console.print(f"  [dim]✗ {nombre} — Teléfono inválido: {telefono}. Ignorado.[/dim]")
            return None

        # --- CATEGORÍA del negocio (opcional pero útil) ---
        categoria = ""
        try:
            cat_el = page.locator('button.DkEaL').first
            if cat_el.count() > 0:
                categoria = _limpiar_texto(cat_el.inner_text())
        except Exception:
            pass

        # --- DIRECCIÓN (opcional) ---
        direccion = ""
        try:
            dir_selectors = [
                'button[data-item-id="address"] .Io6YTe',
                'button[data-item-id="address"]',
                '[data-item-id="address"]',
            ]
            for sel in dir_selectors:
                el = page.locator(sel).first
                if el.count() > 0:
                    aria = el.get_attribute('aria-label')
                    if aria:
                        direccion = _limpiar_texto(aria.replace('Dirección:', '').replace('Address:', ''))
                        break
                    direccion = _limpiar_texto(el.inner_text())
                    break
        except Exception:
            pass

        console.print(f"  [green]✓ {nombre}[/green] — Tel: {telefono_limpio}")

        return {
            "nombre": nombre,
            "telefono_original": telefono,
            "telefono_limpio": telefono_limpio,
            "categoria": categoria,
            "direccion": direccion,
            "link_maps": url,
            "tiene_web": False,
        }

    except PwTimeout:
        console.print(f"  [red]✗ Timeout al cargar: {url[:60]}...[/red]")
        return None
    except Exception as e:
        console.print(f"  [red]✗ Error al extraer datos: {e}[/red]")
        return None


def buscar_negocios(termino: str, cantidad: int) -> list[dict]:
    """
    Función principal de búsqueda.
    Abre Google Maps, busca el término, hace scroll,
    extrae info de cada negocio y filtra los que NO tienen web.
    
    Returns:
        Lista de diccionarios con la información de cada negocio.
    """
    resultados = []

    console.print(f"\n[bold cyan]🔍 Buscando: '{termino}' — Objetivo: {cantidad} negocios sin web[/bold cyan]\n")

    with sync_playwright() as pw:
        # Lanzar navegador (headless=False para ver qué pasa)
        browser: Browser = pw.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=config.USER_AGENT,
            locale='es-ES',
            timezone_id='America/La_Paz',
        )

        # Inyectar script para evitar detección de automatización
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        try:
            # 1. Navegar a Google Maps con la búsqueda
            url_busqueda = f"https://www.google.com/maps/search/{termino.replace(' ', '+')}"
            console.print(f"[cyan]📡 Navegando a Google Maps...[/cyan]")
            page.goto(url_busqueda, timeout=config.TIMEOUT_PAGINA, wait_until="domcontentloaded")
            _pausa(3, 5)

            # Aceptar cookies si aparece el diálogo
            try:
                accept_btn = page.locator('button:has-text("Aceptar todo")').or_(
                    page.locator('button:has-text("Accept all")')
                )
                if accept_btn.count() > 0:
                    accept_btn.first.click()
                    _pausa(1, 2)
            except Exception:
                pass

            # 2. Obtener URLs de negocios haciendo scroll
            console.print("[cyan]📜 Haciendo scroll para cargar resultados...[/cyan]")
            urls = _obtener_urls_negocios(page, cantidad * 3)  # Buscar 3x porque muchos tendrán web
            console.print(f"\n[cyan]📋 Se encontraron {len(urls)} negocios totales para analizar.[/cyan]\n")

            if not urls:
                console.print("[red]❌ No se encontraron resultados para esta búsqueda.[/red]")
                browser.close()
                return []

            # 3. Visitar cada negocio y extraer datos
            console.print("[bold cyan]🔎 Analizando cada negocio...[/bold cyan]\n")
            for i, url in enumerate(urls, 1):
                if len(resultados) >= cantidad:
                    console.print(f"\n[green]✅ Se alcanzó la cantidad deseada: {cantidad} negocios.[/green]")
                    break

                console.print(f"[cyan]  [{i}/{len(urls)}] Analizando...[/cyan]")
                info = _extraer_info_negocio(page, url)

                if info:
                    resultados.append(info)

                # Pausa anti-bloqueo entre cada visita
                _pausa()

        except PwTimeout:
            console.print("[red]❌ Timeout: Google Maps tardó demasiado en cargar.[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error durante la búsqueda: {e}[/red]")
        finally:
            browser.close()

    console.print(f"\n[bold green]📊 Resultado final: {len(resultados)} negocios SIN web encontrados.[/bold green]\n")
    return resultados


# --- Para pruebas directas ---
if __name__ == "__main__":
    resultados = buscar_negocios("Restaurantes en Cochabamba", 5)
    for r in resultados:
        console.print(r)
