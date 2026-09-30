# main.py — TicketCode / Barcode Wallet — passo 2: Gerador (PoC parque)
#
# Arranque blindado: a UI abre sempre; qualquer erro é mostrado no ecra
# (campo copiavel) e gravado em ficheiro legivel sem ferramentas extra.
import os
import sys
import traceback

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.base import ExceptionHandler, ExceptionManager

ANDROID = 'ANDROID_ARGUMENT' in os.environ  # True quando corre no telemovel

# no PC simular proporcao de telemovel; no Android fullscreen nativo
if not ANDROID:
    Window.size = (740, 360)
Window.clearcolor = (0, 0, 0, 1)

# python-barcode/PIL importados de forma PREGUICOSA (so quando se gera um
# codigo). Se falharem no telemovel, a UI abre na mesma e o erro aparece
# como texto, em vez de matar a app no arranque.
_bg = {"SYMBOLOGIES": {
    "Code128": "code128", "Code39": "code39", "ITF": "itf",
    "EAN-13": "ean13", "EAN-8": "ean8", "UPC-A": "upca",
    "GS1-128": "gs1_128", "Codabar": "codabar",
}, "time_code": None, "render": None, "err": None}


def _ensure_barcode():
    """Importa barcodegen na primeira utilizacao. Devolve True se ok."""
    if _bg["render"] is not None:
        return True
    if _bg["err"] is not None:
        return False
    try:
        import barcodegen
        _bg["SYMBOLOGIES"] = barcodegen.SYMBOLOGIES
        _bg["time_code"] = barcodegen.time_code
        _bg["render"] = barcodegen.render
        return True
    except Exception:
        _bg["err"] = traceback.format_exc()
        return False


# ---------------- captura de erros ----------------
def _crash_dir_candidates():
    dirs = []
    # 1) pasta externa da app (sem permissoes; visivel em gestores de ficheiros)
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        act = PythonActivity.mActivity
        d = act.getExternalFilesDir(None)
        if d:
            dirs.append(d.getAbsolutePath())
    except Exception:
        pass
    # 2) armazenamento primario
    dirs.append('/sdcard')
    dirs.append('/sdcard/Download')
    # 3) home (PC / fallback)
    dirs.append(os.path.expanduser('~'))
    return dirs


def _write_crash(text):
    for d in _crash_dir_candidates():
        try:
            path = os.path.join(d, 'btk_crash.txt')
            with open(path, 'w') as f:
                f.write(text)
            return path
        except Exception:
            continue
    return None


def _show_error_root(tb_text, saved_path=None):
    """Widget de erro copiavel para usar como root da app."""
    root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))
    header = 'ERRO — copia este texto:'
    if saved_path:
        header += f'\n(gravado em: {saved_path})'
    root.add_widget(Label(text=header, size_hint_y=None, height=dp(48),
                          color=(1, 0.5, 0.5, 1), font_size='12sp'))
    sv = ScrollView()
    ti = TextInput(text=tb_text, readonly=True, font_size='11sp',
                   background_color=(0.08, 0.08, 0.08, 1),
                   foreground_color=(0.9, 0.9, 0.9, 1))
    ti.size_hint_y = None
    ti.height = max(dp(400), len(tb_text.splitlines()) * dp(16))
    sv.add_widget(ti)
    root.add_widget(sv)
    return root


def _report(tb_text):
    path = _write_crash(tb_text)
    try:
        app = App.get_running_app()
        if app is not None:
            app.root = _show_error_root(tb_text, path)
    except Exception:
        pass
    return path


# excepthook global (apanha erros fora do loop do Kivy)
def _excepthook(exc_type, exc, tb):
    _write_crash(''.join(traceback.format_exception(exc_type, exc, tb)))
    sys.__excepthook__(exc_type, exc, tb)


sys.excepthook = _excepthook


class _CrashHandler(ExceptionHandler):
    def handle_exception(self, inst):
        _report(traceback.format_exc())
        return ExceptionManager.PASS


