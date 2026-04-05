# =====================================================================
# FICHEIRO: config.py (Configurações Globais e Interface Visual)
# =====================================================================
import streamlit as st

# Dicionários de opções para os gráficos
mapa_legenda = {
    'Inferior Direita': dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99, orientation="v"),
    'Superior Direita': dict(yanchor="top", y=0.99, xanchor="right", x=0.99, orientation="v"),
    'Superior (Topo)': dict(yanchor="bottom", y=1.02, xanchor="center", x=0.5, orientation="h"),
    'Inferior (Abaixo do Gráfico)': dict(yanchor="top", y=-0.2, xanchor="center", x=0.5, orientation="h")
}

mapa_marcadores = {
    'Nenhum': 'none', 'Círculo': 'circle', 'Quadrado': 'square', 
    'Losango': 'diamond', 'Triângulo': 'triangle-up', 'X': 'x'
}

mapa_grid = {'Padrão': 'solid', 'Pontilhada': 'dot', 'Tracejada': 'dash'}

def get_mark_index(val):
    """Encontra o índice do marcador na lista para o menu de configurações."""
    for k, v in mapa_marcadores.items():
        if v == val: return list(mapa_marcadores.keys()).index(k)
    return 0

def inicializar_estado_sessao():
    """Carrega as definições padrão para a memória do site na primeira vez que abre."""
    defaults = {
        'pacientes': {},
        'y_min': 0.0, 'y_max': 100.0, 'y_step': 20.0, 'x_step': 5,
        'titulo_grafico': 'Evolução Postural ao Longo do Tempo',
        'titulo_x': 'Tempo (s)', 'titulo_y': 'Valores Normalizados (%)',
        'pos_legenda': 'Inferior Direita',
        'suavizar_linhas': False, 'espessura_linha': 2, 'tamanho_marcador': 6,
        'cor_ml': '#636EFA', 'cor_ap': '#EF553B', 'cor_dt': '#00CC96', 'cor_ae': '#AB63FA',
        'mark_ml': 'circle', 'mark_ap': 'square', 'mark_dt': 'diamond', 'mark_ae': 'x',
        'mostrar_borda': False, 'cor_eixos': '#888888', 'esp_eixos': 1,
        'mostrar_grid': True, 'estilo_grid': 'solid', 'cor_grid': '#E5E5E5',
        'mostrar_interpretacao': True, 'mostrar_tabela': True,
        'form_key': 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def renderizar_painel_configuracoes():
    """Desenha a interface de menus com os ajustes de Títulos, Linhas e Cores."""
    tab_titulos, tab_eixos, tab_linhas, tab_marcadores, tab_legenda, tab_area, tab_exibicao = st.tabs([
        "📝 Títulos", "📏 Limites (X/Y)", "📈 Linhas", "📍 Marcadores", "🏷️ Legenda", "🖼️ Fundo/Bordas", "👁️ Exibição"
    ])
    with tab_titulos:
        st.session_state['titulo_grafico'] = st.text_input("Título Principal", st.session_state['titulo_grafico'])
        col1, col2 = st.columns(2)
        st.session_state['titulo_x'] = col1.text_input("Título Eixo X", st.session_state['titulo_x'])
        st.session_state['titulo_y'] = col2.text_input("Título Eixo Y", st.session_state['titulo_y'])
    with tab_eixos:
        col1, col2, col3, col4 = st.columns(4)
        st.session_state['y_min'] = col1.number_input("Mínimo Eixo Y", value=st.session_state['y_min'])
        st.session_state['y_max'] = col2.number_input("Máximo Eixo Y", value=st.session_state['y_max'])
        st.session_state['y_step'] = col3.number_input("Espaçamento Eixo Y", value=st.session_state['y_step'], min_value=1.0)
        opcoes_x = [5, 10]
        index_x = opcoes_x.index(st.session_state['x_step']) if st.session_state['x_step'] in opcoes_x else 0
        st.session_state['x_step'] = col4.selectbox("Espaçamento Eixo X", opcoes_x, index=index_x)
    with tab_linhas:
        c_c1, c_c2, c_c3, c_c4 = st.columns(4)
        st.session_state['cor_ml'] = c_c1.color_picker("RMS ML", st.session_state['cor_ml'])
        st.session_state['cor_ap'] = c_c2.color_picker("RMS AP", st.session_state['cor_ap'])
        st.session_state['cor_dt'] = c_c3.color_picker("Desvio Total", st.session_state['cor_dt'])
        st.session_state['cor_ae'] = c_c4.color_picker("Área Elipse", st.session_state['cor_ae'])
        col_esp, col_suav = st.columns([2, 1])
        st.session_state['espessura_linha'] = col_esp.slider("Espessura da Linha", 1, 10, st.session_state['espessura_linha'])
        st.session_state['suavizar_linhas'] = col_suav.checkbox("Suavizar linhas (Curva)", value=st.session_state['suavizar_linhas'])
    with tab_marcadores:
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        st.session_state['mark_ml'] = mapa_marcadores[c_m1.selectbox("RMS ML", list(mapa_marcadores.keys()), index=get_mark_index(st.session_state['mark_ml']))]
        st.session_state['mark_ap'] = mapa_marcadores[c_m2.selectbox("RMS AP", list(mapa_marcadores.keys()), index=get_mark_index(st.session_state['mark_ap']))]
        st.session_state['mark_dt'] = mapa_marcadores[c_m3.selectbox("Desvio Total", list(mapa_marcadores.keys()), index=get_mark_index(st.session_state['mark_dt']))]
        st.session_state['mark_ae'] = mapa_marcadores[c_m4.selectbox("Área Elipse", list(mapa_marcadores.keys()), index=get_mark_index(st.session_state['mark_ae']))]
        st.session_state['tamanho_marcador'] = st.slider("Tamanho", 4, 20, st.session_state['tamanho_marcador'])
    with tab_legenda:
        st.session_state['pos_legenda'] = st.selectbox("Posição da Legenda", list(mapa_legenda.keys()), index=list(mapa_legenda.keys()).index(st.session_state['pos_legenda']))
    with tab_area:
        c_a1, c_a2, c_a3 = st.columns(3)
        st.session_state['mostrar_borda'] = c_a1.checkbox("Ativar Quadro", value=st.session_state['mostrar_borda'])
        st.session_state['cor_eixos'] = c_a2.color_picker("Cor dos Eixos", st.session_state['cor_eixos'])
        st.session_state['esp_eixos'] = c_a3.slider("Espessura Eixos", 1, 5, st.session_state['esp_eixos'])
        c_g1, c_g2, c_g3 = st.columns(3)
        st.session_state['mostrar_grid'] = c_g1.checkbox("Mostrar Grade", value=st.session_state['mostrar_grid'])
        estilo_atual_nome = [k for k, v in mapa_grid.items() if v == st.session_state['estilo_grid']][0]
        st.session_state['estilo_grid'] = mapa_grid[c_g2.selectbox("Estilo Grade", list(mapa_grid.keys()), index=list(mapa_grid.keys()).index(estilo_atual_nome))]
        st.session_state['cor_grid'] = c_g3.color_picker("Cor Grade", st.session_state['cor_grid'])
    with tab_exibicao:
        st.markdown("### Painéis Abaixo do Gráfico")
        st.session_state['mostrar_interpretacao'] = st.checkbox("Mostrar separador 'Ver Interpretação'", value=st.session_state['mostrar_interpretacao'])
        st.session_state['mostrar_tabela'] = st.checkbox("Mostrar separador 'Ver Tabela de Dados'", value=st.session_state['mostrar_tabela'])