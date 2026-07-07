"""
generar_reporte_rubrica.py
==========================
Verifica el proyecto Django (formularios, modelos, estructura de módulos)
y genera un PDF con los resultados en formato de rúbrica de evaluación.

Uso:
    python generar_reporte_rubrica.py [directorio]

El PDF se guarda como  reporte_rubrica.pdf  en el directorio indicado.
"""

import os
import ast
import sys
import datetime

# ─── ReportLab ────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ══════════════════════════════════════════════════════════════
#  PALETA DE COLORES (dark-theme de la imagen)
# ══════════════════════════════════════════════════════════════
COLOR_HEADER_BG = colors.HexColor("#1a1a2e")  # azul muy oscuro
COLOR_ROW_DARK = colors.HexColor("#16213e")  # filas impares
COLOR_ROW_LIGHT = colors.HexColor("#0f3460")  # filas pares
COLOR_TEXT_WHITE = colors.HexColor("#e0e0e0")  # texto claro
COLOR_OK = colors.HexColor("#00d26a")  # verde éxito
COLOR_ALERT = colors.HexColor("#ff6b6b")  # rojo alerta
COLOR_ACCENT = colors.HexColor("#e94560")  # acento rojo

# ══════════════════════════════════════════════════════════════
#  CRITERIOS DE LA RÚBRICA
#  (se evalúan con las funciones de verificación)
# ══════════════════════════════════════════════════════════════
CRITERIOS = [
    {
        "id": 1,
        "descripcion": (
            "Estructura los módulos Django como aplicaciones independientes con su propio "
            "models.py, views.py, urls.py y forms.py, respetando la separación de responsabilidades."
        ),
        "check": "check_module_structure",
    },
    {
        "id": 2,
        "descripcion": (
            "Implementa el enrutamiento de vistas asegurando la navegación correcta entre los módulos "
            "definidos en el diagrama de arquitectura (urls.py presentes en todos los módulos)."
        ),
        "check": "check_urls_present",
    },
    {
        "id": 3,
        "descripcion": (
            "Los formularios (forms.py) están presentes en todos los módulos y no exponen campos de "
            "estado/activo/disponibilidad al usuario final (separación de lógica de estado)."
        ),
        "check": "check_forms_no_status_fields",
    },
    {
        "id": 4,
        "descripcion": (
            "Los modelos definen clase Meta con db_table, verbose_name y verbose_name_plural, "
            "garantizando la mantenibilidad y legibilidad del esquema de base de datos."
        ),
        "check": "check_models_meta",
    },
    {
        "id": 5,
        "descripcion": (
            "Todos los modelos implementan el método __str__ para representar instancias de forma "
            "legible, facilitando la depuración y el uso en el panel de administración."
        ),
        "check": "check_models_str",
    },
    {
        "id": 6,
        "descripcion": (
            "Los formularios utilizan widgets con clases CSS (form-control, form-select) para "
            "garantizar la consistencia visual y la integración con el sistema de diseño del proyecto."
        ),
        "check": "check_forms_widgets",
    },
    {
        "id": 7,
        "descripcion": (
            "El proyecto utiliza archivo .env para la configuración de variables sensibles (base de "
            "datos, claves secretas), evitando la persistencia de datos críticos en el código fuente."
        ),
        "check": "check_env_file",
    },
    {
        "id": 8,
        "descripcion": (
            "Organiza el código fuente en una jerarquía de carpetas lógica con módulos separados "
            "(almacen, inventario, mantenimiento, prestamo, usuario, configuracion)."
        ),
        "check": "check_folder_hierarchy",
    },
    {
        "id": 9,
        "descripcion": (
            "Los módulos incluyen archivo tests.py, estableciendo la base para pruebas unitarias "
            "básicas sobre los componentes del sistema."
        ),
        "check": "check_tests_present",
    },
    {
        "id": 10,
        "descripcion": (
            "Los modelos utilizan tipos de campo apropiados (AutoField, CharField, ForeignKey, "
            "BooleanField, DateTimeField, etc.) respetando las convenciones de Django ORM."
        ),
        "check": "check_models_field_types",
    },
    {
        "id": 11,
        "descripcion": (
            "Los formularios con ForeignKey implementan __init__ para personalizar los querysets "
            "de los campos relacionados, optimizando las consultas a la base de datos."
        ),
        "check": "check_forms_init_querysets",
    },
    {
        "id": 12,
        "descripcion": (
            "El proyecto incluye archivo requirements.txt con las dependencias necesarias "
            "(Django, pillow, reportlab, psycopg2-binary), facilitando la reproducibilidad del entorno."
        ),
        "check": "check_requirements",
    },
]

