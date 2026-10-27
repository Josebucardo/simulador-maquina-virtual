#!/usr/bin/env python3
"""Genera la entrega imprimible desde los documentos Markdown del repositorio.

Uso desde cualquier carpeta:
    python scripts/generar_documento.py

Solo esta herramienta requiere ReportLab. El simulador no depende de él.
Los diagramas se dibujan como vectores: no se necesita Mermaid ni Internet.
"""

from __future__ import annotations

import argparse
import html
import math
import os
from pathlib import Path
import re
import textwrap

try:
    from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Image, KeepTogether, PageBreak, Paragraph, Preformatted,
        SimpleDocTemplate, Spacer, Table, TableStyle,
    )
except ImportError as exc:
    raise SystemExit(
        "Para regenerar el PDF instala la dependencia con:\n"
        "python -m pip install -r scripts/requirements_documento.txt"
    ) from exc


REPO = Path(__file__).resolve().parents[1]
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
WIDTH = PAGE_W - MARGIN * 2
NAVY = colors.HexColor("#19364B")
TEAL = colors.HexColor("#176B70")
INK = colors.HexColor("#263442")
MUTED = colors.HexColor("#617180")
PALE = colors.HexColor("#F1F5F7")
LINE = colors.HexColor("#CBD6DD")
FONT, BOLD, ITALIC, MONO = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Courier"


def register_fonts() -> None:
    """Usa fuentes Unicode locales; mantiene una alternativa portátil."""
    global FONT, BOLD, ITALIC, MONO
    windows = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    candidates = [
        (windows, "arial.ttf", "arialbd.ttf", "ariali.ttf", "consola.ttf"),
        (Path("/usr/share/fonts/truetype/dejavu"), "DejaVuSans.ttf",
         "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf", "DejaVuSansMono.ttf"),
    ]
    for directory, regular, bold, italic, mono in candidates:
        if not all((directory / name).is_file() for name in (regular, bold, italic, mono)):
            continue
        for alias, filename in (("Entrega", regular), ("Entrega-Bold", bold),
                                ("Entrega-Italic", italic), ("Entrega-Mono", mono)):
            pdfmetrics.registerFont(TTFont(alias, str(directory / filename)))
        pdfmetrics.registerFontFamily("Entrega", normal="Entrega", bold="Entrega-Bold",
                                      italic="Entrega-Italic", boldItalic="Entrega-Bold")
        FONT, BOLD, ITALIC, MONO = "Entrega", "Entrega-Bold", "Entrega-Italic", "Entrega-Mono"
        return


def clean(text: str) -> str:
    return text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")


def inline(text: str) -> str:
    """Convierte el subconjunto usado por los documentos a Paragraph XML."""
    code: list[str] = []

    def save_code(match: re.Match[str]) -> str:
        code.append(f'<font name="{MONO}" size="8.1">{html.escape(clean(match[1]))}</font>')
        return f"CODEPLACEHOLDER{len(code) - 1}ENDCODE"

    text = re.sub(r"`([^`]+)`", save_code, clean(text))
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#176B70">\1</link>', text)
    for index, value in enumerate(code):
        text = text.replace(f"CODEPLACEHOLDER{index}ENDCODE", value)
    return text


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("EntregaBody", fontName=FONT, fontSize=9.4, leading=14,
                               textColor=INK, spaceAfter=7, splitLongWords=True),
        "h1": ParagraphStyle("EntregaH1", fontName=BOLD, fontSize=21, leading=26,
                             textColor=NAVY, spaceAfter=17, keepWithNext=True),
        "h2": ParagraphStyle("EntregaH2", fontName=BOLD, fontSize=13.4, leading=18,
                             textColor=NAVY, spaceBefore=15, spaceAfter=8, keepWithNext=True),
        "h3": ParagraphStyle("EntregaH3", fontName=BOLD, fontSize=10.8, leading=15,
                             textColor=TEAL, spaceBefore=10, spaceAfter=6, keepWithNext=True),
        "h4": ParagraphStyle("EntregaH4", parent=base["Heading4"], fontName=BOLD,
                             fontSize=9.8, leading=14, textColor=INK, keepWithNext=True),
        "list": ParagraphStyle("EntregaList", fontName=FONT, fontSize=9.4, leading=14,
                               textColor=INK, leftIndent=15, firstLineIndent=0,
                               bulletIndent=1, spaceAfter=4),
        "code": ParagraphStyle("EntregaCode", fontName=MONO, fontSize=7.7, leading=10.6,
                               textColor=INK, backColor=PALE, borderColor=LINE,
                               borderWidth=.4, borderPadding=8, spaceBefore=3, spaceAfter=10),
        "caption": ParagraphStyle("EntregaCaption", fontName=ITALIC, fontSize=8.1,
                                  leading=11.5, textColor=MUTED, spaceAfter=11),
        "figure_caption": ParagraphStyle("EntregaFigureCaption", fontName=ITALIC,
                                         fontSize=8.1, leading=11.5, textColor=MUTED,
                                         spaceAfter=11, keepWithNext=True),
        "cover_label": ParagraphStyle("CoverLabel", fontName=BOLD, fontSize=9,
                                      leading=13, textColor=TEAL),
        "cover_value": ParagraphStyle("CoverValue", fontName=FONT, fontSize=10,
                                      leading=15, textColor=INK),
        "cover_title": ParagraphStyle("CoverTitle", fontName=BOLD, fontSize=26,
                                      leading=33, textColor=NAVY, spaceAfter=15),
        "cover_subtitle": ParagraphStyle("CoverSubtitle", fontName=FONT, fontSize=13,
                                         leading=19, textColor=TEAL, spaceAfter=19),
    }


