import os # Permite leer las api key y variables de entorno
import random # Permite elegir una variante al azar del texto
import asyncio # Permite ejecutar código pesado sin bloquear el sistema
from dotenv import load_dotenv # Permite leer el archivo de .env
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup # Representa el mensaje y botones interactivos
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
# Construye la aplicación del bot
# Asocia un tipo de mensaje o comando con una función
# Filtros para decidir qué mensajes atiende el handler
# Tipos de contexto de la librería

load_dotenv()  # Carga el .env y debe ir antes de predict y leer variables

from predict import analizar_texto, detectar_banderas_rojas

# ─── Configuración ──────────────────────────────────────

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: Variable TELEGRAM_TOKEN no configurada")
    print("📌 Crea un archivo .env con: TELEGRAM_TOKEN=tu_token_aqui")
    exit(1)

# ─── Datos ──────────────────────────────────────────────

# INTERPRETACIONES: Qué significa el mensaje que te enviaron (Mínimo 8 opciones neutras por intención)
INTERPRETACIONES = {
    "reclamo": [
        "📢 Siente que no recibe atención y pide una respuesta pronto.",
        "😤 Hay frustración porque esperaba una respuesta que no llegó a tiempo.",
        "💢 Percibe que hay descuido o falta de interés en la conversación.",
        "⏳ Siente impaciencia e incomodidad por los tiempos de espera.",
        "🗣️ Manifiesta inconformidad y busca una aclaración directa.",
        "💥 Reacciona ante una expectativa que siente que no se cumplió.",
        "📴 Siente distancia y frialdad en la comunicación reciente.",
        "🗯️ Busca que se reconozca que hubo una falta de atención o respuesta.",
    ],
    "celos": [
        "😒 Siente inseguridad y teme que haya alguien más de por medio.",
        "🔍 Necesita confirmar que este vínculo sigue siendo una prioridad.",
        "🤨 Desconfía de ciertas actividades, planes o compañías.",
        "👁️ Compara su lugar frente al que tienen otras personas.",
        "🧩 Imagina situaciones que aumentan la inquietud y el malestar.",
        "🕵️ Busca detalles o explicaciones para calmar sus dudas.",
        "😟 El temor a la distancia se está transformando en desconfianza.",
        "💬 Necesita certezas sobre el valor del vínculo en este momento.",
    ],
    "agresion": [
        "⚠️ Hay mucha rabia y busca desquitarse mediante palabras hirientes.",
        "🔥 El tono es hostil y la tensión puede subir si hay provocaciones.",
        "💥 Hay agresión verbal que sobrepasa los límites del respeto mutuo.",
        "🛑 Descarga frustración de una forma destructiva y ofensiva.",
        "⚡ Perdió la calma y usa expresiones para intimidar o lastimar.",
        "🥊 Busca una reacción impulsiva para justificar su molestia.",
        "🌪️ Hay un clima de violencia verbal que no se debe normalizar.",
        "🚪 La conversación cruzó un límite inaceptable de respeto y buen trato.",
    ],
    "tristeza": [
        "😢 Atraviesa un momento difícil o de dolor emocional.",
        "🫂 Muestra vulnerabilidad y desearía encontrar apoyo y escucha.",
        "💔 Siente un vacío o desánimo y le cuesta sobrellevar la situación.",
        "🌧️ Hay poca energía emocional para continuar con la rutina del día.",
        "🕯️ Comparte su tristeza esperando comprensión y cero juicios.",
        "🥀 Pasa por una situación pesada que cuesta procesar en silencio.",
        "🧸 Busca un espacio cálido sin tener que fingir bienestar.",
        "🪟 Siente sobrecarga emocional y necesita desahogo sincero.",
    ],
    "manipulacion": [
        "🎭 Intenta generar culpa para condicionar tus decisiones.",
        "⛓️ Usa reproches para que actúes según sus expectativas.",
        "🎪 Desvía la responsabilidad para no asumir su parte en el asunto.",
        "🧩 Plantea condiciones bajo una apariencia de afecto o compromiso.",
        "🪤 Hace que dudes de tu propio criterio o de tus intenciones.",
        "📉 Apela a la victimización para desarmar tus posturas o límites.",
        "🕸️ Busca crear un compromiso moral por cosas que no te corresponden.",
        "⚠️ Presiona para que cedas terreno mostrando frialdad o reproche.",
    ],
    "control": [
        "🔒 Busca monitorear tus pasos, tus horarios y tus compañías.",
        "👁️ Hay una demanda invasiva sobre tu privacidad e independencia.",
        "📱 Exige justificaciones inmediatas sobre tu tiempo y ubicación.",
        "🧭 Intenta pautar condiciones sobre lo que puedes o no hacer.",
        "🛑 Dificulta que tengas espacios personales fuera de su supervisión.",
        "📋 Considera que tiene derecho a revisar tus actividades cotidianas.",
        "🚧 Cruza la línea entre interés sano y supervisión asfixiante.",
        "⚠️ La insistencia constante refleja un afán de vigilancia y posesión.",
    ],
    "ruptura": [
        "💔 Plantea con seriedad tomar distancia o cerrar este ciclo.",
        "🚪 Hay un desgaste profundo y siente que el vínculo no da para más.",
        "🥀 Considera que los acuerdos ya no funcionan y busca un cierre.",
        "🔚 Expresa firmeza o agotamiento frente a la continuidad de la relación.",
        "📦 Muestra una disposición clara a desvincularse de la dinámica actual.",
        "🕊️ Prioriza el bienestar personal alejándose de una situación que pesa.",
        "⏳ Siente que la etapa compartida llegó a su fin sin vuelta atrás.",
        "❄️ Comunica una despedida pensada más que una reacción del momento.",
    ],
    "desinteres": [
        "😐 Muestra poco entusiasmo por continuar el diálogo.",
        "❄️ Respuestas cortantes que marcan frialdad y distancia deliberada.",
        "📉 No aporta temas ni muestra interés por saber de ti.",
        "🚶 Responde solo por cortesía o compromiso, sin implicación.",
        "⏳ Da respuestas breves que indican preferencia por hacer otra cosa.",
        "📴 La falta de reciprocidad sugiere que su atención está en otro lado.",
        "🛑 No hay iniciativa para profundizar ni sostener la charla.",
        "💨 Ofrece lo mínimo para concluir la interacción con rapidez.",
    ],
    "inseguridad": [
        "😟 Duda del valor del vínculo y teme que haya un cambio repentino.",
        "🤔 Busca confirmación constante por temor al rechazo o distanciamiento.",
        "🌀 La ansiedad le lleva a sobredimensionar detalles cotidianos.",
        "💭 Necesita validar que el cariño y el interés siguen vigentes.",
        "🪞 Le cuesta confiar en su propio valor dentro de esta relación.",
        "❓ Hace preguntas con timidez buscando calmar una inquietud interna.",
        "🍃 Teme no dar la talla y proyecta ese miedo en sus mensajes.",
        "🩹 Intenta asegurarse de que el lazo se mantiene firme y seguro.",
    ],
    "afecto": [
        "💕 Envía un mensaje lleno de calidez y aprecio genuino.",
        "🤗 Busca estrechar el vínculo y recordarte el valor que tienes.",
        "🌸 Expresa ternura y gratitud por compartir momentos en común.",
        "✨ Hay afecto sincero y ganas de conectar desde la cercanía.",
        "💌 Manifiesta simpatía y buenos deseos de forma espontánea.",
        "🥰 Demuestra gusto por compartir tiempo y conversaciones contigo.",
        "🌷 Transmite tranquilidad mediante palabras amables y cariñosas.",
        "💖 Busca alegrar el momento con una muestra sincera de aprecio.",
    ],
    "curiosidad": [
        "🤔 Quiere saber sobre tus planes y cómo marcha tu jornada.",
        "💬 Muestra interés abierto por conocer tus vivencias y opiniones.",
        "🔍 Busca una excusa agradable para iniciar o continuar la charla.",
        "☕ Le interesa saber de tus actividades para compartir impresiones.",
        "🎒 Desea ponerse al día con tus proyectos y novedades recientes.",
        "💡 Hace preguntas para generar una conversación amena y cercana.",
        "🪁 Intenta retomar contacto y saber qué tal han ido las cosas.",
        "🎯 Demuestra atención hacia ti con preguntas cordiales y directas.",
    ],
    "normal": [
        "💬 Mensaje cotidiano y tranquilo, sin tensión ni intenciones ocultas.",
        "✅ La comunicación fluye con naturalidad sobre temas comunes.",
        "📝 Intercambio práctico enfocado en asuntos puntuales o de coordinación.",
        "☕ El tono es relajado y no requiere interpretaciones complejas.",
        "👌 No hay señales de alarma; todo marcha con normalidad.",
        "🕊️ Conversación estándar orientada a ponerse al día sin presiones.",
        "🌿 Mensaje casual que no genera compromisos ni exigencias.",
        "📌 Comunicación directa y neutral para resolver algo del momento.",
    ],
}

