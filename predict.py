import re  # Sirve para validar expresiones regulares
from pysentimiento import create_analyzer  # Descarga y construye el modelo de procesamiento de lenguaje (machine learning)

print("🔄 Cargando modelos de pysentimiento...")
# Se crea el modelo para que analice la tarea que se le indica y el idioma
emotion_analyzer = create_analyzer(task="emotion", lang="es")
hate_analyzer = create_analyzer(task="hate_speech", lang="es")
print("✅ Modelos cargados correctamente")

ETIQUETAS_TOXICAS = {"hateful", "targeted", "aggressive"}


# ─── Búsqueda de frases con palabra completa ───────────
def contiene_frase(texto: str, lista_frases: list) -> bool:
    for frase in lista_frases:
        # se colca un limite de la palabra el inicio y al final con r \b (r para que pueda leer la \)
        # re.escape neutraliza los caracteres especiales que pueden matar una palabra ej: hola? 
        # El ? convertiria ese caracter anterior como opcional
        if re.search(r"\b" + re.escape(frase) + r"\b", texto):
            # valida la palabra en relación a todo el texto, para ver si encuentra una coincidencia
            # estoy mal - estoy normal
            return True
    return False


# ─── Detector de banderas rojas ────────────────────────
def quitar_tildes(texto: str) -> str:
    # Reemplaza vocales acentuadas por vocales sin tilde para comparar sin importar acentos
    tabla = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    return texto.translate(tabla)


def detectar_banderas_rojas(texto: str) -> list:
    # Convierte a minúsculas y prepara la versión sin tildes para búsqueda flexible
    texto_orig = texto.lower()
    texto_sin_tildes = quitar_tildes(texto_orig)

    categorias = {
        "Culpabilización": [
            "por tu culpa", "me obligas a", "mira lo que me haces hacer", "todo es culpa tuya"
        ],
        "Chantaje emocional": [
            "si me dejas", "sin ti no soy nada", "me voy a hacer daño", "me voy a hacer dano",
            "no me dejes solo", "después de todo lo que hice por ti", "despues de todo lo que hice por ti"
        ],
        "Aislamiento": [
            "no salgas con ellos", "tus amigos son malos", "no hables con", "o ellos o yo",
            "no tienes que ver a tu familia"
        ],
        "Amenazas veladas": [
            "vas a ver", "te vas a arrepentir", "ya verás", "ya veras", "no sabes de lo que soy capaz"
        ],
        "Control": [
            "dime dónde estás", "dime donde estas", "envíame tu ubicación", "enviame tu ubicacion",
            "muéstrame tu celular", "muestrame tu celular", "pásame tu clave", "pasame tu clave"
        ],
    }

    detectadas = []
    # Revisa cada categoría y agrega el nombre de la bandera si encuentra coincidencias con o sin tildes
    for categoria, frases in categorias.items():
        frases_sin_tildes = [quitar_tildes(f) for f in frases]
        if contiene_frase(texto_orig, frases) or contiene_frase(texto_sin_tildes, frases_sin_tildes):
            detectadas.append(categoria)

    return detectadas


# ─── Intención (reglas) ────────────────────────────────
def detectar_intencion(texto: str) -> str:
    texto = texto.lower()

    if contiene_frase(texto, ["te quiero", "te amo", "me gustas", "te extraño", "te necesito", "te adoro"]):
        return "afecto"
    elif contiene_frase(texto, ["por qué no respondes", "me ignoras", "no contestas", "por qué tardas", "no me escribes"]):
        return "reclamo"
    elif contiene_frase(texto, ["con quién", "quién es", "te veo con", "andabas con", "quién te escribió"]):
        return "celos"
    elif contiene_frase(texto, ["te odio", "estúpido", "idiota", "imbécil", "estúpida", "mierda", "qué asco"]):
        return "agresion"
    elif contiene_frase(texto, ["terminar", "quiero dejarte", "voy a dejarte", "no quiero seguir", "se acabó", "hasta aquí", "se terminó"]):
        return "ruptura"
    elif contiene_frase(texto, ["si me quisieras", "deberías", "nunca haces", "siempre igual", "como siempre"]):
        return "manipulacion"
    elif contiene_frase(texto, ["dónde estás", "con quién hablas", "dime la verdad", "ubicación", "envía ubicación"]):
        return "control"
    elif contiene_frase(texto, ["todavía me quieres", "soy suficiente", "me vas a dejar", "ya no me quieres"]):
        return "inseguridad"
    elif contiene_frase(texto, ["ok", "vale", "como digas", "da igual", "me da igual", "jaja"]):
        return "desinteres"
    elif contiene_frase(texto, ["qué tal", "cómo estás", "qué haces", "cómo te va", "en qué andas", "qué cuentas"]):
        return "curiosidad"
    elif contiene_frase(texto, ["triste", "deprimido", "me siento mal", "me siento solo", "me siento sola", "soledad", "llorar"]):
        return "tristeza"
    else:
        return "normal"