def wrap_label(text: str, width: float, size: float = 8.7) -> list[str]:
    result: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and pdfmetrics.stringWidth(candidate, FONT, size) > width:
                result.append(line)
                line = word
            else:
                line = candidate
        result.append(line)
    return result


def label(drawing: Drawing, x: float, y: float, text: str, width: float,
          size: float = 8.7, color=INK, bold: bool = False) -> None:
    lines = wrap_label(text, width, size)
    first = y + (len(lines) - 1) * size * .62
    for index, part in enumerate(lines):
        drawing.add(String(x, first - index * size * 1.24, clean(part),
                           fontName=BOLD if bold else FONT, fontSize=size,
                           fillColor=color, textAnchor="middle"))


def node(drawing: Drawing, x: float, y: float, text: str, w: float = 152,
         h: float = 39, decision: bool = False, accent: bool = False) -> None:
    fill = colors.HexColor("#E6F1F0") if accent else PALE
    if decision:
        shape = Polygon([x, y+h/2, x+w/2, y, x, y-h/2, x-w/2, y],
                        fillColor=fill, strokeColor=TEAL, strokeWidth=.8)
    else:
        shape = Rect(x-w/2, y-h/2, w, h, rx=5, ry=5,
                     fillColor=fill, strokeColor=LINE, strokeWidth=.8)
    drawing.add(shape)
    label(drawing, x, y-2, text, w-16 if not decision else w*.68)


def arrow(drawing: Drawing, points: list[tuple[float, float]], caption: str = "",
          caption_at: tuple[float, float] | None = None, dashed: bool = False) -> None:
    for start, end in zip(points, points[1:]):
        line = Line(*start, *end, strokeColor=MUTED, strokeWidth=.8)
        if dashed:
            line.strokeDashArray = [3, 2]
        drawing.add(line)
    a, b = points[-2:]
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    length, spread = 5.1, .5
    drawing.add(Polygon([b[0], b[1], b[0]-length*math.cos(angle-spread),
                         b[1]-length*math.sin(angle-spread),
                         b[0]-length*math.cos(angle+spread),
                         b[1]-length*math.sin(angle+spread)],
                        fillColor=MUTED, strokeColor=MUTED, strokeWidth=.4))
    if caption:
        middle = caption_at or ((a[0]+b[0])/2, (a[1]+b[1])/2+6)
        label(drawing, middle[0], middle[1], caption, 95, size=7.7, color=TEAL)


def flow_labels(source: str) -> dict[str, str]:
    """Lee los rótulos editables de los tres diagramas de flujo conocidos."""
    result = {}
    for match in re.finditer(r"(\w+)\[([^\]]+)\]|(\w+)\{([^}]+)\}", source):
        result[match[1] or match[3]] = match[2] or match[4]
    return result


