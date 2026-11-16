#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deja la carpeta del proyecto con SOLO lo esencial y los resultados ordenados:

  Vial/
  ├── vial_plomo_v3.py · vial_tungsteno_v3.py · Proyecto_Vial_Blindado.ipynb · README.md
  └── resultados/
      ├── plomo/       plano_200mm … plano_1000mm
      ├── tungsteno/   plano_200mm … plano_1000mm
      └── figuras/     fig_*.png  (+ resumen_planos.csv y transmision_planos.csv en resultados/)

BORRA scripts y resultados antiguos. Los scripts versionados en git se quitan con `git rm`
(recuperables con el historial); las carpetas de resultados sin versionar NO se pueden recuperar.

Uso:  python3 ordenar.py            → solo muestra qué haría (no toca nada)
      python3 ordenar.py --aplicar  → lo hace
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

APLICAR = "--aplicar" in sys.argv
RAIZ    = Path(".")
DISTS   = [200, 400, 600, 800, 1000]

# Seguridad: solo corre dentro de la carpeta del proyecto
for f in ("vial_plomo_v3.py", "vial_tungsteno_v3.py", "Proyecto_Vial_Blindado.ipynb"):
    if not (RAIZ / f).exists():
        sys.exit(f"Falta {f}: ejecuta este script dentro de la carpeta Vial/. No se tocó nada.")

def versionado(p):
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(p)], capture_output=True)
    return r.returncode == 0

# ── 1. Qué se mueve ────────────────────────────────────────────────
mover = []
for d in DISTS:
    mover.append((f"output_plomo_plano_{d}mm",      f"resultados/plomo/plano_{d}mm"))
    mover.append((f"output_tungsteno_plano_{d}mm",  f"resultados/tungsteno/plano_{d}mm"))
mover += [(f.name, f"resultados/figuras/{f.name}") for f in sorted(RAIZ.glob("fig_*.png"))]
mover += [(n, f"resultados/{n}") for n in ("resumen_planos.csv", "transmision_planos.csv")]

# ── 2. Qué se borra (lista explícita; lo que no esté aquí no se toca) ──
borrar = ["vial_plomo.py", "vial_plomo_v2.py", "vial_tungsteno.py", "vial_tungsteno_v2.py", "vial_box_tg.py",
          "output_diag", "output_diag2", "output_diag_box", "output_esferas", "output_esferas_tungsteno",
          "output_pb", "output_plomo_box", "output_tungsteno_box", "output_tungsteno", "__pycache__"]
borrar += sorted(p.name for p in RAIZ.glob("output_plomo_[0-9]*mm"))
borrar += sorted(p.name for p in RAIZ.glob("output_tungsteno_[0-9]*mm"))
borrar += ["archivo", "figuras"]                         # restos de un orden anterior, si existen

print("MOVER:")
for o, d in mover:
    if (RAIZ / o).exists(): print(f"  {o}  →  {d}")
print("\nBORRAR:")
for b in borrar:
    if (RAIZ / b).exists(): print(f"  {b}" + ("   (en git: recuperable)" if versionado(b) else "   (SIN versionar: no recuperable)"))

conocidos = {o for o, _ in mover} | set(borrar) | {"vial_plomo_v3.py", "vial_tungsteno_v3.py", "Proyecto_Vial_Blindado.ipynb",
             "README.md", "resultados", ".git", ".gitignore", "ordenar.py", "ordenar.sh"}
otros = sorted(p.name for p in RAIZ.iterdir() if p.name not in conocidos)
if otros: print("\nNO RECONOCIDO (no se toca):", ", ".join(otros))

# ── 3. Cambios en scripts y notebook (rutas nuevas) ────────────────
def reemplazar(texto, viejo, nuevo, etiqueta):
    n = texto.count(viejo)
    print(f"  {etiqueta}: {n} coincidencia(s)" + ("" if n else "   ← REVISAR A MANO"))
    return texto.replace(viejo, nuevo) if n else texto

