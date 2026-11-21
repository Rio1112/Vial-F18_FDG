#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contenedor de plomo (CT/A-30) — detector ESFÉRICO (cáscara) a distancia variable.
Uso: python vial_plomo_v4.py <distancia_mm>
Ejemplo: python vial_plomo_v4.py 200

Cada corrida escribe en su propia carpeta output_plomo_plano_<dist>mm/
y no sobreescribe resultados previos (ni los de la versión con cubos).
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
    print("Uso: python vial_plomo_v4.py <distancia_mm> [millones_primarios]")
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
OUTPUT_DIR             = f"./resultados/plomo/esfera_{DIST_MM}mm"

# ── Detector: CÁSCARA ESFÉRICA de tejido blando centrada en la fuente ──
# Radio interior = distancia a la fuente. Todos los fotones que salen la cruzan en
# incidencia normal. Se divide en N_Z rebanadas en z (zonas de igual área si z es uniforme):
# la rebanada central es el "cinturón" a la altura de la fuente (donde está el técnico).
# La dosis se calcula con la Edep y la masa real de cada zona (el DoseActor usaría la masa
# de una caja), por eso la masa por rebanada se guarda en los metadatos.
ESPESOR_MM = 5.0          # espesor de la cáscara
N_Z        = 11           # rebanadas en z (impar: la central queda en el ecuador)
ZC_MM      = -22.35         # centro de la esfera = centro del agua (fuente)
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
    "StainlessSteel", ["Fe", "Cr", "Ni"], [70, 20, 10], 7.81 * gcm3
)
sim.volume_manager.material_database.add_material_nb_atoms(
    "Lead", ["Pb"], [1], 11.34 * gcm3
)

# ══════════════════════════════════════════════════════════
#  ACERO INOXIDABLE — carcasa exterior
# ══════════════════════════════════════════════════════════
Ac_Pared             = sim.add_volume("Tubs", "Ac_Pared")
Ac_Pared.mother      = "world"
Ac_Pared.rmin        = 48.5 * mm
Ac_Pared.rmax        = 50.5 * mm
Ac_Pared.dz          = (115.5 / 2.0) * mm
Ac_Pared.material    = "StainlessSteel"
Ac_Pared.color       = [0.7, 0.7, 0.7, 0.3]

Ac_Base             = sim.add_volume("Tubs", "Ac_Base")
Ac_Base.mother      = "world"
Ac_Base.rmin        = 0 * mm
Ac_Base.rmax        = 48.5 * mm
Ac_Base.dz          = 1.0 * mm
Ac_Base.material    = "StainlessSteel"
Ac_Base.color       = [0.7, 0.7, 0.7, 0.8]
Ac_Base.translation = [0, 0, -56.75 * mm]

Ac_Tapa             = sim.add_volume("Tubs", "Ac_Tapa")
Ac_Tapa.mother      = "world"
Ac_Tapa.rmin        = 0 * mm
Ac_Tapa.rmax        = 48.5 * mm
Ac_Tapa.dz          = 1.0 * mm
Ac_Tapa.material    = "StainlessSteel"
Ac_Tapa.color       = [0.7, 0.7, 0.7, 0.8]
Ac_Tapa.translation = [0, 0, 56.75 * mm]

# ══════════════════════════════════════════════════════════
#  PLOMO
# ══════════════════════════════════════════════════════════
Pb_Pared             = sim.add_volume("Tubs", "Pb_Pared")
Pb_Pared.mother      = "world"
Pb_Pared.rmin        = 16.5 * mm
Pb_Pared.rmax        = 48.5 * mm
Pb_Pared.dz          = 37.0 * mm
Pb_Pared.material    = "Lead"
Pb_Pared.color       = [0.2, 0.7, 0.2, 0.6]