def architecture(source: str) -> Drawing:
    d = Drawing(WIDTH, 456)
    names = flow_labels(source)
    left, center, right = 62, WIDTH / 2, WIDTH-62
    placements = [
        ("Usuario", center, 423, 120, 39),
        ("Interfaz", center, 348, 150, 43),
        ("UC", center, 251, 140, 48),
        ("Disco", right, 423, 120, 43),
        ("Teclado", left, 251, 120, 43),
        ("Memoria", right, 251, 120, 43),
        ("Registros", right, 145, 120, 43),
        ("Impresora", center, 67, 150, 43),
    ]
    for identifier, x, y, width, height in placements:
        node(d, x, y, names.get(identifier, identifier), w=width, h=height,
             accent=identifier == "UC")
    arrow(d, [(center, 403.5), (center, 369.5)])  # Usuario -> interfaz
    arrow(d, [(center, 326.5), (center, 275)])  # Interfaz -> UC
    arrow(d, [(right, 401.5), (right, 272.5)])  # Disco -> memoria
    arrow(d, [(122, 251), (center-70, 251)])  # Teclado -> UC
    memory_path = [(center+70, 251), (right-60, 251)]
    arrow(d, memory_path)  # UC <-> memoria
    arrow(d, list(reversed(memory_path)))
    register_path = [(center+70, 237), (341, 237), (341, 145), (right-60, 145)]
    arrow(d, register_path)  # UC <-> registros
    arrow(d, list(reversed(register_path)))
    arrow(d, [(center, 227), (center, 88.5)])  # UC -> impresora
    return d


def step_flow(source: str) -> Drawing:
    d = Drawing(WIDTH, 602)
    names = flow_labels(source)
    x, boxw = WIDTH/2, 208
    node(d, x, 574, names["A"], boxw, 33, accent=True)
    node(d, x, 516, names["B"], 188, 56, decision=True)
    node(d, 56, 516, names["C"], 106, 42)
    arrow(d, [(x, 557.5), (x, 544)])
    arrow(d, [(x-94, 516), (109, 516)], "Sí", (126, 527))
    values = [(447, names["D"]), (390, names["E"]), (333, names["F"]),
              (276, names["G"]), (219, names["H"]), (162, names["I"])]
    previous = 488
    for y, text in values:
        node(d, x, y, text, boxw, 39)
        arrow(d, [(x, previous), (x, y+19.5)],
              "No" if y == 447 else "", (x+16, 476) if y == 447 else None)
        previous = y-19.5
    node(d, x, 93, names["J"], 150, 56, decision=True)
    arrow(d, [(x, previous), (x, 121)])
    node(d, 62, 93, names["K"], 112, 39)
    node(d, WIDTH-65, 93, names["L"], 120, 42)
    arrow(d, [(x-75, 93), (118, 93)], "Sí", (143, 105))
    arrow(d, [(x+75, 93), (WIDTH-125, 93)], "No", (WIDTH-144, 105))
    label(d, x, 33, "Si una fase falla: conservar el PC de la instrucción y pasar a ERROR.", WIDTH-25, size=8)
    return d


def general_flow(source: str) -> Drawing:
    d = Drawing(WIDTH, 488)
    names = flow_labels(source)
    x = WIDTH/2
    ys = [459, 405, 351, 297]
    labels = [names[key] for key in "ABCD"]
    for index, (y, title) in enumerate(zip(ys, labels)):
        node(d, x, y, title, 246, 38, accent=index == 0)
        if index:
            arrow(d, [(x, ys[index-1]-19), (x, y+19)])
    node(d, x, 235, names["E"], 196, 58, decision=True)
    arrow(d, [(x, 278), (x, 264)])
    lx, rx = 112, WIDTH-112
    node(d, lx, 159, names["F"], 197, 40)
    node(d, rx, 159, names["G"], 197, 40)
    arrow(d, [(x-98, 235), (lx, 235), (lx, 179)], "Paso", (lx, 210))
    arrow(d, [(x+98, 235), (rx, 235), (rx, 179)], "Automática", (rx, 210))
    node(d, x, 93, names["H"], 210, 37)
    arrow(d, [(lx, 139), (lx, 118), (x, 118), (x, 111.5)])
    arrow(d, [(rx, 139), (rx, 118), (x, 118), (x, 111.5)])
    node(d, x, 28, names["I"], WIDTH-24, 41)
    arrow(d, [(x, 74.5), (x, 48.5)])
    return d


