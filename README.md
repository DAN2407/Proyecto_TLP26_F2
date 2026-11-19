# Proyecto TLP02-2026 – Fase 2


## Fase 2 – reproducir el experimento (ajuste: informe escrito + evidencia)

Flujo: **cada enfoque escribe un log crudo → `evaluar.py` lee los logs y calcula todas las tablas**.
Nada de las métricas se calcula dentro de los scripts que corren las herramientas.

### Paso a paso
```bash
python -m venv .venv
   # Activar el entorno virtual:
   # En Windows: .venv\Scripts\activate
pip install -r requirements.txt && python -m spacy download es_core_news_sm
$env:GEMINI_API_KEY="tu_clave_aqui" clave propia, tiene que conseguirlas en https://aistudio.google.com/api-keys (no se comparten por cuestiones de seguridad)
mkdir -p Proyecto_TLP26_F2/logs && pip freeze > Proyecto_TLP26_F2/logs/pip_freeze.txt   # versiones para el informe

```

```text
## Estructura del proyecto

Proyecto_TLP26_F2/
├── fase2/
│   ├── resultados/              # (Generado automáticamente) CSVs y PNGs de métricas
│   ├── logs/                    # (Generado automáticamente) JSONLs con los prompts y respuestas
│   ├── dataset.csv              # Corpus de prueba (60 oraciones etiquetadas)
│   ├── lexico.py                # Léxico y rasgos del lenguaje controlado
│   ├── parser_es.py             # Parser descendente recursivo (Enfoque 1)
│   ├── comparar_nlp.py          # Evaluación con spaCy (Enfoque 2)
│   ├── comparar_hf.py           # Evaluación con BETO/HuggingFace (Enfoque 3)
│   ├── llm_experimento.py       # Evaluación con Gemini LLM (Enfoque 4)
│   └── evaluar.py               # Script final que calcula métricas y gráficas
├── formal/
│   └── tree.py                  # Clase para los nodos del árbol sintáctico
├── README.md
└── requirements.txt
```

| # | Comando | Escribe |
|---|---|---|
| 1 | `python -m fase2.comparar_nlp` (`--solo parser` / `--solo spacy`) | `logs/parser.jsonl`, `logs/spacy.jsonl` |
| 2 | `python -m fase2.comparar_hf` (necesita internet la 1.ª vez) | `logs/hf.jsonl` |
| 4 | `python -m fase2.llm_experimento --modo zero` | `logs/llm_zero.jsonl` + `.txt` (prompt, respuesta completa, timestamps) |
| 5 | `python -m fase2.llm_experimento --modo few` | `logs/llm_few.jsonl` + `.txt` |
| 6 | `python -m fase2.evaluar` | `resultados/` (CSV, `tablas_informe.md`, gráficas, `entradas_sha256.txt`) |



### Qué es cada archivo
- `fase2/dataset.csv`: corpus etiquetado (60 oraciones; niveles 1/2/3). Columnas: `esperado_gramatica` (salida esperada: aceptar/rechazar
  según la gramática controlada), `gramatical_es` (juicio nativo), `upos_oro` (estructura esperada como etiquetas UPOS), `split` (dev/test).
- `fase2/logs/*.jsonl`: salida cruda por oración, con `timestamp_utc` (o `timestamp_inicio/fin` en el LLM), versiones y parámetros.
- `fase2/evaluar.py`: único lugar donde se calculan precisión, cobertura, rechazo correcto, clasificación de errores
  (FP, FN, error de etiquetado, sin respuesta), desvío al conocimiento general y costo. Re-ejecutarlo con los mismos logs da tablas idénticas
  (`resultados/entradas_sha256.txt` lista los hashes de las entradas).

### Decisiones metodológicas (explicarlas en el informe)
- **spaCy y BETO no "rechazan"**: la regla aceptar/rechazar de spaCy es una heurística de concordancia (ver docstring de `comparar_nlp.py`);
  la de BETO es un umbral de pseudo-log-verosimilitud calibrado solo con `dev` (ver `evaluar.py`).
- **Dos referencias**: `esperado_gramatica` mide si la herramienta respeta la gramática; `gramatical_es` mide si acierta como español.
  Medir el parser contra `esperado_gramatica` es casi tautológico (la etiqueta se definió con su propia especificación), por eso
  la comparación informativa del parser es contra `gramatical_es` y la del LLM contra `esperado_gramatica`.
- **Respuestas del LLM sin JSON válido** no se convierten en predicción: se excluyen de las matrices y se reportan como `sin_respuesta`.
- **Error de etiquetado**: oración aceptada cuyas etiquetas UPOS difieren de `upos_oro` (se tolera que `que` sea SCONJ o PRON).

### Otros comandos de la Fase 2
`python -m fase2.llm_experimento --modo few --dry-run` · `python -m unittest discover -s tests -t .`
