import argparse, csv, json, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import registro as R

ORDEN = ["parser", "spacy", "hf", "llm_zero", "llm_few"]
NOMBRES = {"parser": "Parser propio", "spacy": "spaCy", "hf": "HF (BETO-PLL)",
           "llm_zero": "LLM zero-shot", "llm_few": "LLM few-shot"}
REFS = {"esperado_gramatica": "salida esperada (gramática)", "gramatical_es": "juicio nativo"}
# UPOS aceptados como equivalentes (documentar en el informe): 'que' relativo puede ser SCONJ o PRON.
UPOS_EQUIV = {"SCONJ": {"SCONJ", "PRON"}}
# Etiquetas de nodo del árbol que devuelve el LLM -> UPOS
LLM_A_UPOS = {"Det": "DET", "N": "NOUN", "Adj": "ADJ", "V": "VERB", "Adv": "ADV", "Prep": "ADP", "A": "ADP",
              "Apers": "ADP", "A_pers": "ADP", "PN": "PROPN", "Que": "SCONJ", "Rel": "SCONJ"}


# ----------------------------------------------------------------------------- lectura de logs
def cargar_logs(logs):
    """{herramienta: {id: registro}}. Falla si un id está duplicado en un log."""
    out = {}
    for h in ORDEN:
        ruta = os.path.join(logs, h + ".jsonl")
        if not os.path.exists(ruta):
            continue
        por_id = {}
        for reg in R.leer_jsonl(ruta):
            if reg["id"] in por_id:
                raise ValueError(f"{ruta}: id duplicado {reg['id']}")
            por_id[reg["id"]] = reg
        out[h] = por_id
    return out


def verificar(logs_cargados, ds, estricto=False):
    problemas = []
    for h, regs in logs_cargados.items():
        faltan = sorted(set(ds) - set(regs))
        extra = sorted(set(regs) - set(ds))
        if faltan:
            problemas.append(f"{h}: faltan {len(faltan)} oraciones del dataset (p. ej. {faltan[:5]})")
        if extra:
            problemas.append(f"{h}: {len(extra)} ids que no están en el dataset")
        for i, reg in regs.items():
            if i in ds and reg.get("oracion") != ds[i]["oracion"]:
                problemas.append(f"{h}[{i}]: la oración del log no coincide con el dataset")
                break
        campo = "timestamp_inicio" if h.startswith("llm") else "timestamp_utc"
        if any(not reg.get(campo) for reg in regs.values()):
            problemas.append(f"{h}: hay líneas sin {campo}")
    for p in problemas:
        print("AVISO:", p)
    if problemas and estricto:
        raise SystemExit("Verificación estricta fallida.")
    return problemas


# ----------------------------------------------------------------------------- derivación de predicciones
def tags_de_arbol_llm(arbol: str):
    """Hojas de '(S (SN (Det la) (N perra)) ...)' -> lista de UPOS en orden; None si no hay árbol."""
    if not arbol:
        return None
    hojas = re.findall(r"\((Rel)\s+(que)\b|\((\w+)\s+([^()\s]+)\)", arbol)
    tags = [LLM_A_UPOS.get(rel or etq, "?") for rel, _q, etq, _pal in hojas]
    return tags or None


def calibrar_umbral(puntajes, ds):
    """Umbral PLL que maximiza la exactitud balanceada vs gramatical_es usando SOLO el split 'dev'."""
    dev = [i for i in puntajes if ds[i]["split"] == "dev"]
    pos = [i for i in dev if int(ds[i]["gramatical_es"])]
    neg = [i for i in dev if not int(ds[i]["gramatical_es"])]
    mejor, umbral = -1.0, min(puntajes.values())
    for u in sorted({puntajes[i] for i in dev}):
        sens = sum(puntajes[i] >= u for i in pos) / len(pos)
        espec = sum(puntajes[i] < u for i in neg) / len(neg)
        if (sens + espec) / 2 > mejor + 1e-12:
            mejor, umbral = (sens + espec) / 2, u
    return umbral, mejor


