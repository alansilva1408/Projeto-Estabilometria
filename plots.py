# =====================================================================
# FICHEIRO: plots.py (Motor Gráfico e Visualizações Avançadas)
# =====================================================================
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

# Importa o mapa de legendas diretamente das configurações
from config import mapa_legenda

def plotar_grafico_individual(df_norm):
    """Desenha o gráfico de linha individual (Evolução Postural) de um participante."""
    fig = go.Figure()
    config_linhas = {
        "RMS ML": {'cor': st.session_state['cor_ml'], 'marca': st.session_state['mark_ml']},
        "RMS AP": {'cor': st.session_state['cor_ap'], 'marca': st.session_state['mark_ap']},
        "Desvio total": {'cor': st.session_state['cor_dt'], 'marca': st.session_state['mark_dt']},
        "Área elipse": {'cor': st.session_state['cor_ae'], 'marca': st.session_state['mark_ae']}
    }
    forma_linha = 'spline' if st.session_state['suavizar_linhas'] else 'linear'
    
    for c in config_linhas.keys():
        if c in df_norm.columns:
            marca = config_linhas[c]['marca']
            modo = 'lines' if marca == 'none' else 'lines+markers'
            fig.add_trace(go.Scatter(
                x=df_norm["Tempo_Num"], y=df_norm[c], name=c, mode=modo, 
                marker=dict(symbol=marca, size=st.session_state['tamanho_marcador']) if marca != 'none' else None,
                line=dict(color=config_linhas[c]['cor'], width=st.session_state['espessura_linha'], shape=forma_linha)
            ))
    
    mirror_eixos = True if st.session_state['mostrar_borda'] else False
    fig.update_layout(
        title=dict(text=st.session_state['titulo_grafico'], x=0.5),
        plot_bgcolor='white', 
        xaxis=dict(title=st.session_state['titulo_x'], dtick=st.session_state['x_step'], showgrid=st.session_state['mostrar_grid'], gridcolor=st.session_state['cor_grid'], linecolor=st.session_state['cor_eixos'], mirror=mirror_eixos),
        yaxis=dict(title=st.session_state['titulo_y'], range=[st.session_state['y_min'], st.session_state['y_max']], dtick=st.session_state['y_step'], showgrid=st.session_state['mostrar_grid'], gridcolor=st.session_state['cor_grid'], linecolor=st.session_state['cor_eixos'], mirror=mirror_eixos, zeroline=False),
        legend=mapa_legenda[st.session_state['pos_legenda']], margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def plotar_estatisticas_avancadas(tipo, df_todos):
    """Gereciona e desenha os 8 gráficos avançados de análise de Coorte."""
    if df_todos.empty: return go.Figure()
    
    if tipo == "Curva Média e Variabilidade":
        fig = go.Figure()
        cores = {'RMS ML': '#636EFA', 'RMS AP': '#EF553B', 'Desvio total': '#00CC96', 'Área elipse': '#AB63FA'}
        for cond, dash_style in [("OA", "solid"), ("OF", "dash")]:
            df_cond = df_todos[df_todos['Condicao'] == cond]
            if df_cond.empty: continue
            df_m = df_cond.groupby('Tempo_Num').mean(numeric_only=True).reset_index()
            df_s = df_cond.groupby('Tempo_Num').std(numeric_only=True).reset_index().fillna(0)
            
            for m in cores.keys():
                if m in df_m.columns:
                    fig.add_trace(go.Scatter(
                        x=df_m['Tempo_Num'], y=df_m[m], name=f"{m} ({cond})", mode='lines+markers',
                        line=dict(color=cores[m], width=2, dash=dash_style),
                        # O ERRO ESTAVA AQUI: removido a opacidade que causava o ValueError
                        error_y=dict(type='data', array=df_s[m], visible=True, thickness=1, color=cores[m])
                    ))
        fig.update_layout(title="Curva Média e Desvio-Padrão Global (OA vs OF)", yaxis_title="Média Normalizada (%)", xaxis_title="Tempo (s)", plot_bgcolor='white', yaxis_range=[0, 105])
        return fig

    elif tipo == "1. Distribuição da Amostra (Boxplot)":
        tempo_max = df_todos['Tempo_Num'].max()
        df_final = df_todos[df_todos['Tempo_Num'] == tempo_max]
        fig = px.box(df_final, x="Condicao", y="Área elipse", points="all", color="Condicao", title=f"Distribuição da Área da Elipse aos {tempo_max}s (Dispersão e Outliers)", color_discrete_map={'OA':'#636EFA', 'OF':'#EF553B'})
        fig.update_layout(plot_bgcolor='white', yaxis_range=[0, 105])
        return fig

    elif tipo == "2. Eixos Afetados (Radar Biomecânico)":
        df_mean = df_todos.groupby('Condicao')[['RMS ML', 'RMS AP', 'Desvio total', 'Área elipse']].mean(numeric_only=True).reset_index()
        fig = go.Figure()
        cores_radar = {'OA': 'blue', 'OF': 'red'}
        for i, row in df_mean.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row['RMS ML'], row['RMS AP'], row['Desvio total'], row['Área elipse'], row['RMS ML']],
                theta=['RMS ML', 'RMS AP', 'Desvio Total', 'Área Elipse', 'RMS ML'],
                fill='toself', name=row['Condicao'], line_color=cores_radar.get(row['Condicao'], 'green')
            ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Média Global dos Eixos Posturais (Comparativo)")
        return fig

    elif tipo == "3. Impacto da Visão (Índice de Romberg)":
        tempo_max = df_todos['Tempo_Num'].max()
        df_final = df_todos[df_todos['Tempo_Num'] == tempo_max]
        romberg = []
        for p in df_final['Paciente'].unique():
            val_oa = df_final[(df_final['Paciente']==p) & (df_final['Condicao']=='OA')]['Área elipse'].mean()
            val_of = df_final[(df_final['Paciente']==p) & (df_final['Condicao']=='OF')]['Área elipse'].mean()
            # Trata casos em que a pessoa só tenha um dos ficheiros
            if pd.notna(val_oa) and pd.notna(val_of):
                diff = val_of - val_oa
                romberg.append({'Paciente': p, 'Diferença OF-OA (%)': diff})
        
        if not romberg:
            return go.Figure().update_layout(title="Dados insuficientes de OA e OF combinados.")
            
        df_r = pd.DataFrame(romberg).sort_values(by='Diferença OF-OA (%)', ascending=False)
        fig = px.bar(df_r, x='Paciente', y='Diferença OF-OA (%)', title="Impacto da Supressão Visual na Área da Elipse (OF - OA)", color='Diferença OF-OA (%)', color_continuous_scale='RdBu_r')
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(plot_bgcolor='white')
        return fig

    elif tipo == "4. Mapa de Calor (Evolução Global)":
        # Se houver dados de OA, usa-os como padrão para o mapa de calor. Caso contrário, usa OF.
        condicao_alvo = "OA" if len(df_todos[df_todos['Condicao']=='OA']) > 0 else "OF"
        df_hm = df_todos[df_todos['Condicao'] == condicao_alvo].pivot(index='Paciente', columns='Tempo_Num', values='Área elipse')
        fig = px.imshow(df_hm, title=f"Mapa de Calor da Instabilidade ao Longo do Tempo ({condicao_alvo})", labels=dict(x="Tempo (s)", y="Participante", color="Instabilidade %"), color_continuous_scale="Turbo", zmin=0, zmax=100)
        return fig

    elif tipo == "5. Taxa de Recuperação Postural":
        recup = []
        condicao_alvo = "OA" if len(df_todos[df_todos['Condicao']=='OA']) > 0 else "OF"
        for p in df_todos['Paciente'].unique():
            df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==condicao_alvo)]
            if df_p.empty: continue
            max_val = df_p['Área elipse'].max() 
            final_val = df_p.loc[df_p['Tempo_Num'].idxmax()]['Área elipse']
            taxa = max_val - final_val
            recup.append({'Paciente': p, 'Recuperação (%)': taxa})
            
        if not recup: return go.Figure()
        df_rec = pd.DataFrame(recup).sort_values(by='Recuperação (%)', ascending=False)
        fig = px.bar(df_rec, x='Paciente', y='Recuperação (%)', title=f"Taxa de Recuperação Postural ({condicao_alvo} - Queda em Relação ao Pico Máximo)", color='Recuperação (%)', color_continuous_scale='Greens')
        fig.update_layout(plot_bgcolor='white', yaxis_range=[0, 100])
        return fig

    elif tipo == "6. Tempo em Zona de Risco (>80%)":
        risco = []
        condicao_alvo = "OA" if len(df_todos[df_todos['Condicao']=='OA']) > 0 else "OF"
        for p in df_todos['Paciente'].unique():
            df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==condicao_alvo)]
            if df_p.empty: continue
            # Conta quantas janelas ficaram acima de 80% (cada janela tem o passo definido, ex: 5s)
            passo = df_p['Tempo_Num'].diff().median()
            if pd.isna(passo): passo = 5
            contagem = len(df_p[df_p['Área elipse'] > 80]) * passo
            risco.append({'Paciente': p, 'Segundos em Risco': contagem})
            
        if not risco: return go.Figure()
        df_risco = pd.DataFrame(risco).sort_values(by='Segundos em Risco', ascending=False)
        fig = px.bar(df_risco, x='Paciente', y='Segundos em Risco', title=f"Tempo de Permanência em Instabilidade Crítica (>80%) ({condicao_alvo})", color='Segundos em Risco', color_continuous_scale='Reds')
        fig.update_layout(plot_bgcolor='white')
        return fig

    elif tipo == "7. Padrão Motor (Adaptação vs Fadiga)":
        padroes = {'Adaptação (Pico até 30s)': 0, 'Fadiga (Pico após 30s)': 0}
        condicao_alvo = "OA" if len(df_todos[df_todos['Condicao']=='OA']) > 0 else "OF"
        for p in df_todos['Paciente'].unique():
            df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==condicao_alvo)]
            if df_p.empty: continue
            momento_pico = df_p.loc[df_p['Área elipse'].idxmax()]['Tempo_Num']
            if momento_pico <= 30: padroes['Adaptação (Pico até 30s)'] += 1
            else: padroes['Fadiga (Pico após 30s)'] += 1
        
        # Só exibe se houver dados
        if sum(padroes.values()) == 0: return go.Figure()
        
        fig = go.Figure(data=[go.Pie(labels=list(padroes.keys()), values=list(padroes.values()), hole=.4, marker_colors=['#00CC96', '#EF553B'])])
        fig.update_layout(title=f"Classificação do Padrão Motor da Amostra ({condicao_alvo})")
        return fig
    
    return go.Figure()