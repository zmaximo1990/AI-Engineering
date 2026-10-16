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
from typing import List
import os
from openai import OpenAIError
from pydantic import BaseModel, Field, ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

MODEL = os.getenv("MODEL", "gpt-4o")
TEMPERATURE = os.getenv("TEMPERATURE", 0)

class EntityExtraction(BaseModel):
    topic: str = Field(description="Main topic of the analyzed text")
    entities: List[str] = Field(description="List of entities mentioned in the text")
    sentiment_score: float = Field(
        ge=0,
        le=1,
        description="Sentiment score between 0 (negative) and 1 (positive)",
    )

async def run_validated_chain(text: str):
    primary_llm = (
        ChatOpenAI(model=MODEL, temperature=TEMPERATURE)
        .with_structured_output(EntityExtraction)
        .with_retry(stop_after_attempt=3, wait_exponential_jitter=True)
    )
    fallback_llm = (
        ChatOpenAI(model="gpt-4o-mini", temperature=TEMPERATURE)
        .with_structured_output(EntityExtraction)
        .with_retry(stop_after_attempt=2, wait_exponential_jitter=True)
    )
    resilient_llm = primary_llm.with_fallbacks([fallback_llm])

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Analiza el texto y extrae las entidades."),
        ("human", "{input}")
    ])

    try:
        chain = prompt | resilient_llm
        result = await chain.ainvoke({"input": text})
        print(result)
    except ValidationError as e:
        print(f"Validation error: {e}")
    except OpenAIError as e:
        print(f"OpenAI SDK error: {e}")

if __name__ == "__main__":
    sample_text = "LangGraph es una extensión de LangChain para agentes cíclicos."
    asyncio.run(run_validated_chain(sample_text))
