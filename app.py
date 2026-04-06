import streamlit as st
import re
import pandas as pd
import requests
from urllib.parse import urlparse
from io import BytesIO

# --- 1. CONFIGURAÇÃO DA PÁGINA (Sempre no topo) ---
st.set_page_config(
    page_title="Mestre de Leads v37", 
    page_icon="🎯", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CSS DEFINITIVO (MATA DEPLOY, MANTÉM INTERFACE) ---
st.markdown("""
    <style>
    /* Esconde o botão Deploy e o menu Settings por ID de sistema */
    [data-testid="stHeaderDeployButton"], .stDeployButton, #MainMenu, [data-testid="stStatusWidget"], footer {
        display: none !important;
        visibility: hidden !important;
    }
    /* Estiliza o botão de abrir a barra lateral (Setinha) em azul */
    button[data-testid="stSidebarCollapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 9999999 !important;
        background-color: #002b36 !important;
        color: white !important;
        border-radius: 6px !important;
        width: 145px !important;
        height: 38px !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.3) !important;
        border: 1px solid #004a99 !important;
    }
    button[data-testid="stSidebarCollapsedControl"]::after {
        content: " CONFIGURAÇÕES";
        font-size: 11px;
        font-weight: bold;
        margin-left: 8px;
        color: white;
    }
    .block-container { padding-top: 3.5rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE INTELIGÊNCIA (RESTAURADA PARA VOLUME MÁXIMO) ---
PROVIDERS = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'uol.com.br', 'bol.com.br', 'ig.com.br', 'ibest.com.br', 'pop.com.br']
BAIRROS_SP = ["Moema", "Itaim Bibi", "Tatuapé", "Santana", "Pinheiros", "Morumbi", "Vila Mariana", "Lapa", "Mooca", "Ipiranga", "Jardins", "Santo Amaro"]
SETORES_UNIV = ["Centro", "Zona Sul", "Zona Norte", "Zona Leste", "Zona Oeste"]

class LeadMasterV37:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}
        self.trash = ['wixpress.com', 'sentry.io', 'test.com', 'xxxx', 'primer.com', 'template']

    def fetch_serper(self, query, num=100):
        payload = {"q": query, "num": int(num), "gl": "br", "hl": "pt-br"}
        try:
            res = requests.post("https://google.serper.dev/search", headers=self.headers, json=payload, timeout=15)
            return res.json().get('organic', []) if res.status_code == 200 else []
        except: return []

    def extract_emails(self, text):
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        raw = re.findall(pattern, str(text))
        return [e.lower().strip().strip('.') for e in raw if len(e) > 8 and not any(t in e.lower() for t in self.trash)]

# --- 4. PAINEL LATERAL ---
with st.sidebar:
    st.markdown('### 🛡️ PAINEL DE CONTROLE')
    st.divider()
    api_key_input = st.text_input("Sua API Key (Serper.dev)", value="60187e815fc00c46f468e0ebf541bf69617162a8", type="password")
    
    st.divider()
    nicho = st.text_input("Nicho / Segmento", placeholder="Ex: Pet shop")
    cidade = st.text_input("Cidade", placeholder="Ex: São Paulo")
    
    st.divider()
    modo_turbo = st.checkbox("Ativar Busca Setorial (Somar Bairros)", value=False)
    filtro_corp = st.toggle("Mostrar Apenas Corporativos", value=False)
    
    st.divider()
    if st.button("🔄 Reiniciar Sistema"):
        st.session_state.clear()
        st.rerun()

# --- 5. EXECUÇÃO ---
st.title("🎯 Mestre de Leads v37 | Recuperação de Volume")
st.markdown("---")

if st.button("🚀 INICIAR VARREDURA TOTAL"):
    if not nicho or not cidade:
        st.error("Preencha o Nicho e a Cidade!")
    else:
        hunter = LeadMasterV37(api_key_input)
        locais = [cidade]
        if modo_turbo:
            sub = BAIRROS_SP if cidade.lower() in ["são paulo", "sao paulo", "sp"] else SETORES_UNIV
            locais += [f"{s} {cidade}" for s in sub]
        
        all_found, seen_emails = [], set()
        bar = st.progress(0)
        status_msg = st.empty()
        counter_box = st.empty()

        for idx, loc in enumerate(locais):
            queries = [
                f'{nicho} {loc} email',
                f'{nicho} {loc} contato',
                f'{nicho} {loc} gmail.com',
                f'{nicho} {loc} hotmail.com'
            ]
            
            for q in queries:
                status_msg.info(f"📍 {loc} | Buscando: {q}")
                results = hunter.fetch_serper(q)
                
                for item in results:
                    snippet, title, link = item.get('snippet', ''), item.get('title', ''), item.get('link', '')
                    emails = hunter.extract_emails(f"{snippet} {title} {link}")
                    
                    if not emails and link.startswith("http") and "facebook.com" not in link:
                        try:
                            r = requests.get(link, timeout=3, headers={'User-Agent': 'Mozilla/5.0'})
                            emails = hunter.extract_emails(r.text)
                        except: pass
                    
                    for email in emails:
                        if email not in seen_emails:
                            all_found.append({
                                "Email": email,
                                "Empresa": title[:60],
                                "URL": link,
                                "Dominio": email.split('@')[-1]
                            })
                            seen_emails.add(email)
                            counter_box.success(f"🔥 Leads únicos na memória: {len(seen_emails)}")
            bar.progress((idx + 1) / len(locais))

        st.session_state.leads_data = all_found
        st.success(f"✅ FINALIZADO! {len(all_found)} leads encontrados.")

# --- 6. EXIBIÇÃO E DOWNLOAD EXCEL (.xlsx) ---
if 'leads_data' in st.session_state and st.session_state.leads_data:
    df_raw = pd.DataFrame(st.session_state.leads_data)
    
    # Aplica o filtro corporativo se ativo
    df_proc = df_raw[~df_raw['Dominio'].isin(PROVIDERS)].copy() if filtro_corp else df_raw.copy()
    
    # Adicionando colunas extras e numeração
    df_proc.insert(0, 'Nº', range(1, len(df_proc) + 1))
    df_proc['Conta de email'] = ""
    df_proc['Senha'] = ""
    
    # Seleção da ordem final das colunas
    df_final = df_proc[['Nº', 'Email', 'Empresa', 'URL', 'Conta de email', 'Senha']]
    
    st.divider()
    st.subheader(f"📊 Planilha: {len(df_final)} leads exibidos")
    st.dataframe(df_final, use_container_width=True)
    
    # Criando arquivo Excel com formatação personalizada
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Leads')
        
        # AJUSTE DE LARGURA DAS COLUNAS (Ajustado para serem mais largas)
        worksheet = writer.sheets['Leads']
        worksheet.column_dimensions['A'].width = 6   # Nº
        worksheet.column_dimensions['B'].width = 35  # Email
        worksheet.column_dimensions['C'].width = 45  # Empresa
        worksheet.column_dimensions['D'].width = 55  # URL
        worksheet.column_dimensions['E'].width = 35  # Conta de email (Ficou mais larga)
        worksheet.column_dimensions['F'].width = 25  # Senha (Ficou mais larga)
    
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 Baixar Leads em EXCEL (.xlsx)",
        data=excel_data,
        file_name=f"leads_{nicho}_{cidade}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )