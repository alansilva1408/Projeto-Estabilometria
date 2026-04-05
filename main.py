# =====================================================================
# ARQUIVO: main.py (O Arquivo Principal / Interface) - ATUALIZADO
# =====================================================================
import streamlit as st
import pandas as pd
import time

# --- IMPORTANDO A ARQUITETURA MODULAR ---
from config import inicializar_estado_sessao, renderizar_painel_configuracoes
from processing import processar_arquivo_bruto, gerar_tabela_e_normalizar
from analyzer import gerar_laudo_matematico, gerar_laudo_estatistico, gerar_resumo_executivo
from plots import plotar_grafico_individual, plotar_estatisticas_avancadas

st.set_page_config(page_title="Gerador de Gráficos - TCC", layout="wide")

# 1. Carrega a memória e configurações iniciais
inicializar_estado_sessao()

# 2. Menu Lateral
st.sidebar.title("📂 Navegue pelas páginas")
menu = st.sidebar.radio(
    "Selecione a etapa:", 
    [
        "🏠 Página Inicial", 
        "⬆️ Importar Dados", 
        "📈 Visualização Gráfica", 
        "📊 Estatísticas Gerais",
        "📤 Exportar Resultados",
        "⚙️ Configurações", 
        "ℹ️ Sobre"
    ],
    label_visibility="collapsed"
)

# =====================================================================
# 🏠 PÁGINA 1: PÁGINA INICIAL
# =====================================================================
if menu == "🏠 Página Inicial":
    st.title("🏠 Painel de Gráficos Biomecânicos")
    st.markdown("Bem-vindo! Siga os passos abaixo para gerar os gráficos da sua pesquisa.")
    st.markdown("---")
    st.markdown("### ⬆️ Importar Dados")
    st.markdown("Faça o upload do arquivo com os dados brutos. O sistema fatiará os dados automaticamente.")
    st.markdown("### 📈 Visualização Gráfica")
    st.markdown("O sistema calculará picos, quedas e momentos de estabilização do balanço postural de cada participante, nos tempos que você escolher.")
    st.markdown("### 📊 Estatísticas Gerais")
    st.markdown("Veja um panorama global e compare os resultados entre os participantes com base em análises avançadas.")
    st.markdown("### 📤 Exportar Resultados")
    st.markdown("Baixe as tabelas em CSV de todos os dados analisados no painel.")
    st.markdown("### ⚙️ Configurações")
    st.markdown("Ajuste o visual dos gráficos (cores, escalas, eixos e legendas).")
    st.markdown("### ℹ️ Sobre")
    st.markdown("Conheça a metodologia matemática por trás da normalização e dos laudos gerados.")

# =====================================================================
# ⬆️ PÁGINA 2: IMPORTAR DADOS
# =====================================================================
elif menu == "⬆️ Importar Dados":
    st.title("⬆️ Importar Dados")
    st.info("Cadastre um participante por vez. Anexe APENAS os arquivos com os dados brutos.")
    
    fk = st.session_state['form_key']
    nome_input = st.text_input("👤 Nome do Participante (Ex: Afonso):", key=f"nome_{fk}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Arquivo OA (Olhos Abertos)")
        up_oa = st.file_uploader("Arraste o arquivo bruto de OA aqui", type=['txt', 'csv'], key=f"up_oa_{fk}")
    with c2:
        st.subheader("Arquivo OF (Olhos Fechados)")
        up_of = st.file_uploader("Arraste o arquivo bruto de OF aqui", type=['txt', 'csv'], key=f"up_of_{fk}")
        
    if st.button("💾 Salvar Dados", use_container_width=True):
        if not nome_input:
            st.error("⚠️ Digite o nome do participante antes de salvar!")
        elif not up_oa and not up_of:
            st.error("⚠️ Anexe pelo menos um arquivo bruto (OA ou OF) para salvar.")
        else:
            t_oa, ml_oa, ap_oa = processar_arquivo_bruto(up_oa) if up_oa else (None, None, None)
            t_of, ml_of, ap_of = processar_arquivo_bruto(up_of) if up_of else (None, None, None)
            
            st.session_state['pacientes'][nome_input] = {
                't_oa': t_oa, 'ml_oa': ml_oa, 'ap_oa': ap_oa,
                't_of': t_of, 'ml_of': ml_of, 'ap_of': ap_of
            }
            st.success(f"✅ Dados do participante **{nome_input}** salvos com sucesso!")
            
            st.session_state['form_key'] += 1
            time.sleep(1.2)
            st.rerun()

    if st.session_state['pacientes']:
        st.markdown("---")
        st.markdown("### 📋 Participantes Cadastrados:")
        for p in list(st.session_state['pacientes'].keys()):
            col_nome, col_btn = st.columns([0.8, 0.2])
            col_nome.markdown(f"👤 **{p}**")
            if col_btn.button("❌ Excluir", key=f"del_{p}"):
                del st.session_state['pacientes'][p]
                st.rerun()
            
        st.markdown("---")
        if st.button("🗑️ Limpar Todos os Dados"):
            st.session_state['pacientes'] = {}
            st.rerun()

# =====================================================================
# 📈 PÁGINA 3: VISUALIZAÇÃO GRÁFICA
# =====================================================================
elif menu == "📈 Visualização Gráfica":
    st.title("📈 Visualização Gráfica")
    
    with st.expander("⚙️ Ajustes Rápidos do Gráfico"):
        renderizar_painel_configuracoes()
        
    colunas_tabela = ['Intervalo', 'RMS ML', 'RMS AP', 'Desvio total', 'Área elipse']
    formato_bruto = {col: "{:.6f}" for col in colunas_tabela if col != 'Intervalo'}
    formato_norm = {col: lambda x: f"{x:.2f}%".replace('.', ',') for col in colunas_tabela if col != 'Intervalo'}
    
    if not st.session_state['pacientes']:
        st.warning("⚠️ Nenhum participante na memória. Vá até a aba 'Importar Dados' para cadastrar!")
    else:
        for nome_paciente, dados in st.session_state['pacientes'].items():
            st.markdown("---")
            st.markdown(f"## 👤 Gráficos de {nome_paciente}")
            
            st.markdown("### ⏱️ Escolha os tempos de recorte:")
            st.caption("Nota: 5 segundos equivalem ao intervalo 0-500, 10 segundos equivalem a 0-1000, e assim por diante.")
            
            opcoes_tempos = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
            tempos_selecionados = st.multiselect(
                "Selecione os recortes (em segundos):", 
                options=opcoes_tempos, default=opcoes_tempos, key=f"ms_{nome_paciente}"
            )

            df_real_oa, df_amp_oa, df_est_oa = gerar_tabela_e_normalizar(dados['ml_oa'], dados['ap_oa'], tempos_selecionados)
            df_real_of, df_amp_of, df_est_of = gerar_tabela_e_normalizar(dados['ml_of'], dados['ap_of'], tempos_selecionados)
            
            tipo_analise = st.radio(
                f"Escolha o tipo de Normalização Gráfica para {nome_paciente}:", 
                ["Amplitude (Pico Máximo = 100%)", "Parâmetros de Estabilidade (Tempo Final = 100%)"], 
                key=f"analise_{nome_paciente}", horizontal=True
            )
            
            df_usar_oa = df_amp_oa if "Amplitude" in tipo_analise else df_est_oa
            df_usar_of = df_amp_of if "Amplitude" in tipo_analise else df_est_of
            
            col_oa, col_of = st.columns(2)
            
            with col_oa:
                if df_usar_oa is not None and not df_usar_oa.empty:
                    st.markdown("<h3 style='text-align: center;'>Gráfico Olhos Abertos (OA)</h3>", unsafe_allow_html=True)
                    st.plotly_chart(plotar_grafico_individual(df_usar_oa), use_container_width=True)
                    
                    if st.session_state['mostrar_interpretacao']:
                        with st.expander("🧮 Ver Interpretação"):
                            st.markdown(f"<div style='text-align: justify;'>\n\n{gerar_laudo_matematico(df_usar_oa, nome_paciente, 'OA')}\n\n</div>", unsafe_allow_html=True)
                            
                    if st.session_state['mostrar_tabela']:
                        with st.expander("📊 Ver Tabela de Dados"):
                            opcao_oa = st.radio("Base:", ["Valores no Tempo (Brutos)", "Valores Normalizados (%)"], key=f"rad_oa_{nome_paciente}", horizontal=True)
                            df_view_oa, fmt_oa = (df_real_oa, formato_bruto.copy()) if "Brutos" in opcao_oa else (df_usar_oa, formato_norm.copy())
                            cols_filtradas = [c for c in df_view_oa.columns if c in colunas_tabela]
                            if "Brutos" in opcao_oa:
                                extras = [c for c in df_view_oa.columns if "Potência" in c or "Freq" in c]
                                cols_filtradas += extras
                                fmt_oa.update({c: "{:.8f}" for c in extras})
                            st.dataframe(df_view_oa[cols_filtradas].style.format(fmt_oa), hide_index=True)
                else:
                    st.info("Nenhum arquivo OA processado.")

            with col_of:
                if df_usar_of is not None and not df_usar_of.empty:
                    st.markdown("<h3 style='text-align: center;'>Gráfico Olhos Fechados (OF)</h3>", unsafe_allow_html=True)
                    st.plotly_chart(plotar_grafico_individual(df_usar_of), use_container_width=True)
                    
                    if st.session_state['mostrar_interpretacao']:
                        with st.expander("🧮 Ver Interpretação"):
                            st.markdown(f"<div style='text-align: justify;'>\n\n{gerar_laudo_matematico(df_usar_of, nome_paciente, 'OF')}\n\n</div>", unsafe_allow_html=True)
                            
                    if st.session_state['mostrar_tabela']:
                        with st.expander("📊 Ver Tabela de Dados"):
                            opcao_of = st.radio("Base:", ["Valores no Tempo (Brutos)", "Valores Normalizados (%)"], key=f"rad_of_{nome_paciente}", horizontal=True)
                            df_view_of, fmt_of = (df_real_of, formato_bruto.copy()) if "Brutos" in opcao_of else (df_usar_of, formato_norm.copy())
                            cols_filtradas_of = [c for c in df_view_of.columns if c in colunas_tabela]
                            if "Brutos" in opcao_of:
                                extras = [c for c in df_view_of.columns if "Potência" in c or "Freq" in c]
                                cols_filtradas_of += extras
                                fmt_of.update({c: "{:.8f}" for c in extras})
                            st.dataframe(df_view_of[cols_filtradas_of].style.format(fmt_of), hide_index=True)
                else:
                    st.info("Nenhum arquivo OF processado.")

