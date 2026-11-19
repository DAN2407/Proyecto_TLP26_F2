import argparse, csv, json, os, re, time, datetime
from .parser_es import GRAMATICA_TEXTO, lexico_texto

AQUI = os.path.dirname(__file__)
LOGS = os.path.join(AQUI, "logs")
RES = os.path.join(AQUI, "resultados")

SISTEMA = ("Eres un analizador sintáctico. Tu única fuente de verdad es la gramática formal que se te da. "
           "NO uses tu conocimiento general del español para aceptar oraciones: si una oración no se deriva "
           "EXACTAMENTE de las reglas y del léxico dados, debes rechazarla, aunque sea español correcto.")

FORMATO = ('Responde únicamente con un objeto JSON, sin texto adicional: '
           '{"acepta": true|false, "regla_violada": "<regla o restricción que falla, o \\"\\" si acepta>", '
           '"arbol": "<árbol entre paréntesis si acepta, o \\"\\">"}')

EJEMPLOS = [
    ("la perra pequeña corre", {"acepta": True, "regla_violada": "",
                                "arbol": "(S (SN (Det la) (N perra) (Adj pequeña)) (SV (V corre)))"}),
    ("las mujeres que ven un hombre duermen",
     {"acepta": True, "regla_violada": "",
      "arbol": "(S (SN (Det las) (N mujeres) (Rel que (SV (V ven) (Obj (SN (Det un) (N hombre)))))) (SV (V duermen)))"}),
    ("unas casas rojos duermen", {"acepta": False, "regla_violada": "Restricción 1: concordancia N-Adj", "arbol": ""}),
    ("Luis corren", {"acepta": False, "regla_violada": "Restricción 2: concordancia sujeto-verbo", "arbol": ""}),
    ("corre el perro", {"acepta": False, "regla_violada": "S -> SN SV: la oración no empieza con SN", "arbol": ""}),
    ("un perro corre un libro", {"acepta": False, "regla_violada": "Restricción 4: 'corre' es I y no admite Obj", "arbol": ""}),
]

def construir_prompt(oracion: str, modo: str) -> str:
    partes = ["GRAMÁTICA:\n" + GRAMATICA_TEXTO, "LÉXICO (forma(rasgos)):\n" + lexico_texto()]
    if modo == "few":
        ej = "\n".join(f"Oración: {s}\nRespuesta: {json.dumps(r, ensure_ascii=False)}" for s, r in EJEMPLOS)
        partes.append("EJEMPLOS:\n" + ej)
    partes += [FORMATO, f"Oración a analizar: {oracion}"]
    return "\n\n".join(partes)

def extraer_json(texto: str):
    for m in re.finditer(r"\{[^{}]*\}", texto, flags=re.S):
        for fin in range(len(m.group()), 0, -1):
            try:
                d = json.loads(m.group()[:fin])
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict) and isinstance(d.get("acepta"), bool):
                return d
    return None

def leer_dataset():
    with open(os.path.join(AQUI, "dataset.csv"), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def obtener_ids_procesados(ruta_pred):
    """Lee el CSV parcial para evitar repetir peticiones si el script se cortó."""
    if not os.path.exists(ruta_pred):
        return set()
    with open(ruta_pred, encoding="utf-8") as f:
        return {row["id"] for row in csv.DictReader(f)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["zero", "few"], default="zero")
    ap.add_argument("--modelo", default="gemini-3.5-flash-lite") # Modelo actualizado
    ap.add_argument("--solo-test", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    filas = leer_dataset()
    if a.solo_test:
        filas = [r for r in filas if r["split"] == "test"]

    if a.dry_run:
        print("--- SISTEMA ---\n" + SISTEMA + "\n\n--- USUARIO (primera oración) ---\n" + construir_prompt(filas[0]["oracion"], a.modo))
        return

    from google import genai
    from google.genai import types

    cliente = genai.Client()
    os.makedirs(LOGS, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    
    # Archivos de salida
    ruta_log = os.path.join(LOGS, f"llm_{a.modo}.jsonl")
    ruta_pred = os.path.join(RES, f"pred_llm_{a.modo}{'_test' if a.solo_test else ''}.csv")
    
    # Checkpoint: ¿qué ya hemos procesado?
    ids_procesados = obtener_ids_procesados(ruta_pred)
    if ids_procesados:
        print(f"Reanudando: se encontraron {len(ids_procesados)} oraciones ya procesadas. Se omitirán.")

    # Abrimos en modo 'a' (append) para no borrar lo que ya había
    with open(ruta_log, "a", encoding="utf-8") as log, open(ruta_pred, "a", newline="", encoding="utf-8") as pf:
        w = csv.writer(pf)
        # Si el archivo está vacío, escribimos la cabecera
        if os.path.getsize(ruta_pred) == 0:
            w.writerow(["id", "acepta"])

        total_a_procesar = len([r for r in filas if r["id"] not in ids_procesados])
        print(f"Iniciando experimento [{a.modo}]: {total_a_procesar} oraciones pendientes...")

        for i, r in enumerate(filas):
            if r["id"] in ids_procesados:
                continue # Ya lo hicimos

            print(f"[{i+1}/{len(filas)}] Procesando id {r['id']}: '{r['oracion']}'...")
            prompt = construir_prompt(r["oracion"], a.modo)
            crudo, uso = "", {}
            exito = False

            # Hasta 5 reintentos si hay problemas de red o de límite (429)
            for intento in range(5):
                try:
                    resp = cliente.models.generate_content(
                        model=a.modelo,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=SISTEMA,
                            temperature=0,
                            top_p=1,
                            max_output_tokens=400,
                        )
                    )
                    crudo = resp.text
                    if resp.usage_metadata:
                        uso = {"entrada": resp.usage_metadata.prompt_token_count,
                               "salida": resp.usage_metadata.candidates_token_count}
                    exito = True
                    break # Si funciona, salimos del bucle de reintentos
                except Exception as e:
                    error_str = str(e)
                    crudo = f"ERROR_API: {error_str}"
                    
                    if "429" in error_str or "Quota exceeded" in error_str:
                        tiempo_espera = 20 * (intento + 1) # 20s, 40s, 60s...
                        print(f"  ⚠️ Límite de velocidad alcanzado (429). Esperando {tiempo_espera}s...")
                        time.sleep(tiempo_espera)
                    else:
                        print(f"  ❌ Error inesperado: {error_str}")
                        time.sleep(5)

            # Guardar log (incluso si falló, para tener registro)
            d = extraer_json(crudo) if exito else None
            log.write(json.dumps({
                "id": r["id"], "oracion": r["oracion"], "modo": a.modo, "modelo": a.modelo,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "prompt": prompt, "respuesta_cruda": crudo, "json": d, "uso": uso
            }, ensure_ascii=False) + "\n")
            log.flush() # Forzar escritura en disco

            if d is not None:
                w.writerow([r["id"], int(d["acepta"])])
                pf.flush() # Forzar escritura en disco
                print(f"  ✅ Acepta: {d['acepta']}")
            else:
                print(f"  ❌ No devolvió JSON válido o falló tras reintentos.")

            # Pausa de cortesía para respetar el límite de 5 RPM (60s/5 = 12s)
            # Usamos 14s para estar seguros.
            if total_a_procesar > 1 and i < len(filas) - 1:
                time.sleep(14)

    print(f"\n¡Terminado! Resultados en: {ruta_pred}\nLog: {ruta_log}")

if __name__ == "__main__":
    main()