Pb_Base             = sim.add_volume("Tubs", "Pb_Base")
Pb_Base.mother      = "world"
Pb_Base.rmin        = 0 * mm
Pb_Base.rmax        = 48.5 * mm
Pb_Base.dz          = (18.75 / 2.0) * mm
Pb_Base.material    = "Lead"
Pb_Base.color       = [0.2, 0.7, 0.2, 0.8]
Pb_Base.translation = [0, 0, -46.375 * mm]

Pb_Tapa             = sim.add_volume("Tubs", "Pb_Tapa")
Pb_Tapa.mother      = "world"
Pb_Tapa.rmin        = 0 * mm
Pb_Tapa.rmax        = 48.5 * mm
Pb_Tapa.dz          = (18.75 / 2.0) * mm
Pb_Tapa.material    = "Lead"
Pb_Tapa.color       = [0.2, 0.7, 0.2, 0.8]
Pb_Tapa.translation = [0, 0, 46.375 * mm]

# ══════════════════════════════════════════════════════════
#  CAVIDAD DE AIRE
# ══════════════════════════════════════════════════════════
Cavidad_Aire             = sim.add_volume("Tubs", "Cavidad_Aire")
Cavidad_Aire.mother      = "world"
Cavidad_Aire.rmin        = 0 * mm
Cavidad_Aire.rmax        = 16.5 * mm
Cavidad_Aire.dz          = 37.0 * mm
Cavidad_Aire.material    = "G4_AIR"
Cavidad_Aire.color       = [0.9, 0.9, 1.0, 0.1]

# ══════════════════════════════════════════════════════════
#  VIAL DE VIDRIO
# ══════════════════════════════════════════════════════════
Glass_Wall             = sim.add_volume("Tubs", "Glass_Wall")
Glass_Wall.mother      = "Cavidad_Aire"
Glass_Wall.rmin        = 11.0 * mm
Glass_Wall.rmax        = 12.5 * mm
Glass_Wall.dz          = (45.0 / 2.0) * mm
Glass_Wall.material    = "G4_Pyrex_Glass"
Glass_Wall.color       = [0.0, 0.8, 0.8, 0.5]
Glass_Wall.translation = [0, 0, -13.0 * mm]

Glass_Bottom             = sim.add_volume("Tubs", "Glass_Bottom")
Glass_Bottom.mother      = "Cavidad_Aire"
Glass_Bottom.rmin        = 0 * mm
Glass_Bottom.rmax        = 11.0 * mm
Glass_Bottom.dz          = (1.5 / 2.0) * mm
Glass_Bottom.material    = "G4_Pyrex_Glass"
Glass_Bottom.color       = [0.0, 0.8, 0.8, 0.5]
Glass_Bottom.translation = [0, 0, -36.25 * mm]

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
waterCil.translation = [0, 0, -22.35 * mm]

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

print(f"[PLOMO] Distancia: {DIST_MM} mm | Primarios: {total_real:,} | Threads: {sim.number_of_threads}")
print(f"[PLOMO] Esfera R={R_INT_MM:g} mm, espesor {ESPESOR_MM:g} mm, {N_Z} rebanadas en z")
inicio = time.time()
sim.run()
duracion_s = time.time() - inicio

print("=" * 55)
print(f"RESUMEN — PLOMO {DIST_MM} mm")
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
    "material_blindaje":      "Plomo (CT/A-30)",
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
    "fuente_centro_mm":       [0.0, 0.0, -22.35],
    "blindaje_radial_mm": {
        "agua":         [0, 11.0],
        "vidrio":       [11.0, 12.5],
        "cavidad_aire": [12.5, 16.5],
        "plomo":        [16.5, 48.5],
        "acero":        [48.5, 50.5],
    },
    "mu_511keV_cm-1": {
        "agua":   0.0966,
        "vidrio": 0.112,
        "aire":   0.000112,
        "plomo":  1.781,
        "acero":  0.624,
    },
    "nota": "Un detector por simulacion — sin interferencia entre distancias.",
}
ruta_metadata = Path(OUTPUT_DIR) / "metadata_simulacion.json"
ruta_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