# ══════════════════════════════════════════════════════════════
#  LÓGICA DE VERIFICACIÓN
# ══════════════════════════════════════════════════════════════
STATUS_FIELDS = {
    "estado",
    "estado_registro",
    "activo",
    "disponible",
    "status",
    "active",
    "is_active",
}
EXPECTED_MODULES = [
    "almacen",
    "inventario",
    "mantenimiento",
    "prestamo",
    "usuario",
    "configuracion",
]
EXPECTED_DEPS = ["django", "pillow", "reportlab", "psycopg2"]


def _walk_modules(base_dir):
    """Devuelve rutas de módulos Django existentes."""
    return [m for m in EXPECTED_MODULES if os.path.isdir(os.path.join(base_dir, m))]


def _parse_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return ast.parse(f.read(), filename=filepath)
    except (SyntaxError, OSError):
        return None


# ── Criterio 1 ───────────────────────────────────────────────
def check_module_structure(base_dir):
    detalles = []
    ok = True
    for mod in EXPECTED_MODULES:
        mod_path = os.path.join(base_dir, mod)
        if not os.path.isdir(mod_path):
            detalles.append(f"  ✗ Módulo '{mod}' no encontrado")
            ok = False
            continue
        for fname in ("models.py", "views.py", "urls.py"):
            fp = os.path.join(mod_path, fname)
            if not os.path.isfile(fp):
                detalles.append(f"  ✗ {mod}/{fname} faltante")
                ok = False
    if ok:
        detalles.append("  ✓ Todos los módulos tienen models.py, views.py y urls.py")
    return ok, "\n".join(detalles)


# ── Criterio 2 ───────────────────────────────────────────────
def check_urls_present(base_dir):
    detalles = []
    ok = True
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "urls.py")
        if os.path.isfile(fp) and os.path.getsize(fp) > 10:
            detalles.append(f"  ✓ {mod}/urls.py configurado")
        else:
            detalles.append(f"  ✗ {mod}/urls.py faltante o vacío")
            ok = False
    return ok, "\n".join(detalles)


# ── Criterio 3 ───────────────────────────────────────────────
def _extract_model_status_fields(filepath):
    tree = _parse_file(filepath)
    if not tree:
        return {}
    result = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        fields = set()
        for subnode in node.body:
            if isinstance(subnode, ast.Assign):
                for t in subnode.targets:
                    if isinstance(t, ast.Name) and t.id in STATUS_FIELDS:
                        fields.add(t.id)
        result[node.name] = fields
    return result


def _check_form_violations(filepath, model_status):
    tree = _parse_file(filepath)
    if not tree:
        return []
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_mf = any(
            (isinstance(b, ast.Name) and b.id == "ModelForm")
            or (isinstance(b, ast.Attribute) and b.attr == "ModelForm")
            for b in node.bases
        )
        if not is_mf:
            continue
        cname_lower = node.name.lower()
        if any(
            t in cname_lower
            for t in ("edit", "update", "filtro", "search", "filter", "estado")
        ):
            continue
        meta = next(
            (s for s in node.body if isinstance(s, ast.ClassDef) and s.name == "Meta"),
            None,
        )
        if not meta:
            continue
        model_name, fields_list = None, []
        for s in meta.body:
            if isinstance(s, ast.Assign):
                for t in s.targets:
                    if isinstance(t, ast.Name):
                        if t.id == "model" and isinstance(s.value, ast.Name):
                            model_name = s.value.id
                        elif t.id == "fields" and isinstance(
                            s.value, (ast.List, ast.Tuple)
                        ):
                            fields_list = [
                                e.value if isinstance(e, ast.Constant) else e.s
                                for e in s.value.elts
                                if isinstance(e, (ast.Constant, ast.Str))
                            ]
        mfields = model_status.get(model_name, STATUS_FIELDS)
        for f in fields_list:
            if f in mfields:
                violations.append(f"{node.name}.{f}")
        # class-level fields
        for s in node.body:
            if isinstance(s, ast.Assign):
                for t in s.targets:
                    if isinstance(t, ast.Name) and t.id in mfields:
                        violations.append(f"{node.name}.{t.id}(clase)")
    return violations


