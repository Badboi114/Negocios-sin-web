# ============================================================
# whatsapp_sender.py — Módulo de envío via WhatsApp Web
# ============================================================
# Maneja la vinculación con WhatsApp Web, verifica conexión,
# envía mensajes con pausas inteligentes anti-bloqueo,
# y detecta cuando WhatsApp limita los envíos masivos.
# ============================================================

import time
import random
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from playwright.sync_api import TimeoutError as PwTimeout
from rich.console import Console
from rich.prompt import Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

import config

console = Console()

# Directorio para guardar la sesión de WhatsApp Web
WHATSAPP_SESSION_DIR = os.path.join(os.path.dirname(__file__), "whatsapp_session")

# --- Configuración de pausas anti-bloqueo ---
PAUSA_ENTRE_MENSAJES_MIN = 45    # Segundos mínimo entre mensajes
PAUSA_ENTRE_MENSAJES_MAX = 120   # Segundos máximo entre mensajes
MENSAJES_ANTES_PAUSA_LARGA = 5   # Cada N mensajes, pausa larga
PAUSA_LARGA_MIN = 300            # 5 minutos mínimo de pausa larga
PAUSA_LARGA_MAX = 600            # 10 minutos máximo de pausa larga
MAX_MENSAJES_POR_SESION = 20     # Máximo mensajes por sesión antes de parar
PAUSA_ENTRE_SESIONES = 3600      # 1 hora entre sesiones

# Textos que indican bloqueo o limitación
TEXTOS_BLOQUEO = [
    "temporalmente",
    "temporarily",
    "too many",
    "demasiados",
    "bloqueado",
    "blocked",
    "limit",
    "límite",
    "restricted",
    "restringido",
    "try again later",
    "intenta más tarde",
    "no se pudo enviar",
    "couldn't send",
    "failed to send",
]


def _pausa_humana(minimo: float, maximo: float, motivo: str = ""):
    """Pausa con cuenta regresiva visible."""
    tiempo = random.uniform(minimo, maximo)
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[cyan]⏳ {motivo} Esperando {{task.fields[remaining]}}s...[/cyan]"),
        console=console,
    ) as progress:
        task = progress.add_task("pausa", total=int(tiempo), remaining=int(tiempo))
        for i in range(int(tiempo)):
            time.sleep(1)
            progress.update(task, advance=1, remaining=int(tiempo) - i - 1)


def verificar_vinculacion(page: Page) -> bool:
    """
    Verifica que WhatsApp Web esté correctamente vinculado.
    Busca elementos que indiquen una sesión activa.
    
    Returns:
        True si está vinculado, False si no.
    """
    try:
        # Esperar a que cargue la página
        time.sleep(5)
        
        # Indicadores de que WhatsApp Web está vinculado:
        # 1. El buscador de chats aparece
        # 2. La lista de chats es visible
        # 3. NO hay código QR visible
        
        # Verificar si hay QR (= NO vinculado)
        qr_visible = False
        try:
            qr = page.locator('canvas[aria-label="Scan this QR code to link a device!"]').or_(
                page.locator('div[data-ref]')
            ).or_(
                page.locator('canvas').first
            )
            # Si encontramos el canvas del QR y es visible
            if qr.count() > 0 and qr.first.is_visible():
                qr_visible = True
        except Exception:
            pass
        
        if qr_visible:
            return False
        
        # Verificar si hay elementos de sesión activa
        sesion_activa = False
        selectores_sesion = [
            'div[contenteditable="true"][data-tab="3"]',   # Barra de búsqueda
            '#side',                                         # Panel lateral de chats
            'div[aria-label="Lista de chats"]',
            'div[aria-label="Chat list"]',
            'header',                                        # Header de WhatsApp
            'span[data-icon="search"]',                     # Ícono de búsqueda
            'div[data-tab="1"]',                            # Panel de chats
        ]
        
        for sel in selectores_sesion:
            try:
                el = page.locator(sel)
                if el.count() > 0 and el.first.is_visible():
                    sesion_activa = True
                    break
            except Exception:
                continue
        
        return sesion_activa
        
    except Exception as e:
        console.print(f"[red]Error verificando vinculación: {e}[/red]")
        return False


