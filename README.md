# Simulación dosimétrica — Vial F-18 FDG

Comparación Monte Carlo (GATE 10) de dos contenedores blindados para F-18 FDG: plomo+acero (CT/A-30) y tungsteno (CT/A-30W), evaluando la dosis recibida por el técnico durante su manipulación.

## Archivos

| Archivo | Descripción |
|---|---|
| `vial_plomo.py` | Simulación GATE — contenedor CT/A-30 |
| `vial_tungsteno.py` | Simulación GATE — contenedor CT/A-30W |
| `Proyecto_Vial_Blindado.ipynb` | Análisis comparativo de resultados |
| `output_pb/` | Resultados del contenedor de plomo |
| `output_tungsteno/` | Resultados del contenedor de tungsteno |

## Qué analiza el notebook

- **Mapas de calor** — distribución espacial de dosis en cada detector
- **Validación estadística** — incertidumbre relativa por detector (umbral 10%)
- **Dosis equivalente en Sv** — por detector, escalada a 10 mCi y 1 hora de exposición
- **Perfil de dosis vs posición** — atenuación a través de cada capa del blindaje desde la fuente hasta el torso
- **Transmitancia corregida por ángulo sólido** — comparación directa de la eficiencia de atenuación entre ambos contenedores

## Limitaciones estadísticas

Los detectores desplazados del eje principal de radiación (`det_cabeza`, `det_manos`) presentan incertidumbre estadística por encima del umbral aceptable del 10%, debido a que el blindaje atenúa fuertemente la radiación en esas direcciones y muy pocos fotones simulados los alcanzan. Se estima que son necesarios al menos 500 millones de primarios para obtener resultados confiables en la mayoría de detectores, lo que equivale a aproximadamente 17 horas de cómputo en un solo hilo.


## Uso

```bash
python vial_plomo.py
python vial_tungsteno.py
```

Luego abrir `Proyecto_Vial_Blindado.ipynb` y ejecutar todas las celdas.

## Requisitos

- GATE 10 (opengate)
- Python 3.10+, numpy, matplotlib

## Autor

Kendall Alvarado Quesada — Universidad de Costa Rica