# =====================================================================
# 📊 PÁGINA 4: ESTATÍSTICAS GERAIS
# =====================================================================
elif menu == "📊 Estatísticas Gerais":
    st.title("📊 Painel de Estatísticas Avançadas (Coorte)")
    st.write("Comportamento global, variabilidade e análises biomecânicas da amostra.")
    
    if not st.session_state['pacientes']:
        st.warning("⚠️ Cadastre participantes na aba 'Importar Dados' para gerar estatísticas.")
    else:
        # Prepara um DataFrame único com toda a amostra baseada em Amplitude!
        dfs_todos = []
        tempos_padrao = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        for p, d in st.session_state['pacientes'].items():
            _, df_amp_oa, _ = gerar_tabela_e_normalizar(d['ml_oa'], d['ap_oa'], tempos_padrao)
            _, df_amp_of, _ = gerar_tabela_e_normalizar(d['ml_of'], d['ap_of'], tempos_padrao)
            
            if df_amp_oa is not None and not df_amp_oa.empty:
                df_amp_oa['Paciente'] = p
                df_amp_oa['Condicao'] = 'OA'
                dfs_todos.append(df_amp_oa)
            if df_amp_of is not None and not df_amp_of.empty:
                df_amp_of['Paciente'] = p
                df_amp_of['Condicao'] = 'OF'
                dfs_todos.append(df_amp_of)
                
        df_amostra = pd.concat(dfs_todos) if dfs_todos else pd.DataFrame()

        # --- NOVO: RELATÓRIO DE TRIAGEM BIOMECÂNICA ---
        with st.expander("📝 Consultar Relatório de Triagem Biomecânica Coletiva", expanded=False):
            st.markdown("### 🧬 Análise Longitudinal e Sensorial da Amostra")
            
            # Aqui chamamos a função que atualizamos no analyzer.py
            laudo_completo = gerar_resumo_executivo(df_amostra)
            
            # Exibimos o texto formatado (HTML)
            st.markdown(laudo_completo, unsafe_allow_html=True)
        
        st.divider()

        # --- 2. CONFIGURAÇÃO DO MENU DE ANÁLISES ---
        opcoes_analise = [
            "1. Curva Média e Variabilidade",
            "2. Distribuição da Amostra (Boxplot)",
            "3. Eixos Afetados (Radar Biomecânico)",
            "4. Impacto da Visão (Índice de Romberg)",
            "5. Mapa de Calor (Evolução Global)",
            "6. Taxa de Recuperação Postural",
            "7. Tempo em Zona de Risco (>80%)",
            "8. Padrão Motor (Adaptação vs Fadiga)"
        ]

        # Caixa de seleção do menu
        escolha = st.selectbox("🎯 Selecione a Análise Desejada:", opcoes_analise)
        
        # --- 3. DICIONÁRIO DE EXPLICAÇÕES (JUSTIFICADO) ---
        explicacoes = {
            "1. Curva Média e Variabilidade": "O gráfico de Curva Média e Variabilidade avalia o padrão evolutivo de 'aprendizado motor' da amostra ao longo do tempo. A curva revela a tendência geral de estabilização do grupo, enquanto as barras de desvio-padrão indicam o nível de concordância ou divergência nas estratégias de equilíbrio.",
            "2. Distribuição da Amostra (Boxplot)": "O gráfico de Distribuição (Boxplot) mapeia a dispersão do controle postural no momento final do teste. Ele é essencial para verificar a homogeneidade estatística da amostra e identificar rapidamente indivíduos com comportamentos atípicos (outliers).",
            "3. Eixos Afetados (Radar Biomecânico)": "O Radar Biomecânico identifica qual plano de movimento exigiu maior esforço compensatório. O predomínio de oscilação no eixo Anteroposterior (AP) reflete o uso da estratégia de tornozelo, enquanto o excesso no eixo Médio-Lateral (ML) indica o uso da estratégia de quadril.",
            "4. Impacto da Visão (Índice de Romberg)": "O gráfico do Índice de Romberg quantifica a dependência do sistema visual para a manutenção da postura ereta. Ao comparar os resultados de Olhos Fechados com Olhos Abertos, este índice revela o quanto a amostra confia na visão em detrimento dos sistemas proprioceptivo e vestibular.",
            "5. Mapa de Calor (Evolução Global)": "O Mapa de Calor proporciona uma matriz de visualização simultânea de toda a coorte. Ele permite rastrear rapidamente, pela intensidade das zonas de calor, em quais janelas de tempo ocorreram os maiores picos de instabilidade individuais.",
            "6. Taxa de Recuperação Postural": "O gráfico de Taxa de Recuperação mensura a resiliência neuromotora da amostra. Ele calcula o quanto o indivíduo conseguiu reduzir sua oscilação após ter atingido seu pior momento de desequilíbrio.",
            "7. Tempo em Zona de Risco (>80%)": "O gráfico de Tempo em Zona de Risco avalia o custo energético do controle postural. Ele mede o tempo acumulado em que o indivíduo permaneceu oscilando perigosamente próximo ao seu limite máximo de queda.",
            "8. Padrão Motor (Adaptação vs Fadiga)": "O gráfico de Padrão Motor classifica a estratégia primária com base no momento crônico de instabilidade. Picos iniciais configuram Adaptação postural, enquanto picos na reta final alertam para Fadiga Neuromuscular."
        }
        
        st.markdown(f"<div style='text-align: justify; margin-bottom: 5px; color: #555;'>{explicacoes[escolha]}</div>", unsafe_allow_html=True)
        
        # --- 4. TRADUTOR DE NOMES PARA OS GRÁFICOS ---
        mapa_nomes_antigos = {
            "1. Curva Média e Variabilidade": "Curva Média e Variabilidade",
            "2. Distribuição da Amostra (Boxplot)": "1. Distribuição da Amostra (Boxplot)",
            "3. Eixos Afetados (Radar Biomecânico)": "2. Eixos Afetados (Radar Biomecânico)",
            "4. Impacto da Visão (Índice de Romberg)": "3. Impacto da Visão (Índice de Romberg)",
            "5. Mapa de Calor (Evolução Global)": "4. Mapa de Calor (Evolução Global)",
            "6. Taxa de Recuperação Postural": "5. Taxa de Recuperação Postural",
            "7. Tempo em Zona de Risco (>80%)": "6. Tempo em Zona de Risco (>80%)",
            "8. Padrão Motor (Adaptação vs Fadiga)": "7. Padrão Motor (Adaptação vs Fadiga)"
        }
        
        nome_grafico_original = mapa_nomes_antigos[escolha]
        
        # --- 5. EXIBIÇÃO DO GRÁFICO E LAUDO ---
        st.plotly_chart(plotar_estatisticas_avancadas(nome_grafico_original, df_amostra), use_container_width=True)
        
        st.markdown(f"### 📋 Interpretação dos Resultados")
        st.info(gerar_laudo_estatistico(escolha, df_amostra))