def parchear_script(nombre, viejo_dir, nuevo_dir):
    print(f"\nPARCHE {nombre}:")
    t = (RAIZ / nombre).read_text(encoding="utf-8")
    t = reemplazar(t, viejo_dir, nuevo_dir, "carpeta de salida")
    t = reemplazar(t, "    sys.exit(0)\n", "    sys.exit(0)\nPath(OUTPUT_DIR).parent.mkdir(parents=True, exist_ok=True)\n", "mkdir de resultados/")
    return t

nuevo_pb = parchear_script("vial_plomo_v3.py",     'f"./output_plomo_plano_{DIST_MM}mm"',     'f"./resultados/plomo/plano_{DIST_MM}mm"')
nuevo_w  = parchear_script("vial_tungsteno_v3.py", 'f"./output_tungsteno_plano_{DIST_MM}mm"', 'f"./resultados/tungsteno/plano_{DIST_MM}mm"')

print("\nPARCHE notebook:")
nb = json.loads((RAIZ / "Proyecto_Vial_Blindado.ipynb").read_text(encoding="utf-8"))
cont = {"pb": 0, "w": 0, "fig": 0, "csv": 0, "base": 0}
for c in nb["cells"]:
    if c.get("cell_type") != "code": continue
    src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]; ori = src
    for k, v, n in (('"output_plomo_plano_{d}mm"', '"resultados/plomo/plano_{d}mm"', "pb"),
                    ('"output_tungsteno_plano_{d}mm"', '"resultados/tungsteno/plano_{d}mm"', "w"),
                    ('savefig("fig_', 'savefig(FIG_DIR / "fig_', "fig"),
                    ('to_csv("resumen_planos.csv"', 'to_csv(RES_DIR / "resumen_planos.csv"', "csv"),
                    ('to_csv("transmision_planos.csv"', 'to_csv(RES_DIR / "transmision_planos.csv"', "csv")):
        cont[n] += src.count(k); src = src.replace(k, v)
    m = re.search(r'^BASE\s*=\s*Path\("\."\).*$', src, flags=re.M)
    if m and "FIG_DIR" not in src:
        src = src[:m.end()] + '\nRES_DIR = BASE / "resultados"; FIG_DIR = RES_DIR / "figuras"; FIG_DIR.mkdir(parents=True, exist_ok=True)' + src[m.end():]
        cont["base"] += 1
    if src != ori: c["source"] = src.splitlines(keepends=True)
print(f"  rutas plomo: {cont['pb']} · rutas tungsteno: {cont['w']} · savefig: {cont['fig']} · csv: {cont['csv']} · FIG_DIR agregado: {cont['base']}")
if cont["base"] != 1 or cont["pb"] != 1 or cont["w"] != 1:
    print("  ← algo no coincidió: revisa a mano las rutas de la celda 1 (CONTENEDORES, BASE) y los savefig")

if not APLICAR:
    print("\n(simulación) No se tocó nada. Si todo se ve bien:  python3 ordenar.py --aplicar")
    sys.exit(0)

# ── 4. Aplicar ─────────────────────────────────────────────────────
for o, d in mover:
    src, dst = RAIZ / o, RAIZ / d
    if not src.exists(): continue
    if dst.exists(): print(f"  [omitido] {d} ya existe"); continue
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(dst))
for b in borrar:
    p = RAIZ / b
    if not p.exists(): continue
    if versionado(b): subprocess.run(["git", "rm", "-r", "-q", "-f", "--", b], capture_output=True)
    if p.exists(): shutil.rmtree(p) if p.is_dir() else p.unlink()
shutil.copy("Proyecto_Vial_Blindado.ipynb", "Proyecto_Vial_Blindado.ipynb.bak")
(RAIZ / "vial_plomo_v3.py").write_text(nuevo_pb, encoding="utf-8")
(RAIZ / "vial_tungsteno_v3.py").write_text(nuevo_w, encoding="utf-8")
(RAIZ / "Proyecto_Vial_Blindado.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
gi = RAIZ / ".gitignore"; lineas = gi.read_text().splitlines() if gi.exists() else []
for l in ("resultados/", "__pycache__/"):
    if l not in lineas: lineas.append(l)
gi.write_text("\n".join(lineas) + "\n")
print("\nListo. Copia de seguridad del notebook: Proyecto_Vial_Blindado.ipynb.bak")