# SUGERENCIAS: Cómo responder al mensaje (Mínimo 8 opciones variadas por intención, con etiquetas de estilo)
SUGERENCIAS = {
    "reclamo": [
        "🗣️ Asertiva: 'Comprendo la molestia por la tardanza, pero había pendientes urgentes. Hablemos con calma.'",
        "🤝 Empática: 'Es comprensible que cause incomodidad esperar tanto. Cuéntame qué pasó.'",
        "🛑 Límite: 'Puedo dar explicaciones de lo sucedido, siempre que la conversación sea con respeto.'",
        "⏰ Práctica: 'No siempre es posible responder al instante. Acordemos mejores momentos para conversar.'",
        "👂 Escucha: 'Noto que esto causó malestar. Conversemos sobre cómo mejorar la comunicación.'",
        "💬 Breve: 'No fue con mala intención. En cuanto termine esta tarea te presto total atención.'",
        "⚖️ Asertiva: 'Entiendo la expectativa de una respuesta rápida, pero también requiero gestionar mis tiempos.'",
        "📌 Firme: 'Podemos revisar lo que incomoda, pero sin presiones ni reproches innecesarios.'",
    ],
    "celos": [
        "🧠 Asertiva: 'No hay motivos para dudar; este vínculo es importante y vale la pena confiar.'",
        "🤝 Empática: 'Veo que este tema genera angustia. Conversemos con franqueza para despejar dudas.'",
        "🛑 Límite: 'Hay aprecio y respeto, pero no es sano justificar cada conversación o salida.'",
        "🔐 Reafirmación: 'Este lazo tiene mucho valor; no permitamos que las suposiciones lo desgasten.'",
        "💬 Directa: '¿Qué situación causó esa inquietud? Aclaremos las cosas de una vez.'",
        "⏸️ Espacio: 'Es mejor conversar cuando baje la tensión para no herir susceptibilidades sin necesidad.'",
        "🕊️ Transparencia: 'No hay nada que ocultar, pero la confianza mutua es fundamental para seguir bien.'",
        "⚖️ Firme: 'Puedo ofrecer tranquilidad hoy, pero la desconfianza reiterada desgasta la relación.'",
    ],
    "agresion": [
        "🛑 Límite: 'No voy a permitir insultos ni faltas de respeto. Hasta aquí llega esta conversación.'",
        "🌬️ Enfriar: 'En este tono no hay forma de dialogar; retomamos cuando haya calma.'",
        "🚪 Distancia: 'Pongo una pausa. Si no existe respeto mutuo, no tiene sentido continuar hablando.'",
        "⚖️ Asertiva: 'Se puede entender el enojo, pero de ninguna manera las ofensas. No acepto ese trato.'",
        "📵 Cierre preventivo: 'Dejaré la conversación en pausa para evitar que el conflicto escale.'",
        "🛡️ Firme: 'No tolero malas palabras. Si la comunicación no es serena, no responderé más.'",
        "⛔ Firmeza total: 'Pongo un alto claro. No merezco agresiones y no me prestaré para este intercambio.'",
        "🆘 Ayuda y seguridad: 'Si este conflicto se sale de control o hay riesgo para tu integridad, busca un espacio seguro y contacta a personas de confianza o líneas de ayuda.'",
    ],
    "tristeza": [
        "🫂 Empática: 'Lamento mucho este momento difícil. Cuentas con mi escucha si necesitas desahogo.'",
        "💬 Apoyo: 'No tienes que enfrentar esto a solas; tómate el tiempo que haga falta y aquí estaré.'",
        "🛋️ Presencia suave: '¿Prefieres conversar sobre lo ocurrido o cambiar de tema un rato para despejarte?'",
        "🍵 Compañía: 'No hay necesidad de cargar con todo en silencio. Si ayuda hablar, cuenta con mi apoyo.'",
        "🤍 Validación: 'Es válido sentir desánimo a veces; no hay prisa por sentirse bien de inmediato.'",
        "📞 Escucha: '¿Resulta más cómodo escribir o hacer una llamada corta? Lo que dé mayor tranquilidad.'",
        "🕊️ Respeto: 'Respira con calma y ve paso a paso. No hay que fingir fortaleza todo el tiempo.'",
        "🆘 Red de apoyo y ayuda: 'Si este dolor resulta abrumador o constante, considera acudir a profesionales de salud mental o apoyarte en tu círculo de confianza.'",
    ],
    "manipulacion": [
        "🚩 Asertiva: 'Noto un intento de generar culpa, pero mis decisiones no se basan en el remordimiento.'",
        "🛑 Límite: 'Cualquier petición debe ser directa y transparente, sin condiciones ni reclamos encubiertos.'",
        "⚖️ Firme: 'Hay aprecio, pero la respuesta sigue siendo no y corresponde respetar esa postura.'",
        "🎭 Desarme: 'No pongamos en juego el afecto solo porque no se actúa según lo esperado.'",
        "💬 Directa: 'Asumo mis responsabilidades, pero no aquellas que corresponden a la otra parte.'",
        "🧘 Neutral: 'Se comprende la discrepancia, pero no habrá concesiones ante presiones emocionales.'",
        "🚪 Distancia: 'Este trato no resulta justo; dialoguemos cuando la sinceridad sea mutua.'",
        "🆘 Apoyo externo: 'Si estas dinámicas de chantaje y culpabilización son reiteradas, apóyate en amistades cercanas o asesoría profesional para evaluar el bienestar del vínculo.'",
    ],
    "control": [
        "📱 Límite: 'Hay planes personales en marcha; daré aviso al desocuparme, sin necesidad de reportes.'",
        "🛑 Firme: 'La confianza es el pilar de todo. No es constructivo exigir ubicación ni comprobaciones constantes.'",
        "🤝 Asertiva: 'Compartir detalles es una decisión voluntaria, no una exigencia ni una obligación.'",
        "🧭 Espacio propio: 'Se requieren tiempos y espacios individuales para que la relación sea sana.'",
        "⚖️ Clara: 'Con gusto respondo inquietudes, pero no bajo un régimen de vigilancia o interrogatorio.'",
        "🧘 Calma: 'No hay nada indebido en marcha, pero tampoco caben cuestionamientos sobre cada minuto del día.'",
        "🚪 Frenar insistencia: 'No es viable contestar cada segundo; hablemos luego con más serenidad.'",
        "🆘 Ayuda y seguridad: 'El control constante y la vigilancia no forman parte del afecto sano. Si sientes agobio o temor, busca apoyo en personas de confianza o servicios especializados.'",
    ],
    "ruptura": [
        "💬 Asertiva: 'Si se considera que es el momento de terminar, hablemos en persona con respeto y calma.'",
        "🕊️ Madura: 'Duele la noticia, pero se respeta la determinación. Gracias por la sinceridad.'",
        "⏸️ Pausa: 'El cansancio es evidente en ambas partes; conviene tomar unos días antes de un paso definitivo.'",
        "📦 Cierre: 'Lo mejor es acordar los términos de este distanciamiento con madurez y tranquilidad.'",
        "🛑 Límite: 'Se acepta que el ciclo concluyó; mantengamos a partir de ahora una distancia prudente.'",
        "🌧️ Firme: 'Es una situación difícil, pero no tiene sentido forzar la permanencia de nadie.'",
        "🚶 Enfoque propio: 'Entendido. Tomaré mi propio espacio para procesar la situación y continuar adelante.'",
        "🆘 Apoyo emocional: 'Afrontar un cierre de ciclo puede resultar muy desgastante; busca el respaldo de seres queridos o acompañamiento psicológico durante este proceso.'",
    ],
    "desinteres": [
        "🧐 Indagación: 'Las respuestas se notan distantes. ¿Ocurre algo o es mejor conversar en otro momento?'",
        "💬 Desenganche: 'Parece que hay ocupaciones pendientes; mejor dejamos la charla para cuando haya tiempo.'",
        "⏸️ No insistir: 'Entendido, seguimos hablando luego. ¡Que todo marche bien!'",
        "⚖️ Asertiva: 'Si no hay ganas de conversar hoy, no hay problema; la sinceridad se agradece.'",
        "🕊️ Soltar: 'No hay prisa por contestar ahora. Retomamos en una mejor oportunidad.'",
        "👋 Ligera: 'Listo, te dejo continuar con tus actividades. ¡Un saludo cordial!'",
        "🎯 Claridad: 'Se percibe poco interés en el intercambio; si prefieres no continuar, se comprende sin problema.'",
        "☕ Espacio: 'Dejemos la conversación hasta este punto por hoy. Nos escribimos después.'",
    ],
    "inseguridad": [
        "🔍 Tranquilizadora: 'Todo marcha en orden en este vínculo; no hace falta anticipar escenarios difíciles.'",
        "💬 Reafirmación: 'El aprecio y el compromiso siguen intactos. Puedes tener tranquilidad al respecto.'",
        "🤝 Cercana: 'Conversemos sobre lo que genera inquietud para aclararlo sin angustias.'",
        "🌸 Empática: 'Se valora mucho que compartas lo que sientes; este lazo tiene gran importancia.'",
        "🧘 Con calma: 'Respira con tranquilidad; hablar con sinceridad no pone en riesgo la relación.'",
        "📖 Diálogo: 'Cualquier duda se puede preguntar abiertamente; no hay intención de tomar distancia.'",
        "🤍 Apoyo: 'A veces la mente genera temores infundados, pero aquí hay constancia y presencia.'",
        "⚖️ Asertiva: 'Hay afecto sincero, pero también es necesario confiar mutuamente para construir estabilidad.'",
    ],
    "afecto": [
        "🌸 Afectuosa: '¡Qué mensaje tan grato! Da mucha alegría leerte, va un abrazo muy fuerte ❤️'",
        "💌 Agradecida: 'Muchas gracias por esas palabras tan amables; alegran completamente el día.'",
        "🥰 Reciprocidad: 'El sentimiento es totalmente compartido. Es una fortuna contar con tu cercanía.'",
        "✨ Cercana: '¡Qué alegría coincidir en esta etapa! Se valora muchísimo todo el cariño.'",
        "🎁 Detallista: 'Mensajes así siempre hacen sonreír. Va todo mi aprecio y gratitud.'",
        "💖 Amable: 'Muchas gracias por tanta calidez; este vínculo tiene un valor inmenso.'",
        "🌷 Ternura: 'Qué bonito leer tanto aprecio. Ojalá haya oportunidad de coincidir pronto.'",
        "🤗 Calidez: 'Un gesto muy significativo; cuenta siempre con el mismo respaldo y cariño sincero.'",
    ],
    "curiosidad": [
        "🔍 Entusiasta: '¡Hola! Todo marcha muy bien por aquí. ¿Y qué tal va tu día? Cuéntame.'",
        "💬 Detallada: 'Justo terminando algunas tareas. ¿Qué planes hay para la jornada? Adelante.'",
        "🌟 Dinámica: '¡Qué bueno tener noticias tuyas! Hay varias novedades interesantes para compartir.'",
        "☕ Invitación: 'Todo en orden. ¿Habrá tiempo luego para un café o una llamada y charlar mejor?'",
        "🎒 Cotidiana: 'Por acá bastante productivo el trabajo. ¿Y qué novedades hay de tu lado?'",
        "🎯 Interesada: 'Me alegra el mensaje. Justo recordaba nuestras charlas, ¿en qué proyectos andas?'",
        "💡 Abierta: 'Todo marchando sobre ruedas por fortuna. ¿Qué cosas buenas han pasado últimamente?'",
        "🙌 Amistosa: '¡Hola! Todo excelente. Da gusto que preguntes; cuéntame también cómo va tu semana.'",
    ],
    "normal": [
        "👍 Natural: '¡Hola! Todo muy bien por aquí, ¿y de tu parte cómo marchan las cosas?'",
        "💬 Práctica: 'Recibido, muchas gracias por la información. Quedamos en contacto.'",
        "🌟 Descomplicada: 'Perfecto, la idea suena muy bien. Sigamos coordinando según se necesite.'",
        "☕ Amable: '¡Excelente! Cualquier novedad se comunica por este mismo canal.'",
        "👌 Concisa: 'De acuerdo, todo entendido. Continuamos la charla más adelante.'",
        "🤝 Colaborativa: 'Listo, cuenta con eso. Si surge algo más, avisa con total confianza.'",
        "🌿 Neutral: 'Todo claro por este lado. ¡Que tengas un excelente resto de jornada!'",
        "📌 Concreta: 'Anotado el dato. Se revisa en cuanto sea posible y confirmo.'",
    ],
}

