import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Dashboard NIP Reembolso", page_icon="📊", layout="wide")

st.title("📊 Dashboard NIP Reembolso")

@st.cache_data
def carregar_dados(uploaded_file):
    try:
        # Lê o Excel sem cabeçalho
        df_raw = pd.read_excel(uploaded_file, sheet_name='NIPS REEMBOLSO', header=None)
        
        dados_limpos = []
        
        for idx, row in df_raw.iterrows():
            cells = [str(c).strip() if pd.notna(c) and str(c).strip().lower() != 'nan' else '' for c in row]
            
            # Pula linhas vazias e cabeçalhos repetidos
            if all(c == '' or c == 'nan' for c in cells[:5]):
                continue
            
            primeira_celula = cells[0].upper() if len(cells) > 0 else ''
            if any(k in primeira_celula for k in ['Nº DA DEMANDA', 'ACOMPANHAMENTO', 'SOLUÇÃO', 'CONTROLE', 'NIPS', 'DIA ABERTURA', 'PREENCHIMENTO']):
                continue
            
            colunas_preenchidas = sum(1 for c in cells if c and c.strip() != '')
            
            if colunas_preenchidas >= 15:
                # Estrutura NIP completa
                # Col 4 = 5 Dias, Col 5 = 10 Dias, Col 9 = Analista, Col 11 = Status Tratativa, Col 14 = Status NIP, Col 17 = Categorização
                if len(cells) > 17 and cells[0]:
                    dados_limpos.append({
                        'Data_Abertura': cells[0],
                        'Data_5_Dias': cells[4] if len(cells) > 4 else '',
                        'Data_10_Dias': cells[5] if len(cells) > 5 else '',
                        'N_Demanda': cells[1] if len(cells) > 1 else '',
                        'Analista_Redistribuido': cells[9] if len(cells) > 9 else '',
                        'Status_Tratativa': cells[11] if len(cells) > 11 else '',
                        'Status_NIP': cells[14] if len(cells) > 14 else '',
                        'Categorizacao_Parecer': cells[17].upper() if len(cells) > 17 else '',
                        'Tipo': 'NIP'
                    })
            elif colunas_preenchidas >= 6:
                # Estrutura PÓS NIP
                if len(cells) > 6:
                    dados_limpos.append({
                        'Data_Abertura': cells[1] if len(cells) > 1 else '',
                        'Data_5_Dias': '',
                        'Data_10_Dias': '',
                        'N_Demanda': cells[0] if len(cells) > 0 else '',
                        'Analista_Redistribuido': cells[3] if len(cells) > 3 else '',
                        'Status_Tratativa': cells[6] if len(cells) > 6 else '',
                        'Status_NIP': '',
                        'Categorizacao_Parecer': '',
                        'Tipo': 'PÓS NIP'
                    })
        
        if len(dados_limpos) == 0:
            return None
        
        df_final = pd.DataFrame(dados_limpos)
        
        # Função robusta para converter datas
        def converter_data(data_str):
            if not data_str or str(data_str).strip() == '' or str(data_str).lower() == 'nan':
                return None
            try:
                return pd.to_datetime(data_str, format='mixed', dayfirst=False)
            except:
                try:
                    return pd.to_datetime(data_str, dayfirst=True)
                except:
                    return None
        
        df_final['Data_Abertura'] = df_final['Data_Abertura'].apply(converter_data)
        df_final['Data_5_Dias'] = df_final['Data_5_Dias'].apply(converter_data)
        df_final['Data_10_Dias'] = df_final['Data_10_Dias'].apply(converter_data)
        
        df_final = df_final.dropna(subset=['Data_Abertura'])
        
        if len(df_final) == 0:
            return None
        
        df_final['MesAno'] = df_final['Data_Abertura'].dt.to_period('M').astype(str)
        df_final = df_final[df_final['Analista_Redistribuido'].str.strip() != '']
        
        return df_final
        
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Sidebar
with st.sidebar:
    st.header("📁 Upload do Arquivo")
    uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=['xlsx'])
    
    if uploaded_file is None:
        st.info("👆 Faça upload do arquivo para continuar")
        st.stop()
    
    st.markdown("---")
    st.header("🔍 Filtros")
    
    df = carregar_dados(uploaded_file)
    
    if df is None or len(df) == 0:
        st.error("❌ Nenhum dado válido encontrado no arquivo!")
        st.stop()
    
    st.success(f"✅ {len(df)} registros carregados!")
    
    st.markdown("---")
    
    # ========== FILTRO ÚNICO: 5 DIAS ==========
    st.subheader("📅 Filtro: 5 Dias")
    data_5_dias = st.date_input(
        "Selecione a data (5 Dias):",
        value=None,
        format="DD/MM/YYYY",
        key="filtro_5_dias"
    )
    
    # ========== FILTRO ÚNICO: 10 DIAS ==========
    st.subheader("📅 Filtro: 10 Dias")
    data_10_dias = st.date_input(
        "Selecione a data (10 Dias):",
        value=None,
        format="DD/MM/YYYY",
        key="filtro_10_dias"
    )
    
    # Outros Filtros
    st.markdown("---")
    st.subheader("🔧 Outros Filtros")
    
    analistas = sorted(df['Analista_Redistribuido'].dropna().unique())
    analista_sel = st.selectbox("👤 Analista/Redistribuído para:", ['TODOS'] + list(analistas))
    
    status_tratativa = sorted(df['Status_Tratativa'].dropna().unique())
    status_trat_sel = st.selectbox("📋 Status da Tratativa:", ['TODOS'] + list(status_tratativa))
    
    status_nip = sorted(df['Status_NIP'].dropna().unique())
    status_nip_sel = st.selectbox("✅ Status da NIP:", ['TODOS'] + list(status_nip))
    
    categorizacoes = sorted(df['Categorizacao_Parecer'].dropna().unique())
    categorizacao_sel = st.selectbox("📝 Categorização do Parecer:", ['TODOS'] + list(categorizacoes))
    
    # ========== APLICAÇÃO DOS FILTROS ==========
    df_f = df.copy()
    
    # Filtro único de 5 Dias
    if data_5_dias:
        df_f = df_f[df_f['Data_5_Dias'].dt.date == data_5_dias]
        st.info(f" Filtrando 5 Dias: **{data_5_dias.strftime('%d/%m/%Y')}**")
    
    # Filtro único de 10 Dias
    if data_10_dias:
        df_f = df_f[df_f['Data_10_Dias'].dt.date == data_10_dias]
        st.info(f" Filtrando 10 Dias: **{data_10_dias.strftime('%d/%m/%Y')}**")
    
    if analista_sel != 'TODOS':
        df_f = df_f[df_f['Analista_Redistribuido'] == analista_sel]
    
    if status_trat_sel != 'TODOS':
        df_f = df_f[df_f['Status_Tratativa'] == status_trat_sel]
    
    if status_nip_sel != 'TODOS':
        df_f = df_f[df_f['Status_NIP'] == status_nip_sel]
    
    if categorizacao_sel != 'TODOS':
        df_f = df_f[df_f['Categorizacao_Parecer'] == categorizacao_sel]
    
    st.markdown("---")
    st.info(f"📊 Registros filtrados: **{len(df_f)}**")

