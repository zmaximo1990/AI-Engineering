Ciclos ReAct y Persistencia de Checkpoints en Agentes Autónomos

Como arquitecto de IA, tu objetivo no es solo que el sistema responda, sino que sea resiliente. En sistemas complejos, un agente puede fallar a mitad de una ejecución de 10 pasos debido a un error de red o un timeout. Sin persistencia, perderías todo el razonamiento y los resultados parciales (y el dinero gastado en tokens).

1. El Ciclo ReAct (Reasoning + Acting)
El patrón ReAct es el estándar de oro para agentes autónomos. A diferencia de una cadena lineal, ReAct permite al LLM:

Pensar (Reason): Analizar la solicitud del usuario y decidir qué necesita.
Actuar (Act): Seleccionar una herramienta y generar los parámetros de llamada.
Observar (Observe): Recibir la salida de la herramienta y re-evaluar el estado.
Este proceso es cíclico. El LLM puede decidir que necesita usar tres herramientas diferentes antes de dar una respuesta final. LangGraph facilita esto permitiendo que una arista (edge) vuelva al mismo nodo o a un nodo anterior, creando un historial de mensajes que crece con cada "observación".

2. Checkpoints: La Caja Negra de tu Agente
En LangGraph, un Checkpointer es un mecanismo de almacenamiento que guarda una "fotografía" del estado del grafo después de cada nodo ejecutado.

Para qué sirve: Si el proceso se detiene, puedes reanudarlo simplemente pasando el mismo thread_id. El sistema buscará en la base de datos (SQLite, Redis o Memoria) y cargará el último estado conocido.
Time Travel: Los checkpoints permiten no solo reanudar, sino "volver atrás" en el tiempo (debugging) o requerir aprobación humana antes de continuar con un nodo crítico (Human-in-the-loop).
Enunciado del Problema
Vas a construir un agente climatológico capaz de razonar si necesita herramientas y que no pierda la memoria incluso si interrumpimos la ejecución del script.

Objetivo:

Implementar un ciclo ReAct completo.
Configurar persistencia en memoria.
Demostrar que el agente recuerda la ubicación mencionada en el primer mensaje al recibir un segundo mensaje, gracias al thread_id.
Restricciones:

Usa Annotated[list[BaseMessage], add_messages] en tu estado para asegurar que los mensajes no se sobrescriban, sino que se concatenen.
El grafo debe terminar solo cuando el LLM decida que no hay más herramientas que llamar.
No olvides que el nodo de herramientas (ToolNode) debe mapear sus resultados de vuelta al agente.
🛠️ Ejercicio: qué tenés que hacer
Objetivo: construir un agente que razone, use una herramienta y recuerde la conversación entre llamadas gracias a un checkpointer.

Qué necesitás: la variable de entorno OPENAI_API_KEY.

Pasos:

tool_node = ToolNode(tools).
model = ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(tools).
En call_model: response = await model.ainvoke(state["messages"]) y return {"messages": [response]}.
Agregá los nodos "agent" (call_model) y "tools" (tool_node), y las aristas START → agent, agent → tools_condition (con add_conditional_edges) y tools → agent.
memory = MemorySaver() y app = workflow.compile(checkpointer=memory).
En main(), ejecutá dos veces await app.ainvoke(...) con el mismo thread_config: primero "¿Qué tiempo hace en Madrid?" y después "¿Y en Londres?". Imprimí el último mensaje de cada respuesta.
Salida esperada: en el paso 1, el agente llama a get_weather y responde con el clima de Madrid. En el paso 2, entiende que "¿Y en Londres?" pregunta por el clima, porque recuerda el paso 1, y vuelve a usar la herramienta. Para comprobar que la memoria funciona, cambiá el thread_id en el paso 2: el agente ya no sabe de qué le estás hablando.