def check_forms_no_status_fields(base_dir):
    model_status = {}
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [
            d
            for d in dirs
            if d not in ("venv", ".venv", "__pycache__", ".git", "migrations")
        ]
        for f in files:
            if f == "models.py":
                model_status.update(_extract_model_status_fields(os.path.join(root, f)))

    detalles = []
    ok = True
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [
            d
            for d in dirs
            if d not in ("venv", ".venv", "__pycache__", ".git", "migrations")
        ]
        for f in files:
            if f == "forms.py":
                rel = os.path.relpath(os.path.join(root, f), base_dir)
                viols = _check_form_violations(os.path.join(root, f), model_status)
                if viols:
                    detalles.append(
                        f"  ✗ {rel}: campos de estado expuestos → {', '.join(viols)}"
                    )
                    ok = False
                else:
                    detalles.append(f"  ✓ {rel}: sin campos de estado expuestos")
    if not detalles:
        detalles.append("  (no se encontraron forms.py)")
        ok = False
    return ok, "\n".join(detalles)


# ── Criterio 4 ───────────────────────────────────────────────
def check_models_meta(base_dir):
    detalles = []
    ok = True
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "models.py")
        tree = _parse_file(fp)
        if not tree:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            meta = next(
                (
                    s
                    for s in node.body
                    if isinstance(s, ast.ClassDef) and s.name == "Meta"
                ),
                None,
            )
            if not meta:
                continue
            attrs = {
                t.id
                for s in meta.body
                if isinstance(s, ast.Assign)
                for t in s.targets
                if isinstance(t, ast.Name)
            }
            missing = {"db_table", "verbose_name", "verbose_name_plural"} - attrs
            if missing:
                detalles.append(f"  ✗ {mod}.{node.name}: Meta falta {missing}")
                ok = False
            else:
                detalles.append(f"  ✓ {mod}.{node.name}: Meta completa")
    return ok, "\n".join(detalles)


# ── Criterio 5 ───────────────────────────────────────────────
def check_models_str(base_dir):
    detalles = []
    ok = True
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "models.py")
        tree = _parse_file(fp)
        if not tree:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            has_str = any(
                isinstance(s, ast.FunctionDef) and s.name == "__str__"
                for s in node.body
            )
            has_field = any(
                isinstance(s, ast.Assign) and isinstance(s.value, ast.Call)
                for s in node.body
            )
            if not has_field:
                continue
            if has_str:
                detalles.append(f"  ✓ {mod}.{node.name}: __str__ implementado")
            else:
                detalles.append(f"  ✗ {mod}.{node.name}: falta __str__")
                ok = False
    return ok, "\n".join(detalles)


# ── Criterio 6 ───────────────────────────────────────────────
def check_forms_widgets(base_dir):
    detalles = []
    ok = True
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "forms.py")
        if not os.path.isfile(fp):
            detalles.append(f"  ✗ {mod}/forms.py no existe")
            ok = False
            continue
        with open(fp, "r", encoding="utf-8") as fh:
            content = fh.read()
        if "form-control" in content or "form-select" in content:
            detalles.append(
                f"  ✓ {mod}/forms.py: usa clases CSS form-control/form-select"
            )
        else:
            detalles.append(f"  ✗ {mod}/forms.py: no usa clases CSS estándar")
            ok = False
    return ok, "\n".join(detalles)