def sequence(source: str) -> Drawing:
    """Conserva el orden y los mensajes del diagrama de secuencia editable."""
    participants: list[tuple[str, str]] = []
    messages: list[tuple[str, str, str, bool]] = []
    for line in source.splitlines():
        participant = re.match(r"\s*participant\s+(\w+)(?:\s+as\s+(.+))?", line)
        message = re.match(r"\s*(\w+)\s*(-+>>|->)\s*(\w+)\s*:\s*(.+)", line)
        if participant:
            participants.append((participant[1], participant[2] or participant[1]))
        elif message:
            messages.append((message[1], message[3], message[4], message[2].startswith("--")))
    if not participants or not messages:
        raise ValueError("Diagrama de secuencia vacío o no reconocido")
    spacing = 47
    height = 92 + len(messages)*spacing
    d = Drawing(WIDTH, height)
    positions = {name: 69 + i*(WIDTH-138)/max(1, len(participants)-1)
                 for i, (name, _) in enumerate(participants)}
    for name, title in participants:
        x = positions[name]
        node(d, x, height-26, title, 128, 35, accent=True)
        d.add(Line(x, height-44, x, 17, strokeColor=LINE, strokeWidth=.7,
                   strokeDashArray=[4, 3]))
    for index, (sender, receiver, text, dashed) in enumerate(messages):
        y = height-78-index*spacing
        start, end = positions[sender], positions[receiver]
        if start == end:
            loop = min(44, WIDTH-start-10)
            arrow(d, [(start, y), (start+loop, y), (start+loop, y-18), (start, y-18)], dashed=dashed)
            label(d, start+105, y-11, text, 174, size=8)
        else:
            arrow(d, [(start, y), (end, y)], dashed=dashed)
            label(d, (start+end)/2, y+11, text, abs(end-start)-9, size=8)
    return d


def diagram(source: str) -> Drawing:
    if "sequenceDiagram" in source:
        return sequence(source)
    if "flowchart LR" in source:
        return architecture(source)
    if "Inicio de step" in source:
        return step_flow(source)
    if re.search(r"Cargar.*(?:archivo|ASM)", source, re.IGNORECASE):
        return general_flow(source)
    raise ValueError("Diagrama Mermaid no reconocido. Añade su representación vectorial al generador.")


def split_table_row(line: str) -> list[str]:
    return [part.strip().replace("\\|", "|") for part in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def markdown_table(lines: list[str], sty: dict[str, ParagraphStyle]) -> Table:
    rows = [split_table_row(line) for line in lines]
    rows = [row for row in rows if not all(re.fullmatch(r":?-{2,}:?", cell or " ") for cell in row)]
    cols = max(len(row) for row in rows)
    for row in rows:
        row.extend([""] * (cols-len(row)))
    weights = []
    for col in range(cols):
        lengths = sorted(len(re.sub(r"[*`]", "", row[col])) for row in rows)
        typical = lengths[min(len(lengths)-1, int(len(lengths)*.85))]
        weights.append(max(8, min(38, typical)))
    # Avoid tiny cells in dense trace tables while assigning more room to explanations.
    floor = 43 if cols <= 7 else 36
    room = WIDTH - floor*cols
    widths = [floor + max(0, room)*weight/sum(weights) for weight in weights]
    size = 8.2 if cols <= 4 else 7.25
    cellstyle = ParagraphStyle("TableCell", parent=sty["body"], fontSize=size,
                               leading=size*1.36, spaceAfter=0, spaceBefore=0)
    headstyle = ParagraphStyle("TableHead", parent=cellstyle, fontName=BOLD, textColor=colors.white)
    data = [[Paragraph(inline(cell), headstyle if index == 0 else cellstyle)
             for cell in row] for index, row in enumerate(rows)]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT", spaceBefore=3, spaceAfter=11)
    vertical_padding = getattr(sty["body"], "tablePadding", 6)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("LINEBELOW", (0, 0), (-1, 0), .6, NAVY),
        ("LINEBELOW", (0, 1), (-1, -1), .25, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), vertical_padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), vertical_padding),
    ]))
    return table


def code_block(source: str, sty: dict[str, ParagraphStyle]) -> list:
    # Preformatted splits only between lines. Wrap lengthy console output before layout.
    maxchars = int((WIDTH-18)/pdfmetrics.stringWidth("M", MONO, sty["code"].fontSize))
    wrapped: list[str] = []
    for line in clean(source).expandtabs(4).splitlines():
        if len(line) <= maxchars:
            wrapped.append(line)
        else:
            wrapped.extend(textwrap.wrap(line, width=maxchars, subsequent_indent="    ",
                                         replace_whitespace=False, drop_whitespace=False,
                                         break_long_words=True, break_on_hyphens=False))
    return [Preformatted("\n".join(wrapped), sty["code"])]