# ─── Ghosting ──────────────────────────────────────────
def calcular_ghosting(texto: str, intencion: str, emocion: str) -> int:
    score = 0
    # El strip quita espacios al inicio y al final
    texto = texto.lower().strip()

    if len(texto) <= 5:
        score += 35
    if len(texto.split()) == 1:
        score += 25
    if contiene_frase(texto, ["ok", "vale", "luego", "ocupado", "ahora no", "después", "mañana"]):
        score += 30

    if intencion == "desinteres":
        score += 35
    elif intencion == "reclamo":
        score += 15
    elif intencion == "afecto":
        score -= 25

    if emocion in ["sadness", "anger", "fear", "disgust"]:
        score += 10
    elif emocion in ["joy", "surprise"]:
        score -= 15

    return max(0, min(score, 95)) #Devuelve el puntaje con un minimo de 0 y tope de 95


# ─── Riesgo ────────────────────────────────────────────
def calcular_riesgo(hate_result, intencion: str, emocion: str) -> str:
    # Convierte las etiquetas en un conjunto y valida si hay una etiqueta toxica
    if set(hate_result.output) & ETIQUETAS_TOXICAS:
        return "🔴 Alto"
    elif intencion in ["celos", "reclamo", "ruptura", "manipulacion", "agresion"]:
        return "🟡 Medio"
    elif emocion in ["anger", "disgust"]:
        return "🟡 Medio"
    return "🟢 Bajo"


# ─── Emociones ─────────────────────────────────────────
def mapear_emocion(emocion_raw: str) -> str:
    # Mapea las emociones en español para compartirlas con el usuario no analiza nada
    emocion_map = {
        "joy": "positivo",
        "sadness": "tristeza",
        "anger": "enojo",
        "surprise": "sorpresa",
        "disgust": "disgusto",
        "fear": "miedo",
        "others": "neutral",
        "neutral": "neutral",
    }

    # Parametriza el neutral para que no devuelva error
    return emocion_map.get(emocion_raw, "neutral")


# ─── Función principal ─────────────────────────────────
# Devuelve 6 valores: emocion, toxicidad, ghosting, riesgo, intencion, confianza
def analizar_texto(texto: str):
    try:
        # El modelo creado al inicio predice la emoción y el odio del texto ingresado
        emocion_pred = emotion_analyzer.predict(texto)
        hate_pred = hate_analyzer.predict(texto)

        # obtiene la emoción en ingles con el .output del modelo
        emocion_raw = emocion_pred.output
        # obtiene la emoción en español al enviarla a la función mapear emoción
        emocion = mapear_emocion(emocion_raw)
        # Entrega un si en toxicidad si hay alguna etiqueta en la salida del hate_pred o de las etiquetas toxicas
        toxicidad = "si" if set(hate_pred.output) & ETIQUETAS_TOXICAS else "no"

        intencion = detectar_intencion(texto)
        ghosting = calcular_ghosting(texto, intencion, emocion_raw)
        riesgo = calcular_riesgo(hate_pred, intencion, emocion_raw)

        # probas es un diccionario que le asigna a cada emoción una probabilidad, el value extrae ese valor, 
        # el max ayuda a devolver el valor maximo de las etiquetas y despues de vuelve un porcentaje *100 
        confianza = int(max(emocion_pred.probas.values()) * 100)

        return emocion, toxicidad, ghosting, riesgo, intencion, confianza

    except Exception as e:
        print(f"Error en analizar_texto: {e}")
        return "neutral", "no", 0, "🟢 Bajo", "normal", 50