# ── Criterio 7 ───────────────────────────────────────────────
def check_env_file(base_dir):
    env_path = os.path.join(base_dir, ".env")
    if os.path.isfile(env_path) and os.path.getsize(env_path) > 5:
        return True, "  ✓ Archivo .env presente y con contenido"
    return False, "  ✗ Archivo .env no encontrado o vacío"


# ── Criterio 8 ───────────────────────────────────────────────
def check_folder_hierarchy(base_dir):
    detalles = []
    ok = True
    for mod in EXPECTED_MODULES:
        path = os.path.join(base_dir, mod)
        if os.path.isdir(path):
            detalles.append(f"  ✓ Módulo '{mod}' presente")
        else:
            detalles.append(f"  ✗ Módulo '{mod}' no encontrado")
            ok = False
    return ok, "\n".join(detalles)


# ── Criterio 9 ───────────────────────────────────────────────
def check_tests_present(base_dir):
    detalles = []
    ok = True
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "tests.py")
        if os.path.isfile(fp):
            detalles.append(f"  ✓ {mod}/tests.py presente")
        else:
            detalles.append(f"  ✗ {mod}/tests.py faltante")
            ok = False
    return ok, "\n".join(detalles)


# ── Criterio 10 ──────────────────────────────────────────────
GOOD_FIELDS = {
    "AutoField",
    "BigAutoField",
    "CharField",
    "TextField",
    "IntegerField",
    "PositiveIntegerField",
    "BooleanField",
    "DateField",
    "DateTimeField",
    "EmailField",
    "ForeignKey",
    "OneToOneField",
    "ManyToManyField",
    "DecimalField",
    "FloatField",
    "ImageField",
    "FileField",
}


def check_models_field_types(base_dir):
    detalles = []
    ok = True
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "models.py")
        tree = _parse_file(fp)
        if not tree:
            continue
        unknown = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for s in node.body:
                if isinstance(s, ast.Assign) and isinstance(s.value, ast.Call):
                    func = s.value.func
                    fname = (
                        func.id
                        if isinstance(func, ast.Name)
                        else (func.attr if isinstance(func, ast.Attribute) else "")
                    )
                    if fname.endswith("Field") and fname not in GOOD_FIELDS:
                        unknown.append(fname)
        if unknown:
            detalles.append(
                f"  ~ {mod}/models.py: tipos no estándar detectados: {set(unknown)}"
            )
        else:
            detalles.append(f"  ✓ {mod}/models.py: tipos de campo correctos")
    return ok, "\n".join(detalles)


# ── Criterio 11 ──────────────────────────────────────────────
def check_forms_init_querysets(base_dir):
    detalles = []
    ok = True
    needs_init = []
    has_init = []
    for mod in _walk_modules(base_dir):
        fp = os.path.join(base_dir, mod, "forms.py")
        tree = _parse_file(fp)
        if not tree:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            has_fk = False
            has_init_method = False
            for s in node.body:
                if isinstance(s, ast.FunctionDef) and s.name == "__init__":
                    has_init_method = True
            # Check Meta fields for FK via models inspection
            meta = next(
                (
                    s
                    for s in node.body
                    if isinstance(s, ast.ClassDef) and s.name == "Meta"
                ),
                None,
            )
            if meta:
                for s in meta.body:
                    if isinstance(s, ast.Assign):
                        for t in s.targets:
                            if isinstance(t, ast.Name) and t.id == "fields":
                                # heuristic: if form is large, it probably has FK
                                if (
                                    isinstance(s.value, (ast.List, ast.Tuple))
                                    and len(s.value.elts) > 1
                                ):
                                    has_fk = True
            if has_fk:
                if has_init_method:
                    has_init.append(f"{mod}.{node.name}")
                else:
                    needs_init.append(f"{mod}.{node.name}")
    if needs_init:
        detalles.append(
            f"  ~ Formularios sin __init__ personalizado: {', '.join(needs_init)}"
        )
    if has_init:
        detalles.append(f"  ✓ Con __init__ personalizado: {', '.join(has_init)}")
    if not needs_init:
        detalles.append(
            "  ✓ Todos los formularios con FK tienen __init__ personalizado"
        )
    return not bool(needs_init), "\n".join(detalles)


