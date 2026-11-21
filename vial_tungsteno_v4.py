#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contenedor de TUNGSTENO (CT/A-30W) — detector ESFÉRICO (cáscara) a distancia variable.
Uso: python vial_tungsteno_v4.py <distancia_mm>
Ejemplo: python vial_tungsteno_v4.py 200

Cada corrida escribe en su propia carpeta output_tungsteno_plano_<dist>mm/
y no sobreescribe resultados previos (ni los de la versión con cubos ni los del plomo).
"""

import json
import math
import os
import sys
import time
from pathlib import Path

import opengate as gate

# ══════════════════════════════════════════════════════════
#  ARGUMENTO: distancia del detector en mm
# ══════════════════════════════════════════════════════════
if len(sys.argv) not in (2, 3):
    print("Uso: python vial_tungsteno_v4.py <distancia_mm> [millones_primarios]")
    print("     distancia_mm: 200 | 400 | 600 | 800 | 1000")
    sys.exit(1)

DIST_MM = int(sys.argv[1])
if DIST_MM not in [200, 400, 600, 800, 1000]:
    print(f"Distancia {DIST_MM} no reconocida. Usar: 200, 400, 600, 800 o 1000.")
    sys.exit(1)

# ══════════════════════════════════════════════════════════
#  PARÁMETROS
# ══════════════════════════════════════════════════════════
ACTIVIDAD_OBJETIVO_MCI = 100.0
N_PRIMARIES            = int(float(sys.argv[2]) * 1_000_000) if len(sys.argv) > 2 else 100_000_000
OUTPUT_DIR             = f"./resultados/tungsteno/esfera_{DIST_MM}mm"

# ── Detector: CÁSCARA ESFÉRICA de tejido blando centrada en la fuente ──
# Radio interior = distancia a la fuente. Todos los fotones que salen la cruzan en
# incidencia normal. Se divide en N_Z rebanadas en z (zonas de igual área si z es uniforme):
# la rebanada central es el "cinturón" a la altura de la fuente (donde está el técnico).
# La dosis se calcula con la Edep y la masa real de cada zona (el DoseActor usaría la masa
# de una caja), por eso la masa por rebanada se guarda en los metadatos.
ESPESOR_MM = 5.0          # espesor de la cáscara
N_Z        = 11           # rebanadas en z (impar: la central queda en el ecuador)
ZC_MM      = -13.85         # centro de la esfera = centro del agua (fuente)
RHO_G_CM3  = 1.03         # G4_TISSUE_SOFT_ICRP

R_INT_MM = float(DIST_MM)
R_EXT_MM = R_INT_MM + ESPESOR_MM
LADO_MM  = 2.0 * R_EXT_MM
DZ_MM    = LADO_MM / N_Z

def _vol_zona_mm3(R, a, b):
    """Volumen de la esfera de radio R entre los planos z=a y z=b (mm^3)."""
    a = max(-R, min(R, a)); b = max(-R, min(R, b))
    return math.pi * (R**2 * (b - a) - (b**3 - a**3) / 3.0)

Z_BORDES = [-R_EXT_MM + i * DZ_MM for i in range(N_Z + 1)]
MASA_KG = [
    RHO_G_CM3 * (_vol_zona_mm3(R_EXT_MM, Z_BORDES[i], Z_BORDES[i + 1])
                 - _vol_zona_mm3(R_INT_MM, Z_BORDES[i], Z_BORDES[i + 1])) / 1000.0 / 1000.0
    for i in range(N_Z)
]
Z_CENTROS = [0.5 * (Z_BORDES[i] + Z_BORDES[i + 1]) for i in range(N_Z)]


# Verificar que no exista ya
if Path(OUTPUT_DIR).exists():
    print(f"[INFO] Ya existe '{OUTPUT_DIR}'. Corrida omitida para no sobreescribir.")
    print(f"       Eliminá la carpeta manualmente si querés repetir la simulación.")
    sys.exit(0)
Path(OUTPUT_DIR).parent.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════
#  SIMULACIÓN
# ══════════════════════════════════════════════════════════
sim = gate.Simulation()
sim.verbose_level         = gate.logger.WARNING
sim.running_verbose_level = 0
sim.g4_verbose            = False
sim.g4_verbose_level      = 0
sim.visu                  = False
sim.random_engine         = "MersenneTwister"
sim.random_seed           = "auto"
sim.output_dir            = OUTPUT_DIR
sim.number_of_threads     = int(os.environ.get("GATE_THREADS", 2))

m    = gate.g4_units.m
mm   = gate.g4_units.mm
MeV  = gate.g4_units.MeV
gcm3 = gate.g4_units.g / (gate.g4_units.cm**3)

# ══════════════════════════════════════════════════════════
#  MUNDO
# ══════════════════════════════════════════════════════════
world          = sim.world
world.size     = [3 * m, 3 * m, 3 * m]
world.material = "G4_AIR"

# ══════════════════════════════════════════════════════════
#  MATERIALES
# ══════════════════════════════════════════════════════════
sim.volume_manager.material_database.add_material_nb_atoms(
    "Tungsten", ["W"], [1], 19.3 * gcm3   # tungsteno puro, densidad estándar
)

# ══════════════════════════════════════════════════════════
#  CONTENEDOR DE TUNGSTENO (CT/A-30W)
#  Radial : cavidad 16.75 mm → +29.5 mm de W → externo 46.25 mm
#  Axial  : cavidad dz=28.5 mm → +21.75 mm de W → externo dz=50.25 mm
#  Tungsteno puro, sin carcasa de acero (el datasheet no deja espacio radial).
# ══════════════════════════════════════════════════════════
W_Pared             = sim.add_volume("Tubs", "W_Pared")
W_Pared.mother      = "world"
W_Pared.rmin        = 16.75 * mm
W_Pared.rmax        = 46.25 * mm
W_Pared.dz          = 28.5 * mm
W_Pared.material    = "Tungsten"
W_Pared.color       = [0.4, 0.4, 0.45, 0.6]

W_Base             = sim.add_volume("Tubs", "W_Base")
W_Base.mother      = "world"
W_Base.rmin        = 0 * mm
W_Base.rmax        = 46.25 * mm
W_Base.dz          = 10.875 * mm            # 21.75 / 2
W_Base.material    = "Tungsten"
W_Base.color       = [0.4, 0.4, 0.45, 0.8]
W_Base.translation = [0, 0, -39.375 * mm]   # -(28.5 + 10.875)

W_Tapa             = sim.add_volume("Tubs", "W_Tapa")
W_Tapa.mother      = "world"
W_Tapa.rmin        = 0 * mm
W_Tapa.rmax        = 46.25 * mm
W_Tapa.dz          = 10.875 * mm
W_Tapa.material    = "Tungsten"
W_Tapa.color       = [0.4, 0.4, 0.45, 0.8]
W_Tapa.translation = [0, 0, 39.375 * mm]

# ══════════════════════════════════════════════════════════
#  CAVIDAD DE AIRE (radio 16.75 mm, dz 28.5 mm)
# ══════════════════════════════════════════════════════════
Cavidad_Aire             = sim.add_volume("Tubs", "Cavidad_Aire")
Cavidad_Aire.mother      = "world"
Cavidad_Aire.rmin        = 0 * mm
Cavidad_Aire.rmax        = 16.75 * mm
Cavidad_Aire.dz          = 28.5 * mm
Cavidad_Aire.material    = "G4_AIR"
Cavidad_Aire.color       = [0.9, 0.9, 1.0, 0.1]

# ══════════════════════════════════════════════════════════
#  VIAL DE VIDRIO — apoyado en el piso de la cavidad (z = -28.5 mm)
# ══════════════════════════════════════════════════════════
Glass_Wall             = sim.add_volume("Tubs", "Glass_Wall")
Glass_Wall.mother      = "Cavidad_Aire"
Glass_Wall.rmin        = 11.0 * mm
Glass_Wall.rmax        = 12.5 * mm
Glass_Wall.dz          = (45.0 / 2.0) * mm
Glass_Wall.material    = "G4_Pyrex_Glass"
Glass_Wall.color       = [0.0, 0.8, 0.8, 0.5]
Glass_Wall.translation = [0, 0, -4.5 * mm]

Glass_Bottom             = sim.add_volume("Tubs", "Glass_Bottom")
Glass_Bottom.mother      = "Cavidad_Aire"
Glass_Bottom.rmin        = 0 * mm
Glass_Bottom.rmax        = 11.0 * mm
Glass_Bottom.dz          = (1.5 / 2.0) * mm
Glass_Bottom.material    = "G4_Pyrex_Glass"
Glass_Bottom.color       = [0.0, 0.8, 0.8, 0.5]
Glass_Bottom.translation = [0, 0, -27.75 * mm]

# ══════════════════════════════════════════════════════════
#  AGUA — 10 mL
# ══════════════════════════════════════════════════════════
waterCil             = sim.add_volume("Tubs", "waterCil")
waterCil.mother      = "Cavidad_Aire"
waterCil.rmin        = 0 * mm
waterCil.rmax        = 11.0 * mm
waterCil.dz          = (26.3 / 2.0) * mm
waterCil.material    = "G4_WATER"
waterCil.color       = [0.0, 0.2, 1.0, 0.7]
waterCil.translation = [0, 0, -13.85 * mm]

# ══════════════════════════════════════════════════════════
#  DETECTOR — cáscara esférica de tejido blando ICRP centrada en la fuente
#  Voxelización: 1 × 1 × N_Z (rebanadas en z). Un solo detector por simulación.
# ══════════════════════════════════════════════════════════
det             = sim.add_volume("Sphere", f"det_{DIST_MM}mm")
det.mother      = "world"
det.rmin        = R_INT_MM * mm
det.rmax        = R_EXT_MM * mm
det.translation = [0, 0, ZC_MM * mm]
det.material    = "G4_TISSUE_SOFT_ICRP"
det.color       = [1.0, 0.2, 0.2, 0.3]

actor                         = sim.add_actor("DoseActor", f"dose_det_{DIST_MM}mm")
actor.attached_to             = f"det_{DIST_MM}mm"
actor.output_filename         = f"dose_det_{DIST_MM}mm.mhd"
actor.size                    = [1, 1, N_Z]
actor.spacing                 = [LADO_MM * mm, LADO_MM * mm, DZ_MM * mm]
actor.hit_type                = "pre"
actor.dose.active             = True
actor.dose_uncertainty.active = True

# ══════════════════════════════════════════════════════════
#  ESTADÍSTICAS
# ══════════════════════════════════════════════════════════
stats                  = sim.add_actor("SimulationStatisticsActor", "Stats")
stats.track_types_flag = True
stats.output_filename  = "stats.txt"

# ══════════════════════════════════════════════════════════
#  FÍSICA
# ══════════════════════════════════════════════════════════
sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option4"
sim.physics_manager.enable_decay      = True

# ══════════════════════════════════════════════════════════
#  FUENTE — F-18 en el vial
# ══════════════════════════════════════════════════════════
n_por_hilo = max(1, N_PRIMARIES // sim.number_of_threads)
total_real = n_por_hilo * sim.number_of_threads

source                 = sim.add_source("GenericSource", "F18_FDG")
source.particle        = "ion 9 18"
source.energy.mono     = 0 * MeV
source.attached_to     = "waterCil"
source.direction.type  = "iso"
source.n               = n_por_hilo
source.position.type   = "cylinder"
source.position.radius = 11.0 * mm
source.position.dz     = (26.3 / 2.0) * mm

# ══════════════════════════════════════════════════════════
#  EJECUCIÓN
# ══════════════════════════════════════════════════════════
sim.check_volumes_overlap = True

print(f"[TUNGSTENO] Distancia: {DIST_MM} mm | Primarios: {total_real:,} | Threads: {sim.number_of_threads}")
print(f"[TUNGSTENO] Esfera R={R_INT_MM:g} mm, espesor {ESPESOR_MM:g} mm, {N_Z} rebanadas en z")
inicio = time.time()
sim.run()
duracion_s = time.time() - inicio

print("=" * 55)
print(f"RESUMEN — TUNGSTENO {DIST_MM} mm")
print("=" * 55)
print(f"Primarios simulados : {total_real:,}")
print(f"Hilos usados        : {sim.number_of_threads}")
print(f"Duración            : {duracion_s:.1f} s  ({duracion_s/60:.2f} min)")
print(f"Carpeta de salida   : {Path(OUTPUT_DIR).resolve()}")
print("=" * 55)

# ══════════════════════════════════════════════════════════
#  METADATA
# ══════════════════════════════════════════════════════════
metadata = {
    "material_blindaje":      "Tungsteno (CT/A-30W)",
    "n_primarios_simulados":  total_real,
    "actividad_objetivo_mci": ACTIVIDAD_OBJETIVO_MCI,
    "physics_list":           sim.physics_manager.physics_list_name,
    "fuente":                 "F-18 (ion 9 18), waterCil, cilindro",
    "detector": {
        "nombre":        f"det_{DIST_MM}mm",
        "tipo":          f"Cáscara esférica R={R_INT_MM:g}–{R_EXT_MM:g} mm centrada en la fuente",
        "distancia_mm":  DIST_MM,
        "espesor_mm":    ESPESOR_MM,
        "n_z":           N_Z,
        "centro_esfera_mm": [0.0, 0.0, ZC_MM],
        "material":      "G4_TISSUE_SOFT_ICRP",
        "densidad_g_cm3": RHO_G_CM3,
        # rebanadas en z, relativas al centro de la esfera (orden creciente en z)
        "z_bordes_mm":   Z_BORDES,
        "z_centros_mm":  Z_CENTROS,
        "masa_kg":       MASA_KG,
        "polar_centro_deg": [math.degrees(math.acos(max(-1.0, min(1.0, zc / R_INT_MM)))) for zc in Z_CENTROS],
        "nota_dosis":    "Dosis[Gy] = Edep[MeV]*1.602e-13/masa_kg por rebanada. NO usar el *_dose.mhd (masa de caja).",
    },
    "fuente_centro_mm":       [0.0, 0.0, -13.85],
    "blindaje_radial_mm": {
        "agua":         [0, 11.0],
        "vidrio":       [11.0, 12.5],
        "cavidad_aire": [12.5, 16.75],
        "tungsteno":    [16.75, 46.25],
    },
    "geometria_axial_mm": {
        "agua":              [-27.0, -0.7],
        "cavidad_aire":      [-28.5, 28.5],
        "tungsteno_base":    [-50.25, -28.5],
        "tungsteno_tapa":    [28.5, 50.25],
    },
    "mu_511keV_cm-1": {
        "agua":       0.0966,
        "vidrio":     0.112,
        "aire":       0.000112,
        "tungsteno":  2.598,   # 0.1346 cm²/g (NIST, interp. 0.5–0.6 MeV) × 19.3 g/cm³
    },
    "nota": "Un detector por simulacion — sin interferencia entre distancias.",
}
ruta_metadata = Path(OUTPUT_DIR) / "metadata_simulacion.json"
ruta_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
