#!/usr/bin/env python3
"""Build Spanish working-edition EPUB, PDF, and static reading site."""

from __future__ import annotations

import html
import shutil
import subprocess
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITION = ROOT / "es"
OEBPS = EDITION / "OEBPS"
TEXT = OEBPS / "Text"
DIST = ROOT / "dist"
DOCS = ROOT / "docs"

NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
    "xhtml": "http://www.w3.org/1999/xhtml",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)
ET.register_namespace("", NS["opf"])

TITLE = "Janonismo cultural: El uso de las redes sociales y la batalla por la democracia en Brasil"
CHAPTERS = [f"a{i}.xhtml" for i in range(5, 17)]
READING_ORDER = [
    "rosto.xhtml",
    "epigrafe.xhtml",
    "sumario.xhtml",
    "a1.xhtml",
    "a2.xhtml",
    "a3.xhtml",
    "a4.xhtml",
    *CHAPTERS,
    "creditos.xhtml",
    "colofao.xhtml",
    "saiba-mais.xhtml",
]
PAGE_LABELS = {
    "rosto.xhtml": "Portada",
    "epigrafe.xhtml": "Epígrafe",
    "sumario.xhtml": "Índice",
    "a1.xhtml": "Presentación",
    "a2.xhtml": "Presentación",
    "a3.xhtml": "Prefacio",
    "a4.xhtml": "Prefacio",
    "creditos.xhtml": "Créditos",
    "colofao.xhtml": "Colofón",
    "saiba-mais.xhtml": "Más información",
}


def parse(path: Path) -> ET.ElementTree:
    return ET.parse(path)