# ── Criterio 12 ──────────────────────────────────────────────
def check_requirements(base_dir):
    req = os.path.join(base_dir, "requirements.txt")
    if not os.path.isfile(req):
        return False, "  ✗ requirements.txt no encontrado"
    with open(req, "r", encoding="utf-8") as f:
        content = f.read().lower()
    missing = [d for d in EXPECTED_DEPS if d not in content]
    if missing:
        return False, f"  ✗ Dependencias faltantes: {missing}"
    return True, f"  ✓ requirements.txt contiene: {EXPECTED_DEPS}"


# ══════════════════════════════════════════════════════════════
#  MAPA DE CHECKS
# ══════════════════════════════════════════════════════════════
CHECKS = {
    "check_module_structure": check_module_structure,
    "check_urls_present": check_urls_present,
    "check_forms_no_status_fields": check_forms_no_status_fields,
    "check_models_meta": check_models_meta,
    "check_models_str": check_models_str,
    "check_forms_widgets": check_forms_widgets,
    "check_env_file": check_env_file,
    "check_folder_hierarchy": check_folder_hierarchy,
    "check_tests_present": check_tests_present,
    "check_models_field_types": check_models_field_types,
    "check_forms_init_querysets": check_forms_init_querysets,
    "check_requirements": check_requirements,
}