EMOJIS = {
    "reclamo": "😔",
    "celos": "😒",
    "agresion": "⚠️",
    "tristeza": "😢",
    "manipulacion": "🚩",
    "control": "🔒",
    "ruptura": "💔",
    "desinteres": "😶",
    "inseguridad": "😟",
    "afecto": "💕",
    "curiosidad": "🤔",
    "normal": "💬",
}

EMOJIS_EMOCION = {
    "positivo": "😊",
    "tristeza": "😢",
    "enojo": "😠",
    "sorpresa": "😲",
    "disgusto": "😖",
    "miedo": "😨",
    "neutral": "😐",
}

# ─── Funciones auxiliares ───────────────────────────────

def construir_barra(valor: int) -> str:
    # realiza una división que devuelve un entero
    bloques = valor // 10 
    return "█" * bloques + "░" * (10 - bloques)


def obtener_texto(diccionario: dict, clave: str, default: str = "normal", user_data: dict = None, tipo: str = "") -> str:
    # Busca dentro de una lista la intención y devuelve un texto al azar que corresponda a esa intención
    # lanza la opción default si no se envió la intención
    # Evita repetir dos veces seguidas la misma opción al mismo usuario guardando la última en context.user_data
    opciones = diccionario.get(clave, diccionario.get(default, []))
    if not opciones:
        return ""
    if len(opciones) == 1:
        return opciones[0]

    clave_historial = f"ultima_{tipo}_{clave}"
    ultima_opcion = None
    if user_data is not None and isinstance(user_data, dict):
        ultima_opcion = user_data.get(clave_historial)

    candidatas = [op for op in opciones if op != ultima_opcion]
    if not candidatas:
        candidatas = opciones

    elegida = random.choice(candidatas)

    if user_data is not None and isinstance(user_data, dict):
        user_data[clave_historial] = elegida

    return elegida


