# Janonismo cultural — edición de trabajo en español

Traducción al español de trabajo de *Janonismo cultural: O uso das redes sociais e a batalha pela democracia no Brasil*, de André Janones (Civilização Brasileira, 2023).

La traducción, las imágenes y los elementos editoriales de esta edición se prepararon para fines de divulgación sin ánimo de lucro. 

La traducción se realizó principalmente con el modelo de IA generativa GPT-6.1-Sol y requiere una revisión profesional humana antes de considerarse definitiva. 


## Entregables

- `dist/janonismo-cultural-es.epub` — EPUB 3
- `dist/janonismo-cultural-es.pdf` — PDF generado desde el EPUB
- `docs/index.html` — sitio estático navegable, listo para GitHub Pages
- `docs/downloads/` — copias EPUB y PDF que ofrece el sitio

La web local se puede abrir directamente en `docs/index.html`. Los capítulos están en `docs/OEBPS/Text/` y conservan la estructura, las notas, las imágenes editoriales y los estilos de la fuente. La cubierta y la portada interior están compuestas en español.

## Reconstruir los formatos

Requisitos: Python 3 y Calibre (`ebook-convert`). Desde la raíz del proyecto:

```sh
python3 build.py
```

El proceso empaqueta los XHTML traducidos de `es/` como EPUB, genera el PDF con Calibre y actualiza el sitio estático y sus descargas en `docs/`.
