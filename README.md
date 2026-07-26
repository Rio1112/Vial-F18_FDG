# Vial F-18 FDG — Simulación dosimétrica comparativa con GATE 10

Simulación Monte Carlo de un vial de F-18 FDG de 10 mCi con dos tipos de blindaje: plomo+acero inoxidable (CT/A-30) y tungsteno (CT/A-30W). El objetivo es comparar la dosis recibida por el técnico durante la manipulación y transporte nacional del vial.

## Descripción

El sistema modela un vial de vidrio con 10 mL de solución de F-18 FDG encapsulado en una cavidad de aire, rodeada por el blindaje correspondiente. Se simulan cinco detectores de tejido blando que representan distintas regiones del cuerpo del técnico: palma y dedos (en contacto con el contenedor) y torso, cabeza y manos (a 15 cm de la superficie externa).

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `vial_plomo.py` | Script de GATE: contenedor CT/A-30 (plomo + acero inoxidable) |
| `vial_tungsteno.py` | Script de GATE: contenedor CT/A-30W (tungsteno puro) |
| `Proyecto_Vial_Blindado.ipynb` | Notebook comparativo: mapas de calor, dosis en Sv, perfil de atenuación y transmitancia para ambos contenedores |
| `output_pb/` | Resultados del contenedor de plomo (.mhd, .raw, metadata_simulacion.json) |
| `output_tungsteno/` | Resultados del contenedor de tungsteno (.mhd, .raw, metadata_simulacion.json) |

## Requisitos

- GATE 10 (con opengate)
- Python 3.10+
- numpy, matplotlib

## Uso

**1. Correr las simulaciones:**
```bash
python vial_plomo.py
python vial_tungsteno.py
```
Cada script genera su propia carpeta de resultados (`output_pb/` y `output_tungsteno/`) con los archivos `.mhd/.raw` y `metadata_simulacion.json`.

**2. Analizar los resultados:**

Abrir `Proyecto_Vial_Blindado.ipynb` en JupyterLab y ejecutar todas las celdas en orden. Ajustar `TIEMPO_EXPOSICION_S` en la celda de parámetros según el escenario a evaluar.

## Parámetros principales

| Parámetro | Valor por defecto |
|---|---|
| Actividad | 10 mCi (F-18 FDG) |
| Primarios simulados | 150,000,000 |
| Tiempo de exposición (notebook) | 3600 s (1 hora) |
| Physics list | QGSP_BIC_EMZ |

## Geometría de los contenedores

| Parámetro | CT/A-30 (plomo) | CT/A-30W (tungsteno) |
|---|---|---|
| Radio cavidad interior | 16.5 mm | 16.75 mm |
| Espesor de blindaje lateral | 32.0 mm (Pb) | 29.5 mm (W) |
| Radio externo | 50.5 mm | 46.25 mm |
| Espesor tapa/base | 18.75 mm (Pb) + 2 mm (acero) | 21.75 mm (W) |

## Detectores

| Detector | Dimensiones | Posición | Representa |
|---|---|---|---|
| `det_palma` | 95×1×70 mm | Y = −55 mm | Palma apoyada sobre el contenedor |
| `det_dedos` | 1×40×70 mm | X = +50 mm, Y = −35 mm | Dedos rodeando el contenedor |
| `det_torso` | 1×300×400 mm | X = −200.5 mm | Torso del técnico a 15 cm |
| `det_cabeza` | 1×130×170 mm | X = −200.5 mm, Z = +450 mm | Cabeza del técnico a 15 cm |
| `det_manos` | 1×80×150 mm | X = −200.5 mm, Y = +200 mm, Z = −180 mm | Manos del técnico a 15 cm |

## Resultados que entrega el notebook

- Mapas de calor de dosis por detector (plomo vs tungsteno)
- Incertidumbre estadística por detector (validación Monte Carlo)
- Dosis absorbida en Gy y equivalente en Sv por detector
- Perfil de dosis vs posición a través del blindaje
- Transmitancia y comparación directa entre ambos contenedores

## Autor

Kendall Alvarado Quesada — Universidad de Costa Rica
