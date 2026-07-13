# Vial F-18 FDG — Simulación dosimétrica con GATE 10

Simulación Monte Carlo de un vial de F-18 FDG de 10 mCi con blindaje de plomo y acero inoxidable, orientada a evaluar la dosis recibida por el técnico durante su manipulación y transporte nacional.

## Descripción

El sistema modela un vial de vidrio con 10 mL de solución de F-18 FDG, encapsulado en una cavidad de aire rodeada por 32 mm de plomo y 2 mm de acero inoxidable. Se simulan cinco detectores de tejido blando que representan distintas regiones del cuerpo del técnico: palma y dedos (en contacto con el contenedor) y torso, cabeza y manos (a 15 cm de la superficie).

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `Simulacion.py` | Script de GATE: geometría, fuente, actores y ejecución |
| `Vial.ipynb` | Notebook de análisis: mapas de calor, dosis en Sv, perfil de atenuación y transmitancia |
| `output/` | Resultados generados por GATE (.mhd, .raw, metadata_simulacion.json) |

## Requisitos

- GATE 10 (con opengate)
- Python 3.10+
- numpy, matplotlib

## Uso

**1. Correr la simulación:**
```bash
python Simulacion.py
```
Genera los archivos `.mhd/.raw` y `output/metadata_simulacion.json`.

**2. Analizar los resultados:**

Abrir `Vial.ipynb` en JupyterLab y ejecutar todas las celdas en orden. Ajustar `TIEMPO_EXPOSICION_S` en la celda de parámetros según el escenario a evaluar.

## Parámetros principales

| Parámetro | Valor por defecto |
|---|---|
| Actividad | 10 mCi (F-18 FDG) |
| Primarios simulados | 150,000,000 |
| Tiempo de exposición (notebook) | 3600 s (1 hora) |
| Physics list | QGSP_BIC_EMZ |

## Resultados que entrega el notebook

- Mapas de calor de dosis por detector
- Incertidumbre estadística por detector (validación Monte Carlo)
- Dosis absorbida en Gy y equivalente en Sv por detector
- Perfil de dosis vs posición a través del blindaje
- Transmitancia por detector

## Autor

Kendall Alvarado Quesada — Universidad de Costa Rica