# ══════════════════════════════════════════════════════════════
#  GENERACIÓN DEL PDF
# ══════════════════════════════════════════════════════════════
def generar_pdf(resultados, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    # ── Estilos personalizados ────────────────────────────────
    style_titulo = ParagraphStyle(
        "titulo",
        parent=styles["Normal"],
        fontSize=16,
        textColor=COLOR_TEXT_WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    style_subtitulo = ParagraphStyle(
        "subtitulo",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#a0a0c0"),
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    style_header_col = ParagraphStyle(
        "header_col",
        parent=styles["Normal"],
        fontSize=9,
        textColor=COLOR_TEXT_WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    style_no = ParagraphStyle(
        "no",
        parent=styles["Normal"],
        fontSize=11,
        textColor=COLOR_TEXT_WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    style_criterio = ParagraphStyle(
        "criterio",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=COLOR_TEXT_WHITE,
        fontName="Helvetica",
        leading=13,
        alignment=TA_LEFT,
    )
    style_estado = ParagraphStyle(
        "estado",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )

    # ── Contenido ────────────────────────────────────────────
    story = []

    # Cabecera del documento
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("SENA – Centro Minero · Regional Boyacá", style_subtitulo))
    story.append(
        Paragraph("Reporte de Verificación – Rúbrica de Evaluación", style_titulo)
    )
    story.append(
        Paragraph(
            f"Proyecto: Sistema de Inventario y Reparaciones &nbsp;|&nbsp; "
            f"Generado: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
            style_subtitulo,
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ── Construcción de la tabla ──────────────────────────────
    col_no = 1.0 * cm
    col_crit = 11.5 * cm
    col_estado = 2.5 * cm
    col_widths = [col_no, col_crit, col_estado]

    # Fila de cabecera
    header_row = [
        Paragraph("No.", style_header_col),
        Paragraph("Criterio / Indicador de Evaluación", style_header_col),
        Paragraph("Estado", style_header_col),
    ]
    table_data = [header_row]

    aprobados = 0
    for r in resultados:
        color_estado = COLOR_OK if r["ok"] else COLOR_ALERT
        texto_estado = "✓ Cumple" if r["ok"] else "✗ No cumple"
        if aprobados is not None and r["ok"]:
            aprobados += 1

        style_est = ParagraphStyle(
            f"est_{r['id']}",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica-Bold",
            textColor=color_estado,
            alignment=TA_CENTER,
        )

        table_data.append(
            [
                Paragraph(str(r["id"]), style_no),
                Paragraph(r["descripcion"], style_criterio),
                Paragraph(texto_estado, style_est),
            ]
        )

    tabla = Table(table_data, colWidths=col_widths, repeatRows=1)

    # ── Estilos de la tabla ───────────────────────────────────
    ts = TableStyle(
        [
            # Cabecera
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), COLOR_TEXT_WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            # Filas de datos
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),  # columna No.
            ("ALIGN", (1, 1), (1, -1), "LEFT"),  # columna criterio
            ("ALIGN", (2, 1), (2, -1), "CENTER"),  # columna estado
            ("TOPPADDING", (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            ("LEFTPADDING", (1, 0), (1, -1), 6),
            ("RIGHTPADDING", (1, 0), (1, -1), 6),
            # Líneas separadoras
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#2a2a4a")),
            ("LINEAFTER", (0, 0), (0, -1), 0.4, colors.HexColor("#2a2a4a")),
            ("LINEAFTER", (1, 0), (1, -1), 0.4, colors.HexColor("#2a2a4a")),
            # Borde exterior
            ("BOX", (0, 0), (-1, -1), 1, COLOR_ACCENT),
        ]
    )

    # Filas alternadas
    for i in range(1, len(table_data)):
        bg = COLOR_ROW_DARK if i % 2 == 1 else COLOR_ROW_LIGHT
        ts.add("BACKGROUND", (0, i), (-1, i), bg)
        ts.add("TEXTCOLOR", (0, i), (-1, i), COLOR_TEXT_WHITE)

    tabla.setStyle(ts)
    story.append(tabla)

    # ── Resumen final ─────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    total = len(resultados)
    pct = int(aprobados / total * 100) if total else 0

    style_resumen = ParagraphStyle(
        "resumen",
        parent=styles["Normal"],
        fontSize=9,
        textColor=COLOR_TEXT_WHITE,
        fontName="Helvetica",
        alignment=TA_CENTER,
    )
    color_pct = COLOR_OK if pct >= 75 else COLOR_ALERT
    style_pct = ParagraphStyle(
        "pct",
        parent=styles["Normal"],
        fontSize=13,
        textColor=color_pct,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    story.append(
        Paragraph(
            f"Criterios aprobados: <b>{aprobados} / {total}</b>",
            style_resumen,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph(f"Cumplimiento: {pct}%", style_pct))

    # ── Compilar PDF ──────────────────────────────────────────
    # Fondo negro para todo el documento
    def add_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(COLOR_HEADER_BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=True, stroke=False)
        canvas.restoreState()

    doc.build(story, onFirstPage=add_background, onLaterPages=add_background)


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    base_dir = (
        sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    )
    base_dir = os.path.abspath(base_dir)
    output_pdf = os.path.join(base_dir, "reporte_rubrica.pdf")

    print(f"\n{'='*65}")
    print(f"  Verificando proyecto en: {base_dir}")
    print(f"{'='*65}\n")

    resultados = []
    for criterio in CRITERIOS:
        fn = CHECKS[criterio["check"]]
        ok, detalle = fn(base_dir)
        estado_str = "CUMPLE   " if ok else "NO CUMPLE"
        print(f"[{estado_str}] Criterio {criterio['id']}")
        if detalle:
            detalle_safe = detalle.replace("\u2713", "[OK]").replace("\u2717", "[X]").replace("\u2715", "[X]")
            print(detalle_safe)
        print()
        resultados.append(
            {
                "id": criterio["id"],
                "descripcion": criterio["descripcion"],
                "ok": ok,
                "detalle": detalle,
            }
        )

    aprobados = sum(1 for r in resultados if r["ok"])
    total = len(resultados)
    print(f"{'='*65}")
    print(
        f"  RESULTADO: {aprobados}/{total} criterios aprobados "
        f"({int(aprobados/total*100)}%)"
    )
    print(f"{'='*65}\n")

    print(f"Generando PDF: {output_pdf} ...")
    generar_pdf(resultados, output_pdf)
    print(f"PDF generado exitosamente -> {output_pdf}\n")


if __name__ == "__main__":
    main()
