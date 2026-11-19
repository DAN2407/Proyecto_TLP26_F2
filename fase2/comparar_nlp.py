import argparse, time
from . import registro as R


def correr_parser(filas, forzar=False, logs=R.LOGS):
    from .parser_es import analizar
    env = R.entorno()
    with R.abrir_log("parser.jsonl", forzar, logs) as fh:
        for r in filas:
            ts, t0 = R.ahora(), time.perf_counter()
            res = analizar(r["oracion"], "SV")
            dt = time.perf_counter() - t0
            R.escribir_linea(fh, {
                "herramienta": "parser", "id": r["id"], "oracion": r["oracion"], "timestamp_utc": ts,
                "tiempo_s": round(dt, 6), "entorno": env, "parametros": {"attach": "SV"},
                "salida": {"acepta": res.acepta, "tipo_error": res.tipo_error, "error": res.error,
                           "arbol": res.arbol.sexp() if res.arbol else "",
                           "pos": [list(p) for p in res.pos]}})
    print(f"parser: {len(filas)} oraciones -> {R.ruta_log('parser.jsonl', logs)}")


def juzgar_spacy(doc):
    """Devuelve (acepta: bool, motivo: str) según la heurística documentada arriba."""
    for t in doc:
        m, mh = t.morph.to_dict(), t.head.morph.to_dict()
        if t.dep_ in ("det", "amod") and t.head.pos_ in ("NOUN", "PROPN"):
            for rasgo in ("Gender", "Number"):
                if rasgo in m and rasgo in mh and m[rasgo] != mh[rasgo]:
                    return False, f"{rasgo}: {t.text}({m[rasgo]}) vs {t.head.text}({mh[rasgo]})"
        if t.dep_ == "nsubj" and t.head.pos_ in ("VERB", "AUX"):
            n1, n2 = m.get("Number"), mh.get("Number")
            if n1 and n2 and n1 != n2:
                return False, f"Number sujeto-verbo: {t.text}({n1}) vs {t.head.text}({n2})"
    return True, ""


def correr_spacy(filas, modelo="es_core_news_sm", forzar=False, logs=R.LOGS):
    import spacy
    nlp = spacy.load(modelo)
    env = R.entorno("spacy", modelo.replace("_", "-"))
    env["modelo_spacy"] = {"nombre": modelo, "version": nlp.meta.get("version")}
    with R.abrir_log("spacy.jsonl", forzar, logs) as fh:
        for r in filas:
            ts, t0 = R.ahora(), time.perf_counter()
            doc = nlp(r["oracion"])
            dt = time.perf_counter() - t0
            ok, motivo = juzgar_spacy(doc)
            R.escribir_linea(fh, {
                "herramienta": "spacy", "id": r["id"], "oracion": r["oracion"], "timestamp_utc": ts,
                "tiempo_s": round(dt, 6), "entorno": env, "parametros": {"modelo": modelo},
                "salida": {"acepta": ok, "motivo": motivo,
                           "tokens": [{"texto": t.text, "pos": t.pos_, "morph": str(t.morph), "dep": t.dep_,
                                       "cabeza": t.head.i} for t in doc]}})
    print(f"spacy ({modelo}): {len(filas)} oraciones -> {R.ruta_log('spacy.jsonl', logs)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=["parser", "spacy"])
    ap.add_argument("--modelo", default="es_core_news_sm")
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args()
    filas = R.leer_dataset()
    if a.solo in (None, "parser"):
        correr_parser(filas, a.forzar)
    if a.solo in (None, "spacy"):
        correr_spacy(filas, a.modelo, a.forzar)


if __name__ == "__main__":
    main()
