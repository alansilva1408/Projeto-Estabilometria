# =====================================================================
# FICHEIRO: analyzer.py (Inteligência Biomecânica e Gerador de Textos)
# =====================================================================
import random
import pandas as pd
import numpy as np

def gerar_resumo_executivo(df_todos):
    """Gera uma visualização completa da triagem biomecânica (G1 a G8) seguida de síntese."""
    if df_todos is None or df_todos.empty: 
        return "Aguardando processamento de dados para gerar a triagem."

    # --- 1. Coleta de Variáveis para o Relatório Integrado ---
    total_p = len(df_todos['Paciente'].unique())
    cond_ref = "OA" if not df_todos[df_todos['Condicao']=='OA'].empty else "OF"
    t_max = df_todos['Tempo_Num'].max()
    df_f = df_todos[(df_todos['Tempo_Num'] == t_max) & (df_todos['Condicao'] == cond_ref)]

    # Variabilidade e Distribuição (G1 e G2)
    df_c = df_todos[df_todos['Condicao'] == cond_ref]
    df_s = df_c.groupby('Tempo_Num').std(numeric_only=True).reset_index()
    sd_max = df_s['Área elipse'].max()
    q1, q3 = df_f['Área elipse'].quantile(0.25), df_f['Área elipse'].quantile(0.75)
    outliers = df_f[(df_f['Área elipse'] > q3 + 1.5*(q3-q1)) | (df_f['Área elipse'] < q1 - 1.5*(q3-q1))]
    
    # Eixos e Radar (G3)
    med_ml, med_ap = df_todos['RMS ML'].mean(), df_todos['RMS AP'].mean()
    pior_eixo = "Anteroposterior (AP)" if med_ap > med_ml else "Médio-Lateral (ML)"
    
    # Visão (G4 - Romberg)
    pior_v, tot_v = 0, 0
    for p in df_todos['Paciente'].unique():
        df_v = df_todos[df_todos['Paciente'] == p]
        oa = df_v[(df_v['Condicao'] == 'OA') & (df_v['Tempo_Num'] == t_max)]['Área elipse']
        of = df_v[(df_v['Condicao'] == 'OF') & (df_v['Tempo_Num'] == t_max)]['Área elipse']
        if not oa.empty and not of.empty:
            tot_v += 1
            if of.values[0] > oa.values[0]: pior_v += 1
    pct_r = (pior_v / tot_v * 100) if tot_v > 0 else 0

    # Mapa e Padrão Motor (G5 e G8)
    t_crit = df_c.groupby('Tempo_Num')['Área elipse'].mean().idxmax()
    fadiga_c = 0
    for p in df_todos['Paciente'].unique():
        df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==cond_ref)]
        if not df_p.empty and df_p.iloc[df_p['Área elipse'].argmax()]['Tempo_Num'] > 30:
            fadiga_c += 1
    pct_f = (fadiga_c / total_p) * 100

    # Recuperação e Risco (G6 e G7)
    recs = []
    for p in df_todos['Paciente'].unique():
        df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==cond_ref)]
        if not df_p.empty:
            m, f = df_p['Área elipse'].max(), df_p.iloc[df_p['Tempo_Num'].argmax()]['Área elipse']
            recs.append((m-f)/m*100 if m > 0 else 0)
    med_rec = sum(recs)/len(recs) if recs else 0

    riscos = []
    for p in df_todos['Paciente'].unique():
        df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==cond_ref)]
        if not df_p.empty: riscos.append(len(df_p[df_p['Área elipse'] > 80]) * 5)
    med_risco = sum(riscos)/len(riscos) if riscos else 0

    # --- 2. Lógica de Status ---
    status_global = "Estabilidade Preservada" if (med_ml + med_ap)/2 < 45 else "Comprometimento Postural Detectado"
    cor_status = "#155724" if (med_ml + med_ap)/2 < 45 else "#721c24"

    # --- 3. Construção do Texto Narrativo (SEM INDENTAÇÃO NAS TAGS) ---
    texto = f"""
<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff;">
<h4 style="color: #007bff; margin-top: 0;">📋 Relatório de Triagem Biomecânica Coletiva</h4>

<p style="text-align: justify;">
<b>Morfologia Postural e Dispersão (G1, G2 e G3):</b> A triagem da coorte de {total_p} participantes indica uma variabilidade máxima de {sd_max:.1f}%. 
No encerramento do registro ({t_max}s), a distribuição dos dados mostra que a metade central da amostra oscila entre {q1:.1f}% e {q3:.1f}%, 
{"com presença de comportamentos atípicos (outliers)" if not outliers.empty else "apresentando uma amostra estatisticamente coesa"}. 
Biomecanicamente, o eixo <b>{pior_eixo}</b> foi identificado como o plano de maior instabilidade média, exigindo reajustes estruturais acentuados do grupo.
</p>

<p style="text-align: justify;">
<b>Domínio Sensorial e Mecanismos de Controle (G4, G5 e G8):</b> A análise de integração sensorial (Romberg) aponta que {pct_r:.1f}% do grupo 
apresenta dependência da âncora visual para estabilização. Coletivamente, o Mapa de Calor localiza a maior zona de instabilidade aos {t_crit}s. 
Este comportamento correlaciona-se com o padrão motor identificado: {pct_f:.1f}% dos indivíduos exibem picos tardios, configurando um perfil predominante de 
<b>{"Fadiga Neuromuscular" if pct_f > 50 else "Adaptação Postural Eficiente"}</b>.
</p>

<p style="text-align: justify;">
<b>Resiliência e Exigência Energética (G6 e G7):</b> No que tange à eficiência de reajuste, a taxa média de recuperação foi de {med_rec:.1f}%, 
mensurando a capacidade de retorno ao equilíbrio após o pico de desequilíbrio. Contudo, a amostra sustenta níveis críticos (>80%) por uma média de {med_risco:.1f} segundos, 
refletindo o <b>{"alto" if med_risco > 10 else "baixo"}</b> custo metabólico sustentado para evitar falhas posturais.
</p>

<hr style="border: 0; border-top: 1px solid #ccc;">

<h4 style="color: {cor_status};">📌 Síntese Conclusiva</h4>
<p style="text-align: justify;">
<b>Status Global:</b> {status_global}.<br>
<b>Resumo:</b> A amostra caracteriza-se por uma <b>{"estratégia motora resiliente" if pct_f < 50 and med_rec > 50 else "instabilidade progressiva com sinais de fadiga"}</b>. 
O principal marcador de risco biomecânico é o eixo <b>{pior_eixo}</b>. Recomenda-se o acompanhamento focado em protocolos de fortalecimento proprioceptivo 
e controle de carga visual para otimizar a estabilidade postural do grupo.
</p>
</div>
"""
    return texto

