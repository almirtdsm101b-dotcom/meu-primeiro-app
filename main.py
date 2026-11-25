from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner


MESES = [
    "Agosto/2026",
    "Setembro/2026",
    "Outubro/2026",
    "Novembro/2026",
    "Dezembro/2026",
]


class ControleFreteApp(App):
    def build(self):
        Window.clearcolor = (0.043, 0.055, 0.078, 1)

        self.mes_atual = "Novembro/2026"
        self.dados = {
            mes: {
                "faturamento": 0.0,
                "km_carregado": 0.0,
                "km_vazio": 0.0,
                "diesel_litros": 0.0,
            }
            for mes in MESES
        }

        raiz = ScrollView(do_scroll_x=False, do_scroll_y=True)

        container = BoxLayout(
            orientation="vertical",
            padding=[16, 20, 16, 24],
            spacing=14,
            size_hint_y=None,
        )
        container.bind(minimum_height=container.setter("height"))

        # Cabeçalho
        titulo = Label(
            text="Controle de Frete",
            font_size="22sp",
            bold=True,
            color=(0.945, 0.953, 0.961, 1),
            size_hint_y=None,
            height=40,
        )
        container.add_widget(titulo)

        # Card: Mês de Referência
        card_mes = BoxLayout(
            orientation="vertical",
            padding=12,
            spacing=8,
            size_hint_y=None,
            height=95,
        )
        label_mes = Label(
            text="MÊS DE REFERÊNCIA",
            font_size="12sp",
            bold=True,
            color=(0.549, 0.584, 0.647, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=20,
        )
        label_mes.bind(size=label_mes.setter("text_size"))

        self.spinner_mes = Spinner(
            text=self.mes_atual,
            values=MESES,
            size_hint_y=None,
            height=44,
            background_color=(0.145, 0.388, 0.922, 1),
            color=(1, 1, 1, 1),
        )
        self.spinner_mes.bind(text=self.ao_mudar_mes)

        card_mes.add_widget(label_mes)
        card_mes.add_widget(self.spinner_mes)
        container.add_widget(card_mes)

        # Card: Resumo do Mês
        card_resumo = BoxLayout(
            orientation="vertical",
            padding=12,
            spacing=8,
            size_hint_y=None,
            height=250,
        )
        label_resumo = Label(
            text="RESUMO DO MÊS",
            font_size="12sp",
            bold=True,
            color=(0.549, 0.584, 0.647, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=22,
        )
        label_resumo.bind(size=label_resumo.setter("text_size"))
        card_resumo.add_widget(label_resumo)

        grid = GridLayout(cols=2, spacing=6, size_hint_y=None, height=195)

        self.lbl_fat_valor = self._criar_linha_resumo(grid, "Total Faturado:", "R$ 0,00", (0.063, 0.725, 0.506, 1))
        self.lbl_km_total_valor = self._criar_linha_resumo(grid, "KM Total Rodado:", "0 km", (0.945, 0.953, 0.961, 1))
        self.lbl_km_carr_valor = self._criar_linha_resumo(grid, "KM Carregado:", "0 km", (0.945, 0.953, 0.961, 1))
        self.lbl_km_vazio_valor = self._criar_linha_resumo(grid, "KM Vazio:", "0 km", (0.945, 0.953, 0.961, 1))
        self.lbl_diesel_valor = self._criar_linha_resumo(grid, "Diesel Abastecido:", "0,00 L", (0.220, 0.741, 0.973, 1))
        self.lbl_media_valor = self._criar_linha_resumo(grid, "Média Geral (KM/L):", "0,00 KM/L", (0.220, 0.741, 0.973, 1))

        card_resumo.add_widget(grid)
        container.add_widget(card_resumo)

        # Botão de teste desta etapa
        btn_teste = Button(
            text="Simular Trecho Teste (+500 km)",
            size_hint_y=None,
            height=48,
            background_color=(0.145, 0.388, 0.922, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        btn_teste.bind(on_press=self.simular_trecho)
        container.add_widget(btn_teste)

        raiz.add_widget(container)
        self.atualizar_resumo()
        return raiz

    def _criar_linha_resumo(self, grid, rotulo, inicial, cor_valor):
        lbl_nome = Label(
            text=rotulo,
            font_size="14sp",
            color=(0.549, 0.584, 0.647, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=28,
        )
        lbl_nome.bind(size=lbl_nome.setter("text_size"))

        lbl_val = Label(
            text=inicial,
            font_size="14sp",
            bold=True,
            color=cor_valor,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=28,
        )
        lbl_val.bind(size=lbl_val.setter("text_size"))

        grid.add_widget(lbl_nome)
        grid.add_widget(lbl_val)
        return lbl_val

    def ao_mudar_mes(self, spinner, texto_mes):
        self.mes_atual = texto_mes
        self.atualizar_resumo()

    def simular_trecho(self, instance):
        m = self.dados[self.mes_atual]
        m["km_carregado"] += 500.0
        m["faturamento"] += 3500.0
        m["diesel_litros"] += 220.0
        self.atualizar_resumo()

    def atualizar_resumo(self):
        m = self.dados[self.mes_atual]
        km_total = m["km_carregado"] + m["km_vazio"]
        diesel = m["diesel_litros"]
        media = (km_total / diesel) if diesel > 0 else 0.0

        fat_fmt = f"R$ {m['faturamento']:.2f}".replace(".", ",")
        self.lbl_fat_valor.text = fat_fmt
        self.lbl_km_total_valor.text = f"{int(km_total)} km"
        self.lbl_km_carr_valor.text = f"{int(m['km_carregado'])} km"
        self.lbl_km_vazio_valor.text = f"{int(m['km_vazio'])} km"
        self.lbl_diesel_valor.text = f"{diesel:.2f} L".replace(".", ",")
        self.lbl_media_valor.text = f"{media:.2f} KM/L".replace(".", ",")


if __name__ == "__main__":
    ControleFreteApp().run()
        