ExceptionManager.add_handler(_CrashHandler())


KV = """
#:set FG (0.88, 0.88, 0.88, 1)
#:set MUTED (0.5, 0.5, 0.5, 1)
#:set BTN (0.16, 0.16, 0.16, 1)
#:set ENTRY (0.10, 0.10, 0.10, 1)

<DarkButton@Button>:
    background_normal: ''
    background_color: BTN
    color: FG
    font_size: '14sp'

<DarkInput@TextInput>:
    multiline: False
    write_tab: False
    background_normal: ''
    background_active: ''
    background_color: ENTRY
    foreground_color: FG
    cursor_color: FG
    size_hint_y: None
    height: '32dp'
    font_size: '14sp'
    padding: '6dp', '6dp'

<FieldLabel@Label>:
    color: FG
    size_hint_x: None
    text_size: self.size
    halign: 'right'
    valign: 'middle'
    font_size: '13sp'

<SpinnerOption>:
    background_normal: ''
    background_color: BTN
    color: FG
    height: '34dp'

<GeradorScreen>:
    name: 'gerador'
    BoxLayout:
        orientation: 'vertical'
        padding: '6dp'
        spacing: '6dp'

        BoxLayout:
            size_hint_y: None
            height: '32dp'
            spacing: '6dp'
            FieldLabel:
                text: 'Offset'
                width: '46dp'
            DarkInput:
                id: offset
                text: '5'
                size_hint_x: None
                width: '52dp'
                input_filter: 'float'
            FieldLabel:
                text: 'Terminal'
                width: '58dp'
            DarkInput:
                id: term
                text: '1170'
                size_hint_x: None
                width: '60dp'
                input_filter: 'int'
            FieldLabel:
                text: 'Refresh'
                width: '52dp'
            DarkInput:
                id: interval
                text: '1'
                size_hint_x: None
                width: '46dp'
                input_filter: 'float'
            Spinner:
                id: sym
                text: 'Code128'
                values: root.symbologies
                background_normal: ''
                background_color: BTN
                color: FG
                size_hint_x: None
                width: '110dp'
                on_text: root.draw()
            CheckBox:
                id: manual
                size_hint_x: None
                width: '30dp'
                on_active: root.draw()
            Label:
                text: 'Manual'
                color: FG
                size_hint_x: None
                width: '54dp'
                font_size: '13sp'
            DarkInput:
                id: manual_code
                on_text_validate: root.draw()

        AnchorLayout:
            id: area
            Widget:
                id: holder
                size_hint: None, None
                size: code_img.width + dp(16), code_img.height + dp(16)
                canvas.before:
                    Color:
                        rgba: 1, 1, 1, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
                Image:
                    id: code_img
                    size_hint: None, None
                    size: 0, 0
                    fit_mode: 'fill'
                    center: holder.center

        Label:
            id: info
            color: FG
            font_size: '14sp'
            size_hint_y: None
            height: '22dp'

        BoxLayout:
            size_hint_y: None
            height: '40dp'
            spacing: '6dp'
            DarkButton:
                text: 'Gerar'
                on_release: root.draw()
            DarkButton:
                id: startbtn
                text: 'Start'
                on_release: root.toggle()
            DarkButton:
                text: '\\u2212'
                size_hint_x: None
                width: '48dp'
                on_release: root.set_zoom(0.8)
            DarkButton:
                text: '+'
                size_hint_x: None
                width: '48dp'
                on_release: root.set_zoom(1.25)
            DarkButton:
                text: 'Carteira \\u00bb'
                size_hint_x: None
                width: '110dp'
                on_release: root.manager.current = 'carteira'

<CarteiraScreen>:
    name: 'carteira'
    BoxLayout:
        orientation: 'vertical'
        padding: '6dp'
        spacing: '6dp'
        AnchorLayout:
            BoxLayout:
                orientation: 'vertical'
                size_hint: None, None
                size: self.minimum_size
                spacing: '6dp'
                Label:
                    text: 'Carteira'
                    color: FG
                    font_size: '22sp'
                    size_hint_y: None
                    height: '30dp'
                Label:
                    text: '(lista SQLite + scanner entram nos passos 3 e 4)'
                    color: MUTED
                    font_size: '13sp'
                    size_hint_y: None
                    height: '22dp'
        BoxLayout:
            size_hint_y: None
            height: '40dp'
            DarkButton:
                text: '\\u00ab Gerador'
                size_hint_x: None
                width: '140dp'
                on_release: root.manager.current = 'gerador'
"""


