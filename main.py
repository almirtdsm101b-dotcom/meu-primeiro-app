import json
import os

from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget


MESES = [
    "Agosto/2026",
    "Setembro/2026",
    "Outubro/2026",
    "Novembro/2026",
    "Dezembro/2026",
]


class CardBox(BoxLayout):
    def __init__(
        self,
        bg_color=(0.082, 0.098, 0.133, 1),
        border_color=(0.165, 0.192, 0.259, 1),
        radius=12,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._bg_color = bg_color
        self._border_color = border_color
        self._radius = radius
        with self.canvas.before:
            Color(*self._bg_color)
            self._rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[self._radius]
            )
            Color(*self._border_color)
            self._line = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    self._radius,
                ),
                width=1.1,
            )
        self.bind(pos=self._atualizar_canvas, size=self._atualizar_canvas)

    def _atualizar_canvas(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self._radius,
        )


def _parse_numero(texto):
    if not texto:
        return None
    limpo = texto.strip().replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _fmt_virgula(valor, decimais=2):
    return f"{valor:.{decimais}f}".replace(".", ",")


class ControleFreteApp(App):
    def build(self):
        Window.clearcolor = (0.043, 0.055, 0.078, 1)

        self.mes_atual = "Novembro/2026"
        self.media_pedida = 2.0
        self.indice_editando = None
        self.tipo_viagem = "carregado"
        self.avancado_aberto = False
        self.dados = {mes: {"viagens": [], "diesel": []} for mes in MESES}

        self._carregar_dados()

        raiz = ScrollView(do_scroll_x=False, do_scroll_y=True)

        self.container = BoxLayout(
            orientation="vertical",
            padding=[18, 24, 18, 28],
            spacing=14,
            size_hint_y=None,
        )
        self.container.bind(minimum_height=self.container.setter("height"))

        # Respiro superior para não encostar na barra do sistema e centralizar o bloco
        self.container.add_widget(Widget(size_hint_y=None, height=26))

        # Cabeçalho
        box_header = CardBox(
            bg_color=(0.067, 0.082, 0.114, 1),
            border_color=(0.145, 0.388, 0.922, 1),
            orientation="vertical",
            padding=[14, 12, 14, 12],
            size_hint_y=None,
            height=64,
        )
        titulo = Label(
            text="CONTROLE DE FRETE",
            font_size="20sp",
            bold=True,
            color=(0.945, 0.953, 0.961, 1),
        )
        box_header.add_widget(titulo)
        self.container.add_widget(box_header)

        # Card: Mês de Referência
        card_mes = CardBox(
            orientation="vertical",
            padding=[14, 12, 14, 14],
            spacing=8,
            size_hint_y=None,
            height=104,
        )
        card_mes.add_widget(self._criar_titulo_card("MÊS DE REFERÊNCIA"))

        self.spinner_mes = Spinner(
            text=self.mes_atual,
            values=MESES,
            size_hint_y=None,
            height=44,
            background_color=(0.145, 0.388, 0.922, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.spinner_mes.bind(text=self.ao_mudar_mes)
        card_mes.add_widget(self.spinner_mes)
        self.container.add_widget(card_mes)

        # Card: Resumo do Mês
        card_resumo = CardBox(
            orientation="vertical",
            padding=[14, 12, 14, 14],
            spacing=8,
            size_hint_y=None,
            height=272,
        )
        card_resumo.add_widget(self._criar_titulo_card("RESUMO DO MÊS"))

        grid = GridLayout(cols=2, spacing=[6, 6], size_hint_y=None, height=210)
        self.lbl_fat_valor = self._criar_linha_resumo(
            grid, "Total Faturado:", "R$ 0,00", (0.063, 0.725, 0.506, 1)
        )
        self.lbl_km_total_valor = self._criar_linha_resumo(
            grid, "KM Total Rodado:", "0 km", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_km_carr_valor = self._criar_linha_resumo(
            grid, "KM Carregado:", "0 km", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_km_vazio_valor = self._criar_linha_resumo(
            grid, "KM Vazio:", "0 km", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_diesel_valor = self._criar_linha_resumo(
            grid, "Diesel Abastecido:", "0,00 L", (0.220, 0.741, 0.973, 1)
        )
        self.lbl_media_valor = self._criar_linha_resumo(
            grid, "Média Geral (KM/L):", "0,00 KM/L", (0.220, 0.741, 0.973, 1)
        )
        card_resumo.add_widget(grid)
        self.container.add_widget(card_resumo)

        # Card: Nova Viagem / Trecho
        card_viagem = CardBox(
            orientation="vertical",
            padding=[14, 12, 14, 14],
            spacing=8,
            size_hint_y=None,
            height=402,
        )
        card_viagem.add_widget(self._criar_titulo_card("NOVA VIAGEM / TRECHO"))

        card_viagem.add_widget(self._criar_rotulo("Rota / Descrição"))
        self.input_rota = self._criar_input("Ex: Paranaguá para Cacoal")
        card_viagem.add_widget(self.input_rota)

        box_tipo = BoxLayout(spacing=8, size_hint_y=None, height=40)
        self.btn_tipo_carr = ToggleButton(
            text="Carregado",
            group="tipo_viagem",
            state="down",
            bold=True,
            background_color=(0.145, 0.388, 0.922, 1),
        )
        self.btn_tipo_vazio = ToggleButton(
            text="Vazio",
            group="tipo_viagem",
            state="normal",
            bold=True,
            background_color=(0.200, 0.255, 0.333, 1),
        )
        self.btn_tipo_carr.bind(on_press=lambda *_: self._set_tipo("carregado"))
        self.btn_tipo_vazio.bind(on_press=lambda *_: self._set_tipo("vazio"))
        box_tipo.add_widget(self.btn_tipo_carr)
        box_tipo.add_widget(self.btn_tipo_vazio)
        card_viagem.add_widget(box_tipo)

        box_km = BoxLayout(spacing=8, size_hint_y=None, height=62)
        col_ini = BoxLayout(orientation="vertical", spacing=4)
        col_ini.add_widget(self._criar_rotulo("KM Início"))
        self.input_km_ini = self._criar_input("0", input_filter="float")
        col_ini.add_widget(self.input_km_ini)

        col_fim = BoxLayout(orientation="vertical", spacing=4)
        col_fim.add_widget(self._criar_rotulo("KM Fim"))
        self.input_km_fim = self._criar_input("0", input_filter="float")
        col_fim.add_widget(self.input_km_fim)

        box_km.add_widget(col_ini)
        box_km.add_widget(col_fim)
        card_viagem.add_widget(box_km)

        card_viagem.add_widget(self._criar_rotulo("Faturamento (R$)"))
        self.input_fat = self._criar_input("0.00", input_filter="float")
        card_viagem.add_widget(self.input_fat)

        self.lbl_aviso = Label(
            text="",
            font_size="12sp",
            color=(0.988, 0.647, 0.647, 1),
            size_hint_y=None,
            height=22,
        )
        card_viagem.add_widget(self.lbl_aviso)

        self.btn_salvar_viagem = Button(
            text="Salvar Viagem",
            size_hint_y=None,
            height=44,
            background_color=(0.145, 0.388, 0.922, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.btn_salvar_viagem.bind(on_press=self.salvar_viagem)
        card_viagem.add_widget(self.btn_salvar_viagem)

        self.container.add_widget(card_viagem)

        # Card: Abastecimento de Diesel
        card_diesel = CardBox(
            orientation="vertical",
            padding=[14, 12, 14, 14],
            spacing=8,
            size_hint_y=None,
            height=172,
        )
        card_diesel.add_widget(
            self._criar_titulo_card("REGISTRAR ABASTECIMENTO DE DIESEL")
        )
        card_diesel.add_widget(self._criar_rotulo("Litros Abastecidos"))
        self.input_diesel = self._criar_input("Ex: 450.5", input_filter="float")
        card_diesel.add_widget(self.input_diesel)

        btn_diesel = Button(
            text="Adicionar Diesel",
            size_hint_y=None,
            height=42,
            background_color=(0.200, 0.255, 0.333, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_diesel.bind(on_press=self.salvar_diesel)
        card_diesel.add_widget(btn_diesel)
        self.container.add_widget(card_diesel)

        # Card: Histórico de Lançamentos + Resumo/Relatório
        self.card_historico = CardBox(
            orientation="vertical",
            padding=[14, 12, 14, 14],
            spacing=8,
            size_hint_y=None,
            height=165,
        )
        self.card_historico.add_widget(
            self._criar_titulo_card("HISTÓRICO DE LANÇAMENTOS")
        )

        self.box_historico = BoxLayout(
            orientation="vertical",
            spacing=8,
            size_hint_y=None,
            height=44,
        )
        self.box_historico.bind(minimum_height=self.box_historico.setter("height"))
        self.card_historico.add_widget(self.box_historico)

        self.btn_resumo_relatorio = Button(
            text="Ver Fechamento do Mês",
            size_hint_y=None,
            height=44,
            background_color=(0.063, 0.725, 0.506, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        self.btn_resumo_relatorio.bind(on_press=self.abrir_relatorio_mes)
        self.card_historico.add_widget(self.btn_resumo_relatorio)

        self.container.add_widget(self.card_historico)

        # Card: Cálculo Avançado de Desempenho (expansível)
        self.card_avancado = CardBox(
            bg_color=(0.059, 0.075, 0.102, 1),
            border_color=(0.118, 0.149, 0.212, 1),
            orientation="vertical",
            padding=[14, 12, 14, 14],
            spacing=8,
            size_hint_y=None,
            height=64,
        )

        self.btn_toggle_avancado = Button(
            text="Cálculo Avançado de Desempenho  ▼",
            size_hint_y=None,
            height=38,
            background_color=(0.118, 0.149, 0.212, 1),
            color=(0.75, 0.80, 0.88, 1),
            bold=True,
            font_size="13sp",
        )
        self.btn_toggle_avancado.bind(on_press=self.alternar_avancado)
        self.card_avancado.add_widget(self.btn_toggle_avancado)

        self.box_corpo_avancado = BoxLayout(
            orientation="vertical",
            spacing=6,
            size_hint_y=None,
            height=0,
            opacity=0,
        )

        self.box_corpo_avancado.add_widget(self._criar_rotulo("Média Pedida (Base)"))
        self.input_media_pedida = self._criar_input(
            "2.0", input_filter="float"
        )
        self.input_media_pedida.text = str(self.media_pedida)
        self.input_media_pedida.bind(text=self.ao_alterar_media_pedida)
        self.box_corpo_avancado.add_widget(self.input_media_pedida)

        grid_av = GridLayout(cols=2, spacing=[6, 6], size_hint_y=None, height=140)
        self.lbl_porc_carr = self._criar_linha_resumo(
            grid_av, "% Carregado:", "0,0%", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_meta_aj = self._criar_linha_resumo(
            grid_av, "Média Meta:", "0,00", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_media_real_av = self._criar_linha_resumo(
            grid_av, "Média Real:", "0,00", (0.220, 0.741, 0.973, 1)
        )
        self.lbl_media_equiv = self._criar_linha_resumo(
            grid_av, "Média Equivalente:", "0,00", (0.961, 0.620, 0.043, 1)
        )
        self.lbl_status_meta = self._criar_linha_resumo(
            grid_av, "Situação vs Meta:", "Aguardando diesel", (0.580, 0.639, 0.722, 1)
        )
        self.box_corpo_avancado.add_widget(grid_av)

        self.card_avancado.add_widget(self.box_corpo_avancado)
        self.container.add_widget(self.card_avancado)

        self.container.add_widget(Widget(size_hint_y=None, height=28))
        raiz.add_widget(self.container)

        self.atualizar_tudo()
        return raiz

    def _caminho_arquivo_dados(self):
        return os.path.join(self.user_data_dir, "controle_frete_dados.json")

    def _carregar_dados(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        caminho = self._caminho_arquivo_dados()
        if not os.path.exists(caminho):
            return
        try:
            with open(caminho, "r", encoding="utf-8") as arq:
                conteudo = json.load(arq)
            if isinstance(conteudo, dict):
                if conteudo.get("mes_atual") in MESES:
                    self.mes_atual = conteudo["mes_atual"]
                if conteudo.get("media_pedida") is not None:
                    self.media_pedida = float(conteudo["media_pedida"])
                salvos = conteudo.get("meses", {})
                for mes in MESES:
                    item = salvos.get(mes, {})
                    self.dados[mes] = {
                        "viagens": list(item.get("viagens", [])),
                        "diesel": list(item.get("diesel", [])),
                    }
        except Exception:
            pass

    def _salvar_dados(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        caminho = self._caminho_arquivo_dados()
        payload = {
            "mes_atual": self.mes_atual,
            "media_pedida": self.media_pedida,
            "meses": self.dados,
        }
        try:
            with open(caminho, "w", encoding="utf-8") as arq:
                json.dump(payload, arq, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _criar_titulo_card(self, texto):
        lbl = Label(
            text=texto,
            font_size="12sp",
            bold=True,
            color=(0.549, 0.584, 0.647, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=20,
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _criar_rotulo(self, texto):
        lbl = Label(
            text=texto,
            font_size="12sp",
            color=(0.549, 0.584, 0.647, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=18,
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _criar_input(self, hint, input_filter=None):
        return TextInput(
            hint_text=hint,
            input_filter=input_filter,
            multiline=False,
            size_hint_y=None,
            height=38,
            background_color=(0.043, 0.055, 0.078, 1),
            foreground_color=(0.945, 0.953, 0.961, 1),
            hint_text_color=(0.392, 0.455, 0.545, 1),
            cursor_color=(0.220, 0.741, 0.973, 1),
            padding=[10, 8],
        )

    def _criar_linha_resumo(self, grid, rotulo, inicial, cor_valor):
        lbl_nome = Label(
            text=rotulo,
            font_size="13.5sp",
            color=(0.549, 0.584, 0.647, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=27,
        )
        lbl_nome.bind(size=lbl_nome.setter("text_size"))

        lbl_val = Label(
            text=inicial,
            font_size="13.5sp",
            bold=True,
            color=cor_valor,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=27,
        )
        lbl_val.bind(size=lbl_val.setter("text_size"))

        grid.add_widget(lbl_nome)
        grid.add_widget(lbl_val)
        return lbl_val

    def _set_tipo(self, tipo):
        self.tipo_viagem = tipo
        if tipo == "carregado":
            self.btn_tipo_carr.state = "down"
            self.btn_tipo_vazio.state = "normal"
        else:
            self.btn_tipo_carr.state = "normal"
            self.btn_tipo_vazio.state = "down"

    def _limpar_form_viagem(self):
        self.indice_editando = None
        self.input_rota.text = ""
        self.input_km_ini.text = ""
        self.input_km_fim.text = ""
        self.input_fat.text = ""
        self._set_tipo("carregado")
        self.btn_salvar_viagem.text = "Salvar Viagem"

    def alternar_avancado(self, instance):
        self.avancado_aberto = not self.avancado_aberto
        if self.avancado_aberto:
            self.box_corpo_avancado.height = 205
            self.box_corpo_avancado.opacity = 1
            self.card_avancado.height = 278
            self.btn_toggle_avancado.text = "Cálculo Avançado de Desempenho  ▲"
        else:
            self.box_corpo_avancado.height = 0
            self.box_corpo_avancado.opacity = 0
            self.card_avancado.height = 64
            self.btn_toggle_avancado.text = "Cálculo Avançado de Desempenho  ▼"

    def ao_alterar_media_pedida(self, instance, valor_texto):
        parsed = _parse_numero(valor_texto)
        if parsed is not None and parsed >= 0:
            self.media_pedida = parsed
            self.atualizar_tudo()

    def ao_mudar_mes(self, spinner, texto_mes):
        self.mes_atual = texto_mes
        self.lbl_aviso.text = ""
        self._limpar_form_viagem()
        self.atualizar_tudo()

    def salvar_viagem(self, instance):
        rota = self.input_rota.text.strip()
        km_ini = _parse_numero(self.input_km_ini.text)
        km_fim = _parse_numero(self.input_km_fim.text)
        fat = _parse_numero(self.input_fat.text)
        if fat is None:
            fat = 0.0

        if not rota or km_ini is None or km_fim is None:
            self.lbl_aviso.text = "Preencha a Rota, KM Início e KM Fim."
            return

        if km_fim < km_ini:
            self.lbl_aviso.text = "KM Fim não pode ser menor que KM Início."
            return

        self.lbl_aviso.text = ""
        viagens = self.dados[self.mes_atual]["viagens"]
        item = {
            "rota": rota,
            "tipo": self.tipo_viagem,
            "km_inicio": km_ini,
            "km_fim": km_fim,
            "faturamento": fat,
        }

        if self.indice_editando is not None and 0 <= self.indice_editando < len(viagens):
            viagens[self.indice_editando] = item
        else:
            viagens.append(item)

        self._limpar_form_viagem()
        self.atualizar_tudo()

    def salvar_diesel(self, instance):
        litros = _parse_numero(self.input_diesel.text)
        if litros is None or litros <= 0:
            self.lbl_aviso.text = "Informe a quantidade de litros de diesel."
            return

        self.lbl_aviso.text = ""
        self.dados[self.mes_atual]["diesel"].append({"litros": litros})
        self.input_diesel.text = ""
        self.atualizar_tudo()

    def iniciar_edicao(self, idx):
        viagens = self.dados[self.mes_atual]["viagens"]
        if not (0 <= idx < len(viagens)):
            return
        v = viagens[idx]
        self.indice_editando = idx
        self.lbl_aviso.text = ""
        self.input_rota.text = str(v.get("rota", ""))
        self.input_km_ini.text = str(v.get("km_inicio", ""))
        self.input_km_fim.text = str(v.get("km_fim", ""))
        self.input_fat.text = str(v.get("faturamento", ""))
        self._set_tipo(v.get("tipo", "carregado"))
        self.btn_salvar_viagem.text = "Salvar Alteração"

    def excluir_item(self, categoria, idx):
        lista = self.dados[self.mes_atual][categoria]
        if not (0 <= idx < len(lista)):
            return
        if categoria == "viagens" and self.indice_editando == idx:
            self._limpar_form_viagem()
        lista.pop(idx)
        self.atualizar_tudo()

    def _calcular_metricas_mes(self, mes_data):
        fat_total = 0.0
        km_carr = 0.0
        km_vazio = 0.0
        total_litros = 0.0

        for v in mes_data["viagens"]:
            dist = max(0.0, float(v.get("km_fim", 0)) - float(v.get("km_inicio", 0)))
            fat_total += float(v.get("faturamento", 0))
            if v.get("tipo") == "vazio":
                km_vazio += dist
            else:
                km_carr += dist

        for d in mes_data["diesel"]:
            total_litros += float(d.get("litros", 0))

        km_total = km_carr + km_vazio
        media_real = (km_total / total_litros) if total_litros > 0 else 0.0

        media_pedida = self.media_pedida
        porc_carr = (km_carr / km_total) * 100.0 if km_total > 0 else 0.0
        porc_menos_50 = porc_carr - 50.0
        media_meta = (
            (media_pedida - (porc_menos_50 * 0.014)) if km_total > 0 else media_pedida
        )

        media_equiv = media_pedida
        status_texto = "Aguardando diesel"
        status_cor = (0.580, 0.639, 0.722, 1)

        if total_litros > 0 and media_meta > 0:
            media_equiv = media_pedida * (media_real / media_meta)
            diff_meta = media_real - media_meta
            diff_base = media_equiv - media_pedida
            sinal_base = "+" if diff_base >= 0 else ""

            if diff_meta >= 0:
                status_texto = f"ACIMA DA META ({sinal_base}{_fmt_virgula(diff_base)})"
                status_cor = (0.063, 0.725, 0.506, 1)
            else:
                status_texto = f"ABAIXO DA META ({sinal_base}{_fmt_virgula(diff_base)})"
                status_cor = (0.973, 0.443, 0.443, 1)

        return {
            "fat_total": fat_total,
            "km_total": km_total,
            "km_carr": km_carr,
            "km_vazio": km_vazio,
            "total_litros": total_litros,
            "media_real": media_real,
            "porc_carr": porc_carr,
            "media_meta": media_meta,
            "media_equiv": media_equiv,
            "status_texto": status_texto,
            "status_cor": status_cor,
        }

    def abrir_relatorio_mes(self, instance):
        m = self._calcular_metricas_mes(self.dados[self.mes_atual])
        texto = (
            f"Mês: {self.mes_atual}\n"
            f"Total Faturado: R$ {_fmt_virgula(m['fat_total'])}\n"
            f"KM Total: {m['km_total']:.0f} km\n"
            f"KM Carregado: {m['km_carr']:.0f} km ({_fmt_virgula(m['porc_carr'], 1)}%)\n"
            f"KM Vazio: {m['km_vazio']:.0f} km\n"
            f"Diesel: {_fmt_virgula(m['total_litros'])} L\n"
            f"Média Real: {_fmt_virgula(m['media_real'])} KM/L\n"
            f"Média Meta: {_fmt_virgula(m['media_meta'])} KM/L\n"
            f"Média Equivalente: {_fmt_virgula(m['media_equiv'])} KM/L\n"
            f"Situação: {m['status_texto']}"
        )

        conteudo_popup = BoxLayout(orientation="vertical", padding=14, spacing=12)
        lbl = Label(
            text=texto,
            font_size="14sp",
            halign="left",
            valign="middle",
        )
        lbl.bind(size=lbl.setter("text_size"))

        btn_fechar = Button(
            text="Fechar",
            size_hint_y=None,
            height=42,
            background_color=(0.145, 0.388, 0.922, 1),
            bold=True,
        )
        conteudo_popup.add_widget(lbl)
        conteudo_popup.add_widget(btn_fechar)

        popup = Popup(
            title=f"Fechamento - {self.mes_atual}",
            content=conteudo_popup,
            size_hint=(0.9, 0.68),
            background_color=(0.082, 0.098, 0.133, 1),
        )
        btn_fechar.bind(on_press=popup.dismiss)
        popup.open()

    def _construir_historico(self, mes_data):
        self.box_historico.clear_widgets()
        viagens = mes_data["viagens"]
        diesels = mes_data["diesel"]

        if not viagens and not diesels:
            vazio = Label(
                text="Nenhum lançamento neste mês.",
                font_size="13sp",
                color=(0.392, 0.455, 0.545, 1),
                size_hint_y=None,
                height=34,
            )
            self.box_historico.add_widget(vazio)
            self.card_historico.height = 156
            return

        altura_itens = 0

        for idx, v in enumerate(viagens):
            dist = max(0.0, float(v.get("km_fim", 0)) - float(v.get("km_inicio", 0)))
            fat = float(v.get("faturamento", 0))
            tipo = v.get("tipo", "carregado")

            linha = CardBox(
                bg_color=(0.043, 0.055, 0.078, 1),
                border_color=(0.165, 0.192, 0.259, 1),
                orientation="horizontal",
                padding=[10, 8, 10, 8],
                spacing=8,
                size_hint_y=None,
                height=68,
            )

            info = Label(
                text=(
                    f"[b][color=38bdf8][Viagem] {v.get('rota', '')}[/color][/b]\n"
                    f"Tipo: {tipo} | KM: {dist:.0f} km | Fat: R$ {_fmt_virgula(fat)}"
                ),
                markup=True,
                font_size="12sp",
                halign="left",
                valign="middle",
            )
            info.bind(size=info.setter("text_size"))

            btn_edit = Button(
                text="Editar",
                size_hint=(None, None),
                size=(62, 34),
                font_size="12sp",
                background_color=(0.145, 0.388, 0.922, 1),
                pos_hint={"center_y": 0.5},
            )
            btn_edit.bind(on_press=lambda _, i=idx: self.iniciar_edicao(i))

            btn_del = Button(
                text="Excluir",
                size_hint=(None, None),
                size=(64, 34),
                font_size="12sp",
                background_color=(0.937, 0.267, 0.267, 1),
                pos_hint={"center_y": 0.5},
            )
            btn_del.bind(on_press=lambda _, i=idx: self.excluir_item("viagens", i))

            linha.add_widget(info)
            linha.add_widget(btn_edit)
            linha.add_widget(btn_del)
            self.box_historico.add_widget(linha)
            altura_itens += 76

        for idx, d in enumerate(diesels):
            litros = float(d.get("litros", 0))
            linha_d = CardBox(
                bg_color=(0.043, 0.055, 0.078, 1),
                border_color=(0.165, 0.192, 0.259, 1),
                orientation="horizontal",
                padding=[10, 8, 10, 8],
                spacing=8,
                size_hint_y=None,
                height=58,
            )

            info_d = Label(
                text=(
                    f"[b][color=f59e0b][Abastecimento Diesel][/color][/b]\n"
                    f"Litros: {_fmt_virgula(litros)} L"
                ),
                markup=True,
                font_size="12sp",
                halign="left",
                valign="middle",
            )
            info_d.bind(size=info_d.setter("text_size"))

            btn_del_d = Button(
                text="Excluir",
                size_hint=(None, None),
                size=(64, 34),
                font_size="12sp",
                background_color=(0.937, 0.267, 0.267, 1),
                pos_hint={"center_y": 0.5},
            )
            btn_del_d.bind(on_press=lambda _, i=idx: self.excluir_item("diesel", i))

            linha_d.add_widget(info_d)
            linha_d.add_widget(btn_del_d)
            self.box_historico.add_widget(linha_d)
            altura_itens += 66

        self.card_historico.height = altura_itens + 108

    def atualizar_tudo(self):
        mes_data = self.dados[self.mes_atual]
        m = self._calcular_metricas_mes(mes_data)

        self.lbl_fat_valor.text = f"R$ {_fmt_virgula(m['fat_total'])}"
        self.lbl_km_total_valor.text = f"{m['km_total']:.0f} km"
        self.lbl_km_carr_valor.text = f"{m['km_carr']:.0f} km"
        self.lbl_km_vazio_valor.text = f"{m['km_vazio']:.0f} km"
        self.lbl_diesel_valor.text = f"{_fmt_virgula(m['total_litros'])} L"
        self.lbl_media_valor.text = f"{_fmt_virgula(m['media_real'])} KM/L"

        self.lbl_porc_carr.text = f"{_fmt_virgula(m['porc_carr'], 1)}%"
        self.lbl_meta_aj.text = _fmt_virgula(m["media_meta"])
        self.lbl_media_real_av.text = _fmt_virgula(m["media_real"])
        self.lbl_media_equiv.text = _fmt_virgula(m["media_equiv"])
        self.lbl_status_meta.text = m["status_texto"]
        self.lbl_status_meta.color = m["status_cor"]

        self._construir_historico(mes_data)
        self._salvar_dados()


if __name__ == "__main__":
    ControleFreteApp().run()