# =====================================================================
# 📤 PÁGINA 5: EXPORTAR RESULTADOS
# =====================================================================
elif menu == "📤 Exportar Resultados":
    st.title("📤 Exportar Resultados")
    st.markdown("Baixe as tabelas no formato CSV.")
    
    colunas_tabela = ['Intervalo', 'RMS ML', 'RMS AP', 'Desvio total', 'Área elipse']
    formato_tabela = {col: "{:.6f}" for col in colunas_tabela if col != 'Intervalo'}
    
    if not st.session_state['pacientes']:
        st.warning("⚠️ Nenhum participante na memória para exportar.")
    else:
        for nome_paciente, dados in st.session_state['pacientes'].items():
            with st.expander(f"📥 Tabelas de: {nome_paciente}"):
                c1, c2 = st.columns(2)
                tempos_export = st.session_state.get(f"ms_{nome_paciente}", [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60])
                df_real_oa, _, _ = gerar_tabela_e_normalizar(dados['ml_oa'], dados['ap_oa'], tempos_export)
                df_real_of, _, _ = gerar_tabela_e_normalizar(dados['ml_of'], dados['ap_of'], tempos_export)
                
                with c1:
                    if df_real_oa is not None and not df_real_oa.empty:
                        st.markdown("**Olhos Abertos (OA)**")
                        cols_exp = [c for c in df_real_oa.columns if c != 'Tempo_Num']
                        st.dataframe(df_real_oa[cols_exp].style.format(formato_tabela), hide_index=True)
                        st.download_button("Baixar CSV OA", df_real_oa[cols_exp].to_csv(index=False, float_format="%.6f").encode('utf-8'), f"dados_oa_{nome_paciente}.csv", "text/csv")
                with c2:
                    if df_real_of is not None and not df_real_of.empty:
                        st.markdown("**Olhos Fechados (OF)**")
                        cols_exp = [c for c in df_real_of.columns if c != 'Tempo_Num']
                        st.dataframe(df_real_of[cols_exp].style.format(formato_tabela), hide_index=True)
                        st.download_button("Baixar CSV OF", df_real_of[cols_exp].to_csv(index=False, float_format="%.6f").encode('utf-8'), f"dados_of_{nome_paciente}.csv", "text/csv")

