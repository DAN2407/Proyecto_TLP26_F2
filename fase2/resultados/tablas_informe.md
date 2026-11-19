# Tablas para el informe (generadas por fase2/evaluar.py; no editar a mano)

## Métricas globales, referencia: salida esperada (gramática) (todo el corpus)

| herramienta | n | precision | cobertura | rechazo_correcto | exactitud | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 60 | 1.000 | 1.000 | 1.000 | 1.000 | 39 | 0 | 0 | 21 |
| spaCy | 60 | 0.684 | 1.000 | 0.143 | 0.700 | 39 | 18 | 0 | 3 |
| HF (BETO-PLL) | 60 | 0.718 | 0.718 | 0.476 | 0.633 | 28 | 11 | 11 | 10 |
| LLM zero-shot | 59 | 0.884 | 1.000 | 0.762 | 0.915 | 38 | 5 | 0 | 16 |
| LLM few-shot | 58 | 0.925 | 1.000 | 0.857 | 0.948 | 37 | 3 | 0 | 18 |

## Métricas sobre el split test, referencia: salida esperada (gramática)

| herramienta | n | precision | cobertura | rechazo_correcto | exactitud | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 19 | 1.000 | 1.000 | 1.000 | 1.000 | 13 | 0 | 0 | 6 |
| spaCy | 19 | 0.722 | 1.000 | 0.167 | 0.737 | 13 | 5 | 0 | 1 |
| HF (BETO-PLL) | 19 | 0.727 | 0.615 | 0.500 | 0.579 | 8 | 3 | 5 | 3 |
| LLM zero-shot | 18 | 0.923 | 1.000 | 0.833 | 0.944 | 12 | 1 | 0 | 5 |
| LLM few-shot | 18 | 0.923 | 1.000 | 0.833 | 0.944 | 12 | 1 | 0 | 5 |

## Métricas por nivel, referencia: salida esperada (gramática)

| herramienta | nivel | n | precision | cobertura | rechazo_correcto | exactitud | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 1 | 20 | 1.000 | 1.000 | – | 1.000 | 20 | 0 | 0 | 0 |
| Parser propio | 2 | 26 | 1.000 | 1.000 | 1.000 | 1.000 | 19 | 0 | 0 | 7 |
| Parser propio | 3 | 14 | – | – | 1.000 | 1.000 | 0 | 0 | 0 | 14 |
| spaCy | 1 | 20 | 1.000 | 1.000 | – | 1.000 | 20 | 0 | 0 | 0 |
| spaCy | 2 | 26 | 0.826 | 1.000 | 0.429 | 0.846 | 19 | 4 | 0 | 3 |
| spaCy | 3 | 14 | 0.000 | – | 0.000 | 0.000 | 0 | 14 | 0 | 0 |
| HF (BETO-PLL) | 1 | 20 | 1.000 | 0.700 | – | 0.700 | 14 | 0 | 6 | 0 |
| HF (BETO-PLL) | 2 | 26 | 1.000 | 0.737 | 1.000 | 0.808 | 14 | 0 | 5 | 7 |
| HF (BETO-PLL) | 3 | 14 | 0.000 | – | 0.214 | 0.214 | 0 | 11 | 0 | 3 |
| LLM zero-shot | 1 | 20 | 1.000 | 1.000 | – | 1.000 | 20 | 0 | 0 | 0 |
| LLM zero-shot | 2 | 25 | 1.000 | 1.000 | 1.000 | 1.000 | 18 | 0 | 0 | 7 |
| LLM zero-shot | 3 | 14 | 0.000 | – | 0.643 | 0.643 | 0 | 5 | 0 | 9 |
| LLM few-shot | 1 | 19 | 1.000 | 1.000 | – | 1.000 | 19 | 0 | 0 | 0 |
| LLM few-shot | 2 | 25 | 1.000 | 1.000 | 1.000 | 1.000 | 18 | 0 | 0 | 7 |
| LLM few-shot | 3 | 14 | 0.000 | – | 0.786 | 0.786 | 0 | 3 | 0 | 11 |

## Métricas globales, referencia: juicio nativo (todo el corpus)

| herramienta | n | precision | cobertura | rechazo_correcto | exactitud | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 60 | 1.000 | 0.736 | 1.000 | 0.767 | 39 | 0 | 14 | 7 |
| spaCy | 60 | 0.930 | 1.000 | 0.429 | 0.933 | 53 | 4 | 0 | 3 |
| HF (BETO-PLL) | 60 | 1.000 | 0.736 | 1.000 | 0.767 | 39 | 0 | 14 | 7 |
| LLM zero-shot | 59 | 1.000 | 0.827 | 1.000 | 0.847 | 43 | 0 | 9 | 7 |
| LLM few-shot | 58 | 1.000 | 0.784 | 1.000 | 0.810 | 40 | 0 | 11 | 7 |

## Métricas sobre el split test, referencia: juicio nativo

| herramienta | n | precision | cobertura | rechazo_correcto | exactitud | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 19 | 1.000 | 0.765 | 1.000 | 0.789 | 13 | 0 | 4 | 2 |
| spaCy | 19 | 0.944 | 1.000 | 0.500 | 0.947 | 17 | 1 | 0 | 1 |
| HF (BETO-PLL) | 19 | 1.000 | 0.647 | 1.000 | 0.684 | 11 | 0 | 6 | 2 |
| LLM zero-shot | 18 | 1.000 | 0.812 | 1.000 | 0.833 | 13 | 0 | 3 | 2 |
| LLM few-shot | 18 | 1.000 | 0.812 | 1.000 | 0.833 | 13 | 0 | 3 | 2 |

