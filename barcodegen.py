# barcodegen.py — geração de códigos (lógica portada de poc_tkinter.py)
# Sem dependências de GUI: devolve PIL.Image; o ecrã converte para textura.
from datetime import datetime, timedelta
import barcode
from barcode.writer import ImageWriter

EPOCH = datetime(2000, 1, 1)   # contador em hora local naive (sem DST)

SYMBOLOGIES = {
    "Code128":  "code128",   # aceita tudo
    "Code39":   "code39",    # alfanumérico
    "ITF":      "itf",       # só dígitos, nº par
    "EAN-13":   "ean13",     # 12 dígitos (13º é check)
    "EAN-8":    "ean8",      # 7 dígitos
    "UPC-A":    "upca",      # 11 dígitos
    "GS1-128":  "gs1_128",   # aceita tudo
    "Codabar":  "codabar",   # dígitos + A-D nas pontas
}


def time_code(offset_min, terminal):
    t = datetime.now() - timedelta(minutes=offset_min)
    secs = int((t - EPOCH).total_seconds())
    return f"{secs:09d}{int(terminal):04d}", t


def render(payload, sym_name, zoom):
    cls = barcode.get_barcode_class(SYMBOLOGIES[sym_name])
    p = payload
    if sym_name == "ITF" and len(p) % 2:
        p = "0" + p
    return cls(p, writer=ImageWriter()).render({
        "module_height": 22.0 * zoom,
        "module_width":  0.42 * zoom,
        "write_text":    False,       # sem texto sob as barras (vai no label)
        "quiet_zone":    4.0,
        "background":    "white",
        "foreground":    "black",
    })