def parse_markdown(source: str, sty: dict[str, ParagraphStyle], folder: Path) -> list:
    lines = source.splitlines()
    story: list = []
    index = 0
    figure_count = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.lstrip().startswith("```"):
            language = line.strip()[3:].strip().lower()
            end = index+1
            while end < len(lines) and not lines[end].lstrip().startswith("```"):
                end += 1
            content = "\n".join(lines[index+1:end])
            if language == "mermaid":
                figure_count += 1
                if "sequenceDiagram" in content:
                    caption = "Secuencia Fetch-Decode-Execute"
                elif "flowchart LR" in content:
                    caption = "Arquitectura del simulador"
                elif "Inicio de step" in content:
                    caption = "Flujo de ejecución de una instrucción"
                else:
                    caption = "Funcionamiento general"
                story.extend([
                    Paragraph(f"Figura {figure_count}. {caption}.", sty["figure_caption"]),
                    diagram(content), Spacer(1, 9),
                ])
            else:
                blocks = code_block(content, sty)
                if language == "asm" and len(content.splitlines()) <= 40:
                    # Keep a complete sample with its short introduction and heading.
                    if story and isinstance(story[-1], Paragraph) and story[-1].style.name == "EntregaBody":
                        blocks.insert(0, story.pop())
                    if story and isinstance(story[-1], Paragraph) and story[-1].style.name in ("EntregaH2", "EntregaH3", "EntregaH4"):
                        blocks.insert(0, story.pop())
                    story.append(KeepTogether(blocks))
                else:
                    story.extend(blocks)
            index = end+1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = min(len(heading[1]), 4)
            story.append(Paragraph(inline(heading[2]), sty[f"h{level}"]))
            index += 1
            continue
        if line.lstrip().startswith("|") and index+1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[index+1]):
            end = index+1
            while end < len(lines) and lines[end].strip().startswith("|"):
                end += 1
            story.append(markdown_table(lines[index:end], sty))
            index = end
            continue
        image_match = re.fullmatch(r"\s*!\[([^\]]*)\]\(([^)]+)\)\s*", line)
        if image_match:
            path = (folder / image_match[2]).resolve()
            if not path.is_file():
                raise FileNotFoundError(f"Imagen del documento ausente: {path}")
            img = Image(str(path))
            scale = min(WIDTH/img.imageWidth, 470/img.imageHeight, 1)
            img.drawWidth, img.drawHeight = img.imageWidth*scale, img.imageHeight*scale
            story.append(KeepTogether([img, Paragraph(inline(image_match[1]), sty["caption"])]))
            index += 1
            continue
        item = re.match(r"^\s*(?:([-*])|(\d+)[.)])\s+(.+)$", line)
        if item:
            content = item[3]
            index += 1
            while index < len(lines) and re.match(r"^\s{2,}\S", lines[index]) and not lines[index].lstrip().startswith(("- ", "* ")):
                content += " " + lines[index].strip()
                index += 1
            bullet = "•" if item[1] else item[2]+"."
            story.append(Paragraph(inline(content), sty["list"], bulletText=bullet))
            continue
        if re.fullmatch(r"\s*[-*_]{3,}\s*", line):
            story.append(Spacer(1, 6))
            index += 1
            continue
        paragraph = [line.strip()]
        hard_breaks = [line.endswith("  ")]
        index += 1
        while index < len(lines) and lines[index].strip():
            following = lines[index]
            if re.match(r"^\s*(?:#{1,6}\s|```|\||[-*]\s|\d+[.)]\s|!\[)", following):
                break
            paragraph.append(following.strip())
            hard_breaks.append(following.endswith("  "))
            index += 1
        text = ""
        for position, part in enumerate(paragraph):
            if position:
                text += "<br/>" if hard_breaks[position-1] else " "
            text += inline(part)
        story.append(Paragraph(text, sty["body"]))
    return story


def extract_cover(source: str) -> tuple[str, str, str]:
    title_match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
    title = title_match[1] if title_match else "Documento técnico y diseño del simulador"
    section = re.search(r"^##\s+Portada\s*\n(.*?)(?=^##\s|\Z)", source,
                        re.MULTILINE | re.DOTALL)
    if section:
        rest = source[:section.start()] + source[section.end():]
        cover = section[1].strip()
    else:
        rest, cover = source, ""
    rest = re.sub(r"^#\s+.+\n?", "", rest, count=1, flags=re.MULTILINE)
    return title, cover, rest


