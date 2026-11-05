El Patrón Supervisor: Delegación Dinámica

En sistemas multi-agente, la complejidad crece exponencialmente con cada nuevo "agente" que añadimos. Si conectamos todos con todos (una topología de red), el ruido y la falta de control hacen que el sistema sea impredecible. Aquí es donde entra el Patrón Supervisor.



¿Qué es el Patrón Supervisor?
Imagina una redacción de noticias: tienes reporteros (investigadores) y redactores. No se mandan correos entre ellos de forma caótica; hay un Editor Jefe (el Supervisor) que recibe la noticia, decide quién debe investigar, revisa el borrador y finalmente aprueba la publicación.

En LangGraph, el Supervisor es un nodo central que:

Analiza el estado actual: Lee el historial de mensajes para entender qué se ha hecho.
Toma una decisión de ruteo: Decide qué especialista es el más apto para el siguiente paso.
Valida el progreso: Actúa como un "control de calidad", pudiendo pedir a un agente que repita su tarea si no es satisfactoria.
¿Por qué usar este patrón en lugar de una cadena simple?
Especialización de Modelos: Puedes usar un modelo costoso (GPT-4o) para el Supervisor y modelos ligeros (Llama-3-8B) para los agentes especialistas.
Escalabilidad: Añadir una nueva funcionalidad es tan sencillo como crear un nodo y registrarlo en las opciones del Supervisor.
Recuperación de Errores: Si un agente falla, el Supervisor puede decidir reintentar o cambiar de estrategia.
Implementación en LangGraph
Para implementar este patrón, dependemos de las Aristas Condicionales. El supervisor no tiene una ruta fija; su salida determina el flujo dinámicamente.

Un error común es intentar que el Supervisor haga el trabajo de los especialistas. Recuerda: El Supervisor coordina, el Especialista ejecuta. Si tu Supervisor está escribiendo código, tu arquitectura está perdiendo la ventaja de la especialización.

En esta unidad, construiremos un orquestador que delegará tareas de análisis y escritura de forma inteligente.

🛠️ Ejercicio: qué tenés que hacer
Objetivo: armar un sistema multi-agente donde un supervisor decide, en cada paso, qué especialista trabaja y cuándo terminar.

Qué necesitás: la variable de entorno OPENAI_API_KEY (el supervisor usa un LLM).

Pasos:

En AgentState, definí messages: Annotated[list[BaseMessage], add_messages] y next: str.
En supervisor_node, pedile al LLM una salida estructurada con with_structured_output de un TypedDict con un campo next_agent: Literal["Analista", "Escritor", "FINALIZAR"]. En el prompt de sistema, indicá el orden: primero el Analista, después el Escritor y FINALIZAR cuando el informe esté listo. Devolvé {"next": ...}.
Agregá los nodos "supervisor", "Analista" y "Escritor", y marcá "supervisor" como punto de entrada.
Agregá las aristas Analista → supervisor y Escritor → supervisor, y la arista condicional desde "supervisor": lambda s: s["next"], con el mapa {"Analista": "Analista", "Escritor": "Escritor", "FINALIZAR": END}.
Compilá el grafo y ejecutalo con astream y el mensaje "Necesito un reporte sobre ventas.".
Salida esperada: la secuencia supervisor → Analista → supervisor → Escritor → supervisor → fin. Si el grafo entra en un bucle, el prompt del supervisor no deja claro cuándo responder FINALIZAR.