def gerar_laudo_matematico(df_norm, nome_paciente, condicao):
    """Gera a interpretação para os gráficos individuais (Página 3) com frases aleatórias."""
    if df_norm is None or df_norm.empty: return ""
    
    pico_ml = int(df_norm.iloc[df_norm['RMS ML'].argmax()]['Tempo_Num'])
    pico_ap = int(df_norm.iloc[df_norm['RMS AP'].argmax()]['Tempo_Num'])
    pico_elipse = int(df_norm.iloc[df_norm['Área elipse'].argmax()]['Tempo_Num'])

    def analisar_comportamento(coluna, tempo_pico):
        estabilizou_em = None
        tempo_max = int(df_norm['Tempo_Num'].max())
        if tempo_pico < (tempo_max - 10):
            for t in range(tempo_pico + 5, tempo_max - 5):
                janela = df_norm[df_norm['Tempo_Num'] >= t][coluna]
                if len(janela) > 0 and (janela.max() - janela.min() <= 10):
                    estabilizou_em = int(t)
                    break
        if estabilizou_em:
            frases = [
                f"conseguiu recuperar o controle, estabilizando-se aos {estabilizou_em} segundos",
                f"reduziu as oscilações e encontrou seu ponto de equilíbrio aos {estabilizou_em} segundos",
                f"apresentou melhora contínua, atingindo um platô de estabilidade aos {estabilizou_em} segundos"
            ]
            return random.choice(frases).strip()
        ultimos_10s = df_norm[df_norm['Tempo_Num'] >= df_norm['Tempo_Num'].max() - 10][coluna].mean()
        if ultimos_10s >= 70: 
            return random.choice(["manteve oscilações elevadas até o final do teste", "continuou apresentando instabilidade constante", "não conseguiu recuperar o controle postural de forma efetiva"])
        elif ultimos_10s >= 40: 
            return random.choice(["mostrou uma recuperação apenas parcial do equilíbrio", "apresentou uma redução moderada, mas sem estabilizar totalmente", "conseguiu conter parcialmente a instabilidade"])
        else: 
            return random.choice(["teve uma queda nas oscilações, porém sem estabilização completa", "apresentou melhora no final, mas sem atingir um platô fixo", "reduziu a instabilidade, embora sem firmar o equilíbrio"])

    pos_ml, pos_ap, pos_el = analisar_comportamento('RMS ML', pico_ml), analisar_comportamento('RMS AP', pico_ap), analisar_comportamento('Área elipse', pico_elipse)

    if condicao == "OA":
        return f"O gráfico na condição de olhos abertos de **{nome_paciente}** mostra que o RMS ML (oscilação lateral) atinge seu pico aos **{pico_ml}s**. Após esse momento, o participante {pos_ml}. Já o RMS AP (oscilação frente-trás) atinge seu pico aos **{pico_ap}s**, e a partir desse ponto o participante {pos_ap}. Por fim, a área da elipse chega ao seu máximo aos **{pico_elipse}s**, observando-se que o participante {pos_el}."
    return f"Já o gráfico com a condição de olhos fechados mostra que o RMS ML atinge seu pico aos **{pico_ml}s**. Em seguida, o participante {pos_ml}. O RMS AP atinge o valor máximo aos **{pico_ap}s**, e após esse pico o participante {pos_ap}. A área da elipse atinge seu pico aos **{pico_elipse}s**, momento após o qual o participante {pos_el}."