# Área Principal
if uploaded_file is not None and df is not None:
    
    total = len(df_f)
    com_resp = len(df_f[df_f['Status_NIP'].str.contains('Com Resposta', case=False, na=False)]) if 'Status_NIP' in df_f.columns else 0
    sem_resp = total - com_resp
    com_rve = len(df_f[df_f['Categorizacao_Parecer'].str.contains('COM RVE', case=False, na=False)]) if 'Categorizacao_Parecer' in df_f.columns else 0
    sem_rve = len(df_f[df_f['Categorizacao_Parecer'].str.contains('SEM RVE', case=False, na=False)]) if 'Categorizacao_Parecer' in df_f.columns else 0
    pct_resp = (com_resp / total * 100) if total > 0 else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(label="Total de Casos", value=total)
    with col2:
        st.metric(label="Com Resposta", value=com_resp)
    with col3:
        st.metric(label="Sem Resposta", value=sem_resp)
    with col4:
        st.metric(label="Com RVE", value=com_rve)
    with col5:
        st.metric(label="Sem RVE", value=sem_rve)
    with col6:
        st.metric(label="% Resposta", value=f"{pct_resp:.1f}%")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Status da NIP")
        if 'Status_NIP' in df_f.columns:
            df_status = df_f[df_f['Status_NIP'] != '']['Status_NIP'].value_counts().reset_index()
            df_status.columns = ['Status', 'Qtd']
            if len(df_status) > 0:
                fig = px.pie(df_status, values='Qtd', names='Status', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados para este gráfico")
        else:
            st.info("Coluna Status_NIP não encontrada")
            
    with col2:
        st.subheader("📈 Evolução Mensal")
        df_evol = df_f.groupby('MesAno').size().reset_index(name='Qtd').sort_values('MesAno')
        if len(df_evol) > 0:
            fig = px.line(df_evol, x='MesAno', y='Qtd', markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
    st.subheader(" Categorização do Parecer")
    if 'Categorizacao_Parecer' in df_f.columns:
        df_cat = df_f[df_f['Categorizacao_Parecer'] != '']['Categorizacao_Parecer'].value_counts().reset_index()
        df_cat.columns = ['Categoria', 'Qtd']
        if len(df_cat) > 0:
            fig = px.bar(df_cat, x='Qtd', y='Categoria', orientation='h', color='Qtd', color_continuous_scale='Blues')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de categorização")
    else:
        st.info("Coluna Categorizacao_Parecer não encontrada")
            
    st.subheader("👥 Top 10 Analistas/Redistribuídos")
    df_anal = df_f.groupby('Analista_Redistribuido').size().reset_index(name='Total').sort_values('Total', ascending=False).head(10)
    if len(df_anal) > 0:
        fig = px.bar(df_anal, x='Analista_Redistribuido', y='Total', color='Total', color_continuous_scale='Reds')
        fig.update_layout(showlegend=False, xaxis_tickangle=-45, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    st.subheader("📋 Status da Tratativa")
    if 'Status_Tratativa' in df_f.columns:
        df_trat = df_f[df_f['Status_Tratativa'] != '']['Status_Tratativa'].value_counts().reset_index()
        df_trat.columns = ['Status', 'Qtd']
        if len(df_trat) > 0:
            fig = px.bar(df_trat, x='Qtd', y='Status', orientation='h', color='Qtd', color_continuous_scale='Viridis')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de status da tratativa")
        
    st.subheader("📋 Tabela de Dados Completa")
    with st.expander("Clique para ver a tabela completa"):
        df_exibicao = df_f.copy()
        for col in ['Data_Abertura', 'Data_5_Dias', 'Data_10_Dias']:
            if col in df_exibicao.columns:
                df_exibicao[col] = df_exibicao[col].dt.strftime('%d/%m/%Y')
        
        st.dataframe(
            df_exibicao,
            use_container_width=True,
            height=400
        )
        
        st.markdown("""
        **Legenda das Colunas Principais:**
        - **Data_Abertura**: Data de abertura da demanda
        - **Data_5_Dias**: Data do prazo de 5 dias
        - **Data_10_Dias**: Data do prazo de 10 dias
        - **Analista_Redistribuido**: Analista/Redistribuído para
        - **Status_Tratativa**: Status da tratativa
        - **Status_NIP**: Status da NIP
        - **Categorizacao_Parecer**: Categorização do parecer
        """)