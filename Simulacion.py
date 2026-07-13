#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Este script SOLO construye la geometría, corre la simulación y guarda los
resultados en disco (.mhd/.raw + metadata_simulacion.json). No hace ningún
análisis, gráfico ni cálculo de dosis/transmitancia — eso lo hace un jupyter
externo.
"""

import json
import time
from pathlib import Path

import opengate as gate

if __name__ == "__main__":

    # N_PRIMARIES: Primarios simulados, puede cambiarse desde acá
    ACTIVIDAD_OBJETIVO_MCI = 10.0
    N_PRIMARIES            = 100_000_000

    sim = gate.Simulation()


    sim.verbose_level         = gate.logger.WARNING
    sim.running_verbose_level = 0   
    sim.g4_verbose            = False
    sim.g4_verbose_level      = 0
    sim.visu                  = False
    sim.random_engine         = "MersenneTwister"
    sim.random_seed           = "auto"
    sim.output_dir            = "./output"
    sim.number_of_threads     = 1

    # --------------------
    # Unidades
    # --------------------
    m    = gate.g4_units.m
    cm   = gate.g4_units.cm
    mm   = gate.g4_units.mm
    MeV  = gate.g4_units.MeV
    gcm3 = gate.g4_units.g / (gate.g4_units.cm**3)

    # ======
    #  MUNDO
    # ======
    world          = sim.world
    world.size     = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # ===========
    #  MATERIALES
    # ===========
    sim.volume_manager.material_database.add_material_nb_atoms(
        "StainlessSteel", ["Fe", "Cr", "Ni"], [70, 20, 10], 7.81 * gcm3
    )
    sim.volume_manager.material_database.add_material_nb_atoms(
        "Lead", ["Pb"], [1], 11.4 * gcm3
    )

    # ===================================
    #  ACERO INOXIDABLE — carcasa exterior
    # ===================================
    Ac_Pared             = sim.add_volume("Tubs", "Ac_Pared")
    Ac_Pared.mother      = "world"
    Ac_Pared.rmin        = 48.5 * mm
    Ac_Pared.rmax        = 50.5 * mm
    Ac_Pared.dz          = (115.5 / 2.0) * mm
    Ac_Pared.material    = "StainlessSteel"
    Ac_Pared.color       = [0.7, 0.7, 0.7, 0.3]
    Ac_Pared.translation = [0, 0, 0]

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

    # ======
    #  PLOMO
    # ======
    Pb_Pared             = sim.add_volume("Tubs", "Pb_Pared")
    Pb_Pared.mother      = "world"
    Pb_Pared.rmin        = 16.5 * mm
    Pb_Pared.rmax        = 48.5 * mm
    Pb_Pared.dz          = 37.0 * mm
    Pb_Pared.material    = "Lead"
    Pb_Pared.color       = [0.2, 0.7, 0.2, 0.6]
    Pb_Pared.translation = [0, 0, 0]

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

    # =========================
    #  CAVIDAD DE AIRE interior
    # =========================
    Cavidad_Aire             = sim.add_volume("Tubs", "Cavidad_Aire")
    Cavidad_Aire.mother      = "world"
    Cavidad_Aire.rmin        = 0 * mm
    Cavidad_Aire.rmax        = 16.5 * mm
    Cavidad_Aire.dz          = 37.0 * mm
    Cavidad_Aire.material    = "G4_AIR"
    Cavidad_Aire.color       = [0.9, 0.9, 1.0, 0.1]
    Cavidad_Aire.translation = [0, 0, 0]

    # ==============
    #  VIAL DE VIDRIO
    # ==============
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

    # ==================================================
    #  AGUA (10 mL) — disolución de F-18 FDG
    # ==================================================
    waterCil             = sim.add_volume("Tubs", "waterCil")
    waterCil.mother      = "Cavidad_Aire"
    waterCil.rmin        = 0 * mm
    waterCil.rmax        = 11.0 * mm
    waterCil.dz          = (26.3 / 2.0) * mm
    waterCil.material    = "G4_WATER"
    waterCil.color       = [0.0, 0.2, 1.0, 0.7]
    waterCil.translation = [0, 0, -22.35 * mm]

    # ==================================================
    #  DETECTORES
    # ==================================================
    Z_ref = 0 * mm   # centro del contenedor

    # ── Grupo A — justo afuera del contenedor ─────────
    det_palma             = sim.add_volume("Box", "det_palma")
    det_palma.mother      = "world"
    det_palma.size        = [95 * mm, 1 * mm, 70 * mm]   # area de agarre de una mano sobre el vial
    det_palma.material    = "G4_TISSUE_SOFT_ICRP"
    det_palma.color       = [1.5, 0.5, 0.0, 0.8]
    det_palma.translation = [0 * mm, -55 * mm, Z_ref]

    

    det_dedos            = sim.add_volume("Box", "det_dedos")
    det_dedos.mother      = "world"
    det_dedos.size        = [1 * mm, 40.0 * mm, 70 * mm]
    det_dedos.material    = "G4_TISSUE_SOFT_ICRP"
    det_dedos.color       = [1.0, 0.0, 0.5, 0.8]
    det_dedos.translation = [50*mm , -35* mm, 0 * mm]  

    # ── Grupo B — técnico a 15cm DE LA SUPERFICIE del contenedor ──────
    DISTANCIA_A_SUPERFICIE_MM = 200.5   # 50.5mm(radio externo) + 150mm(15cm)

    det_torso             = sim.add_volume("Box", "det_torso")
    det_torso.mother      = "world"
    det_torso.size        = [1 * mm, 300  * mm, 400 * mm]
    det_torso.material    = "G4_TISSUE_SOFT_ICRP"   
    det_torso.color       = [1.0, 0.8, 0.6, 0.8]
    det_torso.translation = [-DISTANCIA_A_SUPERFICIE_MM * mm, 0, Z_ref]

    det_cabeza             = sim.add_volume("Box", "det_cabeza")
    det_cabeza.mother      = "world"
    det_cabeza.size        = [1 * mm, 130 * mm, 170 * mm]
    det_cabeza.material    = "G4_TISSUE_SOFT_ICRP"   
    det_cabeza.color       = [0.0, 0.8, 1.0, 0.8]
    det_cabeza.translation = [-DISTANCIA_A_SUPERFICIE_MM * mm, 0, Z_ref + 450 * mm]

    det_manos             = sim.add_volume("Box", "det_manos")
    det_manos.mother      = "world"
    det_manos.size        = [1 * mm, 80 * mm, 150  * mm]
    det_manos.material    = "G4_TISSUE_SOFT_ICRP"  
    det_manos.color       = [1.0, 0.4, 0.0, 0.8]
    det_manos.translation = [-DISTANCIA_A_SUPERFICIE_MM * mm, 200 * mm , Z_ref - 180 * mm]

    dimensiones_detectores = {
        "det_palma":  ([95, 1, 70], [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_dedos": ([1, 40, 70], [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_torso":    ([1, 300, 400], [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_cabeza":     ([1, 130, 170], [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_manos":    ([1, 80, 150], [1.0 * mm, 1.0 * mm, 1.0 * mm]),
    }
    for nombre, (size_real, spacing_real) in dimensiones_detectores.items():
        actor                          = sim.add_actor("DoseActor", f"dose_{nombre}")
        actor.attached_to              = nombre
        actor.size                     = size_real
        actor.spacing                  = spacing_real
        actor.hit_type                 = "random"
        actor.dose.active              = True
        actor.dose_uncertainty.active  = True

    # ==================================================
    #  PERFILES DE LÍNEA — energía vs posición (radial y axial)
    # ==================================================
    dose_perfil_radial             = sim.add_actor("DoseActor", "dose_perfil_radial")
    dose_perfil_radial.attached_to = "world"
    dose_perfil_radial.size        = [880, 5, 5]     
    dose_perfil_radial.spacing     = [0.5 * mm, 5.0 * mm, 5.0 * mm]   
    dose_perfil_radial.translation = [0, 0, 0]        
    dose_perfil_radial.hit_type    = "random"
    dose_perfil_radial.dose.active = True

#    dose_perfil_axial             = sim.add_actor("DoseActor", "dose_perfil_axial")
#    dose_perfil_axial.attached_to = "world"
#    dose_perfil_axial.size        = [5, 5, 560]     
#    dose_perfil_axial.spacing     = [5.0 * mm, 5.0 * mm, 0.25 * mm] 
#    dose_perfil_axial.translation = [0, 0, 0]
#    dose_perfil_axial.hit_type    = "random"
#    dose_perfil_axial.dose.active = True

    # ==================================================
    #  ESTADÍSTICAS 
    # ==================================================
    stats                     = sim.add_actor("SimulationStatisticsActor", "Stats")
    stats.track_types_flag    = True
    stats.output_filename     = "stats.txt"

    # ==================================================
    #  FUENTE — F-18 FDG disuelto en el agua
    # ==================================================
    sim.physics_manager.physics_list_name = "QGSP_BIC_EMZ"
    sim.physics_manager.enable_decay      = True

    source                 = sim.add_source("GenericSource", "F18_FDG")
    source.particle        = "ion 9 18"
    source.energy.mono     = 0 * MeV
    source.attached_to     = "waterCil"
    source.direction.type  = "iso"
    source.n               = N_PRIMARIES
    source.position.type   = "cylinder"
    source.position.radius = 11.0 * mm
    source.position.dz     = (26.3 / 2.0) * mm

    # ==================================================
    #  VERIFICACIÓN Y EJECUCIÓN
    # ==================================================
    sim.check_volumes_overlap = True

    inicio = time.time()
    sim.run()
    duracion_s = time.time() - inicio

    # ==================================================
    #  RESUMEN BÁSICO 
    # ==================================================
    print("=" * 55)
    print("RESUMEN DE LA SIMULACIÓN")
    print("=" * 55)
    print(f"Primarios simulados : {N_PRIMARIES:,}")
    print(f"Hilos usados         : {sim.number_of_threads}")
    print(f"Physics list          : {sim.physics_manager.physics_list_name}")
    print(f"Duración              : {duracion_s:.1f} s  ({duracion_s/60:.2f} min)")
    print(f"Carpeta de salida     : {Path(sim.output_dir).resolve()}")
    print("=" * 55)

    # ==================================================
    #  METADATA 
    # ==================================================
    metadata = {
        "n_primarios_simulados": N_PRIMARIES,
        "actividad_objetivo_mci": ACTIVIDAD_OBJETIVO_MCI,
        "physics_list": sim.physics_manager.physics_list_name,
        "fuente": "F-18 (ion 9 18), disuelto en waterCil, geometria cilindro",
        "energia_media_por_decaimiento_MeV": 0.9686 * 0.2495 + 1.9372 * 0.511,
        "geometria": {
            "radial_mm": {
                "agua":         [0, 11.0],
                "vidrio":       [11.0, 12.5],
                "cavidad_aire": [12.5, 16.5],
                "plomo":        [16.5, 48.5],
                "acero":        [48.5, 50.5],
                "det_lateral_centro": 55.0,
                "det_dedos_centro": 50,
                "det_torso_centro": 200.5,
            },
            "axial_mm": {
                "agua":         [-35.5, -9.2],
                "cavidad_aire": [-9.2, 37.0],
                "plomo":        [37.0, 55.75],
                "acero":        [55.75, 57.75]
            },
        },
    }
    ruta_metadata = Path(sim.output_dir) / "metadata_simulacion.json"
    ruta_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
