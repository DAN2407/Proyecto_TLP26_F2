import csv, datetime, hashlib, json, os, platform, sys
from importlib import metadata

AQUI = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(AQUI, "logs")
RES = os.path.join(AQUI, "resultados")
DATASET = os.path.join(AQUI, "dataset.csv")


def ahora() -> str:
    """Timestamp UTC ISO-8601 con milisegundos."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds")


def leer_dataset(ruta: str = DATASET):
    with open(ruta, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def entorno(*paquetes: str) -> dict:
    """Versión de Python, sistema y de los paquetes indicados (None si no están instalados)."""
    vers = {}
    for p in paquetes:
        try:
            vers[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            vers[p] = None
    return {"python": sys.version.split()[0], "sistema": platform.platform(), "paquetes": vers}


def ruta_log(nombre: str, logs: str = LOGS) -> str:
    os.makedirs(logs, exist_ok=True)
    return os.path.join(logs, nombre)


def abrir_log(nombre: str, forzar: bool = False, logs: str = LOGS):
    """Abre logs/<nombre> para escribir; aborta si ya existe y no se pidió --forzar."""
    ruta = ruta_log(nombre, logs)
    if os.path.exists(ruta) and not forzar:
        raise SystemExit(f"{ruta} ya existe. Es evidencia del experimento: use --forzar si quiere regenerarlo.")
    return open(ruta, "w", encoding="utf-8")


def escribir_linea(fh, obj: dict):
    fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    fh.flush()


def leer_jsonl(ruta: str):
    out = []
    with open(ruta, encoding="utf-8") as fh:
        for n, linea in enumerate(fh, 1):
            if linea.strip():
                try:
                    out.append(json.loads(linea))
                except json.JSONDecodeError as e:
                    raise ValueError(f"{ruta}, línea {n}: JSON inválido ({e})")
    return out


def sha256(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()