def obtener_teclado_sugerencia() -> InlineKeyboardMarkup:
    # Retorna un teclado inline con el botón para pedir otra sugerencia
    boton = InlineKeyboardButton("🔄 Otra sugerencia", callback_data="otra_sugerencia")
    return InlineKeyboardMarkup([[boton]])


def formatear_respuesta(datos: dict) -> str:
    # Construye la línea de confianza con advertencia si es menor a 50
    linea_confianza = f"🎯 Confianza: {datos['confianza']}%"
    if datos['confianza'] < 50:
        linea_confianza += " (baja, toma el resultado con cautela)"

    # Línea de banderas rojas solo si se detectó al menos una
    linea_banderas = ""
    if datos.get("banderas_rojas"):
        linea_banderas = f"\n🚩 Banderas rojas: {', '.join(datos['banderas_rojas'])}"

    return (
        f"{datos['emoji_principal']} Análisis del mensaje que te enviaron\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{datos['emoji_emocion']} Emoción detectada: {datos['emocion']}\n"
        f"🚩 Toxicidad: {datos['toxicidad']}\n"
        f"🧠 Intención: {datos['intencion']}\n"
        f"💔 Ghosting: {datos['ghosting_bar']} {datos['ghosting']}%\n"
        f"🔥 Riesgo: {datos['riesgo']}\n"
        f"{linea_confianza}"
        f"{linea_banderas}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 Qué significa:\n{datos['interpretacion']}\n\n"
        f"💬 Cómo responder:\n{datos['sugerencia']}"
    )