def detectar_bloqueo(page: Page) -> bool:
    """
    Detecta si WhatsApp ha limitado o bloqueado el envío de mensajes.
    
    Returns:
        True si se detectó un bloqueo/limitación.
    """
    try:
        # Obtener todo el texto visible en la página
        body_text = page.locator('body').inner_text().lower()
        
        for texto in TEXTOS_BLOQUEO:
            if texto.lower() in body_text:
                console.print(f"\n[bold red]🚫 ALERTA: Se detectó posible bloqueo ({texto})[/bold red]")
                return True
        
        # También verificar si aparecen pop-ups de error
        try:
            popups = page.locator('[role="alert"]').or_(
                page.locator('.popup-container')
            ).or_(
                page.locator('[data-animate-modal-popup="true"]')
            )
            if popups.count() > 0:
                popup_text = popups.first.inner_text().lower()
                for texto in TEXTOS_BLOQUEO:
                    if texto.lower() in popup_text:
                        return True
        except Exception:
            pass
            
    except Exception:
        pass
    
    return False


def enviar_mensaje_individual(page: Page, telefono: str, mensaje: str) -> dict:
    """
    Envía un mensaje a un número específico via WhatsApp Web.
    
    Returns:
        Dict con resultado: {'exito': bool, 'motivo': str}
    """
    try:
        import urllib.parse
        
        # Usar la URL directa de WhatsApp Web para abrir chat
        msg_encoded = urllib.parse.quote(mensaje, safe='')
        url = f"https://web.whatsapp.com/send?phone={telefono}&text={msg_encoded}"
        
        page.goto(url, timeout=config.TIMEOUT_PAGINA, wait_until="domcontentloaded")
        time.sleep(8)  # Esperar a que cargue completamente
        
        # Verificar si aparece "Número de teléfono no válido" o similar
        try:
            invalido = page.locator('div:has-text("invalid")').or_(
                page.locator('div:has-text("inválido")')
            ).or_(
                page.locator('div:has-text("no está en WhatsApp")')
            ).or_(
                page.locator('div:has-text("not on WhatsApp")')
            ).or_(
                page.locator('div:has-text("Phone number shared via url is invalid")')
            )
            
            # Buscar el popup/modal de número inválido
            popup = page.locator('div[data-animate-modal-popup="true"]')
            if popup.count() > 0:
                popup_text = popup.inner_text().lower()
                if "invalid" in popup_text or "inválido" in popup_text or "no está" in popup_text:
                    # Cerrar popup si hay botón OK
                    try:
                        ok_btn = popup.locator('div[role="button"]')
                        if ok_btn.count() > 0:
                            ok_btn.first.click()
                    except Exception:
                        pass
                    return {"exito": False, "motivo": "Número no tiene WhatsApp"}
        except Exception:
            pass
        
        # Esperar a que aparezca el campo de texto del chat
        try:
            input_field = page.locator(
                'div[contenteditable="true"][data-tab="10"]'
            ).or_(
                page.locator('div[contenteditable="true"][data-tab="6"]')
            ).or_(
                page.locator('footer div[contenteditable="true"]')
            )
            
            input_field.first.wait_for(state="visible", timeout=20000)
            time.sleep(2)
            
        except PwTimeout:
            # Si no aparece el campo de texto, el número puede no tener WhatsApp
            return {"exito": False, "motivo": "No se pudo abrir el chat (posible número sin WhatsApp)"}
        
        # El mensaje ya debería estar escrito por la URL, solo enviar
        # Buscar y hacer clic en el botón de enviar
        try:
            send_btn = page.locator('button[aria-label="Enviar"]').or_(
                page.locator('button[aria-label="Send"]')
            ).or_(
                page.locator('span[data-icon="send"]')
            )
            
            if send_btn.count() > 0:
                send_btn.first.click()
                time.sleep(3)
                return {"exito": True, "motivo": "Enviado correctamente"}
            else:
                # Intentar enviar con Enter
                input_field.first.press("Enter")
                time.sleep(3)
                return {"exito": True, "motivo": "Enviado (Enter)"}
                
        except Exception as e:
            return {"exito": False, "motivo": f"Error al hacer clic en enviar: {e}"}
        
    except PwTimeout:
        return {"exito": False, "motivo": "Timeout al cargar WhatsApp Web"}
    except Exception as e:
        return {"exito": False, "motivo": f"Error inesperado: {e}"}


