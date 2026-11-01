Tool Calling: Definición y Ejecución Segura

En el desarrollo de sistemas de IA, un LLM "desnudo" es como un cerebro brillante en una habitación sin ventanas: puede razonar, pero no puede interactuar con el mundo exterior. El Tool Calling (Invocación de Herramientas) es el mecanismo que le da "manos" a ese cerebro.

¿Qué es Tool Calling?
No es que el modelo ejecute código Python directamente. En su lugar, el modelo genera una solicitud estructurada (usualmente JSON) indicando qué función quiere ejecutar y con qué parámetros. Tu aplicación intercepta esa solicitud, ejecuta el código real, y le devuelve el resultado al modelo.

El "Contrato" de la Herramienta
Para que un modelo como GPT-4 o Claude 3.5 use una herramienta con éxito, necesita un contrato claro. Este contrato tiene cuatro pilares:

Nombre: Identificador único (ej. get_stock_price).
Descripción: Explicación semántica. El LLM decide si usar la herramienta basándose en esto.
Esquema de Entrada (Input Schema): Definición estricta de variables (tipos, obligatoriedad).
Esquema de Salida: Qué esperar de vuelta.
Definición Segura con Pydantic y LangChain
En entornos escalables, no podemos confiar en que el LLM envíe siempre los datos correctos. Usamos Pydantic para validar los tipos antes de que el código toque nuestra infraestructura.

python


from pydantic import BaseModel, Field
from langchain_core.tools import tool
class CalculatorInput(BaseModel):
    a: int = Field(description="Primer número")
    b: int = Field(description="Segundo día")
@tool(args_schema=CalculatorInput)
def multiply(a: int, b: int) -> int:
    """Multiplica dos números enteros."""
    return a * b
El Ciclo de Ejecución (Reason-Act Loop)
Reasoning: El LLM recibe el prompt y las definiciones de herramientas. Decide que necesita multiply.
Tool Call: El LLM responde con un objeto especial: tool_calls: [{name: 'multiply', args: {a: 5, b: 2}}].
Execution (Local): Tu servidor detecta esta intención, valida los argumentos con Pydantic y ejecuta la función multiply(5, 2).
Observation: El resultado (10) se envía de vuelta al LLM en un nuevo mensaje con el rol tool.
Final Response: El LLM procesa el 10 y responde al usuario: "El resultado es 10".
Errores Comunes y Seguridad
Confundir Invocación con Ejecución: El LLM no ejecuta el código. Tu arquitectura debe garantizar que las herramientas tengan permisos limitados (Least Privilege). Nunca permitas que una herramienta ejecute SQL raw generado por el LLM sin validación.
Descripciones Ambiguas: Si tu descripción es "Busca datos", el modelo fallará. Sé específico: "Busca precios de acciones en tiempo real para empresas del S&P 500".
Ignorar Errores: Si la herramienta falla (ej. timeout de API), debes capturar el error y enviarlo como un string al LLM para que este pueda explicarle al usuario qué salió mal o intentar otra estrategia.
En la siguiente práctica, conectarás este concepto con el sistema RAG que construiste anteriormente, permitiendo que tu agente decida cuándo consultar la base de conocimientos.

🛠️ Ejercicio: qué tenés que hacer
Objetivo: definir una herramienta que un agente pueda usar, con un contrato de entrada validado por Pydantic y una descripción clara para que el LLM sepa cuándo llamarla.

Pasos:

Definí SearchInput(BaseModel) con query: str y limit: int = 3. Usá Field(..., description="...") en los dos, y en limit agregá ge=1, le=10.
Decorá la función con @tool(args_schema=SearchInput) y dejala asíncrona (async def).
Reescribí el docstring: qué busca la herramienta, cuándo conviene usarla y qué devuelve. Es la instrucción que lee el LLM.
Dentro de la función, llamá a await db.similarity_search(query, k=limit) dentro de un try. Si falla, devolvé un mensaje de error en lugar de cortar la ejecución.
Para probar (no hace falta ningún LLM): agregá al final del código:

python


import asyncio
print(search_knowledge_base.name, search_knowledge_base.args)
print(asyncio.run(search_knowledge_base.ainvoke({"query": "políticas de vacaciones", "limit": 2})))
Salida esperada: el nombre search_knowledge_base, los argumentos query y limit con sus descripciones, y el resultado ['Resultado para políticas de vacaciones']. Si probás con "limit": 50, tiene que aparecer un error de validación.