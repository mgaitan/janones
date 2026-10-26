# Janonismo cultural — edición de trabajo en español

Traducción al español de trabajo de *Janonismo cultural: O uso das redes sociais e a batalha pela democracia no Brasil*, de André Janones (Civilização Brasileira, 2023).

> **Privado y no autorizado para distribución.** La traducción, las imágenes y los elementos editoriales de esta edición se prepararon para revisión privada. No publicar el repositorio, la web ni los archivos descargables hasta obtener autorización escrita de los titulares de derechos.

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

## Publicación (desactivada hasta contar con autorización)

Hay un workflow manual en `.github/workflows/pages.yml`; no se ejecuta con cada `push`. Solo tras obtener permiso escrito, revisar la traducción y confirmar la visibilidad/ajustes de Pages, se debe cambiar el repositorio a la visibilidad deseada, habilitar GitHub Pages con **GitHub Actions** como fuente y ejecutar **Publish GitHub Pages** desde la pestaña Actions.

La traducción requiere una revisión editorial humana antes de considerarse definitiva. El ISBN que figura en los créditos pertenece únicamente a la edición original en portugués; esta traducción no tiene ISBN propio.
