import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import json
import os
import time
def adicionar_recursos_extras():
    temperatura = st.sidebar.slider("Smart Levels", 0.0, 1.0, 0.7)
    estilo = st.sidebar.selectbox(
        "Style.IA (still in test. BETA)",
        ["Realista", "Cartoon", "Anime", "Cyberpunk", "Frutiger aero style", "Pintura a óleo", "Aquarela", "Surrealista", "Pixel art"]
    )
    audio = st.audio_input("Fale algo para o Codex responder na função de Áudio Inteligente:")
    return temperatura, estilo, audio

# ativa os controles extras do sidebar (slider / estilo / audio)
temperatura, estilo, audio = adicionar_recursos_extras()

# Nome do arquivo que vai guardar as conversas no seu PC
ARQUIVO_SALVO = "historico_codex.json"
NOTAS_ATUALIZACAO = "Notas da atualização: agora Codex mostra 'pensando...' por 2s antes de responder e gera imagens com prompt melhorado."

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Codex.AI", page_icon="🚀", layout="centered")

# --- MENU LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://gstatic.com", width=60)
    st.title("🤖 Codex.AI")
    st.caption("Codex: Uma IA incrivel para conversas do dia a dia, gerar imagens e se divertir!🚀")
    st.markdown("---")
    tema = st.selectbox("Tema do Site", ["Escuro", "White"])
    st.subheader("📊 Ficha Técnica")
    st.markdown("* **Modelo de Texto/Visão:** Gemini-2.5-Flash\n* **Modelo de Imagem:** Flux-Architecture")

    estilo_divertido = st.selectbox(
        "Modo divertido",
        ["Normal", "Futurista", "Anime", "Retrô"]
    )

    if st.button("🎲 IDEIAS"):
        st.session_state.ultima_ideia = "desenhe um gato robô voando sobre uma cidade neon"

    if "ultima_ideia" in st.session_state:
        st.info(f"💡 Experimente: {st.session_state.ultima_ideia}")

    tema_escuro = st.checkbox("Tema Blackout", value=True)

    st.write("DICA: Vc ja testou os truques da IA? peça para ela desenhar um gato astronauta na lua ou analisar uma foto sua junto com uma pergunta! 🚀")

    st.markdown("---")
    
    # Botão caso você queira apagar o histórico e começar do zero
    if st.button("🗑️ Limpar Conversa Salva"):
        if os.path.exists(ARQUIVO_SALVO):
            os.remove(ARQUIVO_SALVO)
        st.session_state.historico_codex = []
        st.rerun()

if tema == "White":
    fundo = "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #dbeafe 100%)"
    painel = "rgba(255, 255, 255, 0.92)"
    texto = "#111111"
else:
    fundo = "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%)"
    painel = "rgba(255, 255, 255, 0.04)"
    texto = "#f8fafc"

