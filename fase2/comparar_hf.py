import argparse, time
from . import registro as R

MODELO = "dccuchile/bert-base-spanish-wwm-cased"


def pll(oracion, tok, modelo, torch):
    ids = tok(oracion, return_tensors="pt")["input_ids"][0]
    total = 0.0
    for i in range(1, len(ids) - 1):                 # sin [CLS] ni [SEP]
        enmascarado = ids.clone(); enmascarado[i] = tok.mask_token_id
        with torch.no_grad():
            logits = modelo(enmascarado.unsqueeze(0)).logits[0, i]
        total += torch.log_softmax(logits, -1)[ids[i]].item()
    n = max(1, len(ids) - 2)
    return total / n, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default=MODELO)
    ap.add_argument("--forzar", action="store_true")
    a = ap.parse_args()
    import torch
    from transformers import AutoTokenizer, AutoModelForMaskedLM
    tok = AutoTokenizer.from_pretrained(a.modelo)
    mod = AutoModelForMaskedLM.from_pretrained(a.modelo).eval()
    env = R.entorno("transformers", "torch")
    filas = R.leer_dataset()
    with R.abrir_log("hf.jsonl", a.forzar) as fh:
        for r in filas:
            ts, t0 = R.ahora(), time.perf_counter()
            puntaje, n = pll(r["oracion"], tok, mod, torch)
            R.escribir_linea(fh, {
                "herramienta": "hf", "id": r["id"], "oracion": r["oracion"], "timestamp_utc": ts,
                "tiempo_s": round(time.perf_counter() - t0, 6), "entorno": env,
                "parametros": {"modelo": a.modelo, "metrica": "PLL normalizada por token"},
                "salida": {"pll_norm": puntaje, "n_tokens": n}})
    print(f"hf: {len(filas)} oraciones -> {R.ruta_log('hf.jsonl')}")


if __name__ == "__main__":
    main()