def derivar(h, regs, ds):
    """Devuelve (pred {id: 0/1/None}, tags {id: [UPOS] | None}, detalle {id: str}, info dict)."""
    pred, tags, det, info = {}, {}, {}, {}
    if h == "hf":
        punt = {i: r["salida"]["pll_norm"] for i, r in regs.items() if i in ds}
        umbral, bal = calibrar_umbral(punt, ds)
        info = {"umbral_pll": round(umbral, 4), "exactitud_balanceada_dev": round(bal, 3)}
        for i, p in punt.items():
            pred[i], tags[i], det[i] = int(p >= umbral), None, f"pll_norm={p:.3f} (umbral {umbral:.3f})"
        return pred, tags, det, info
    for i, r in regs.items():
        if i not in ds:
            continue
        if h == "parser":
            s = r["salida"]
            pred[i] = int(s["acepta"])
            tags[i] = [p[1] for p in s["pos"]] if s["acepta"] else None
            det[i] = s["error"]
        elif h == "spacy":
            s = r["salida"]
            pred[i] = int(s["acepta"])
            tags[i] = [t["pos"] for t in s["tokens"] if t["pos"] != "PUNCT"]
            det[i] = s["motivo"]
        else:                                                        # llm_zero / llm_few
            j = r.get("json")
            if not isinstance(j, dict) or not isinstance(j.get("acepta"), bool):
                pred[i], tags[i], det[i] = None, None, "sin JSON válido: " + (r.get("respuesta_cruda") or "")[:120]
                continue
            pred[i] = int(j["acepta"])
            tags[i] = tags_de_arbol_llm(j.get("arbol", "")) if j["acepta"] else None
            det[i] = j.get("regla_violada", "")
    return pred, tags, det, info


# ----------------------------------------------------------------------------- métricas
def matriz(pred, gold, ids):
    ids = [i for i in ids if pred.get(i) is not None]
    tp = sum(1 for i in ids if pred[i] == 1 and gold[i] == 1)
    fp = sum(1 for i in ids if pred[i] == 1 and gold[i] == 0)
    fn = sum(1 for i in ids if pred[i] == 0 and gold[i] == 1)
    tn = sum(1 for i in ids if pred[i] == 0 and gold[i] == 0)
    return tp, fp, fn, tn


def metricas(tp, fp, fn, tn):
    d = lambda a, b: round(a / b, 3) if b else None
    return {"precision": d(tp, tp + fp), "cobertura": d(tp, tp + fn),
            "rechazo_correcto": d(tn, tn + fp), "exactitud": d(tp + tn, tp + fp + fn + tn),
            "TP": tp, "FP": fp, "FN": fn, "TN": tn}


def etiquetado_ok(oro, pred_tags):
    """(oración_correcta, aciertos, n_tokens_oro). Si la tokenización no coincide, la oración falla."""
    oro_t = [p.split("/")[1] for p in oro.split()]
    if pred_tags is None or len(pred_tags) != len(oro_t):
        return False, 0, len(oro_t)
    ac = sum(1 for o, p in zip(oro_t, pred_tags) if p in UPOS_EQUIV.get(o, {o}))
    return ac == len(oro_t), ac, len(oro_t)


