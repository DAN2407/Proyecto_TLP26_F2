# Proyecto TLP02-2026 – Fase 2


## Fase 2 – reproducir el experimento (ajuste: informe escrito + evidencia)

### inicialización del entorno virtual y dependencias
```bash
# Crear un entorno virtual (opcional pero recomendado):
python -m venv .venv

# Activar el entorno virtual:
En Linux/Mac: source .venv/bin/activate
En Windows: .venv\Scripts\activate

# Instalar dependencias y descargar modelo spaCy
pip install -r requirements.txt && python -m spacy download es_core_news_sm

# Configurar la variable de entorno con la clave de Gemini LLM
$env:GEMINI_API_KEY="tu_clave_aqui" clave propia, tiene que conseguirlas en https://aistudio.google.com/api-keys (no se comparten por cuestiones de seguridad)
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


### Qué es cada archivo
- `fase2/dataset.csv`: corpus etiquetado (60 oraciones; niveles 1/2/3). Columnas: `esperado_gramatica` (salida esperada: aceptar/rechazar
  según la gramática controlada), `gramatical_es` (juicio nativo), `upos_oro` (estructura esperada como etiquetas UPOS), `split` (dev/test).
- `fase2/logs/*.jsonl`: salida cruda por oración, con `timestamp_utc` (o `timestamp_inicio/fin` en el LLM), versiones y parámetros.
- `fase2/evaluar.py`: único lugar donde se calculan precisión, cobertura, rechazo correcto, clasificación de errores
  (FP, FN, error de etiquetado, sin respuesta), desvío al conocimiento general y costo. Re-ejecutarlo con los mismos logs da tablas idénticas
  (`resultados/entradas_sha256.txt` lista los hashes de las entradas).

## 🚀 Guía de Ejecución Paso a Paso

Todos los scripts deben ejecutarse desde la carpeta raíz del proyecto (`Proyecto_TLP26_F2`) utilizando la bandera `-m` para respetar la estructura de paquetes de Python.

### Paso 1: Evaluar el Parser Propio y spaCy

Este comando corre el corpus a través del parser formal y a través de spaCy.

```bash
python -m fase2.comparar_nlp
```

Resultado esperado: Se crean los `parser.jsonl` y `spacy.jsonl` en la carpeta logs/.

### Paso 2: Evaluar con HuggingFace (BETO)

Este comando descarga el modelo BETO (la primera vez puede tardar unos minutos) y calcula la Pseudo-Log-Verosimilitud (PLL) para cada oración.
```bash
python -m fase2.comparar_hf
```

Resultado esperado: Se crea el archivo `hf.jsonl` en la carpeta logs/.


### Paso 3: Evaluar con el LLM (Gemini)

Se deben correr los dos modos (Zero-Shot y Few-Shot).

    
  *Nota: El script tiene un sistema de pausas de 14 segundos para respetar el límite de 5 peticiones por minuto del tier gratuito de Gemini, por lo que cada ejecución tardará aproximadamente 15 minutos.*


```bash
python -m fase2.llm_experimento --modo zero --modelo gemini-3.5-flash-lite
python -m fase2.llm_experimento --modo few --modelo gemini-3.5-flash-lite
```

Resultado esperado: los logs completos con timestamps en `logs/llm_zero.jsonl` y `logs/llm_few.jsonl`.


### Paso 4: Calcular las métricas finales

Una vez que existan todos los archivos pred_*.csv en la carpeta resultados/, ejecuta el script de evaluación.

```bash
python -m fase2.evaluar
```

Resultado esperado: El script imprimirá las tablas comparativas en la consola y generará en resultados:

    metricas_global.csv (Precisión, Cobertura, Exactitud).

    metricas_por_nivel.csv (Resultados separados por Nivel 1, 2 y 3).

    errores.csv (Listado detallado de Falsos Positivos y Falsos Negativos).

    Gráficas .png (Barras comparativas y matrices de confusión).

### Notas sobre la Reproducibilidad

Auditoría del LLM: Cada llamada a la API de Gemini quedó registrada en los archivos .jsonl dentro de la carpeta logs/. Cada línea incluye el prompt exacto enviado, la respuesta cruda del modelo, el JSON parseado y el timestamp UTC exacto de la petición.

Corpus etiquetado: El archivo dataset.csv contiene el corpus completo (60 oraciones). Las columnas gramatical_es y esperado_gramatica representan las dos referencias de verdad (juicio nativo y validación formal) utilizadas para calcular las métricas.

Semilla y Determinismo: Todos los scripts están diseñados para ser deterministas. El LLM se ejecutó con temperature=0 y el parser es 100% simbólico. Ejecutar el flujo completo de nuevo con los mismos archivos de entrada producirá exactamente los mismos resultados reportados en el informe. Si se quiere replicar el experimento debe borrarse la carpeta logs/ y resultados/ y volver a ejecutar los scripts en el orden indicado.