def cover_page(title: str, cover: str, sty: dict[str, ParagraphStyle]) -> list:
    story = [Spacer(1, 22), Paragraph("GRUPO 13 / ARQUITECTURA DE SISTEMAS OPERATIVOS", sty["cover_label"]),
             Spacer(1, 23), Paragraph("Implementación de una<br/>Máquina Virtual Simple", sty["cover_title"]),
             Paragraph(inline(title), sty["cover_subtitle"])]
    rows = []
    extras = []
    for line in cover.splitlines():
        if not line.strip():
            if extras:
                extras.append("")
            continue
        field = re.match(r"^\s*\*\*([^*]+?):?\*\*\s*:?[ \t]*(.*)$", line.strip())
        if field:
            rows.append([Paragraph(inline(field[1].rstrip(":")), sty["cover_label"]),
                         Paragraph(inline(field[2].strip()), sty["cover_value"])])
        else:
            extras.append(line)
    if rows:
        table = Table(rows, colWidths=[116, WIDTH-116], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), .35, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ]))
        story.append(table)
    if extras:
        story.append(Spacer(1, 13))
        story.extend(parse_markdown("\n".join(extras), sty, REPO/"docs"))
    story.append(PageBreak())
    return story


def decorate(canvas, doc) -> None:
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.5)
        canvas.line(MARGIN, PAGE_H-13*mm, PAGE_W-MARGIN, PAGE_H-13*mm)
        canvas.setFont(FONT, 7.6)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, PAGE_H-10.7*mm, "VM Studio | Documento técnico y anexos")
        canvas.drawRightString(PAGE_W-MARGIN, PAGE_H-10.7*mm, "Grupo 13")
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(MARGIN, 10.5*mm, "Implementación de una Máquina Virtual Simple")
    canvas.drawRightString(PAGE_W-MARGIN, 10.5*mm, f"Página {doc.page}")
    canvas.restoreState()


def generate(output: Path) -> Path:
    register_fonts()
    sty = styles()
    docs = REPO/"docs"
    main = (docs/"DOCUMENTO_TECNICO_GRUPO13.md").read_text(encoding="utf-8-sig")
    title, cover, main = extract_cover(main)
    story = cover_page(title, cover, sty)
    story.extend(parse_markdown(main, sty, docs))
    annexes = [
        ("MANUAL_USUARIO.md", "Anexo A. Manual de usuario"),
        ("MANUAL_TECNICO.md", "Anexo B. Manual técnico"),
        ("EVIDENCIAS_PRUEBAS.md", "Anexo C. Evidencias de pruebas"),
        ("GUIA_DEFENSA.md", "Anexo D. Guía de defensa"),
    ]
    for filename, heading in annexes:
        content = (docs/filename).read_text(encoding="utf-8-sig")
        content = re.sub(r"^#\s+.+\n?", "", content, count=1, flags=re.MULTILINE)
        story.extend([PageBreak(), Paragraph(heading, sty["h1"])])
        annex_styles = sty
        if filename == "MANUAL_USUARIO.md":
            # The short user manual fits three pages without a nearly empty last page.
            annex_styles = dict(sty)
            annex_styles["body"] = ParagraphStyle(sty["body"].name, parent=sty["body"],
                                                  leading=13, spaceAfter=5, tablePadding=4)
            annex_styles["list"] = ParagraphStyle(sty["list"].name, parent=sty["list"],
                                                  leading=13, spaceAfter=3)
            annex_styles["h2"] = ParagraphStyle(sty["h2"].name, parent=sty["h2"],
                                                spaceBefore=12, spaceAfter=7)
            annex_styles["h3"] = ParagraphStyle(sty["h3"].name, parent=sty["h3"],
                                                spaceBefore=8, spaceAfter=5)
        story.extend(parse_markdown(content, annex_styles, docs))
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=MARGIN,
                                 leftMargin=MARGIN, topMargin=20*mm, bottomMargin=18*mm,
                                 title="Grupo 13 - Máquina Virtual Simple",
                                 author="Grupo 13", subject="Documento técnico, manuales y evidencias",
                                 pageCompression=1, allowSplitting=True)
    document.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", type=Path, default=REPO/"output/pdf/ENTREGA_GRUPO13.pdf",
                        help="Ruta del PDF de salida")
    args = parser.parse_args()
    output = generate(args.salida.resolve())
    print(f"PDF generado: {output}")


if __name__ == "__main__":
    main()
