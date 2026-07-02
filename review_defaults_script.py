import os
import ast
import argparse
from pathlib import Path


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=SyntaxWarning)
            tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return [], []

    defaults = []
    suspicious = []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    value = node.value
                    if isinstance(value, ast.Constant):
                        defaults.append((name, value.value, node.lineno))
                    else:
                        suspicious.append((name, node.lineno))

    return defaults, suspicious


def main():
    parser = argparse.ArgumentParser(description="Analiza archivos para revisar defaults y configuraciones de Django.")
    parser.add_argument('directory', nargs='?', default='.', help="Directorio a escanear (por defecto: actual)")
    args = parser.parse_args()

    total_files_scanned = 0
    total_defaults_found = 0
    total_suspicious = 0

    print(f"Escanendo el directorio: {os.path.abspath(args.directory)}")
    print("-" * 50)

    for root, dirs, files in os.walk(args.directory):
        dirs[:] = [d for d in dirs if d not in ('venv', '.venv', 'env', '__pycache__', '.git', 'migrations')]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_files_scanned += 1
                defaults, suspicious = process_file(filepath)
                total_defaults_found += len(defaults)
                total_suspicious += len(suspicious)
                if suspicious:
                    line_str = ", ".join(str(l) for _, l in suspicious)
                    print(f"[ALERTA] {filepath}: Tiene {len(suspicious)} default(s) no literales en las líneas [{line_str}].")
                else:
                    print(f"[OK]     {filepath}: {len(defaults)} default(s) literales correctos.")

    print("-" * 50)
    print("REPORTE FINAL (SOLO LECTURA):")
    print(f"Archivos Python escaneados    : {total_files_scanned}")
    print(f"Total de defaults detectados  : {total_defaults_found}")
    print(f"Defaults no literales         : {total_suspicious}")
    print(f"Defaults literales correctos  : {total_defaults_found - total_suspicious}")


if __name__ == "__main__":
    main()
