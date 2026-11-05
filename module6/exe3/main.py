from typing import Annotated, TypedDict, List, Optional
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, END
import asyncio

# TODO: Define ResearchArtifact y ReviewArtifact usando Pydantic
# Asegúrate de incluir validaciones (ej. score entre 0 y 1)

class AgentState(TypedDict):
    topic: str
    # TODO: Añadir campos para researcher_output y reviewer_output
    pass

# TODO: Implementar el nodo de investigación asíncrono
async def researcher_node(state: AgentState):
    # 1. Crear un ResearchArtifact
    # 2. Retornar la actualización del estado para 'researcher_output'
    return {}

# TODO: Implementar el nodo de revisión asíncrono
async def reviewer_node(state: AgentState):
    # 1. Leer researcher_output del estado
    # 2. Validar y crear un ReviewArtifact
    # 3. Retornar la actualización para 'reviewer_output'
    return {}

# Configuración del Grafo
workflow = StateGraph(AgentState)

# TODO: Añadir nodos y definir el flujo (entry point, edges)

app = workflow.compile()

async def run_example():
    initial_state = {"topic": "Sistemas Multi-Agente"}
    # TODO: Ejecutar el grafo usando app.astream
    pass

if __name__ == "__main__":
    asyncio.run(run_example())