# ─── Función auxiliar de análisis y respuesta ───────────

async def analizar_y_responder(update: Update, context: ContextTypes.DEFAULT_TYPE, texto: str):
    # Función auxiliar asíncrona para ejecutar el análisis, armar el diccionario y enviar la respuesta
    try:
        # Asyncio.to_thread permite que el bot no se bloquee mientras responde a otros usuarios
        emocion, toxicidad, ghosting, riesgo, intencion, confianza = (
            await asyncio.to_thread(analizar_texto, texto)
        )

        # Se llama a detectar_banderas_rojas por separado
        banderas_detectadas = detectar_banderas_rojas(texto)

        user_data = context.user_data if context else None

        interpretacion = obtener_texto(
            INTERPRETACIONES, intencion, default="normal",
            user_data=user_data, tipo="interpretacion"
        )
        sugerencia = obtener_texto(
            SUGERENCIAS, intencion, default="normal",
            user_data=user_data, tipo="sugerencia"
        )

        datos = {
            # Busca los emojis de intención y emoción si no existe trae lo que tiene al lado
            "emoji_principal": EMOJIS.get(intencion, "💬"),
            "emoji_emocion": EMOJIS_EMOCION.get(emocion, "😐"),
            # Pasa la primera letra mayúscula de la emoción
            "emocion": emocion.capitalize(),
            "toxicidad": "🔴 Alta" if toxicidad == "si" else "🟢 Baja",
            # Pasa la primera letra mayúscula de la intención
            "intencion": intencion.capitalize(),
            "intencion_clave": intencion,
            "ghosting": ghosting,
            "ghosting_bar": construir_barra(ghosting),
            "riesgo": riesgo,
            "confianza": confianza,
            "banderas_rojas": banderas_detectadas,
            "interpretacion": interpretacion,
            "sugerencia": sugerencia,
        }

        # Envía una sola respuesta con el análisis y el botón inline adjunto
        mensaje = await update.message.reply_text(
            formatear_respuesta(datos),
            reply_markup=obtener_teclado_sugerencia()
        )

        # Guarda en context.user_data los análisis recientes indexados por message_id (límite de 20)
        if context and context.user_data is not None:
            if "analisis" not in context.user_data:
                context.user_data["analisis"] = {}
            context.user_data["analisis"][mensaje.message_id] = datos

            # Limita a los últimos 20 análisis para que no crezca sin control
            if len(context.user_data["analisis"]) > 20:
                primer_id = next(iter(context.user_data["analisis"]))
                del context.user_data["analisis"][primer_id]

    except Exception as e:
        print(f"❌ Error en analizar_y_responder: {e}")
        await update.message.reply_text("⚠️ Ocurrió un error al procesar el mensaje.")