## Métricas por nivel, referencia: juicio nativo

| herramienta | nivel | n | precision | cobertura | rechazo_correcto | exactitud | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|---|---|---|
| Parser propio | 1 | 20 | 1.000 | 1.000 | – | 1.000 | 20 | 0 | 0 | 0 |
| Parser propio | 2 | 26 | 1.000 | 1.000 | 1.000 | 1.000 | 19 | 0 | 0 | 7 |
| Parser propio | 3 | 14 | – | 0.000 | – | 0.000 | 0 | 0 | 14 | 0 |
| spaCy | 1 | 20 | 1.000 | 1.000 | – | 1.000 | 20 | 0 | 0 | 0 |
| spaCy | 2 | 26 | 0.826 | 1.000 | 0.429 | 0.846 | 19 | 4 | 0 | 3 |
| spaCy | 3 | 14 | 1.000 | 1.000 | – | 1.000 | 14 | 0 | 0 | 0 |
| HF (BETO-PLL) | 1 | 20 | 1.000 | 0.700 | – | 0.700 | 14 | 0 | 6 | 0 |
| HF (BETO-PLL) | 2 | 26 | 1.000 | 0.737 | 1.000 | 0.808 | 14 | 0 | 5 | 7 |
| HF (BETO-PLL) | 3 | 14 | 1.000 | 0.786 | – | 0.786 | 11 | 0 | 3 | 0 |
| LLM zero-shot | 1 | 20 | 1.000 | 1.000 | – | 1.000 | 20 | 0 | 0 | 0 |
| LLM zero-shot | 2 | 25 | 1.000 | 1.000 | 1.000 | 1.000 | 18 | 0 | 0 | 7 |
| LLM zero-shot | 3 | 14 | 1.000 | 0.357 | – | 0.357 | 5 | 0 | 9 | 0 |
| LLM few-shot | 1 | 19 | 1.000 | 1.000 | – | 1.000 | 19 | 0 | 0 | 0 |
| LLM few-shot | 2 | 25 | 1.000 | 1.000 | 1.000 | 1.000 | 18 | 0 | 0 | 7 |
| LLM few-shot | 3 | 14 | 1.000 | 0.214 | – | 0.214 | 3 | 0 | 11 | 0 |

## Clasificación de errores

| herramienta | referencia | falsos_positivos | falsos_negativos | errores_etiquetado | sin_respuesta |
|---|---|---|---|---|---|
| Parser propio | esperado_gramatica | 0 | 0 | 0 | 0 |
| Parser propio | gramatical_es | 0 | 14 | 0 | 0 |
| spaCy | esperado_gramatica | 18 | 0 | 3 | 0 |
| spaCy | gramatical_es | 4 | 0 | 3 | 0 |
| HF (BETO-PLL) | esperado_gramatica | 11 | 11 | – | 0 |
| HF (BETO-PLL) | gramatical_es | 0 | 14 | – | 0 |
| LLM zero-shot | esperado_gramatica | 5 | 0 | 31 | 1 |
| LLM zero-shot | gramatical_es | 0 | 9 | 31 | 1 |
| LLM few-shot | esperado_gramatica | 3 | 0 | 6 | 2 |
| LLM few-shot | gramatical_es | 0 | 11 | 6 | 2 |

## Etiquetado UPOS (oraciones aceptadas con etiquetas de oro)

| herramienta | oraciones_evaluadas | oraciones_con_error | exactitud_oracion | tokens_oro | tokens_correctos | exactitud_token |
|---|---|---|---|---|---|---|
| Parser propio | 39 | 0 | 1.000 | 187 | 187 | 1.000 |
| spaCy | 39 | 3 | 0.923 | 187 | 184 | 0.984 |
| LLM zero-shot | 38 | 31 | 0.184 | 180 | 40 | 0.222 |
| LLM few-shot | 37 | 6 | 0.838 | 177 | 171 | 0.966 |

## Desvío al conocimiento general / respeto de las reglas

| herramienta | n_fuera_de_gramatica | acepta_fuera_de_gramatica | n_en_gramatica | rechaza_en_gramatica | n_agramaticales | rechaza_agramaticales |
|---|---|---|---|---|---|---|
| Parser propio | 14 | 0.000 | 39 | 0.000 | 7 | 1.000 |
| spaCy | 14 | 1.000 | 39 | 0.000 | 7 | 0.429 |
| HF (BETO-PLL) | 14 | 0.786 | 39 | 0.282 | 7 | 1.000 |
| LLM zero-shot | 14 | 0.357 | 38 | 0.000 | 7 | 1.000 |
| LLM few-shot | 14 | 0.214 | 37 | 0.000 | 7 | 1.000 |

## Costo computacional

| herramienta | oraciones | tiempo_total_s | tiempo_medio_s | tokens_entrada | tokens_salida | modelo |
|---|---|---|---|---|---|---|
| Parser propio | 60 | 0.001 | 0.000 | – | – | – |
| spaCy | 60 | 0.262 | 0.004 | – | – | – |
| HF (BETO-PLL) | 60 | 12.315 | 0.205 | – | – | – |
| LLM zero-shot | 60 | 0 | – | 47377 | 2732 | gemini-3.5-flash-lite |
| LLM few-shot | 60 | 0 | – | 66157 | 2664 | gemini-3.5-flash-lite |

## Calibración (HF, solo split dev)

- HF (BETO-PLL): {"umbral_pll": -4.8822, "exactitud_balanceada_dev": 0.889}
