# main.py — TicketCode / Barcode Wallet — passo 2: Gerador (PoC parque)
import os
import platform
import traceback

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.base import ExceptionHandler, ExceptionManager

from barcodegen import SYMBOLOGIES, time_code, render

ANDROID = 'ANDROID_ARGUMENT' in os.environ  # True quando corre no telemóvel

# no PC simular proporção de telemóvel; no Android deixar em fullscreen nativo
if not ANDROID:
    Window.size = (740, 360)
Window.clearcolor = (0, 0, 0, 1)   # fundo preto


# --- rede de segurança: em vez de crash silencioso, mostra o traceback ---
class _CrashHandler(ExceptionHandler):
    def handle_exception(self, inst):
        tb = traceback.format_exc()
        # gravar num ficheiro acessível
        for path in ('/sdcard/barcodetoolkit_crash.txt',
                     os.path.join(os.path.expanduser('~'), 'btk_crash.txt')):
            try:
                with open(path, 'w') as f:
                    f.write(tb)
                break
            except Exception:
                continue
        # mostrar no ecrã
        try:
            app = App.get_running_app()
            if app and app.root is not None:
                app.root.clear_widgets()
                app.root.add_widget(Label(
                    text=tb[-3500:], color=(1, 1, 1, 1),
                    font_size='11sp', halign='left', valign='top'))
        except Exception:
            pass
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

        # ---- barra de controlos (topo) ----
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

        # ---- código (ocupa todo o espaço livre) ----
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

        # ---- info ----
        Label:
            id: info
            color: FG
            font_size: '14sp'
            size_hint_y: None
            height: '22dp'

        # ---- barra inferior (ações + navegação) ----
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
    """PIL.Image -> Texture do Kivy (RGBA evita problemas de alinhamento GL)."""
    img = img.convert('RGBA')
    tex = Texture.create(size=img.size, colorfmt='rgba')
    tex.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
    tex.flip_vertical()            # PIL tem origem em cima, GL em baixo
    tex.mag_filter = 'nearest'     # barras nítidas se houver reescala
    return tex


class GeradorScreen(Screen):
    symbologies = list(SYMBOLOGIES)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.zoom = 1.0
        self.running = False
        self.job = None

    def on_kv_post(self, base_widget):
        # ids só existem depois de aplicada a regra KV
        self.ids.area.bind(size=lambda *a: self.fit_image())
        Clock.schedule_once(lambda dt: self.draw())

    def set_zoom(self, factor):
        self.zoom = min(6.0, max(0.4, self.zoom * factor))
        self.draw()

    def payload(self):
        if self.ids.manual.active:
            return self.ids.manual_code.text.strip(), None
        return time_code(float(self.ids.offset.text or 0), self.ids.term.text or 0)

    def draw(self):
        info = self.ids.info
        try:
            code, t = self.payload()
            if not code:
                info.text = '(código vazio)'
                return
            self.ids.code_img.texture = pil_to_texture(render(code, self.ids.sym.text, self.zoom))
            self.fit_image()
            stamp = f'   {t:%d-%m-%Y %H:%M:%S}' if t else '   [manual]'
            info.text = f'{code}{stamp}'
        except Exception as e:
            info.text = f'erro: {e}'

    def fit_image(self):
        """Tamanho nativo da textura; só encolhe se não couber na área."""
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
        Builder.load_string(KV)          # regras de classe (<GeradorScreen> etc.)
        sm = ScreenManager()
        sm.add_widget(GeradorScreen())   # instanciados em código, não via regra raiz
        sm.add_widget(CarteiraScreen())
        return sm


if __name__ == '__main__':
    TicketCodeApp().run()