# ─── Handlers ───────────────────────────────────────────

# Handler del comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👋 ¡Hola! Te doy la bienvenida al bot de análisis de mensajes.\n\n"
        "📌 Mi función es ayudarte a analizar los mensajes que TE ENVÍAN en tus conversaciones "
        "y sugerirte formas útiles y asertivas de responder.\n\n"
        "💬 Para comenzar, solo envíame o pega aquí cualquier mensaje que hayas recibido "
        "y te daré un análisis detallado al instante.\n\n"
        "Escribe /ayuda si quieres conocer qué significa cada métrica del análisis."
    )
    await update.message.reply_text(mensaje)


# Handler del comando /ayuda
async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "ℹ️ Guía de uso y significado del análisis\n\n"
        "📱 ¿Cómo usar el bot?\n"
        "Solo copia y pega aquí el mensaje que recibiste de otra persona. "
        "El bot lo procesará y te dará sugerencias sobre cómo responder.\n\n"
        "📊 ¿Qué significa cada parte del resultado?\n"
        "• Emoción detectada: El estado anímico predominante en el texto (positivo, tristeza, enojo, etc.).\n"
        "• Toxicidad: Detecta lenguaje ofensivo, agresivo o de odio.\n"
        "• Intención: El propósito detrás del mensaje (afecto, reclamo, celos, desinterés, etc.).\n"
        "• Ghosting: Nivel de probabilidad de desinterés o de que la conversación se corte.\n"
        "• Riesgo: Nivel general de tensión o conflicto potencial en la interacción.\n"
        "• Confianza: Certeza del modelo predictivo en la emoción clasificada.\n"
        "• Banderas rojas: Señales de alerta temprana sobre dinámicas dañinas (si se detectan).\n"
        "• Qué significa: Explicación de la intención detectada.\n"
        "• Cómo responder: Sugerencia de respuesta (puedes pedir otra con el botón).\n\n"
    )
    await update.message.reply_text(mensaje)


