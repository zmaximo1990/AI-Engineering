Ingesta masiva y gestión de metadatos avanzados

Resumir
En un sistema RAG de producción, no basta con "subir archivos". La capacidad de respuesta y la precisión del sistema dependen crucialmente de cómo estructuramos los datos en el momento de la ingesta. Cuando pasamos de 100 documentos a 1,000,000, el filtrado por metadatos y el procesamiento por lotes (batching) dejan de ser extras para convertirse en requisitos de arquitectura.

El Corazón de la Escalabilidad: Ingesta Distribuida y Batching
Ingresar datos uno por uno (vector a vector) es ineficiente debido al overhead de red y los límites de la API de Pinecone. La estrategia correcta es el Batch Upsert.

¿Por qué batches?: Reduce latencia de red y aprovecha el paralelismo interno de la base de datos vectorial.
Tamaño ideal: Generalmente, batches de entre 100 y 200 vectores son el "punto dulce" entre velocidad y estabilidad.


Metadatos: El Índice Selectivo para la IA
Si buscas "factura de Amazon" en un mar de 10 millones de documentos, la búsqueda semántica pura puede darte resultados de "facturas de Azure" o "recibos de Walmart" porque son semánticamente similares. Los metadatos permiten aplicar un filtro rígido (Hard Filter) antes o durante la búsqueda semántica.

En Pinecone, los metadatos se almacenan junto al vector y permiten consultas SQL-like. Algunos casos de uso avanzados incluyen:

Multi-tenancy: Filtrar por user_id o org_id para asegurar que un usuario nunca vea datos de otro.
Temporalidad: Filtrar por year > 2023 para evitar información obsoleta.
Categorización: Limitar el contexto a department == 'legal'.
El Riesgo del "Schema Drift"
Un error común es no estandarizar los metadatos. Si un proceso guarda la fecha como ingest_date y otro como date_created, tus filtros fallarán. Como arquitecto, debes definir una interfaz de metadatos estricta.

Ejemplo de Filtro en Pinecone (Conceptual)
python


# Queremos buscar similitud solo en documentos de la categoría 'legal'
index.query(
    vector=[0.1, 0.2, ...],
    top_k=10,
    filter={
        "category": {"$eq": "legal"},
        "status": {"$in": ["reviewed", "final"]}
    }
)
Este enfoque reduce drásticamente el espacio de búsqueda, mejorando la latencia y eliminando el "ruido" de categorías irrelevantes.

🛠️ Ejercicio: qué tenés que hacer
Objetivo: cargar muchos documentos en lotes, cada uno con sus metadatos, y buscar filtrando por categoría. Se trabaja con un índice simulado (MockPineconeIndex), así que no hace falta una cuenta de Pinecone.

Pasos:

create_metadata: devolvé un diccionario con category, author, ingested_at (datetime.now().isoformat()) y char_count (len(doc_text)).
process_and_upsert_batches: recorré documents de a batch_size con range(0, len(documents), batch_size). Para cada lote, armá la lista de vectores con id (str(uuid.uuid4())), values (un embedding simulado, por ejemplo [0.1] * 8) y metadata. Llamá a await self.index.upsert(vectors) una vez por lote y devolvé el total procesado.
search_by_category: await self.index.query(vector=query_vector, top_k=5, filter={"category": {"$eq": category}}).
main: ejecutá la ingesta con batch_size=2 y después una búsqueda de la categoría "legal".
Input de prueba: reemplazá la lista docs por 5 documentos: 2 de legal, 2 de hr y 1 de finanzas. Para ver cada lote, agregá un print(len(vectors)) dentro de MockPineconeIndex.upsert.

Salida esperada: 3 llamadas a upsert, con 2, 2 y 1 vectores, y un total procesado de 5. La búsqueda tiene que mostrar el filtro {"category": {"$eq": "legal"}}. El índice simulado devuelve matches vacío: lo que se evalúa es que el filtro esté bien armado.