def guardar_csv(res, nombre, filas):
    if not filas:
        return
    with open(os.path.join(res, nombre), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader(); w.writerows(filas)


def fmt(v):
    return "–" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


def tabla_md(filas, cols):
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    out += ["| " + " | ".join(fmt(f.get(c)) for c in cols) + " |" for f in filas]
    return "\n".join(out)


# ----------------------------------------------------------------------------- programa principal
def evaluar(logs=R.LOGS, res=R.RES, estricto=False, dataset=R.DATASET, verbose=True):
    ds = {r["id"]: r for r in R.leer_dataset(dataset)}
    L = cargar_logs(logs)
    if not L:
        raise SystemExit(f"No hay logs en {logs}. Ejecute primero comparar_nlp / comparar_hf / llm_experimento.")
    verificar(L, ds, estricto)
    os.makedirs(res, exist_ok=True)
    herr = [h for h in ORDEN if h in L]

    glob_rows, nivel_rows, err_rows, clas_rows, desv_rows = [], [], [], [], []
    costo_rows, upos_rows, calib, derivadas = [], [], {}, {}
    for h in herr:
        pred, tags, det, info = derivar(h, L[h], ds)
        derivadas[h] = pred
        if info:
            calib[h] = info
        ids_all = sorted(i for i in pred if i in ds)
        sin_resp = [i for i in ids_all if pred[i] is None]
        for i in sin_resp:
            err_rows.append({"herramienta": h, "referencia": "ambas", "id": i, "oracion": ds[i]["oracion"],
                             "nivel": ds[i]["nivel"], "fenomeno": ds[i]["fenomeno"], "tipo_error": "sin_respuesta",
                             "detalle": det[i]})
        # --- etiquetado UPOS: oraciones con upos_oro que la herramienta aceptó (solo si emite etiquetas)
        emite_tags = any(t is not None for t in tags.values())
        et_err = et_n = tok_ok = tok_n = 0
        if emite_tags:
            for i in ids_all:
                if ds[i]["upos_oro"] and pred[i] == 1:
                    ok, ac, n = etiquetado_ok(ds[i]["upos_oro"], tags[i])
                    et_n += 1; tok_ok += ac; tok_n += n
                    if not ok:
                        et_err += 1
                        err_rows.append({"herramienta": h, "referencia": "ambas", "id": i, "oracion": ds[i]["oracion"],
                                         "nivel": ds[i]["nivel"], "fenomeno": ds[i]["fenomeno"],
                                         "tipo_error": "error_de_etiquetado",
                                         "detalle": f"oro={ds[i]['upos_oro']} | pred={' '.join(tags[i] or ['(sin etiquetas)'])}"})
            upos_rows.append({"herramienta": h, "oraciones_evaluadas": et_n, "oraciones_con_error": et_err,
                              "exactitud_oracion": round((et_n - et_err) / et_n, 3) if et_n else None,
                              "tokens_oro": tok_n, "tokens_correctos": tok_ok,
                              "exactitud_token": round(tok_ok / tok_n, 3) if tok_n else None})
        for ref in REFS:
            gold = {i: int(ds[i][ref]) for i in ds}
            for sub, ids in [("todo", ids_all), ("test", [i for i in ids_all if ds[i]["split"] == "test"])]:
                glob_rows.append({"herramienta": h, "referencia": ref, "subconjunto": sub,
                                  "n": len([i for i in ids if pred[i] is not None]),
                                  **metricas(*matriz(pred, gold, ids))})
            for nv in ("1", "2", "3"):
                ids = [i for i in ids_all if ds[i]["nivel"] == nv]
                nivel_rows.append({"herramienta": h, "referencia": ref, "nivel": nv,
                                   "n": len([i for i in ids if pred[i] is not None]),
                                   **metricas(*matriz(pred, gold, ids))})
            fp = fn = 0
            for i in ids_all:
                if pred[i] is None or pred[i] == gold[i]:
                    continue
                tipo = "falso_positivo" if pred[i] == 1 else "falso_negativo"
                fp += tipo == "falso_positivo"; fn += tipo == "falso_negativo"
                err_rows.append({"herramienta": h, "referencia": ref, "id": i, "oracion": ds[i]["oracion"],
                                 "nivel": ds[i]["nivel"], "fenomeno": ds[i]["fenomeno"], "tipo_error": tipo,
                                 "detalle": det[i]})
            clas_rows.append({"herramienta": h, "referencia": ref, "falsos_positivos": fp, "falsos_negativos": fn,
                              "errores_etiquetado": et_err if emite_tags else None, "sin_respuesta": len(sin_resp)})
        ok_ids = lambda cond: [i for i in ids_all if pred[i] is not None and cond(ds[i])]
        fuera = ok_ids(lambda r: r["gramatical_es"] == "1" and r["esperado_gramatica"] == "0")
        dentro = ok_ids(lambda r: r["esperado_gramatica"] == "1")
        agram = ok_ids(lambda r: r["gramatical_es"] == "0")
        d = lambda a, b: round(a / b, 3) if b else None
        desv_rows.append({"herramienta": h, "n_fuera_de_gramatica": len(fuera),
                          "acepta_fuera_de_gramatica": d(sum(pred[i] for i in fuera), len(fuera)),
                          "n_en_gramatica": len(dentro),
                          "rechaza_en_gramatica": d(sum(1 - pred[i] for i in dentro), len(dentro)),
                          "n_agramaticales": len(agram),
                          "rechaza_agramaticales": d(sum(1 - pred[i] for i in agram), len(agram))})
        tiempos = [L[h][i]["tiempo_s"] for i in ids_all if L[h][i].get("tiempo_s") is not None]
        usos = [L[h][i].get("uso") or {} for i in ids_all] if h.startswith("llm") else []
        modelo = None
        if h.startswith("llm") and ids_all:
            modelo = L[h][ids_all[0]].get("modelo_devuelto") or L[h][ids_all[0]].get("modelo")
        costo_rows.append({"herramienta": h, "oraciones": len(ids_all), "tiempo_total_s": round(sum(tiempos), 3),
                           "tiempo_medio_s": round(sum(tiempos) / len(tiempos), 4) if tiempos else None,
                           "tokens_entrada": sum(u.get("entrada", 0) for u in usos) if usos else None,
                           "tokens_salida": sum(u.get("salida", 0) for u in usos) if usos else None,
                           "modelo": modelo})

    orden_err = lambda r: (ORDEN.index(r["herramienta"]), r["referencia"], r["id"], r["tipo_error"])
    guardar_csv(res, "metricas_global.csv", glob_rows)
    guardar_csv(res, "metricas_por_nivel.csv", nivel_rows)
    guardar_csv(res, "errores.csv", sorted(err_rows, key=orden_err))
    guardar_csv(res, "clasificacion_errores.csv", clas_rows)
    guardar_csv(res, "desvio_conocimiento_general.csv", desv_rows)
    guardar_csv(res, "costo_computacional.csv", costo_rows)
    guardar_csv(res, "etiquetado_upos.csv", upos_rows)

    # predicciones derivadas, una fila por oración (para auditar a mano)
    filas_pred = []
    for i in sorted(ds):
        f = {"id": i, "oracion": ds[i]["oracion"], "nivel": ds[i]["nivel"],
             "esperado_gramatica": ds[i]["esperado_gramatica"], "gramatical_es": ds[i]["gramatical_es"]}
        for h in herr:
            p = derivadas[h].get(i, "")
            f[h] = "" if p is None else p
        filas_pred.append(f)
    guardar_csv(res, "predicciones_derivadas.csv", filas_pred)

    # manifiesto de entradas: demuestra de qué archivos salen las tablas
    with open(os.path.join(res, "entradas_sha256.txt"), "w", encoding="utf-8") as f:
        f.write(f"dataset.csv  {R.sha256(dataset)}\n")
        for h in herr:
            f.write(f"logs/{h}.jsonl  {R.sha256(os.path.join(logs, h + '.jsonl'))}\n")

    escribir_markdown(res, glob_rows, nivel_rows, clas_rows, desv_rows, costo_rows, upos_rows, calib)
    graficas(res, herr, glob_rows, nivel_rows)
    if verbose:
        imprimir(glob_rows)
        print(f"\nTablas y gráficas guardadas en {res}")
    return {"global": glob_rows, "nivel": nivel_rows, "errores": err_rows, "desvio": desv_rows, "calibracion": calib}


def escribir_markdown(res, glob_rows, nivel_rows, clas_rows, desv_rows, costo_rows, upos_rows, calib):
    nom = lambda rows: [{**r, "herramienta": NOMBRES[r["herramienta"]]} for r in rows]
    partes = ["# Tablas para el informe (generadas por fase2/evaluar.py; no editar a mano)\n"]
    cols = ["herramienta", "n", "precision", "cobertura", "rechazo_correcto", "exactitud", "TP", "FP", "FN", "TN"]
    for ref, nombre in REFS.items():
        partes.append(f"## Métricas globales, referencia: {nombre} (todo el corpus)\n")
        partes.append(tabla_md(nom([r for r in glob_rows if r["referencia"] == ref and r["subconjunto"] == "todo"]), cols) + "\n")
        partes.append(f"## Métricas sobre el split test, referencia: {nombre}\n")
        partes.append(tabla_md(nom([r for r in glob_rows if r["referencia"] == ref and r["subconjunto"] == "test"]), cols) + "\n")
        partes.append(f"## Métricas por nivel, referencia: {nombre}\n")
        partes.append(tabla_md(nom([r for r in nivel_rows if r["referencia"] == ref]), ["herramienta", "nivel"] + cols[1:]) + "\n")
    partes.append("## Clasificación de errores\n")
    partes.append(tabla_md(nom(clas_rows), ["herramienta", "referencia", "falsos_positivos", "falsos_negativos",
                                            "errores_etiquetado", "sin_respuesta"]) + "\n")
    if upos_rows:
        partes.append("## Etiquetado UPOS (oraciones aceptadas con etiquetas de oro)\n")
        partes.append(tabla_md(nom(upos_rows), list(upos_rows[0])) + "\n")
    partes.append("## Desvío al conocimiento general / respeto de las reglas\n")
    partes.append(tabla_md(nom(desv_rows), list(desv_rows[0])) + "\n")
    partes.append("## Costo computacional\n")
    partes.append(tabla_md(nom(costo_rows), list(costo_rows[0])) + "\n")
    if calib:
        partes.append("## Calibración (HF, solo split dev)\n")
        partes.append("\n".join(f"- {NOMBRES[h]}: {json.dumps(v, ensure_ascii=False)}" for h, v in calib.items()) + "\n")
    with open(os.path.join(res, "tablas_informe.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(partes))


def imprimir(glob_rows):
    print(f"{'herramienta':<16}{'referencia':<20}{'sub':<6}{'n':>4}{'prec':>7}{'cob':>7}{'rech':>7}{'exac':>7}  TP FP FN TN")
    for r in glob_rows:
        f = lambda v: f"{v:.2f}" if v is not None else "  -  "
        print(f"{NOMBRES[r['herramienta']]:<16}{r['referencia']:<20}{r['subconjunto']:<6}{r['n']:>4}"
              f"{f(r['precision']):>7}{f(r['cobertura']):>7}{f(r['rechazo_correcto']):>7}{f(r['exactitud']):>7}"
              f"  {r['TP']:>2} {r['FP']:>2} {r['FN']:>2} {r['TN']:>2}")


def graficas(res, herr, glob_rows, nivel_rows):
    colores = ["#2a6fb0", "#d9822b", "#3a9a5b", "#8a5fb5", "#b04a4a"]
    etiquetas, claves = ["precisión", "cobertura", "rechazo correcto"], ["precision", "cobertura", "rechazo_correcto"]
    ancho = 0.8 / len(herr)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, ref in zip(axs, REFS):
        for k, h in enumerate(herr):
            fila = next(r for r in glob_rows if r["herramienta"] == h and r["referencia"] == ref and r["subconjunto"] == "todo")
            vals = [fila[c] or 0 for c in claves]
            xs = [j + k * ancho for j in range(3)]
            ax.bar(xs, vals, ancho, label=NOMBRES[h], color=colores[k % 5])
            for x, v in zip(xs, vals):
                ax.text(x, v + 0.01, f"{v:.2f}", ha="center", fontsize=7)
        ax.set_xticks([j + 0.4 - ancho / 2 for j in range(3)]); ax.set_xticklabels(etiquetas)
        ax.set_title(f"Referencia: {REFS[ref]}"); ax.set_ylim(0, 1.12)
    axs[0].set_ylabel("valor"); axs[0].legend(fontsize=8); fig.tight_layout()
    fig.savefig(os.path.join(res, "grafica_metricas.png"), dpi=150); plt.close(fig)

    fig, axs = plt.subplots(2, 3, figsize=(13, 6.5), sharey=True)
    for fila_ax, ref in zip(axs, REFS):
        for ax, nv in zip(fila_ax, ("1", "2", "3")):
            for k, h in enumerate(herr):
                f = next(r for r in nivel_rows if r["herramienta"] == h and r["referencia"] == ref and r["nivel"] == nv)
                v = f["exactitud"] or 0
                ax.bar(k, v, 0.7, color=colores[k % 5]); ax.text(k, v + 0.01, f"{v:.2f}", ha="center", fontsize=8)
            ax.set_xticks(range(len(herr))); ax.set_xticklabels([NOMBRES[h] for h in herr], rotation=25, fontsize=7)
            ax.set_title(f"Nivel {nv} – ref. {REFS[ref]}", fontsize=9); ax.set_ylim(0, 1.1)
        fila_ax[0].set_ylabel("exactitud")
    fig.tight_layout(); fig.savefig(os.path.join(res, "grafica_por_nivel.png"), dpi=150); plt.close(fig)

    fig, axs = plt.subplots(2, len(herr), figsize=(3.3 * len(herr), 6.4), squeeze=False)
    for fila_ax, ref in zip(axs, REFS):
        for ax, h in zip(fila_ax, herr):
            f = next(r for r in glob_rows if r["herramienta"] == h and r["referencia"] == ref and r["subconjunto"] == "todo")
            m = [[f["TN"], f["FP"]], [f["FN"], f["TP"]]]
            ax.imshow(m, cmap="Blues")
            for a in range(2):
                for b in range(2):
                    ax.text(b, a, m[a][b], ha="center", va="center", fontsize=13)
            ax.set_xticks([0, 1]); ax.set_xticklabels(["rechaza", "acepta"], fontsize=8)
            ax.set_yticks([0, 1]); ax.set_yticklabels(["debía rechazar", "debía aceptar"], fontsize=8)
            ax.set_title(f"{NOMBRES[h]}\n({REFS[ref]})", fontsize=8)
    fig.suptitle("Matrices de confusión"); fig.tight_layout()
    fig.savefig(os.path.join(res, "matrices_confusion.png"), dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=R.LOGS)
    ap.add_argument("--salida", default=R.RES)
    ap.add_argument("--estricto", action="store_true")
    a = ap.parse_args()
    evaluar(a.logs, a.salida, a.estricto)


if __name__ == "__main__":
    main()
