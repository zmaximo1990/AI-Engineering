Estrategias de Chunking y preprocesamiento de documentos

Resumir
En la arquitectura RAG (Generación Aumentada por Recuperación), la calidad de la respuesta del LLM no depende solo del modelo, sino fundamentalmente de la calidad de los datos que recuperamos. Aquí es donde el Chunking se vuelve crítico.



¿Por qué necesitamos fragmentar?
Los modelos de lenguaje y, más importante aún, los modelos de Embedding, tienen límites de "ventana de contexto". Si intentas convertir un PDF de 50 páginas en un solo vector, perderás todos los matices y detalles. El resultado será un promedio semántico tan diluido que no servirá para encontrar respuestas específicas.

El objetivo del chunking es crear unidades de información atómicas y semánticamente coherentes.

1. El Proceso de Limpieza (Preprocessing)
Antes de dividir, debemos limpiar. Los documentos reales (PDFs, HTMLs) suelen traer ruido:

Encabezados y pies de página repetidos.
Saltos de línea dobles o triples.
Caracteres especiales resultantes de una mala extracción de tablas.
Rutas de archivos o metadatos basura.
Por qué importa: Si un chunk contiene un pie de página en medio de una frase importante, el modelo de embedding capturará ese ruido, afectando la similitud semántica.

2. Estrategias de Chunking
A. Fixed-size (Tamaño Fijo)
Divide el texto cada X caracteres o tokens. Es el método más simple pero el más peligroso, ya que puede cortar una oración o un concepto por la mitad.

B. Recursive Character Splitting (El estándar de industria)
Es el enfoque preferido en LangChain. Intenta dividir el texto usando una jerarquía de separadores:

Párrafos (\n\n)
Saltos de línea (\n)
Espacios ( )
Caracteres individuales (como último recurso)
Esto garantiza que, en la medida de lo posible, los párrafos y oraciones se mantengan unidos.

C. Overlap (Solapamiento)
Al dividir, permitimos que el final del "Chunk 1" sea el inicio del "Chunk 2".

Motivación: Imagina que un concepto clave se explica en una frase que queda justo en el límite entre dos fragmentos. El overlap asegura que el contexto se preserve en ambos, facilitando la recuperación sin importar por dónde se "cortó" el papel virtual.
Errores Comunes
Chunks demasiado pequeños: Generan ruido y pierden contexto global. El LLM tendrá dificultades para entender de qué trata el fragmento.
Ignorar los límites de tokens: Muchos desarrolladores miden en caracteres, pero los modelos cobran y limitan por tokens. Siempre valida tus chunks con un tokenizador real (como tiktoken).
No limpiar el texto: "Basura entra, basura sale". Un chunk mal preprocesado reduce la precisión de la búsqueda vectorial.
Síntesis
Un buen chunking es un equilibrio entre:

Granularidad: Fragmentos pequeños para precisión.
Contexto: Fragmentos lo suficientemente grandes (u con overlap) para ser comprensibles.
Limpieza: Datos normalizados para embeddings precisos.
🛠️ Ejercicio: qué tenés que hacer
Objetivo: armar un pipeline que limpie un documento y lo divida en fragmentos medidos en tokens, con solapamiento entre ellos.

Pasos:

__init__: self.tokenizer = tiktoken.get_encoding(model_encoding). Configurá el splitter con RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50, length_function=self.calculate_tokens, separators=["\n\n", "\n", ". ", " ", ""]).
clean_text: con re.sub, (a) borrá las líneas de encabezado que se repiten en cada página, (b) dejá como máximo un salto doble (\n\n) entre párrafos, (c) reemplazá espacios múltiples por uno y (d) eliminá caracteres basura como ■. No borres todos los saltos de línea: el splitter los usa para cortar por párrafo.
calculate_tokens: return len(self.tokenizer.encode(text)).
process_document: limpiá, aplicá self.splitter.split_text(...), imprimí cuántos tokens tiene cada chunk y devolvé la lista.
Input de prueba: en el código, reemplazá text = "Tu texto largo aquí..." por este texto, que trae el ruido típico de un PDF convertido:

python


text = """ACME S.A. — Manual interno — Pág. 1
Política de devoluciones■■
Los clientes pueden devolver un producto dentro de los 30 días    corridos desde la compra, siempre que conserven el ticket.
ACME S.A. — Manual interno — Pág. 2
El reintegro se hace por el mismo medio de pago. Si la compra fue en efectivo, se entrega una nota de crédito.
Envíos
Los envíos dentro de la ciudad demoran 48 horas hábiles. Para el interior del país, el plazo es de 5 a 7 días hábiles y el costo depende del peso del paquete.
ACME S.A. — Manual interno — Pág. 3
Garantía
Todos los productos electrónicos tienen 12 meses de garantía. La garantía no cubre daños por mal uso ni golpes."""
Este texto es corto. Para ver el corte, probá primero con chunk_size=40 y chunk_overlap=10, y después volvé a 500 / 50.

Salida esperada (con 40 / 10): varios chunks (entre 4 y 8), ninguno de más de 40 tokens. Ningún chunk contiene "ACME S.A. — Manual interno" ni "■". Cuando un párrafo no entra entero en un chunk, sus últimas palabras se repiten al comienzo del siguiente: ese es el overlap.