# =====================================================================
# ⚙️ PÁGINA 6: CONFIGURAÇÕES
# =====================================================================
elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações Globais")
    st.caption("Ajuste a identidade visual e limites de todos os gráficos.")
    renderizar_painel_configuracoes()

# =====================================================================
# ℹ️ PÁGINA 7: SOBRE (METODOLOGIA E CÁLCULOS)
# =====================================================================
elif menu == "ℹ️ Sobre":
    st.title("ℹ️ Metodologia e Arquitetura de Cálculos")
    st.markdown("""
    Este painel utiliza algoritmos de processamento biomecânico para transformar dados brutos de força em métricas normalizadas, permitindo a comparação entre diferentes indivíduos e condições.
    """)

    # --- SEÇÃO 1: MÉTODOS DE NORMALIZAÇÃO (CONFORME ANEXO) ---
    st.header("1. Métodos de Normalização")
    st.markdown("""
    Para permitir que participantes com diferentes níveis de equilíbrio sejam comparados na mesma escala (0 a 100%), o sistema aplica dois modelos matemáticos:
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("A. Amplitude (Pico Máximo)")
        st.markdown("""
        Neste modelo, o sistema identifica o maior valor absoluto registrado em toda a sessão do participante para cada variável. Esse valor é definido como o limite de 100%.
        """)
        st.latex(r"Fórmula: Valor_{norm} = \left( \frac{Valor_{bruto}}{Valor_{máximo\_da\_sessão}} \right) \times 100")
        
    with col2:
        st.subheader("B. Parâmetros de Estabilidade")
        st.markdown("""
        Este modelo utiliza o desempenho do participante no tempo final (geralmente aos 60 segundos) como a linha de base de 100%.
        """)
        st.latex(r"Fórmula: Valor_{norm} = \left( \frac{Valor_{bruto}}{Valor_{aos\_60s}} \right) \times 100")

    st.divider()

    # --- SEÇÃO 2: DETALHAMENTO DOS GRÁFICOS (1 AO 8) ---
    st.header("2. Lógica das Estatísticas Gerais (G1 ao G8)")
    st.markdown("Entenda como o sistema processa os dados para gerar cada visualização da coorte:")

    # --- G1 e G2 ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("1. Curva Média e Variabilidade")
        st.markdown("""
        O sistema agrupa todos os participantes por janela de tempo e calcula a **Média Aritmética** dos valores de oscilação. 
        A área sombreada representa o **Desvio-Padrão (σ)**, indicando o nível de dispersão do grupo em relação à média naquele instante.
        """)
    with c2:
        st.subheader("2. Distribuição da Amostra (Boxplot)")
        st.markdown("""
        Focado no tempo final (60s), divide o grupo em quartis. O sistema aplica a **Regra de Tukey**, onde valores que excedem $1,5 \times$ o Intervalo Interquartil ($IQR$) são detectados como **Outliers** (casos atípicos).
        """)

    # --- G3 e G4 ---
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("3. Eixos Afetados (Radar)")
        st.markdown("""
        Identifica a direção preferencial da instabilidade comparando a média global de **RMS ML** (Médio-Lateral) versus **RMS AP** (Anteroposterior). Calcula também a variação percentual entre as condições OA e OF.
        """)
    with c4:
        st.subheader("4. Impacto da Visão (Romberg)")
        st.markdown("""
        Compara a área da elipse final individual de cada participante em Olhos Fechados contra Olhos Abertos. A IA destaca se a maior variação do grupo indica **Dependência Visual** ou **Conflito Sensorial**.
        """)

    # --- G5 e G6 ---
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("5. Mapa de Calor (Evolução Global)")
        st.markdown("""
        Funciona como um rastreador de densidade. O sistema identifica o exato segundo onde a média de todos os participantes atingiu o ápice de instabilidade e busca o valor máximo absoluto da matriz de dados.
        """)
    with c6:
        st.subheader("6. Taxa de Recuperação Postural")
        st.markdown("""
        Avalia a capacidade do sistema de controle de dissipar oscilações. Compara o pior momento do teste (Pico 100%) com o valor estabilizado no último segundo.
        """)
        st.latex(r"Recup\% = \left( \frac{Valor_{Máx} - Valor_{Final}}{Valor_{Máx}} \right) \times 100")

    # --- G7 e G8 ---
    c7, c8 = st.columns(2)
    with c7:
        st.subheader("7. Tempo em Zona de Risco (>80%)")
        st.markdown("""
        Mede o custo energético postural. O algoritmo contabiliza quantas amostras temporais cada participante permaneceu acima de 80% de seu limite individual e converte essa contagem em segundos totais.
        """)
    with c8:
        st.subheader("8. Padrão Motor (Adaptação vs Fadiga)")
        st.markdown("""
        Classifica a estratégia neuromuscular baseada no *timing* do pico de instabilidade. Picos ocorridos até os 30s são definidos como **Adaptação**, enquanto picos após os 30s sugerem **Fadiga Neuromuscular**.
        """)

    st.info("💡 **Nota Técnica:** Todas as análises de coorte utilizam os dados normalizados pela **Amplitude** para garantir uma base comparativa justa entre indivíduos.")