# =====================================================================
# FICHEIRO: processing.py (O Motor Matemático e Processamento de Sinais)
# =====================================================================
import pandas as pd
import numpy as np
import streamlit as st
from scipy.interpolate import interp1d
from scipy.signal import butter, filtfilt, detrend
from scipy.integrate import trapezoid

def processar_arquivo_bruto(arquivo_up):
    try:
        df = pd.read_csv(arquivo_up, sep=';')
        t_original = df['DURACAO'] / 1000.0  # ms para s
        
        # Lendo os dados originais puros
        x = df['ACC EIXO X'].values
        z = df['ACC EIXO Z'].values

        # Interpolação para 100Hz (Adequado ao artigo de Scoppa et al. 2013)
        fs_novo = 100
        dt_novo = 1 / fs_novo
        t_novo = np.arange(t_original.iloc[0], t_original.iloc[-1], dt_novo)

        interp_ml = interp1d(t_original, x, kind='linear', fill_value="extrapolate")
        interp_ap = interp1d(t_original, z, kind='linear', fill_value="extrapolate")

        ml_100Hz = interp_ml(t_novo)
        ap_100Hz = interp_ap(t_novo)

        # Detrend e Filtro Passa-Baixa (8Hz)
        ml_detrended = detrend(ml_100Hz)
        ap_detrended = detrend(ap_100Hz)

        b, a = butter(4, 8.0 / (fs_novo / 2), btype='low', analog=False)
        ml_filtrado = filtfilt(b, a, ml_detrended)
        ap_filtrado = filtfilt(b, a, ap_detrended)

        return t_novo, ml_filtrado, ap_filtrado
    except Exception as e:
        st.error(f"Erro ao processar o arquivo bruto: {e}")
        return None, None, None

