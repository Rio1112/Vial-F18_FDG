#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Variante del contenedor con blindaje de TUNGSTENO (CT/A-30W, datasheet TEMA
Sinergie Rev.01), en vez del contenedor de plomo+acero (CT/A-30).

Diferencias vs. la versión de plomo:
  - Geometría del contenedor: pura tungsteno (SIN carcasa de acero separada
    -- el radio externo del datasheet coincide EXACTO con radio_cavidad +
    29.5mm de tungsteno, sin espacio para una capa de acero adicional).
  - Cavidad interna más chica (33.5mm diámetro x 57mm altura, vs 33mm x 74mm
    del contenedor de plomo) -> el vial de vidrio se REPOSICIONÓ (no se
    resize) para seguir apoyado en el piso de la cavidad, igual que antes.
  - Espesor de tungsteno: 29.5mm lateral (coincide exacto con el dato del
    datasheet, confirmado por radios). Para base/tapa, el datasheet dice
    "29.5mm alrededor" como simplificación, pero la altura real (externa
    sin tapa vs interna) da 21.75mm -- se usó el valor DERIVADO (21.75mm),
    igual que hicimos con el vial de plomo, donde el ~30mm redondeado del
    datasheet no coincidía con el espesor real calculado (32mm).

Todo lo demás (detectores, fuente F-18, física, actores, estructura del
metadata) se mantuvo igual a la versión de plomo.
"""

import json
import time
from pathlib import Path

import opengate as gate

if __name__ == "__main__":

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
    sim.output_dir            = "./output_tungsteno"
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
        "Tungsten", ["W"], [1], 19.3 * gcm3   # densidad estandar del tungsteno puro
    )

    # ===================================
    #  CONTENEDOR DE TUNGSTENO (CT/A-30W)
    #  Radial : cavidad 16.75mm -> +29.5mm de W -> externo 46.25mm (coincide
    #           exacto con el datasheet: diametro externo 92.5mm)
    #  Axial  : cavidad dz=28.5mm -> +21.75mm de W -> externo dz=50.25mm
    #           (coincide exacto con "altura externa sin tapa" = 100.5mm)
    #  Pura tungsteno, sin carcasa de acero adicional (el datasheet no deja
    #  espacio radial para eso).
    # ===================================
    W_Pared             = sim.add_volume("Tubs", "W_Pared")
    W_Pared.mother      = "world"
    W_Pared.rmin        = 16.75 * mm
    W_Pared.rmax        = 46.25 * mm
    W_Pared.dz          = 28.5 * mm
    W_Pared.material    = "Tungsten"
    W_Pared.color       = [0.4, 0.4, 0.45, 0.6]
    W_Pared.translation = [0, 0, 0]

    W_Base             = sim.add_volume("Tubs", "W_Base")
    W_Base.mother      = "world"
    W_Base.rmin        = 0 * mm
    W_Base.rmax        = 46.25 * mm
    W_Base.dz          = 10.875 * mm            # (21.75/2)
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

    # =========================
    #  CAVIDAD DE AIRE interior (reducida: radio 16.75mm, dz 28.5mm)
    # =========================
    Cavidad_Aire             = sim.add_volume("Tubs", "Cavidad_Aire")
    Cavidad_Aire.mother      = "world"
    Cavidad_Aire.rmin        = 0 * mm
    Cavidad_Aire.rmax        = 16.75 * mm
    Cavidad_Aire.dz          = 28.5 * mm
    Cavidad_Aire.material    = "G4_AIR"
    Cavidad_Aire.color       = [0.9, 0.9, 1.0, 0.1]
    Cavidad_Aire.translation = [0, 0, 0]

    # ==============
    #  VIAL DE VIDRIO — REPOSICIONADO (mismo tamaño, apoyado en el piso de
    #  la cavidad nueva, igual lógica relativa que en el contenedor de plomo)
    # ==============
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

    # ==================================================
    #  AGUA (10 mL) — disolución de F-18 FDG — reposicionada igual
    # ==================================================
    waterCil             = sim.add_volume("Tubs", "waterCil")
    waterCil.mother      = "Cavidad_Aire"
    waterCil.rmin        = 0 * mm
    waterCil.rmax        = 11.0 * mm
    waterCil.dz          = (26.3 / 2.0) * mm
    waterCil.material    = "G4_WATER"
    waterCil.color       = [0.0, 0.2, 1.0, 0.7]
    waterCil.translation = [0, 0, -13.85 * mm]

    # ==================================================
    #  DETECTORES — sin cambios respecto a la versión de plomo
    # ==================================================
    Z_ref = 0 * mm

    # ── Grupo A — justo afuera del contenedor (mano sujetando el vial) ──
    det_palma             = sim.add_volume("Box", "det_palma")
    det_palma.mother      = "world"
    det_palma.size        = [95 * mm, 1 * mm, 70 * mm]
    det_palma.material    = "G4_TISSUE_SOFT_ICRP"
    det_palma.color       = [1.0, 0.5, 0.0, 0.8]
    det_palma.translation = [0 * mm, -55 * mm, Z_ref]

    det_dedos             = sim.add_volume("Box", "det_dedos")
    det_dedos.mother      = "world"
    det_dedos.size        = [1 * mm, 40.0 * mm, 70 * mm]
    det_dedos.material    = "G4_TISSUE_SOFT_ICRP"
    det_dedos.color       = [1.0, 0.0, 0.5, 0.8]
    det_dedos.translation = [50 * mm, -35 * mm, 0 * mm]

    DISTANCIA_A_SUPERFICIE_MM = 46.25 + 150.0   # radio externo tungsteno + 15cm

    det_torso             = sim.add_volume("Box", "det_torso")
    det_torso.mother      = "world"
    det_torso.size        = [1 * mm, 300 * mm, 400 * mm]
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
    det_manos.size        = [1 * mm, 80 * mm, 150 * mm]
    det_manos.material    = "G4_TISSUE_SOFT_ICRP"
    det_manos.color       = [1.0, 0.4, 0.0, 0.8]
    det_manos.translation = [-DISTANCIA_A_SUPERFICIE_MM * mm, 200 * mm, Z_ref - 180 * mm]

    dimensiones_detectores = {
        "det_palma":  ([95, 1, 70],    [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_dedos":  ([1, 40, 70],    [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_torso":  ([1, 300, 400],  [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_cabeza": ([1, 130, 170],  [1.0 * mm, 1.0 * mm, 1.0 * mm]),
        "det_manos":  ([1, 80, 150],   [1.0 * mm, 1.0 * mm, 1.0 * mm]),
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
    #  PERFILES DE LÍNEA
    # ==================================================
    dose_perfil_radial             = sim.add_actor("DoseActor", "dose_perfil_radial")
    dose_perfil_radial.attached_to = "world"
    dose_perfil_radial.size        = [880, 5, 5]     
    dose_perfil_radial.spacing     = [0.5 * mm, 5.0 * mm, 5.0 * mm]
    dose_perfil_radial.translation = [0, 0, 0]
    dose_perfil_radial.hit_type    = "random"
    dose_perfil_radial.dose.active = True


    # ==================================================
    #  ESTADÍSTICAS
    # ==================================================
    stats                     = sim.add_actor("SimulationStatisticsActor", "Stats")
    stats.track_types_flag    = True
    stats.output_filename     = "stats.txt"

    # ==================================================
    #  FUENTE — F-18 FDG disuelto en el agua (sin cambios)
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

    print("=" * 55)
    print("RESUMEN DE LA SIMULACIÓN — CONTENEDOR DE TUNGSTENO")
    print("=" * 55)
    print(f"Primarios simulados : {N_PRIMARIES:,}")
    print(f"Duración             : {duracion_s:.1f} s  ({duracion_s/60:.2f} min)")
    print(f"Carpeta de salida    : {Path(sim.output_dir).resolve()}")
    print("=" * 55)

    # ==================================================
    #  METADATA
    # ==================================================
    metadata = {
        "n_primarios_simulados": N_PRIMARIES,
        "actividad_objetivo_mci": ACTIVIDAD_OBJETIVO_MCI,
        "physics_list": sim.physics_manager.physics_list_name,
        "fuente": "F-18 (ion 9 18), disuelto en waterCil, contenedor CT/A-30W (tungsteno)",
        "energia_media_por_decaimiento_MeV": 0.9686 * 0.2495 + 1.9372 * 0.511,
        "geometria": {
            "radial_mm": {
                "agua":              [0, 11.0],
                "vidrio":            [11.0, 12.5],
                "cavidad_aire":      [12.5, 16.75],
                "tungsteno":         [16.75, 46.25],
                "det_palma_centro":  -55.0,
                "det_dedos_centro":  50.0,
                "det_torso_centro":  -(46.25 + 150.0),
            },
            "axial_mm": {
                "agua":          [-27.0, -0.7],
                "cavidad_aire":  [-0.65, 28.5],
                "tungsteno":     [28.5, 50.25],
            },
        },
    }
    ruta_metadata = Path(sim.output_dir) / "metadata_simulacion.json"
    ruta_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