# Handler para mensajes de texto
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Si no hay mensaje o mensaje sin texto no devuelve nada
    if not update.message or not update.message.text:
        return
    await analizar_y_responder(update, context, update.message.text)


# Handler para el botón inline "Otra sugerencia"
async def boton_otra_sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    # Llama a query.answer() siempre
    await query.answer()

    message_id = query.message.message_id if query.message else None
    analisis_dict = context.user_data.get("analisis", {}) if context.user_data else {}

    # Si los datos ya no existen (bot reiniciado o análisis muy antiguo), responde con alerta
    if not message_id or message_id not in analisis_dict:
        await query.answer("Este análisis ya no está disponible, envía el mensaje de nuevo.", show_alert=True)
        return

    datos = analisis_dict[message_id]
    intencion = datos.get("intencion_clave", datos.get("intencion", "").lower())

    sugerencia_actual = datos.get("sugerencia")
    opciones = SUGERENCIAS.get(intencion, SUGERENCIAS.get("normal", []))

    # Elige otra sugerencia de la misma intención distinta a la actual
    candidatas = [op for op in opciones if op != sugerencia_actual]
    if not candidatas:
        candidatas = opciones

    nueva_sugerencia = random.choice(candidatas)
    datos["sugerencia"] = nueva_sugerencia

    # Actualiza en user_data la última sugerencia usada
    if context.user_data is not None:
        context.user_data[f"ultima_sugerencia_{intencion}"] = nueva_sugerencia

    try:
        # Edita el mensaje con la nueva sugerencia y mantiene el botón
        await query.edit_message_text(
            formatear_respuesta(datos),
            reply_markup=obtener_teclado_sugerencia()
        )
    except Exception as e:
        # Captura el error si el mensaje no fue modificado para no romper el bot
        if "Message is not modified" in str(e):
            pass
        else:
            print(f"❌ Error al editar mensaje: {e}")


# ─── Inicialización ─────────────────────────────────────

def main():
    print("🤖 Bot de análisis de mensajes activo...")
    print("📌 Analizo los mensajes que TE ENVÍAN y te digo cómo responder")

    # Configura y construye la aplicación con el token
    # CAMBIO: concurrent_updates(True) procesa los mensajes de varios usuarios al mismo tiempo
    # (junto con to_thread evita que un usuario haga esperar a los demás)
    app = ApplicationBuilder().token(TOKEN).concurrent_updates(True).build()

    # Comandos de bienvenida y ayuda
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))

    # Handler para el callback del botón "Otra sugerencia"
    app.add_handler(CallbackQueryHandler(boton_otra_sugerencia, pattern="^otra_sugerencia$"))

    # Registra un control donde se configura el bot para que lea mensajes de texto y no comandos
    # y llama a responder
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("🟢 Bot corriendo... Esperando mensajes")
    app.run_polling()


# Ejecuta el sistema solo si se corre directamente este archivo
if __name__ == "__main__":
    main()