def text_of(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def update_metadata() -> None:
    path = OEBPS / "content.opf"
    tree = parse(path)
    package = tree.getroot()
    package.set("{http://www.w3.org/XML/1998/namespace}lang", "es")
    metadata = package.find("opf:metadata", NS)
    if metadata is None:
        raise RuntimeError("No se encontró el bloque metadata del EPUB")
    title = metadata.find("dc:title", NS)
    if title is not None:
        title.text = TITLE
    language = metadata.find("dc:language", NS)
    if language is not None:
        language.text = "es"
    identifier = metadata.find("dc:identifier", NS)
    if identifier is not None:
        identifier.text = "urn:uuid:" + str(
            uuid.uuid5(uuid.NAMESPACE_URL, "urn:isbn:9786558021131/es")
        )
    for tag in ("source", "description"):
        for existing in metadata.findall(f"dc:{tag}", NS):
            metadata.remove(existing)
    source = ET.SubElement(metadata, f"{{{NS['dc']}}}source")
    source.text = "Janonismo cultural: O uso das redes sociais e a batalha pela democracia no Brasil (2023), ISBN 978-65-5802-113-1"
    description = ET.SubElement(metadata, f"{{{NS['dc']}}}description")
    description.text = "Traducción de trabajo al español. Distribución sujeta a autorización de los titulares de derechos."
    cover_meta = metadata.find("opf:meta[@name='cover']", NS)
    if cover_meta is not None:
        cover_meta.set("content", "cover-es.svg")
    manifest = package.find("opf:manifest", NS)
    if manifest is not None and not any(
        item.get("id") == "cover-es.svg" for item in manifest.findall("opf:item", NS)
    ):
        ET.SubElement(
            manifest,
            f"{{{NS['opf']}}}item",
            {
                "id": "cover-es.svg",
                "href": "Images/capa-es.svg",
                "media-type": "image/svg+xml",
                "properties": "cover-image",
            },
        )
    for modified in metadata.findall("opf:meta[@property='dcterms:modified']", NS):
        modified.text = (
            datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        )
    tree.write(path, encoding="utf-8", xml_declaration=True)


def update_cover_and_toc() -> None:
    cover_path = TEXT / "cover.xhtml"
    cover = ET.parse(cover_path)
    root = cover.getroot()
    root.set("lang", "es")
    root.set("{http://www.w3.org/XML/1998/namespace}lang", "es")
    for image in root.iter("{http://www.w3.org/1999/xhtml}img"):
        image.set(
            "alt",
            "Janonismo cultural. El uso de las redes sociales y la batalla por la democracia en Brasil. André Janones. Civilização Brasileira.",
        )
    cover.write(cover_path, encoding="utf-8", xml_declaration=True)

    nav_tree = parse(TEXT / "toc.xhtml")
    labels = {}
    for anchor in nav_tree.getroot().iter("{http://www.w3.org/1999/xhtml}a"):
        href = anchor.get("href", "")
        labels[href] = text_of(anchor)

    opf = parse(OEBPS / "content.opf").getroot()
    spine = opf.find("opf:spine", NS)
    manifest = {
        item.get("id"): item.get("href")
        for item in opf.findall("opf:manifest/opf:item", NS)
    }
    if spine is None:
        raise RuntimeError("No se encontró el spine del EPUB")
    targets = []
    for itemref in spine.findall("opf:itemref", NS):
        href = manifest.get(itemref.get("idref"), "")
        if href.startswith("Text/") and href.endswith(".xhtml"):
            name = href.removeprefix("Text/")
            label = labels.get(name)
            if not label:
                page = TEXT / name
                if page.exists():
                    root = parse(page).getroot()
                    h1 = root.find(".//{http://www.w3.org/1999/xhtml}h1")
                    title = root.find(".//{http://www.w3.org/1999/xhtml}title")
                    label = (
                        text_of(h1 if h1 is not None else title)
                        if h1 is not None or title is not None
                        else name
                    )
                else:
                    label = name
            targets.append((name, label))

    ncx = ET.Element(f"{{{NS['ncx']}}}ncx", {"version": "2005-1"})
    head = ET.SubElement(ncx, f"{{{NS['ncx']}}}head")
    ET.SubElement(
        head,
        f"{{{NS['ncx']}}}meta",
        {
            "name": "dtb:uid",
            "content": "urn:uuid:"
            + str(uuid.uuid5(uuid.NAMESPACE_URL, "urn:isbn:9786558021131/es")),
        },
    )
    doc_title = ET.SubElement(ncx, f"{{{NS['ncx']}}}docTitle")
    ET.SubElement(doc_title, f"{{{NS['ncx']}}}text").text = TITLE
    nav_map = ET.SubElement(ncx, f"{{{NS['ncx']}}}navMap")
    for index, (name, label) in enumerate(targets, 1):
        point = ET.SubElement(
            nav_map,
            f"{{{NS['ncx']}}}navPoint",
            {"id": f"navpoint-{index}", "playOrder": str(index)},
        )
        nav_label = ET.SubElement(point, f"{{{NS['ncx']}}}navLabel")
        ET.SubElement(nav_label, f"{{{NS['ncx']}}}text").text = label
        ET.SubElement(point, f"{{{NS['ncx']}}}content", {"src": f"Text/{name}"})
    ET.ElementTree(ncx).write(OEBPS / "toc.ncx", encoding="utf-8", xml_declaration=True)


def copy_site_assets() -> None:
    if DOCS.exists():
        shutil.rmtree(DOCS)
    shutil.copytree(OEBPS, DOCS / "OEBPS")
    (DOCS / "downloads").mkdir(parents=True)


def build_reader_site() -> None:
    pages = []
    for index, name in enumerate(READING_ORDER):
        path = DOCS / "OEBPS" / "Text" / name
        tree = parse(path)
        root = tree.getroot()
        body = root.find("{http://www.w3.org/1999/xhtml}body")
        if body is None:
            continue
        h1 = body.find(".//{http://www.w3.org/1999/xhtml}h1")
        label = text_of(h1) if h1 is not None else PAGE_LABELS.get(name, name)
        label = PAGE_LABELS.get(name, label) if name not in CHAPTERS else label
        previous = READING_ORDER[index - 1] if index else None
        following = READING_ORDER[index + 1] if index + 1 < len(READING_ORDER) else None
        nav = ET.Element(
            "{http://www.w3.org/1999/xhtml}nav",
            {"class": "reader-nav", "aria-label": "Navegación del libro"},
        )
        home = ET.SubElement(
            nav,
            "{http://www.w3.org/1999/xhtml}a",
            {"href": "../../index.html", "class": "reader-home"},
        )
        home.text = "Índice del libro"
        if previous:
            ET.SubElement(
                nav,
                "{http://www.w3.org/1999/xhtml}a",
                {"href": previous, "rel": "prev"},
            ).text = "← Sección anterior"
        if following:
            ET.SubElement(
                nav,
                "{http://www.w3.org/1999/xhtml}a",
                {"href": following, "rel": "next"},
            ).text = "Sección siguiente →"
        body.insert(0, nav)
        body.append(ET.fromstring(ET.tostring(nav, encoding="unicode")))
        head = root.find("{http://www.w3.org/1999/xhtml}head")
        if head is not None:
            ET.SubElement(
                head,
                "{http://www.w3.org/1999/xhtml}link",
                {"rel": "stylesheet", "href": "../../site.css", "type": "text/css"},
            )
        tree.write(path, encoding="utf-8", xml_declaration=True)
        pages.append((name, label))

    toc_items = "\n".join(
        f'<li><a href="OEBPS/Text/{html.escape(name)}">{html.escape(label)}</a></li>'
        for name, label in pages
    )
    index_html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Edición de trabajo en español de Janonismo cultural, de André Janones.">
<title>{html.escape(TITLE)}</title><link rel="stylesheet" href="site.css">
</head><body><main class="landing">
<p class="eyebrow">EDICIÓN DE TRABAJO · ESPAÑOL</p>
<h1>Janonismo<br><em>cultural</em></h1>
<p class="subtitle">El uso de las redes sociales y la batalla por la democracia en Brasil</p>
<p class="byline">André Janones</p>
<div class="downloads"><a class="button" href="downloads/janonismo-cultural-es.epub">Descargar EPUB</a><a class="button secondary" href="downloads/janonismo-cultural-es.pdf">Descargar PDF</a></div>
<section class="notice"><strong>Versión de trabajo.</strong> Traducción al español pendiente de revisión editorial. La distribución pública está sujeta a autorización de los titulares de derechos.</section>
<section class="contents"><h2>Contenido</h2><ol>{toc_items}</ol></section>
<footer>Texto original publicado en portugués por Civilização Brasileira (2023). ISBN de la edición original: 978-65-5802-113-1.</footer>
</main></body></html>"""
    (DOCS / "index.html").write_text(index_html, encoding="utf-8")
    (DOCS / "site.css").write_text(SITE_CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")


def build_epub() -> Path:
    DIST.mkdir(exist_ok=True)
    path = DIST / "janonismo-cultural-es.epub"
    with zipfile.ZipFile(path, "w") as archive:
        archive.write(
            EDITION / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED
        )
        for file in sorted(
            p for p in EDITION.rglob("*") if p.is_file() and p != EDITION / "mimetype"
        ):
            archive.write(
                file,
                file.relative_to(EDITION).as_posix(),
                compress_type=zipfile.ZIP_DEFLATED,
            )
    return path


def main() -> None:
    update_metadata()
    update_cover_and_toc()
    epub = build_epub()
    pdf = DIST / "janonismo-cultural-es.pdf"
    subprocess.run(["ebook-convert", str(epub), str(pdf)], check=True)
    copy_site_assets()
    build_reader_site()
    shutil.copy2(epub, DOCS / "downloads" / epub.name)
    shutil.copy2(pdf, DOCS / "downloads" / pdf.name)
    print(f"EPUB: {epub} ({epub.stat().st_size:,} bytes)")
    print(f"PDF:  {pdf} ({pdf.stat().st_size:,} bytes)")
    print(f"Web:  {DOCS / 'index.html'}")


SITE_CSS = """:root{color-scheme:light;--ink:#1c2422;--muted:#66706c;--paper:#faf9f5;--accent:#d34d35;--line:#deded6;--green:#35594b}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.72 system-ui,sans-serif}.landing{max-width:850px;margin:0 auto;padding:8vh 28px 60px}.eyebrow{font-size:.75rem;font-weight:700;letter-spacing:.17em;color:var(--accent)}h1{font:700 clamp(3.8rem,12vw,7rem)/.94 Georgia,serif;letter-spacing:-.06em;margin:2rem 0 1rem}h1 em{color:var(--accent)}.subtitle{font-size:1.2rem;max-width:600px;color:var(--muted)}.byline{font-weight:600;margin:2rem 0}.downloads{display:flex;gap:12px;flex-wrap:wrap;margin:2rem 0}.button{display:inline-block;padding:12px 18px;border-radius:5px;background:var(--green);color:white;text-decoration:none;font-weight:700}.button.secondary{background:transparent;color:var(--green);border:1px solid var(--green)}.notice{padding:16px 20px;border-left:4px solid var(--accent);background:#f1eee5;color:#454b47}.contents{margin-top:4rem}.contents h2{font:600 2rem Georgia,serif}.contents ol{list-style:none;padding:0;border-top:1px solid var(--line)}.contents li{border-bottom:1px solid var(--line)}.contents li a{display:block;padding:12px 2px;color:var(--ink);text-decoration:none}.contents li a:hover{color:var(--accent)}footer{margin-top:4rem;padding-top:1rem;border-top:1px solid var(--line);font-size:.8rem;color:var(--muted)}.reader-nav{display:flex;align-items:center;justify-content:space-between;gap:1rem;max-width:850px;margin:1rem auto;padding:12px 20px;border-block:1px solid var(--line);font:600 .9rem system-ui,sans-serif}.reader-nav a{color:var(--green);text-decoration:none}.reader-nav a:hover{text-decoration:underline}.reader-nav .reader-home{margin-right:auto}body:has(.reader-nav) .Quadro-de-texto-b-sico{max-width:740px;margin:3rem auto;padding:0 24px;font:19px/1.8 'Adobe Garamond Pro',Georgia,serif}body:has(.reader-nav) h1{font:700 2rem/1.2 system-ui,sans-serif;letter-spacing:0;margin-bottom:2rem}body:has(.reader-nav) p{margin:0 0 1.25em}body:has(.reader-nav) a{color:var(--accent)}@media(max-width:600px){body{font-size:16px}.landing{padding:7vh 20px 40px}.reader-nav{font-size:.8rem;padding:10px 12px}.reader-nav .reader-home{display:none}body:has(.reader-nav) .Quadro-de-texto-b-sico{margin:2rem auto;padding:0 20px;font-size:18px}}
"""

if __name__ == "__main__":
    main()