st.markdown(f"""
    <style>
    .stApp {{ background: {fundo}; }}
    div[data-testid="stSidebar"], .stChatMessage, div[data-testid="stFileUploader"] {{
        background: {painel} !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
    }}
    h1, h2, h3, p, span, label {{ color: {texto} !important; font-family: 'Inter', sans-serif; }}
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE MEMÓRIA (CARREGAR E SALVAR) ---
if "historico_codex" not in st.session_state:
    if os.path.exists(ARQUIVO_SALVO):
        with open(ARQUIVO_SALVO, "r", encoding="utf-8") as f:
            st.session_state.historico_codex = json.load(f)
    else:
        st.session_state.historico_codex = []

def guardar_conversa():
    # Guarda apenas os textos para não dar erro no arquivo salvo
    mensagens_texto = [msg for msg in st.session_state.historico_codex if msg["type"] == "text"]
    with open(ARQUIVO_SALVO, "w", encoding="utf-8") as f:
        json.dump(mensagens_texto, f, ensure_ascii=False, indent=4)

# --- CORPO PRINCIPAL DO CHAT ---
st.title("🚀 Codex.AI BETA VERSION")
st.caption("Modelos usados: Gemini-2.5-Flash para conversa e Flux-Architecture para imagem")
st.info(f"👋 Bem-vindo ao Codex.IA {NOTAS_ATUALIZACAO}")

# Exibe o histórico salvo na tela
for item in st.session_state.historico_codex:
    with st.chat_message(item["role"]):
        st.write(item["content"])

# Caixa para enviar fotos
foto_enviada = st.file_uploader("📸 Envie uma foto para o Codex analisar junto com seu texto:", type=["png", "jpg", "jpeg"])

# Caixa de Entrada de Texto
pergunta = st.chat_input("DICA: Codex.IA esta em desenvolvimento na versao teste e pode apresentar BUGS")

if pergunta:
    texto_usuario = pergunta
    # Se tiver foto, avisa no balão do chat
    if foto_enviada:
        texto_usuario += f" 📸 [Foto anexada: {foto_enviada.name}]"
        
    with st.chat_message("user"):
        st.write(texto_usuario)
        if foto_enviada:
            st.image(Image.open(foto_enviada), width=300)
            
    st.session_state.historico_codex.append({"role": "user", "type": "text", "content": texto_usuario})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        # 🎨 MODO CRIAÇÃO DE IMAGENS (Flux)
        if any(termo in pergunta.lower() for termo in ["crie", "desenhe", "imagem", "foto de"]):
            placeholder.write("🎨 Conectando ao motor Flux... Criando sua arte! 🚀")
            try:
                texto_limpo = pergunta.lower()
                for termo in [
                    "crie a imagem de um", "crie a imagem de", "crie imagem de um", "crie imagem de",
                    "desenhe um", "desenhe uma", "desenhe o", "desenhe a", "desenhe", "faça uma foto de um", "faça um", "faça uma foto de", "faca uma foto de", "foto de um", "foto de uma", "foto do", "foto da", "foto de"
                ]:
                    texto_limpo = texto_limpo.replace(termo, "")
                texto_limpo = texto_limpo.strip().replace(" ", "%20")
                
                url_gerador = f"https://image.pollinations.ai/prompt/{texto_limpo}?width=1024&height=1024&model=flux"
                
                placeholder.empty()
                st.write(f"🖼️ Aqui está sua imagem para: **{texto_limpo.replace('%20', ' ')}**")
                st.image(url_gerador)
                st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": f"🖼️ Imagem gerada: {url_gerador}"})
                guardar_conversa()
            except Exception as e:
                placeholder.write(f"❌ Erro na imagem: {e}")
        
        # 🧠 MODO CONVERSA E VISÃO (Gemini-2.5-Flash Sem Bug de URL)
        else:
            placeholder.write("🔎 Codex está analisando...")
            time.sleep(1)  # Simula o "pensando..." por 1 segundos
            placeholder.write("DICA: Vc pode pedir para o Codex 'desenhar imagens!' ou 'analisar uma foto' junto com seu texto! 🚀")
            try:
                contexto_sistema = "Você é o Codex.AI, uma inteligência artificial criada por mim (pedro) incrível e descontraída rodando o modelo Gemini-2.5-Flash. Use bastantes emojis nas respostas e aja um pouco louca para ser mais divertido! Responda de forma clara, criativa e com uma pitada de humor. Se o usuário enviar uma foto, analise visualmente e responda considerando o conteúdo da imagem junto com a pergunta. Seja breve, objetivo e use muitos emojis para deixar a conversa leve e divertida!"
                
                # Monta os dados em formato de lista segura (JSON)
                dados_chat = [{"role": "system", "content": contexto_sistema}]
                for h in st.session_state.historico_codex:
                    dados_chat.append({"role": h["role"], "content": h["content"]})
                
                if foto_enviada:
                    dados_chat.append({"role": "user", "content": f"Analise visualmente a imagem anexada ({foto_enviada.name}). O usuário perguntou: {pergunta}"})

                # Envia de forma blindada (POST) com timeout e tratamento de erro
                try:
                    resposta_api = requests.post(
                        "https://pollinations.ai",
                        json={"messages": dados_chat, "model": "openai"},
                        timeout=20
                    )
                    if resposta_api.status_code == 200:
                        texto_final = resposta_api.text
                        placeholder.empty()
                        st.write(texto_final)
                        st.snow()  # Efeito de neve para deixar mais divertido! ❄️
                        st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": texto_final})
                        guardar_conversa()
                    else:
                        detalhe = resposta_api.text[:400]
                        placeholder.write(f"❌ Erro do servidor ({resposta_api.status_code}): {detalhe}")
                except requests.exceptions.Timeout:
                    # Fallback local quando o servidor demora demais
                    texto_final = f"Desculpe — o servidor demorou demais. Resposta rápida local: {pergunta}"
                    placeholder.empty()
                    st.write(texto_final)
                    st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": texto_final})
                    guardar_conversa()
                except Exception as e:
                    # Fallback local em caso de erro de conexão
                    texto_final = f"Desculpe — não foi possível conectar ao servidor ({e}). Resposta local: {pergunta}"
                    placeholder.empty()
                    st.write(texto_final)
                    st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": texto_final})
                    guardar_conversa()
            except Exception as e:
                placeholder.write(f"❌ Erro de conexão: {e}")
