# ============================================================
# config.py — Configuración global del sistema de prospección
# ============================================================

# --- Código de país por defecto (Bolivia = 591) ---
CODIGO_PAIS = "591"

# --- META DIARIA DE MENSAJES ---
# El sistema completará esta cantidad cada vez que se ejecute,
# descontando los que ya se enviaron hoy.
MENSAJES_DIARIOS_META = 50

# --- Cantidad de negocios a buscar por cada categoría ---
CANTIDAD_POR_CATEGORIA = 5

# --- Ciudades de Bolivia (SECUENCIAL: se agota una antes de pasar a la siguiente) ---
# Primero TODO el departamento de Cochabamba, luego otros departamentos.
CIUDADES_BOLIVIA = [
    # ── Departamento de Cochabamba (PRIMERO) ──
    "Cochabamba",
    "Sacaba",
    "Quillacollo",
    "Colcapirhua",
    "Tiquipaya",
    "Vinto",
    "Punata",
    "Cliza",
    # ── Departamento de Santa Cruz ──
    "Santa Cruz de la Sierra",
    "Montero",
    "Warnes",
    "Camiri",
    # ── Departamento de La Paz ──
    "La Paz",
    "El Alto",
    # ── Departamento de Chuquisaca ──
    "Sucre",
    # ── Departamento de Oruro ──
    "Oruro",
    # ── Departamento de Tarija ──
    "Tarija",
    "Yacuiba",
    "Bermejo",
    "Villazón",
    # ── Departamento de Potosí ──
    "Potosí",
    "Tupiza",
    # ── Departamento de Beni ──
    "Trinidad",
    "Riberalta",
    "Guayaramerín",
    # ── Departamento de Pando ──
    "Cobija",
]

# Ciudad actual (se actualiza automáticamente según progreso)
CIUDAD = CIUDADES_BOLIVIA[0]

# Archivos de progreso de ciudades
ARCHIVO_CIUDAD_ACTUAL = "ciudad_actual.txt"
ARCHIVO_CIUDADES_COMPLETADAS = "ciudades_completadas.csv"

# --- Categorías de negocios (PRIORIZADAS) ---
# PRIMERO: Peluquerías, Licorerías y Locales de Comida en TODA BOLIVIA
# DESPUÉS: Resto de negocios
CATEGORIAS_NEGOCIOS = [
    # ═══════════════════════════════════════════════════════════
    # MÁXIMA PRIORIDAD - ESTOS PRIMERO EN TODA BOLIVIA
    # ═══════════════════════════════════════════════════════════
    
    # 1. PELUQUERÍAS Y BARBERÍAS
    "Peluquerías", "Barberías", "Salones de belleza",
    
    # 2. LICORERÍAS
    "Licorerías", "Distribuidoras de bebidas", "Vinotecas",
    
    # 3. LOCALES DE COMIDA
    "Pizzerías", "Hamburgeserías", "Heladerías", "Comida rápida",
    "Restaurantes", "Pollerías", "Churrasquerías", "Salteñerías",
    "Snacks", "Cafeterías", "Juguerías", "Cevicherías",
    "Panaderías", "Pastelerías", "Food trucks", "Açaí",
    "Comida china", "Comida mexicana", "Comida japonesa", "Catering",
    
    # ═══════════════════════════════════════════════════════════
    # PRIORIDAD SECUNDARIA - DESPUÉS DE COMPLETAR LAS ANTERIORES
    # ═══════════════════════════════════════════════════════════
    
    # Belleza y cuidado personal (resto)
    "Spa", "Centros de masajes", "Manicure y pedicure", 
    "Centros de estética", "Depilación", "Tatuajes", "Maquillaje profesional",
    
    # Comercio
    "Tiendas de ropa", "Zapaterías", "Joyerías", "Librerías",
    "Floristerías", "Jugueterías", "Mueblerías", "Electrodomésticos",
    "Ferreterías", "Papelerías", "Minimarkets",
    "Tiendas de celulares", "Tiendas de computadoras", "Ópticas",
    "Tiendas de mascotas", "Tiendas deportivas", "Tiendas de bicicletas",
    "Perfumerías", "Tiendas de cosméticos", "Bazares",
    "Tiendas de telas", "Mercerías",
    
    # Salud
    "Dentistas", "Consultorios médicos", "Clínicas veterinarias",
    "Farmacias", "Fisioterapia", "Nutricionistas",
    "Psicólogos", "Laboratorios clínicos", "Consultorios oftalmológicos",
    
    # Servicios técnicos
    "Talleres mecánicos", "Electricistas", "Plomeros", "Cerrajerías",
    "Carpinterías", "Tornerías", "Vidrerías", "Tapicerías",
    "Reparación de celulares", "Reparación de computadoras",
    "Reparación de electrodomésticos", "Soldaduras", "Pintores",
    "Alarmas y seguridad", "Aire acondicionado",
    
    # Servicios profesionales
    "Abogados", "Contadores", "Arquitectos", "Ingenieros civiles",
    "Notarías", "Consultoras", "Agencias de publicidad",
    "Diseñadores gráficos", "Traductores", "Agentes de seguros",
    
    # Educación
    "Academias", "Escuelas de manejo", "Institutos de idiomas",
    "Guarderías", "Centros de tutorías", "Academias de música",
    "Academias de baile", "Academias de cocina",
    
    # Turismo y hospedaje
    "Hoteles", "Hostales", "Alojamientos", "Agencias de viaje",
    "Rent a car", "Transporte turístico",
    
    # Construcción e inmobiliaria
    "Constructoras", "Inmobiliarias", "Corralones",
    "Pisos y cerámicas", "Pinturerías", "Materiales de construcción",
    
    # Otros servicios
    "Imprentas", "Estudios fotográficos", "Lavanderías",
    "Tintorería", "Fumigación", "Mudanzas", "Limpieza profesional",
    "Decoración de eventos", "Alquiler de salones", "DJ y sonido",
    "Serigrafía", "Bordados", "Sastrería", "Funerarias",
    "Gimnasios", "Centros deportivos", "Yoga", "CrossFit",
    "Estacionamientos", "Lavado de autos", "Autolavados",
]

