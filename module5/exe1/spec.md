Propósito del ejercicio
Practicar el pensamiento arquitectónico necesario para diseñar agentes autónomos. Antes de escribir código, un arquitecto de IA debe ser capaz de visualizar cómo fluye la información y bajo qué condiciones el sistema debe iterar.

Escenario
Vas a diseñar un Asistente de Soporte Técnico Multinivel. El sistema recibe una duda del usuario, intenta resolverla buscando en una base de conocimientos, valida si la solución es útil y, si no lo es o es muy compleja, escala el caso a un agente humano.

Tarea
Definición del Estado (State): Escribe (en el mismo diagrama o en un cuadro de texto adjunto) la estructura del TypedDict que usará tu grafo. Debe incluir al menos:
messages: Para el historial de conversación.
is_escalated: Un booleano para marcar si el caso pasó a un humano.
attempts: Un contador de cuántas veces el agente ha intentado resolver el problema.
Diseño del Grafo: Crea un diagrama que contenga:
Nodo START: El punto de entrada.
Nodo "Triage": Clasifica la duda del usuario.
Nodo "Search_Knowledge": Busca soluciones (Simula un RAG).
Nodo "Evaluator": Revisa si la solución encontrada responde a la duda.
Arista Condicional: Desde "Evaluator" hacia "END" (si la solución es buena) o hacia "Human_Support" (si ha fallado 3 veces) o de vuelta a "Search_Knowledge" (para intentar otra búsqueda).
Nodo "Human_Support": Marca is_escalated=True.
Nodo END: Cierre del flujo.
Criterios de Aceptación
El diagrama utiliza una notación clara (nodos como cajas, aristas como flechas).
Se incluye explícitamente el nodo START y el nodo END.
Existe al menos un ciclo (el flujo vuelve a un nodo anterior).
Se especifica la lógica de la arista condicional (bajo qué condición se toma cada camino).
El esquema del Estado (State) está correctamente definido con tipos de datos de Python.
