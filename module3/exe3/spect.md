Persistencia local con ChromaDB: operaciones CRUD

Resumir
En el desarrollo de sistemas de IA, los embeddings (vectores que representan el significado del texto) son volátiles si solo viven en la memoria RAM. Para aplicaciones reales, necesitamos que el conocimiento del sistema "sobreviva" al reinicio del servidor y pueda actualizarse sin reindexar todo desde cero. Aquí es donde entra ChromaDB.



¿Por qué ChromaDB local?
ChromaDB es una base de datos vectorial de código abierto diseñada para ser simple. En un entorno de desarrollo o para aplicaciones de escritorio/privadas, su modo Local Persistente es ideal:

No requiere levantar un contenedor Docker complejo (por defecto).
Guarda los datos en archivos .parquet y bin en una carpeta de tu elección.
Permite operaciones CRUD (Create, Read, Update, Delete) sobre el "conocimiento" de tu agente.
Operaciones CRUD en el Espacio Vectorial
A diferencia de una base de datos SQL tradicional, el CRUD en una DB vectorial tiene matices importantes:

Create (Añadir/Upsert): No solo guardamos texto, sino su vector asociado. Si el texto cambia, el vector debe recalcularse. El uso de upsert es una mejor práctica: si el ID ya existe, actualiza; si no, lo crea.
Read (Get vs Query):
get(): Busca por IDs exactos o filtros de metadatos (como un SELECT tradicional).
query(): Busca por similitud semántica. Es el corazón de RAG.
Update: Actualiza los metadatos o el documento (disparando una nueva vectorización).
Delete: Elimina vectores que ya no son relevantes para el contexto.
El Rol de los Metadatos
Los metadatos son "etiquetas" que adjuntamos a los vectores (ej: {"autor": "Juan", "fecha": "2024-05", "source": "pdf_v1"}). Son cruciales para:

Filtrar resultados antes de la búsqueda vectorial.
Rastrear el origen de la información que usa el LLM (citación de fuentes).
Errores Comunes
ID no determinista: Usar IDs aleatorios hace imposible el update eficiente. Se recomienda usar hashes del contenido o IDs estructurados.
Desajuste de Embeddings: Intentar consultar una base de datos local con un modelo de embeddings diferente al que se usó para crearla. Los resultados serán ruido aleatorio.
Ignorar la persistencia: No inicializar el cliente con una ruta de disco, causando pérdida de datos al cerrar el script.
En este ejercicio, aprenderás a encapsular estas operaciones en una clase robusta preparada para escalar.

🛠️ Ejercicio: qué tenés que hacer
Objetivo: construir una memoria vectorial que se guarde en disco y permita insertar, buscar, actualizar, filtrar y borrar documentos.

Pasos:

__init__: self.client = chromadb.PersistentClient(path=persist_path) y self.collection = self.client.get_or_create_collection(name=collection_name, embedding_function=embedding_functions.DefaultEmbeddingFunction()).
upsert_documents: self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas). Con upsert, si repetís un ID se actualiza el documento en lugar de duplicarse.
semantic_search: usá self.collection.query(query_texts=[query_text], n_results=n_results) y devolvé una lista de diccionarios con document, metadata y distance.
Agregá un parámetro opcional where a semantic_search y pasalo a query() para filtrar por metadato.
Agregá un método delete_by_id(ids) que use self.collection.delete(ids=ids).
Input de prueba:

python


manager = VectorMemoryManager("./chroma_db", "knowledge_base")
manager.upsert_documents(
    ["doc1", "doc2", "doc3"],
    ["Python 3.12 introduce mejoras en asyncio y tipos.",
     "Las bases de datos vectoriales son clave para la memoria de largo plazo en IA.",
     "FastAPI permite crear APIs asíncronas en Python."],
    [{"source": "news"}, {"source": "tech_blog"}, {"source": "tech_blog"}],
)
print(manager.semantic_search("mejoras en python"))
print(manager.semantic_search("memoria de IA", where={"source": "tech_blog"}))
manager.delete_by_id(["doc2"])
print(manager.collection.count())
Salida esperada: la primera búsqueda devuelve primero el documento de Python 3.12. La segunda solo devuelve documentos con source: tech_blog. Después de borrar, count() da 2. Si corrés el script de nuevo, los datos siguen ahí, porque están guardados en disco. La primera vez, ChromaDB descarga un modelo de embeddings: puede tardar un poco.