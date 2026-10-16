"""
Validación estructurada y resiliencia en cadenas

Resumir
En la ingeniería de software tradicional, los contratos de datos (como una especificación OpenAPI o una interfaz de TypeScript) aseguran que dos sistemas se comuniquen sin errores de formato. En el mundo de la IA, este principio es aún más crítico: los LLMs son probabilísticos y su salida natural es texto libre, lo cual es veneno para la escalabilidad.

Esta unidad se centra en transformar la "magia" de las respuestas de texto en sistemas predecibles y resilientes mediante dos pilares: la validación estricta de esquemas y el manejo proactivo de errores.



1. El Contrato de Datos: Salidas Estructuradas
Cuando un LLM responde en lenguaje natural, corres el riesgo de que cambie el formato de la respuesta, alucine con claves JSON o devuelva tipos de datos incorrectos (como un string donde esperabas un número).

¿Por qué Pydantic?
Pydantic es la librería de validación de datos estándar en Python moderno. Al integrarla con LangChain, definimos un esquema formal que el modelo está obligado a seguir.

Validación Sintáctica: El JSON es íntegro y parseable.
Validación Estructural: Todos los campos requeridos están presentes.
Validación Semántica: Los valores cumplen reglas de negocio (ej. un valor de confianza debe estar entre 0 y 1).
El método with_structured_output
LangChain abstrae la complejidad de parsear manualmente las salidas mediante este método. Por debajo, utiliza técnicas como el Tool Calling o JSON Mode de los proveedores (OpenAI, Anthropic) para garantizar que el modelo "encaje" su pensamiento en tu molde.

2. Resiliencia: Manejo de Errores y Reintentos
Un sistema de IA en producción no solo debe ser correcto, debe ser robusto. Las llamadas a modelos pueden fallar por:

Errores Transitorios: Caídas de red, latencia o límites de tasa (429 Rate Limit).
Errores de Formato: El modelo no pudo seguir exactamente el esquema Pydantic.
Estrategias de Recuperación
En lugar de dejar que el sistema falle y devuelva un error al usuario, implementamos:

Retries con Backoff Exponencial: Si falla, esperamos un poco más antes de intentar de nuevo. Esto evita saturar el servicio y permite que fallos momentáneos se resuelvan solos.
Fallbacks: Si un modelo (ej. GPT-4o) falla repetidamente, podemos redirigir la carga a un modelo más ligero o a una respuesta predefinida.
Errores Comunes de Arquitectura
Confiar ciegamente en el JSON del modelo: Nunca asumas que un json.loads funcionará. Usa siempre un validador de esquema.
Reintentar errores permanentes: Si el prompt tiene un error lógico que causa rechazo, reintentar 10 veces solo desperdicia dinero y latencia. Diferencia entre errores de transporte (red) y errores de lógica.
En el siguiente ejercicio, aplicarás estos conceptos para convertir una cadena frágil en un pipeline de grado producción
"""

import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# TODO 1: Define la clase Pydantic 'EntityExtraction' 
# Debe tener: topic (str), entities (Lista de str), y sentiment_score (float entre 0 y 1)
class EntityExtraction(BaseModel):
    pass

async def run_validated_chain(text: str):
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # TODO 2: Configura el modelo para usar la salida estructurada con Pydantic
    # Tip: Usa el método .with_structured_output()
    structured_llm = None 
    
    # TODO 3: Agrega una estrategia de reintento con .with_retry() 
    # para que sea resiliente ante fallos de conexión (máximo 3 intentos).
    resilient_llm = None
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analiza el texto y extrae las entidades."),
        ("human", "{input}")
    ])
    
    # TODO 4: Une el prompt con el resilient_llm y ejecuta asíncronamente
    # No olvides manejar excepciones con try/except para capturar fallos de validación
    try:
        pass
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sample_text = "LangGraph es una extensión de LangChain para agentes cíclicos."
    asyncio.run(run_validated_chain(sample_text))