# --- Archivos de control ---
ARCHIVO_CONTACTADOS = "contactados.csv"
ARCHIVO_HISTORICO = "historico_contactos.csv"
ARCHIVO_CATEGORIAS_BUSCADAS = "categorias_buscadas.csv"

# --- Pausas anti-bloqueo (en segundos) ---
PAUSA_MIN = 3
PAUSA_MAX = 7
PAUSA_SCROLL_MIN = 2
PAUSA_SCROLL_MAX = 4

# --- Límites de seguridad ---
MAX_SCROLLS_SIN_RESULTADOS = 5
TIMEOUT_PAGINA = 60000
TIMEOUT_ELEMENTO = 15000

# --- Plantilla del mensaje personalizado ---
PLANTILLA_MENSAJE = (
    "Estimados *{nombre_negocio}*, un cordial saludo.\n\n"
    "Me pongo en contacto con ustedes tras encontrar su ubicación a través de Google Maps:\n"
    "📍 {link_maps}\n\n"
    "Les contacto para proponerles llevar su negocio al siguiente nivel con una tienda virtual propia o una página web.\n\n"
    "Para que tengan una idea clara, el desarrollo completo se divide en dos partes y estos son los precios base:\n\n"
    "📱 *1. La página para sus clientes*\n"
    "Es lo que ven sus compradores: el catálogo, información de contacto y la sección para hacer pedidos.\n"
    "*(Costo: 250 a 500 Bs)*\n\n"
    "⚙️ *2. Su panel de administrador*\n"
    "Es su sistema interno para subir productos, gestionar el catálogo y controlar toda la información de la página.\n"
    "*(Costo: 500 a 750 Bs)*\n\n"
    "💡 Si solo están interesados en tener presencia online, pueden adquirir únicamente la página web para que los clientes vean su negocio y su información, sin la necesidad del panel administrador.\n\n"
    "¿Les interesaría que lo charlemos sin compromiso?\n\n"
    "Atentamente,\n"
    "William Lujan Arispe"
)

# --- Archivo de salida ---
ARCHIVO_CSV = "prospectos.csv"
ARCHIVO_EXCEL = "prospectos.xlsx"

# --- User Agent para el navegador ---
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