def pil_to_texture(img):
    img = img.convert('RGBA')
    tex = Texture.create(size=img.size, colorfmt='rgba')
    tex.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
    tex.flip_vertical()
    tex.mag_filter = 'nearest'
    return tex


class GeradorScreen(Screen):
    symbologies = list(_bg["SYMBOLOGIES"])

    def __init__(self, **kw):
        super().__init__(**kw)
        self.zoom = 1.0
        self.running = False
        self.job = None

    def on_kv_post(self, base_widget):
        try:
            self.ids.area.bind(size=lambda *a: self.fit_image())
        except Exception:
            _report(traceback.format_exc())
        # NAO geramos automaticamente: a UI abre limpa; o utilizador prime Gerar
        self.ids.info.text = 'Prime "Gerar"'

    def set_zoom(self, factor):
        self.zoom = min(6.0, max(0.4, self.zoom * factor))
        self.draw()

    def payload(self):
        if self.ids.manual.active:
            return self.ids.manual_code.text.strip(), None
        return _bg["time_code"](float(self.ids.offset.text or 0),
                                self.ids.term.text or 0)

    def draw(self):
        info = self.ids.info
        if not _ensure_barcode():
            # import do barcode/PIL falhou -> mostrar o motivo real
            info.text = 'erro no import (ver btk_crash.txt)'
            _report(_bg["err"] or 'import falhou')
            return
        try:
            code, t = self.payload()
            if not code:
                info.text = '(codigo vazio)'
                return
            img = _bg["render"](code, self.ids.sym.text, self.zoom)
            self.ids.code_img.texture = pil_to_texture(img)
            self.fit_image()
            stamp = f'   {t:%d-%m-%Y %H:%M:%S}' if t else '   [manual]'
            info.text = f'{code}{stamp}'
        except Exception:
            tb = traceback.format_exc()
            info.text = 'erro ao gerar (ver btk_crash.txt)'
            _write_crash(tb)

    def fit_image(self):
        img, area = self.ids.code_img, self.ids.area
        if not img.texture:
            return
        tw, th = img.texture.size
        pad = dp(16)
        s = max(0.0, min(1.0, (area.width - pad) / tw, (area.height - pad) / th))
        img.size = (tw * s, th * s)

    def toggle(self):
        self.running = not self.running
        self.ids.startbtn.text = 'Stop' if self.running else 'Start'
        if self.running:
            self.loop()
        elif self.job:
            self.job.cancel()
            self.job = None

    def loop(self, *a):
        if not self.running:
            return
        if not self.ids.manual.active:
            self.draw()
        try:
            secs = max(0.2, float(self.ids.interval.text))
        except ValueError:
            secs = 1.0
        self.job = Clock.schedule_once(self.loop, secs)


class CarteiraScreen(Screen):
    pass


class TicketCodeApp(App):
    def build(self):
        self.title = 'TicketCode / Barcode Wallet'
        try:
            Builder.load_string(KV)
            sm = ScreenManager()
            sm.add_widget(GeradorScreen())
            sm.add_widget(CarteiraScreen())
            return sm
        except Exception:
            tb = traceback.format_exc()
            path = _write_crash(tb)
            return _show_error_root(tb, path)


if __name__ == '__main__':
    try:
        TicketCodeApp().run()
    except Exception:
        _write_crash(traceback.format_exc())
        raise