def iniciar_envio_masivo(prospectos: list[dict]) -> list[dict]:
    """
    Función principal que maneja todo el flujo de envío masivo:
    1. Abre WhatsApp Web
    2. Pide vinculación con QR
    3. Verifica conexión
    4. Envía mensajes con pausas inteligentes
    5. Detecta bloqueos y se pausa automáticamente
    
    Args:
        prospectos: Lista de diccionarios con los prospectos.
    
    Returns:
        Lista actualizada con el estado de cada envío.
    """
    if not prospectos:
        console.print("[yellow]⚠ No hay prospectos para enviar.[/yellow]")
        return prospectos

    pendientes = [p for p in prospectos if p.get("Estado") == "Pendiente"]
    if not pendientes:
        console.print("[yellow]⚠ Todos los prospectos ya fueron procesados.[/yellow]")
        return prospectos

    console.print(Panel(
        "[bold yellow]⚠️  IMPORTANTE — ANTES DE CONTINUAR[/bold yellow]\n\n"
        "Este módulo enviará mensajes por WhatsApp Web.\n"
        "Se abrirá un navegador con WhatsApp Web y necesitarás:\n\n"
        "1. 📱 Escanear el código QR con tu teléfono\n"
        "2. ⏳ Esperar a que se vincule completamente\n"
        "3. ✅ Confirmar que ves tus chats\n\n"
        f"[cyan]Se enviarán máximo {MAX_MENSAJES_POR_SESION} mensajes por sesión.[/cyan]\n"
        f"[cyan]Pausa entre mensajes: {PAUSA_ENTRE_MENSAJES_MIN}-{PAUSA_ENTRE_MENSAJES_MAX} segundos.[/cyan]\n"
        f"[cyan]Pausa larga cada {MENSAJES_ANTES_PAUSA_LARGA} mensajes: "
        f"{PAUSA_LARGA_MIN//60}-{PAUSA_LARGA_MAX//60} minutos.[/cyan]\n\n"
        f"[bold]Prospectos pendientes: {len(pendientes)}[/bold]",
        title="WhatsApp Web — Envío de Mensajes",
        border_style="yellow",
    ))

    if not Confirm.ask("\n¿Deseas continuar con el envío?"):
        console.print("[yellow]Envío cancelado.[/yellow]")
        return prospectos

    # Preguntar cuántos enviar esta sesión
    max_esta_sesion = IntPrompt.ask(
        f"\n¿Cuántos mensajes enviar esta sesión? (Recomendado máx {MAX_MENSAJES_POR_SESION})",
        default=min(MAX_MENSAJES_POR_SESION, len(pendientes))
    )
    max_esta_sesion = min(max_esta_sesion, len(pendientes))

    with sync_playwright() as pw:
        # Lanzar navegador con sesión persistente
        console.print("\n[cyan]🌐 Abriendo WhatsApp Web...[/cyan]\n")
        
        # Crear directorio de sesión si no existe
        os.makedirs(WHATSAPP_SESSION_DIR, exist_ok=True)
        
        context: BrowserContext = pw.chromium.launch_persistent_context(
            WHATSAPP_SESSION_DIR,
            headless=False,
            viewport={"width": 1366, "height": 768},
            user_agent=config.USER_AGENT,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        
        try:
            # 1. Navegar a WhatsApp Web
            page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)
            
            # 2. Esperar vinculación
            console.print(Panel(
                "[bold green]📱 ESCANEA EL CÓDIGO QR[/bold green]\n\n"
                "1. Abre WhatsApp en tu teléfono\n"
                "2. Ve a Configuración > Dispositivos vinculados\n"
                "3. Toca 'Vincular un dispositivo'\n"
                "4. Escanea el código QR que aparece en el navegador\n\n"
                "[dim]Si ya estás vinculado, espera a que carguen tus chats...[/dim]",
                title="Vinculación",
                border_style="green",
            ))
            
            # Esperar hasta que el usuario confirme
            vinculado = False
            intentos_verificacion = 0
            max_intentos = 60  # 5 minutos máximo de espera (cada 5s)
            
            while not vinculado and intentos_verificacion < max_intentos:
                time.sleep(5)
                vinculado = verificar_vinculacion(page)
                intentos_verificacion += 1
                
                if not vinculado and intentos_verificacion % 6 == 0:  # Cada 30s
                    console.print("[yellow]⏳ Esperando vinculación... "
                                  "Escanea el QR si aún no lo has hecho.[/yellow]")
            
            if not vinculado:
                console.print("[red]❌ No se pudo verificar la vinculación después de 5 minutos.[/red]")
                if not Confirm.ask("¿Deseas continuar de todas formas?"):
                    context.close()
                    return prospectos
            
            console.print("\n[bold green]✅ ¡WhatsApp Web vinculado correctamente![/bold green]\n")
            time.sleep(3)
            
            # 3. VERIFICACIÓN FINAL antes de enviar
            console.print("[cyan]🔒 Verificación final de conexión...[/cyan]")
            if not verificar_vinculacion(page):
                console.print("[red]❌ La verificación final falló. WhatsApp Web no parece estar activo.[/red]")
                if not Confirm.ask("¿Continuar de todas formas?"):
                    context.close()
                    return prospectos
            
            console.print("[green]✅ Conexión verificada. Iniciando envío...[/green]\n")
            
            # 4. Enviar mensajes
            enviados = 0
            fallidos = 0
            bloqueado = False
            
            for i, prospecto in enumerate(prospectos):
                if prospecto.get("Estado") != "Pendiente":
                    continue
                    
                if enviados >= max_esta_sesion:
                    console.print(f"\n[yellow]⚠ Se alcanzó el límite de {max_esta_sesion} "
                                  f"mensajes para esta sesión.[/yellow]")
                    break
                
                # Verificar bloqueo
                if detectar_bloqueo(page):
                    bloqueado = True
                    console.print(Panel(
                        "[bold red]🚫 BLOQUEO DETECTADO[/bold red]\n\n"
                        "WhatsApp ha limitado el envío de mensajes.\n"
                        "El sistema se pondrá en PAUSA AUTOMÁTICA.\n\n"
                        f"[cyan]Se reintentará en {PAUSA_ENTRE_SESIONES//60} minutos...[/cyan]\n"
                        f"[dim]Mensajes enviados esta sesión: {enviados}[/dim]\n"
                        f"[dim]Mensajes fallidos: {fallidos}[/dim]",
                        title="⚠️ Pausa de Seguridad",
                        border_style="red",
                    ))
                    
                    _pausa_humana(
                        PAUSA_ENTRE_SESIONES,
                        PAUSA_ENTRE_SESIONES + 600,
                        "Pausa por bloqueo detectado."
                    )
                    
                    # Verificar si se resolvió
                    page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)
                    time.sleep(10)
                    
                    if detectar_bloqueo(page):
                        console.print("[red]❌ El bloqueo persiste. Deteniendo envío.[/red]")
                        break
                    else:
                        console.print("[green]✅ Bloqueo resuelto. Continuando...[/green]")
                        bloqueado = False
                
                nombre = prospecto.get("Nombre", "???")
                telefono = prospecto.get("Telefono_Limpio", "")
                mensaje = prospecto.get("Mensaje", "")
                
                console.print(f"\n[cyan]📤 [{enviados + 1}/{max_esta_sesion}] "
                              f"Enviando a: [bold]{nombre}[/bold] ({telefono})[/cyan]")
                
                # Verificar que WhatsApp sigue vinculado
                if enviados > 0 and enviados % 3 == 0:
                    # Cada 3 mensajes, volver a verificar vinculación
                    page.goto("https://web.whatsapp.com", timeout=config.TIMEOUT_PAGINA)
                    time.sleep(5)
                    if not verificar_vinculacion(page):
                        console.print("[red]❌ WhatsApp Web se desvinculó. Deteniendo envío.[/red]")
                        console.print("[yellow]Vuelve a vincular y ejecuta de nuevo.[/yellow]")
                        break
                
                # Enviar mensaje
                resultado = enviar_mensaje_individual(page, telefono, mensaje)
                
                if resultado["exito"]:
                    prospecto["Estado"] = "Enviado"
                    prospecto["Fecha_Envio"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    enviados += 1
                    console.print(f"  [green]✅ {resultado['motivo']}[/green]")
                else:
                    prospecto["Estado"] = f"Fallido: {resultado['motivo']}"
                    fallidos += 1
                    console.print(f"  [red]❌ {resultado['motivo']}[/red]")
                
                # Pausa entre mensajes
                if enviados < max_esta_sesion:
                    # Pausa larga cada N mensajes
                    if enviados > 0 and enviados % MENSAJES_ANTES_PAUSA_LARGA == 0:
                        console.print(f"\n[yellow]⏸  Pausa de seguridad (cada {MENSAJES_ANTES_PAUSA_LARGA} mensajes)...[/yellow]")
                        _pausa_humana(
                            PAUSA_LARGA_MIN,
                            PAUSA_LARGA_MAX,
                            f"Pausa de seguridad ({PAUSA_LARGA_MIN//60}-{PAUSA_LARGA_MAX//60} min)"
                        )
                    else:
                        # Pausa normal entre mensajes
                        _pausa_humana(
                            PAUSA_ENTRE_MENSAJES_MIN,
                            PAUSA_ENTRE_MENSAJES_MAX,
                            "Pausa entre mensajes"
                        )
        
        # 5. Cerrar sesión de WhatsApp Web de forma segura
            console.print("\n[cyan]🔓 Cerrando sesión de WhatsApp...[/cyan]")
            try:
                page.goto("https://web.whatsapp.com", timeout=10000)
                time.sleep(2)
                try:
                    menu_btn = page.locator('button[title*="Menu"]').or_(
                        page.locator('button[data-testid="headerMenuButton"]')
                    )
                    if menu_btn.count() > 0:
                        menu_btn.first.click()
                        time.sleep(1)
                        logout_opts = page.locator(
                            'text="Cerrar sesión"'
                        ).or_(page.locator('text="Log out"')).or_(
                            page.locator('text="Sign out"')
                        )
                        if logout_opts.count() > 0:
                            logout_opts.first.click()
                            time.sleep(2)
                except Exception:
                    pass
                console.print("[green]✅ Sesión cerrada[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ No se pudo cerrar sesión: {e}[/yellow]")
            
            # 6. Resumen final
            console.print(Panel(
                f"[bold green]📊 RESUMEN DE ENVÍO[/bold green]\n\n"
                f"✅ Enviados: {enviados}\n"
                f"❌ Fallidos: {fallidos}\n"
                f"⏳ Pendientes: {len([p for p in prospectos if p.get('Estado') == 'Pendiente'])}\n"
                f"{'🚫 Se detectó bloqueo durante la sesión' if bloqueado else '✅ Sin bloqueos detectados'}",
                title="Sesión Finalizada",
                border_style="green" if not bloqueado else "yellow",
            ))
            
        except Exception as e:
            console.print(f"[red]❌ Error durante el envío: {e}[/red]")
        finally:
            console.print("\n[cyan]Cerrando navegador...[/cyan]")
            try:
                context.close()
            except Exception:
                pass