def gerar_laudo_estatistico(analise, df_todos):
    """Laudos de Estatística Geral (Página 4) seguindo fielmente os modelos de cenários."""
    if df_todos is None or df_todos.empty: return ""
    cond_ref = "OA" if not df_todos[df_todos['Condicao']=='OA'].empty else "OF"

    if "1. Curva Média" in analise:
        df_c = df_todos[df_todos['Condicao'] == cond_ref]
        df_s = df_c.groupby('Tempo_Num').std(numeric_only=True).reset_index()
        idx = df_s['Área elipse'].argmax()
        pico_s, tempo_s = df_s.iloc[idx]['Área elipse'], df_s.iloc[idx]['Tempo_Num']
        if pico_s <= 25:
            return f"Nesta amostra, o sistema detectou uma **baixa variabilidade**, atingindo seu ponto de maior dispersão aos **{tempo_s} segundos** (Desvio-Padrão Máx: **{pico_s:.1f}%**). Isso sugere que este foi o instante de maior divergência, mas a amostra apresentou respostas motoras consistentes."
        df_p = df_c[df_c['Tempo_Num'] == tempo_s].copy()
        df_p['Dist'] = abs(df_p['Área elipse'] - df_p['Área elipse'].mean())
        culpado = df_p.iloc[df_p['Dist'].argmax()]['Paciente']
        return f"Nesta amostra, o sistema detectou uma **alta variabilidade** aos **{tempo_s} segundos** (DP Máx: **{pico_s:.1f}%**). O participante que mais contribuiu para essa divergência foi **{culpado}**, sugerindo um episódio isolado de desequilíbrio."

    elif "2. Distribuição" in analise:
        t_max = df_todos['Tempo_Num'].max()
        df_f = df_todos[(df_todos['Tempo_Num'] == t_max) & (df_todos['Condicao'] == cond_ref)]
        q1, q3 = df_f['Área elipse'].quantile(0.25), df_f['Área elipse'].quantile(0.75)
        outliers = df_f[(df_f['Área elipse'] > q3 + 1.5*(q3-q1)) | (df_f['Área elipse'] < q1 - 1.5*(q3-q1))]
        base = f"A análise no tempo final (**{t_max}s**) revela que a maior parte dos participantes (50% centrais) concentrou sua oscilação numa faixa entre **{q1:.1f}% e {q3:.1f}%**."
        if outliers.empty:
            return base + " O sistema não identificou outliers nesta condição, apontando para uma estabilização coesa do grupo no final do registro."
        return base + f" O sistema identificou comportamento atípico (outlier) no(s) participante(s) **{', '.join(outliers['Paciente'].unique())}**, que encerraram o teste com níveis de instabilidade discrepantes da maioria."

    elif "3. Eixos Afetados" in analise:
        med_ml, med_ap = df_todos['RMS ML'].mean(), df_todos['RMS AP'].mean()
        eixo, col, estrat = ("Anteroposterior (AP)", "RMS AP", "tornozelo") if med_ap >= med_ml else ("Médio-Lateral (ML)", "RMS ML", "quadril compensatória")
        idx_m = df_todos[col].argmax()
        rec, val = df_todos.iloc[idx_m]['Paciente'], df_todos.iloc[idx_m][col]
        dif_txt = ""
        df_m = df_todos.groupby('Condicao')['Área elipse'].mean()
        if 'OA' in df_m and 'OF' in df_m:
            dif_txt = f" A supressão visual (olhos fechados) causou uma alteração global média de **{((df_m['OF'] - df_m['OA']) / df_m['OA'] * 100):.1f}%** na área de oscilação em relação aos olhos abertos."
        p1 = f"Observando a morfologia do controle postural da amostra, nota-se que a maior exigência de reajuste ocorreu no eixo **{eixo}**. Esta projeção evidencia o plano de movimento com maior déficit de estabilização estrutural.{dif_txt}"
        p2 = f"Ao analisar o desempenho individual, o participante que atingiu o maior pico de oscilação {'lateral' if 'ML' in eixo else 'neste eixo'} foi **{rec}** ({col} Máx: **{val:.1f}%**), sugerindo uma {'forte instabilidade neste plano e acentuada' if 'ML' in eixo else 'alta exigência ou possível sobrecarga na'} dependência da estratégia de {estrat} para manter o equilíbrio."
        return f"{p1}\n\n{p2}"

    elif "4. Impacto da Visão" in analise:
        df_f = df_todos[df_todos['Tempo_Num'] == df_todos['Tempo_Num'].max()]
        comp = []
        for p in df_f['Paciente'].unique():
            oa = df_f[(df_f['Paciente']==p) & (df_f['Condicao']=='OA')]['Área elipse'].mean()
            of = df_f[(df_f['Paciente']==p) & (df_f['Condicao']=='OF')]['Área elipse'].mean()
            if pd.notna(oa) and pd.notna(of): comp.append({'p':p, 'diff': ((of-oa)/oa*100)})
        if not comp: return "Dados insuficientes para comparar OA vs OF."
        pior = [c for c in comp if c['diff'] > 0]
        pct_p = (len(pior)/len(comp)*100)
        campeao = max(comp, key=lambda x: abs(x['diff']))
        base = f"Os dados demonstram que **{pct_p:.1f}%** do grupo sofreu degradação do controle postural ao suprimir a visão, configurando o comportamento biomecânico padrão. Contudo, **{100-pct_p:.1f}%** apresentou um desempenho inverso (melhora de estabilidade de olhos fechados)."
        if campeao['diff'] > 0:
            return base + f"\n\nAo analisar o impacto individual, o participante que demonstrou a maior dependência visual foi **{campeao['p']}**, cuja área de oscilação sofreu um aumento de **{campeao['diff']:.1f}%** ao fechar os olhos. Este déficit acentuado sugere que o indivíduo necessita fortemente da âncora visual para compensar possíveis ineficiências proprioceptivas ou vestibulares."
        return base + f"\n\nDestaca-se o comportamento atípico do participante **{campeao['p']}**, que apresentou a maior melhora de estabilidade (redução de **{abs(campeao['diff']):.1f}%** na oscilação) ao fechar os olhos. Isso sugere um possível conflito sensorial, sobrecarga de processamento visual ou desatenção significativa na condição de olhos abertos."

    elif "5. Mapa de Calor" in analise:
        df_c = df_todos[df_todos['Condicao'] == cond_ref]
        t_crit = df_c.groupby('Tempo_Num')['Área elipse'].mean().idxmax()
        idx_m = df_c['Área elipse'].argmax()
        nome, t_ind = df_c.iloc[idx_m]['Paciente'], df_c.iloc[idx_m]['Tempo_Num']
        if t_crit <= 30:
            p1 = f"A leitura da matriz térmica para o grupo atual indica que a amostra atingiu sua maior 'zona de calor' (instabilidade máxima concentrada) na fase inicial do teste, em torno dos **{t_crit} segundos**. Este padrão reflete um comportamento fisiológico de adaptação motora à nova postura."
            p2 = f"Realizando o rastreio térmico individual, o participante que registrou a 'temperatura' mais crítica (maior pico isolado de desequilíbrio na matriz) foi **{nome}** aos **{t_ind} segundos**, indicando a resposta neuromuscular mais exacerbada durante esta janela de calibragem."
        else:
            p1 = f"A leitura da matriz térmica para o grupo atual indica que a amostra atingiu sua maior 'zona de calor' (instabilidade máxima concentrada) na fase avançada do teste, em torno dos **{t_crit} segundos**. Este aquecimento tardio na matriz sugere um provável quadro de fadiga neuromuscular ou declínio atencional coletivo."
            p2 = f"Realizando o rastreio térmico individual, o participante que sofreu a 'temperatura' mais crítica (maior pico isolado de desequilíbrio) foi **{nome}** aos **{t_ind} segundos**, representando o caso mais severo de esgotamento estabilizador neste período."
        return f"{p1}\n\n{p2}"

    elif "6. Taxa de Recuperação" in analise:
        rec = []
        for p in df_todos['Paciente'].unique():
            df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==cond_ref)]
            if not df_p.empty:
                m, f = df_p['Área elipse'].max(), df_p.iloc[df_p['Tempo_Num'].argmax()]['Área elipse']
                rec.append({'p':p, 'r': (m-f)/m*100 if m>0 else 0})
        med_r = sum(i['r'] for i in rec)/len(rec)
        n_exc = len([i for i in rec if i['r'] >= 60])
        n_ruim = len([i for i in rec if i['r'] <= 30])
        if med_r >= 50:
            best = max(rec, key=lambda x: x['r'])
            p1 = f"A amostra avaliada demonstrou boa resiliência neuromotora, apresentando uma recuperação postural média de **{med_r:.1f}%**. Os dados apontam que **{n_exc} participante(s)** obtiveram excelente readaptação (redução de oscilação > 60% após o pico de instabilidade)."
            p2 = f"Ao focar no desempenho individual, o grande destaque de eficiência motora foi o participante **{best['p']}**, que atingiu a maior taxa de reajuste da coorte (**{best['r']:.1f}%**). Este indivíduo conseguiu retornar rapidamente a um estado de estabilidade confortável após atingir o seu limite de desequilíbrio."
        else:
            worst = min(rec, key=lambda x: x['r'])
            p1 = f"A amostra avaliada demonstrou dificuldade na resiliência neuromotora, apresentando uma recuperação postural média de apenas **{med_r:.1f}%**. Os dados alertam que **{n_ruim} participante(s)** apresentaram severa dificuldade de reajuste (recuperação < 30%)."
            p2 = f"No rastreio individual, o caso clínico mais crítico foi o do participante **{worst['p']}**, que obteve a menor taxa de readaptação (**{worst['r']:.1f}%**). Este indivíduo foi incapaz de dissipar a instabilidade de forma efetiva, encerrando o teste ainda perigosamente próximo ao seu limite máximo de queda, o que sugere exaustão dos estabilizadores posturais."
        return f"{p1}\n\n{p2}"

    elif "7. Tempo em Zona de Risco" in analise:
        risco = []
        for p in df_todos['Paciente'].unique():
            df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==cond_ref)]
            if not df_p.empty: risco.append({'p':p, 't': len(df_p[df_p['Área elipse'] > 80]) * 5})
        med_t = sum(i['t'] for i in risco)/len(risco)
        worst = max(risco, key=lambda x: x['t'])
        if med_t < 10:
            p1 = f"O sistema quantificou que o grupo demonstrou boa resistência postural, sustentando níveis críticos de oscilação (>80% do limite individual) por uma média de apenas **{med_t:.1f} segundos**. Tempos reduzidos nesta zona indicam estratégias de controle motor eficientes e baixo gasto energético para manter a postura ereta."
            p2 = f"Apesar do bom desempenho geral, ao analisar o esforço individual, o participante que permaneceu por mais tempo nesta zona de alta exigência foi **{worst['p']}** (**{worst['t']:.1f} segundos**). Este valor serve como um marcador de atenção para uma possível fadiga muscular precoce ou menor eficiência compensatória em comparação aos seus pares."
        else:
            p1 = f"O sistema quantificou que o grupo apresentou dificuldade na resistência postural, sustentando níveis críticos de oscilação (>80% do limite individual) por uma média elevada de **{med_t:.1f} segundos**. Tempos prolongados nesta zona refletem alta co-contração muscular e um elevado esgotamento energético para evitar a queda."
            p2 = f"No rastreio individual, o alerta clínico máximo recai sobre o participante **{worst['p']}**, que sustentou a instabilidade crítica por expressivos **{worst['t']:.1f} segundos**. Este tempo excessivo na zona de risco evidencia um déficit severo na correção motora e um comportamento biomecânico limítrofe à falha estabilizadora."
        return f"{p1}\n\n{p2}"

    elif "8. Padrão Motor" in analise:
        fad, tempos = 0, []
        for p in df_todos['Paciente'].unique():
            df_p = df_todos[(df_todos['Paciente']==p) & (df_todos['Condicao']==cond_ref)]
            if not df_p.empty:
                t_p = df_p.iloc[df_p['Área elipse'].argmax()]['Tempo_Num']
                tempos.append({'p':p, 't':t_p})
                if t_p > 30: fad += 1
        pct_f, pct_a = (fad/len(tempos)*100), (100 - (fad/len(tempos)*100))
        worst = max(tempos, key=lambda x: x['t'])
        if pct_a >= pct_f:
            return f"Com base no momento do pico de instabilidade, a IA identificou que a estratégia predominante do grupo foi a **Adaptação Postural** (**{pct_a:.1f}%** atingiram o limite na fase inicial, até 30s). Isso demonstra que a amostra conseguiu calibrar o equilíbrio rapidamente.\n\nApesar do bom padrão global, o participante **{worst['p']}** destoou do grupo, registrando sua maior instabilidade apenas aos **{worst['t']} segundos** (reta final). Este atraso sugere um quadro isolado de fadiga neuromuscular ou perda de foco tardia."
        return f"Com base no momento do pico de instabilidade, a IA identificou que a estratégia predominante do grupo foi a **Fadiga Neuromuscular** (**{pct_f:.1f}%** registraram a maior instabilidade nas janelas finais, após 30s). Isso indica declínio atencional ou exaustão física progressiva da amostra.\n\nO caso mais crítico de instabilidade tardia foi o do participante **{worst['p']}**, que sustentou o equilíbrio inicialmente, mas sofreu a sua pior quebra de controle aos **{worst['t']} segundos**, ilustrando perfeitamente o esgotamento do sistema neuromotor evidenciado no grupo."
    
    return ""