def calcular_metricas_recorte(ml_sel, ap_sel):
    rms_ml = np.sqrt(np.mean(ml_sel**2))
    rms_ap = np.sqrt(np.mean(ap_sel**2))
    dev_total = np.sum(np.sqrt(ml_sel**2 + ap_sel**2))

    cov = np.cov(ml_sel, ap_sel)
    vals, _ = np.linalg.eigh(cov)
    vals = np.sort(vals)[::-1]
    scale = np.sqrt(vals * 5.991)
    elipse = np.pi * scale[0] * scale[1]

    # Cálculos de Frequência e Potência
    n = len(ml_sel)
    fft_ml = np.fft.fft(ml_sel)
    fft_ap = np.fft.fft(ap_sel)
    freqs = np.fft.fftfreq(n, d=1/100)
    
    psd_ml = np.abs(fft_ml[:n//2])**2 / (n*100)
    psd_ap = np.abs(fft_ap[:n//2])**2 / (n*100)

    psd_ml_sel = psd_ml[1:]
    psd_ap_sel = psd_ap[1:]
    freqs_sel = freqs[1:n//2]

    pot_total_ml = pot_baixa_ml = pot_media_ml = pot_alta_ml = freq_median_ml = 0
    pot_total_ap = pot_baixa_ap = pot_media_ap = pot_alta_ap = freq_median_ap = 0

    if len(psd_ml_sel) >= 80:
        pot_total_ml = trapezoid(psd_ml_sel, freqs_sel)
        pot_baixa_ml = trapezoid(psd_ml_sel[0:4], freqs_sel[0:4])
        pot_media_ml = trapezoid(psd_ml_sel[5:19], freqs_sel[5:19])
        pot_alta_ml = trapezoid(psd_ml_sel[20:79], freqs_sel[20:79])
        for i, val in enumerate(psd_ml_sel):
            if np.sum(psd_ml_sel[0:i]) > pot_total_ml / 2:
                freq_median_ml = freqs_sel[i-1]
                break

    if len(psd_ap_sel) >= 80:
        pot_total_ap = trapezoid(psd_ap_sel, freqs_sel)
        pot_baixa_ap = trapezoid(psd_ap_sel[0:4], freqs_sel[0:4])
        pot_media_ap = trapezoid(psd_ap_sel[5:19], freqs_sel[5:19])
        pot_alta_ap = trapezoid(psd_ap_sel[20:79], freqs_sel[20:79])
        for i, val in enumerate(psd_ap_sel):
            if np.sum(psd_ap_sel[0:i]) > pot_total_ap / 2:
                freq_median_ap = freqs_sel[i-1]
                break

    return {
        "RMS ML": rms_ml, "RMS AP": rms_ap, "Desvio total": dev_total, "Área elipse": elipse,
        "Potência total ML": pot_total_ml, "Potência total AP": pot_total_ap,
        "Potência Baixa Freq ML": pot_baixa_ml, "Potência Baixa Freq AP": pot_baixa_ap,
        "Potência Média Freq ML": pot_media_ml, "Potência Média Freq AP": pot_media_ap,
        "Potência Alta Freq ML": pot_alta_ml, "Potência Alta Freq AP": pot_alta_ap,
        "Frequência mediana ML": freq_median_ml, "Frequência mediana AP": freq_median_ap
    }

def gerar_tabela_e_normalizar(ml_full, ap_full, tempos):
    """Gera as duas tabelas de normalização (Amplitude e Estabilidade) para os Gráficos Individuais."""
    if ml_full is None or len(tempos) == 0: return None, None, None
    linhas = []
    for t in sorted(tempos):
        endRec = int(t * 100) # fs = 100Hz
        if endRec > 0 and endRec <= len(ml_full):
            mets = calcular_metricas_recorte(ml_full[:endRec], ap_full[:endRec])
            mets["Tempo_Num"] = t
            mets["Intervalo"] = f"0-{endRec}" 
            
            linha = {"Tempo_Num": mets["Tempo_Num"], "Intervalo": mets["Intervalo"]}
            linha.update({k: v for k, v in mets.items() if k not in ["Tempo_Num", "Intervalo"]})
            linhas.append(linha)
            
    df_real = pd.DataFrame(linhas)
    if df_real.empty: return None, None, None
    
    df_amp = df_real.copy()
    df_est = df_real.copy()
    metricas_grafico = ["RMS ML", "RMS AP", "Desvio total", "Área elipse"]
    
    idx_final = df_real['Tempo_Num'].idxmax()
    
    for m in metricas_grafico:
        if m in df_real.columns:
            max_v = df_real[m].max()
            val_final = df_real.loc[idx_final, m]
            
            df_amp[m] = (df_real[m] / max_v) * 100 if max_v != 0 else 0
            df_est[m] = (df_real[m] / val_final) * 100 if val_final != 0 else 0
            
    return df_real, df_amp, df_est

def extrair_dados_brutos(ml_full, ap_full, tempos):
    """Função extra para extrair apenas a tabela crua (Usada pelas Estatísticas de Coorte)."""
    if ml_full is None or len(tempos) == 0: return pd.DataFrame()
    linhas = []
    for t in sorted(tempos):
        endRec = int(t * 100)
        if endRec > 0 and endRec <= len(ml_full):
            mets = calcular_metricas_recorte(ml_full[:endRec], ap_full[:endRec])
            mets["Tempo_Num"] = t
            mets["Intervalo"] = f"0-{endRec}"
            linha = {"Tempo_Num": mets["Tempo_Num"], "Intervalo": mets["Intervalo"]}
            linha.update({k: v for k, v in mets.items() if k not in ["Tempo_Num", "Intervalo"]})
            linhas.append(linha)
    return pd.DataFrame(linhas)

def normalizar_paciente_global(df_oa, df_of):
    """Regra solicitada pelo orientador: O 100% é o maior valor do paciente considerando ambas as condições (OA e OF)."""
    df_norm_oa = df_oa.copy() if not df_oa.empty else pd.DataFrame()
    df_norm_of = df_of.copy() if not df_of.empty else pd.DataFrame()
    
    metricas_grafico = ["RMS ML", "RMS AP", "Desvio total", "Área elipse"]
    
    for m in metricas_grafico:
        max_oa = df_oa[m].max() if (not df_oa.empty and m in df_oa.columns) else 0
        max_of = df_of[m].max() if (not df_of.empty and m in df_of.columns) else 0
        max_global = max(max_oa, max_of)
        
        if max_global != 0:
            if not df_norm_oa.empty and m in df_norm_oa.columns:
                df_norm_oa[m] = (df_oa[m] / max_global) * 100
            if not df_norm_of.empty and m in df_norm_of.columns:
                df_norm_of[m] = (df_of[m] / max_global) * 100
                
    return df_norm_oa, df_norm_of