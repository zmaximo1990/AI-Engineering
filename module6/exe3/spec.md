Estado Compartido y Comunicación Asíncrona

En sistemas multi-agente, la comunicación no es simplemente "enviar un mensaje". Se trata de gestionar la coherencia del conocimiento a medida que este evoluciona. Cuando trabajamos con agentes especializados, el mayor desafío no es que el LLM genere texto, sino que todos los componentes del sistema operen sobre una versión válida y actualizada de la realidad.

Por qué Asyncio es vital en Arquitecturas de IA
Los LLMs son intrínsecamente lentos. Una llamada a GPT-4 o Claude 3.5 puede tardar varios segundos. Si tienes 5 agentes trabajando de forma síncrona, el tiempo de respuesta total será la suma de todos los retardos.

Utilizar asyncio permite que mientras un agente espera la respuesta de una API, el orquestador pueda:

Procesar resultados de otros agentes.
Realizar escrituras en bases de datos vectoriales.
Mantener la interfaz de usuario receptiva (streaming).


El Estado Compartido: De Diccionarios a Esquemas Validados
En unidades anteriores usamos diccionarios simples. Sin embargo, en un sistema de grado industrial, necesitamos contratos.

Un error común es permitir que cualquier agente modifique cualquier parte del estado. Esto conduce a condiciones de carrera (race conditions) donde el Agente B sobrescribe lo que el Agente A acaba de calcular basándose en datos obsoletos.

Estrategia Recomendada:

Aislamiento de Escritura: Cada agente es dueño de una "parcela" del estado. Por ejemplo, el agente researcher solo escribe en state["research_results"].
Validación con Pydantic: Antes de "inyectar" datos en el estado compartido, los validamos contra un modelo de Pydantic. Si el LLM alucina un formato de fecha incorrecto o un score fuera de rango, el error se captura inmediatamente.
Consistencia Eventual
En sistemas asíncronos, aceptamos que por unos milisegundos, algunos agentes podrían ver una versión del estado ligeramente antigua. Esto se llama Consistencia Eventual. En LangGraph, gestionamos esto mediante el flujo de nodos: un nodo solo se ejecuta cuando tiene la garantía de que sus dependencias (aristas de entrada) han completado su escritura.

Errores Comunes
Shared Mutable State: Intentar usar una lista global de Python y hacer .append() desde múltiples funciones async. Esto fallará en entornos distribuidos o bajo alta concurrencia. Usa siempre el mecanismo de retorno de estados del grafo.
No manejar excepciones en Nodos: Si un nodo asíncrono falla y no se captura, puede dejar el estado del sistema en un limbo ("bloqueado"). Siempre valida los outputs del LLM antes de retornarlos al grafo.
​

🛠️ Ejercicio: qué tenés que hacer
Objetivo: hacer que dos agentes compartan información a través del estado del grafo, con datos validados por Pydantic y sin pisarse entre sí.

Pasos:

Definí ResearchArtifact (topic: str, findings: List[str], confidence_score: float = Field(ge=0, le=1)) y ReviewArtifact (is_approved: bool, feedback: str).
En AgentState, agregá researcher_output: Optional[ResearchArtifact] y reviewer_output: Optional[ReviewArtifact].
researcher_node: simulá la investigación con await asyncio.sleep(1), creá un ResearchArtifact y devolvé solo {"researcher_output": ...}. Así cada nodo escribe únicamente su parte del estado.
reviewer_node: leé researcher_output. Si confidence_score > 0.8, aprobá; si no, rechazá con un feedback. Si no hay datos, devolvé is_approved=False. Devolvé solo {"reviewer_output": ...}.
Agregá los nodos "investigador" y "revisor", y armá el flujo: entrada en investigador, después revisor y después END. En run_example, recorré app.astream(initial_state) e imprimí qué nodo terminó.
Salida esperada: --- Investigando: Sistemas Multi-Agente ---, después Nodo 'investigador' finalizado., --- Revisando resultados --- y Nodo 'revisor' finalizado., con la revisión aprobada. Para probar la validación, cambiá confidence_score a 1.5: tiene que aparecer un ValidationError manejado, no un corte del programa.