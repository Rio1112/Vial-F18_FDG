#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vial de F-18 SIN blindaje — detector ESFÉRICO (cáscara de tejido blando) centrado en la fuente.
Uso: python vial_no_blindaje_v4.py [distancia_mm] [zc_mm] [millones_primarios]
     (por defecto 200, 0 y 5)
  zc_mm: z del centro del agua (y de la esfera). Con 0 todo está en el origen; con -22.35
         se prueba una esfera trasladada (como en el contenedor de plomo).
Escribe en resultados/sin_blindaje/esfera_<dist>mm[_zc<zc>]/ (no sobreescribe).
"""

import json
import math
import os
import sys
import time
from pathlib import Path

import opengate as gate

DIST_MM = int(sys.argv[1]) if len(sys.argv) > 1 else 200
if DIST_MM not in [200, 400, 600, 800, 1000]:
    print(f"Distancia {DIST_MM} no reconocida. Usar: 200, 400, 600, 800 o 1000.")
    sys.exit(1)
ZC_MM = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
N_PRIMARIES = int(float(sys.argv[3]) * 1_000_000) if len(sys.argv) > 3 else 5_000_000
ACTIVIDAD_OBJETIVO_MCI = 100.0
OUTPUT_DIR = f"./resultados/sin_blindaje/esfera_{DIST_MM}mm" + (f"_zc{ZC_MM:g}" if ZC_MM != 0 else "")

# ── Detector: cáscara esférica de tejido blando centrada en la fuente ──
ESPESOR_MM = 5.0
N_Z        = 11
RHO_G_CM3  = 1.03

R_INT_MM = float(DIST_MM)
R_EXT_MM = R_INT_MM + ESPESOR_MM
LADO_MM  = 2.0 * R_EXT_MM
DZ_MM    = LADO_MM / N_Z

def _vol_zona_mm3(R, a, b):
    a = max(-R, min(R, a)); b = max(-R, min(R, b))
    return math.pi * (R**2 * (b - a) - (b**3 - a**3) / 3.0)

Z_BORDES = [-R_EXT_MM + i * DZ_MM for i in range(N_Z + 1)]
MASA_KG = [
    RHO_G_CM3 * (_vol_zona_mm3(R_EXT_MM, Z_BORDES[i], Z_BORDES[i + 1])
                 - _vol_zona_mm3(R_INT_MM, Z_BORDES[i], Z_BORDES[i + 1])) / 1000.0 / 1000.0
    for i in range(N_Z)
]
Z_CENTROS = [0.5 * (Z_BORDES[i] + Z_BORDES[i + 1]) for i in range(N_Z)]

if Path(OUTPUT_DIR).exists():
    print(f"[INFO] Ya existe '{OUTPUT_DIR}'. Corrida omitida para no sobreescribir.")
    sys.exit(0)
Path(OUTPUT_DIR).parent.mkdir(parents=True, exist_ok=True)

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

m   = gate.g4_units.m
mm  = gate.g4_units.mm
MeV = gate.g4_units.MeV

world          = sim.world
world.size     = [3 * m, 3 * m, 3 * m]
world.material = "G4_AIR"

# Vial de vidrio + agua (10 mL) en el aire; el centro del agua queda en z = ZC_MM
Glass_Wall             = sim.add_volume("Tubs", "Glass_Wall")
Glass_Wall.mother      = "world"
Glass_Wall.rmin        = 11.0 * mm
Glass_Wall.rmax        = 12.5 * mm
Glass_Wall.dz          = (45.0 / 2.0) * mm
Glass_Wall.material    = "G4_Pyrex_Glass"
Glass_Wall.translation = [0, 0, (ZC_MM + 9.35) * mm]

Glass_Bottom             = sim.add_volume("Tubs", "Glass_Bottom")
Glass_Bottom.mother      = "world"
Glass_Bottom.rmin        = 0 * mm
Glass_Bottom.rmax        = 11.0 * mm
Glass_Bottom.dz          = (1.5 / 2.0) * mm
Glass_Bottom.material    = "G4_Pyrex_Glass"
Glass_Bottom.translation = [0, 0, (ZC_MM - 13.9) * mm]

waterCil             = sim.add_volume("Tubs", "waterCil")
waterCil.mother      = "world"
waterCil.rmin        = 0 * mm
waterCil.rmax        = 11.0 * mm
waterCil.dz          = (26.3 / 2.0) * mm
waterCil.material    = "G4_WATER"
waterCil.translation = [0, 0, ZC_MM * mm]

# Detector: cáscara esférica, rebanadas en z
det             = sim.add_volume("Sphere", f"det_{DIST_MM}mm")
det.mother      = "world"
det.rmin        = R_INT_MM * mm
det.rmax        = R_EXT_MM * mm
det.translation = [0, 0, ZC_MM * mm]
det.material    = "G4_TISSUE_SOFT_ICRP"

actor                         = sim.add_actor("DoseActor", f"dose_det_{DIST_MM}mm")
actor.attached_to             = f"det_{DIST_MM}mm"
actor.output_filename         = f"dose_det_{DIST_MM}mm.mhd"
actor.size                    = [1, 1, N_Z]
actor.spacing                 = [LADO_MM * mm, LADO_MM * mm, DZ_MM * mm]
actor.hit_type                = "pre"
actor.dose.active             = True
actor.dose_uncertainty.active = True

stats                  = sim.add_actor("SimulationStatisticsActor", "Stats")
stats.track_types_flag = True
stats.output_filename  = "stats.txt"

sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option4"
sim.physics_manager.enable_decay      = True

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

sim.check_volumes_overlap = True

print(f"[SIN BLINDAJE] Distancia: {DIST_MM} mm | zc {ZC_MM:g} mm | Primarios: {total_real:,} | Threads: {sim.number_of_threads}")
inicio = time.time()
sim.run()
duracion_s = time.time() - inicio
print(f"[SIN BLINDAJE] Duración: {duracion_s:.1f} s ({duracion_s/60:.2f} min) | Salida: {Path(OUTPUT_DIR).resolve()}")

metadata = {
    "material_blindaje":      "Ninguno (vial en aire)",
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
        "z_bordes_mm":   Z_BORDES,
        "z_centros_mm":  Z_CENTROS,
        "masa_kg":       MASA_KG,
        "polar_centro_deg": [math.degrees(math.acos(max(-1.0, min(1.0, zc / R_INT_MM)))) for zc in Z_CENTROS],
        "nota_dosis":    "Dosis[Gy] = Edep[MeV]*1.602e-13/masa_kg por rebanada. NO usar el *_dose.mhd (masa de caja).",
    },
    "fuente_centro_mm":       [0.0, 0.0, ZC_MM],
}
(Path(OUTPUT_DIR) / "metadata_simulacion.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
