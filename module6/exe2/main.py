import asyncio
from typing import Annotated, Literal, TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages

# TODO: Define el estado global del agente (AgentState)
# Debe incluir una lista de mensajes y una variable 'next' para la delegación.
class AgentState(TypedDict):
    pass

# TODO: Implementa el nodo Supervisor
# Debe usar el LLM para decidir si el siguiente paso es "Analista", "Escritor" o "FINALIZAR".
def supervisor_node(state: AgentState):
    pass

# Nodos especialistas (ya implementados para este ejercicio)
def analyst_node(state: AgentState):
    return {"messages": [HumanMessage(content="Datos procesados: +20% incremento.", name="Analista")]}

def writer_node(state: AgentState):
    return {"messages": [HumanMessage(content="El informe está listo: Crecimiento positivo.", name="Escritor")]}

# TODO: Configura el Grafo
# 1. Crea el StateGraph
# 2. Añade los nodos: 'supervisor', 'Analista', 'Escritor'
# 3. Añade aristas: Analista -> supervisor, Escritor -> supervisor
# 4. Añade la arista condicional desde 'supervisor' basada en el estado['next']
builder = StateGraph(AgentState)

# Implementa aquí...

# Compilar y ejecutar
# graph = builder.compile()
