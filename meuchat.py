import streamlit as st
import requests
from io import BytesIO
from PIL import Image
import json
import os
import time

API_COST_PER_1000_TOKENS = 0.002
DEFAULT_BILLING_DOLLARS = 5.0


def estimativa_tokens_por_dolar(dollar):
    return int((dollar / API_COST_PER_1000_TOKENS) * 1000)


def estimativa_mensagens(dollar, tokens_por_mensagem=200):
    return int(estimativa_tokens_por_dolar(dollar) / tokens_por_mensagem)


def estimativa_tokens_por_texto(texto):
    # Estimativa simples: 1 token ~ 0,75 palavras, arredondando para cima
    palavras = len(texto.split())
    return int(palavras * 1.3) + 10


def transcrever_audio(audio_file):
    """Transcreve áudio usando a API de áudio do OpenAI."""
    api_key = os.environ.get("OPENAI_API_KEY") or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    if not api_key:
        raise RuntimeError("Defina a variavel ambiente OPENAI_API_KEY antes de executar.")

    audio_file.seek(0)
    files = {
        "file": (audio_file.name, audio_file, audio_file.type)
    }
    data = {
        "model": "whisper-1"
    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    resp = requests.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data.get("text", "")

def adicionar_recursos_extras():
    temperatura = st.sidebar.slider("Smart Levels", 0.0, 1.0, 0.7)
    estilo = st.sidebar.selectbox(
        "Style.IA (still in test. BETA)",
        ["Realista", "Cartoon", "Anime", "Cyberpunk", "Frutiger aero style", "Pintura a óleo", "Aquarela", "Surrealista", "Pixel art"]
    )
    # Uploader de áudio para teste (mp3/wav). Substitui o inexistente `st.audio_input`.
    audio = st.sidebar.file_uploader("Envie áudio para o Codex (mp3/wav)", type=["mp3", "wav"])
    if audio:
        try:
            st.sidebar.audio(audio)
        except Exception:
            pass

        if st.sidebar.button("Transcrever áudio"):
            try:
                st.session_state.audio_transcricao = transcrever_audio(audio)
                st.session_state.audio_status = "Áudio transcrito com sucesso. Clique em enviar para usar a transcrição."
            except Exception as e:
                st.session_state.audio_status = f"Erro ao transcrever: {e}"

        if st.session_state.audio_status:
            st.sidebar.info(st.session_state.audio_status)

        if st.session_state.audio_transcricao:
            st.sidebar.markdown("**Transcrição atual:**")
            st.sidebar.write(st.session_state.audio_transcricao)
            if st.sidebar.button("Enviar áudio transcrito como mensagem"):
                st.session_state.enviar_audio_transcrito = True

    return temperatura, estilo, audio

# ativa os controles extras do sidebar (slider / estilo / audio)
temperatura, estilo, audio = adicionar_recursos_extras()


def send_openai_chat(dados_chat, temperatura=0.7):
    """Envia `dados_chat` para a API OpenAI Chat e retorna o texto gerado.
    Lê a chave em OPENAI_API_KEY (variável de ambiente) ou em st.secrets.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
    if not api_key:
        raise RuntimeError("Defina a variavel ambiente OPENAI_API_KEY antes de executar.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": dados_chat,
        "temperature": float(temperatura),
        "max_tokens": 800
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    # extrai texto da primeira escolha
    return data["choices"][0]["message"]["content"]


# Nome do arquivo que vai guardar as conversas no seu PC
ARQUIVO_SALVO = "historico_codex.json"
NOTAS_ATUALIZACAO = "Notas da atualização: agora Codex mostra 'pensando...' por 2s antes de responder e gera imagens com prompt melhorado."

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Codex.AI", page_icon="🚀", layout="centered")
api_key = os.environ.get("OPENAI_API_KEY") or (st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None)
if not api_key:
    st.warning("Defina a variavel ambiente OPENAI_API_KEY antes de executar.")

# --- MENU LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://gstatic.com", width=60)
    st.title("🤖 Codex.AI")
    st.caption("Codex: Uma IA incrivel para conversas do dia a dia, gerar imagens e se divertir!🚀")
    with st.expander("💰 Estimativa de custo da API"):
        st.write("OpenAI `gpt-3.5-turbo` custa cerca de US$0,002 por 1000 tokens.")
        budget_usd = st.number_input("Simular orçamento em dólares", min_value=1.0, max_value=50.0, value=DEFAULT_BILLING_DOLLARS, step=1.0)
        tokens = estimativa_tokens_por_dolar(budget_usd)
        mensagens = estimativa_mensagens(budget_usd)
        st.metric("Tokens estimados", f"{tokens:,}")
        st.metric("Mensagens estimadas", f"{mensagens:,}")
        st.write(f"Com US${budget_usd:.2f}, você tem aproximadamente {tokens:,} tokens.")
        st.write(f"Isso equivale a cerca de {mensagens:,} trocas de mensagem se cada conversa usar 200 tokens.")
        st.info("As imagens do app são geradas pelo Pollinations, então só o chat consome a quota da OpenAI. Áudio transcrito também consome tokens.")
    # Instruções rápidas para guardar a chave de forma segura
    with st.expander("Como salvar a chave de forma segura (recomendado)"):
        st.write("Para rodar localmente, cada pessoa precisa da própria chave OpenAI.")
        st.markdown("**1)** Defina a variável de ambiente `OPENAI_API_KEY` no seu terminal (PowerShell).")
        st.code('$env:OPENAI_API_KEY = "sk-SUA_CHAVE_AQUI"', language='powershell')
        st.markdown("**2)** Crie um arquivo local `.streamlit/secrets.toml` (não commitá-lo).")
        st.code('''mkdir .streamlit -Force
@"
OPENAI_API_KEY = "sk-SUA_CHAVE_AQUI"
"@ > .streamlit/secrets.toml''', language='powershell')
        st.markdown("**3)** Se você publicar no Streamlit Cloud, configure `OPENAI_API_KEY` nos Secrets do app.")
        st.write("O app não mostra mais um campo de chave temporária; isso evita risco de vazar o token.")
    st.markdown("---")
    tema = st.selectbox("Tema do Site", ["Escuro", "White"])
    modo_pijama = st.checkbox("🎉 Festa do pijama☁️", value=False)
    st.subheader("📊 Ficha Técnica")
    st.markdown("* **Modelo de Texto/Visão:** Gemini-2.5-Flash\n* **Modelo de Imagem:** Flux-Architecture")

    estilo_divertido = st.selectbox(
        "Modo divertido",
        ["Normal", "Futurista", "Anime", "Retrô"]
    )

    if modo_pijama:
        st.markdown("<div style='padding: 14px; border-radius: 18px; background: rgba(255,255,255,0.18); border: 1px dashed #d8b4fe; color: #2b1532;'>🎀 <strong>Modo Festa do Pijama ativado!</strong> Tudo fica mais macio, divertido e com nuvens. Peça uma história, um desenho fofo ou uma dica de travesseiro.</div>", unsafe_allow_html=True)
        if not st.session_state.get("pijama_balloons", False):
            st.balloons()
            st.session_state.pijama_balloons = True
        st.info("✨ Está tudo temático: nuvens, travesseiros e emojis suaves estão liberados.")
        if st.button("📖 Conta uma história de pijama"):
            st.session_state.pijama_story_request = True

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

extra_css = ""
extra_html = ""
if 'modo_pijama' in locals() and modo_pijama:
    fundo = "linear-gradient(135deg, #b4a7e7 0%, #c8b6ff 40%, #f7d9ff 100%)"
    painel = "rgba(255, 255, 255, 0.18)"
    texto = "#2b1532"
    extra_css = """
    @keyframes floaty {
        0% { transform: translateY(0px) translateX(0px); opacity: 0.9; }
        50% { transform: translateY(-12px) translateX(5px); opacity: 1; }
        100% { transform: translateY(0px) translateX(0px); opacity: 0.9; }
    }
    .pijama-cloud { position: fixed; width: 130px; height: 130px; background: rgba(255,255,255,0.24); border-radius: 50%; box-shadow: 0 12px 40px rgba(255,255,255,0.3); animation: floaty 12s ease-in-out infinite; z-index: 1; }
    .pijama-cloud:nth-child(1) { top: 8%; left: 5%; }
    .pijama-cloud:nth-child(2) { top: 20%; right: 8%; width: 100px; height: 100px; animation-delay: 2s; }
    .pijama-cloud:nth-child(3) { bottom: 18%; left: 12%; width: 120px; height: 120px; animation-delay: 4s; }
    .pijama-cloud:nth-child(4) { bottom: 10%; right: 18%; width: 90px; height: 90px; animation-delay: 6s; }
    .pijama-badge { position: fixed; top: 14%; right: 14%; z-index: 2; color: #5d2b7e; font-size: 19px; font-weight: 700; }
    .stApp {{ overflow: hidden; }}
    """
    extra_html = """
    <div class='pijama-cloud'></div>
    <div class='pijama-cloud'></div>
    <div class='pijama-cloud'></div>
    <div class='pijama-cloud'></div>
    <div class='pijama-badge'>☁️ Festa do Pijama ☁️</div>
    """

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
    {extra_css}
    </style>
    {extra_html}
""", unsafe_allow_html=True)

# --- SISTEMA DE MEMÓRIA (CARREGAR E SALVAR) ---
if "historico_codex" not in st.session_state:
    if os.path.exists(ARQUIVO_SALVO):
        with open(ARQUIVO_SALVO, "r", encoding="utf-8") as f:
            st.session_state.historico_codex = json.load(f)
    else:
        st.session_state.historico_codex = []

if "audio_transcricao" not in st.session_state:
    st.session_state.audio_transcricao = ""

if "audio_status" not in st.session_state:
    st.session_state.audio_status = ""

if "enviar_audio_transcrito" not in st.session_state:
    st.session_state.enviar_audio_transcrito = False

def guardar_conversa():
    # Guarda apenas os textos para não dar erro no arquivo salvo
    mensagens_texto = [msg for msg in st.session_state.historico_codex if msg["type"] == "text"]
    with open(ARQUIVO_SALVO, "w", encoding="utf-8") as f:
        json.dump(mensagens_texto, f, ensure_ascii=False, indent=4)

# --- CORPO PRINCIPAL DO CHAT ---
st.title("🚀 Codex.AI BETA VERSION")
if 'modo_pijama' in locals() and modo_pijama:
    st.markdown("### 🌙 Bem-vindo à Festa do Pijama ☁️\nVamos conversar como se estivéssemos em uma noite de travesseiros e nuvens.")
st.caption("Modelos usados: Gemini-2.5-Flash para conversa e Flux-Architecture para imagem")
st.info(f"👋 Bem-vindo ao Codex.IA {NOTAS_ATUALIZACAO}")

# Exibe o histórico salvo na tela
for item in st.session_state.historico_codex:
    with st.chat_message(item["role"]):
        st.write(item["content"])

# Caixa para enviar fotos
foto_enviada = st.file_uploader("📸 Envie uma foto para o Codex analisar junto com seu texto:", type=["png", "jpg", "jpeg"])

# Caixa de Entrada de Texto
if st.session_state.get("pijama_story_request", False):
    pergunta = "Conte uma história de festa do pijama com travesseiros, nuvens, emojis fofos e muita diversão."
    st.session_state.pijama_story_request = False
else:
    pergunta = st.chat_input("DICA: Codex.IA esta em desenvolvimento na versao teste e pode apresentar BUGS")

if st.session_state.enviar_audio_transcrito and st.session_state.audio_transcricao:
    pergunta = st.session_state.audio_transcricao
    st.session_state.enviar_audio_transcrito = False

if pergunta:
    texto_usuario = pergunta
    audio_transcricao = None
    # Se tiver áudio, tenta transcrever primeiro
    if audio:
        try:
            audio_transcricao = transcrever_audio(audio)
            texto_usuario += f" 🎧 [Áudio anexado: {audio.name}]"
        except Exception as e:
            st.sidebar.error(f"Não foi possível transcrever o áudio: {e}")

    # Se tiver foto, avisa no balão do chat
    if foto_enviada:
        texto_usuario += f" 📸 [Foto anexada: {foto_enviada.name}]"
        
    with st.chat_message("user"):
        st.write(texto_usuario)
        if foto_enviada:
            st.image(Image.open(foto_enviada), width=300)
        if audio_transcricao:
            st.write(f"📝 Transcrição do áudio: {audio_transcricao}")
            st.info("O áudio foi transcrito automaticamente e será usado na resposta.")
            texto_usuario += f"\n\nTranscrição do áudio: {audio_transcricao}"
            st.session_state.historico_codex.append({"role": "user", "type": "text", "content": texto_usuario})
        else:
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
            with st.spinner("🔎 Codex está analisando..."):
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
                    if modo_pijama:
                        dados_chat.append({"role": "system", "content": "Você está em uma festa do pijama, responda com diversão, emojis fofos e referências a nuvens, travesseiros e histórias noturnas."})

                    # Envia usando OpenAI Chat (leitura da chave em OPENAI_API_KEY)
                    try:
                        texto_final = send_openai_chat(dados_chat, temperatura=temperatura)
                        placeholder.empty()
                        st.write(texto_final)
                        st.snow()
                        st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": texto_final})
                        guardar_conversa()
                    except RuntimeError as e:
                        placeholder.write(f"❌ {e}")
                    except requests.exceptions.Timeout:
                        # Fallback local quando o servidor demora demais
                        texto_final = f"Desculpe — o servidor demorou demais. Resposta rápida local: {pergunta}"
                        placeholder.empty()
                        st.write(texto_final)
                        st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": texto_final})
                        guardar_conversa()
                    except requests.exceptions.HTTPError as e:
                        resp = getattr(e, 'response', None)
                        detalhe = resp.text[:400] if resp is not None else str(e)
                        placeholder.write(f"❌ Erro HTTP: {detalhe}")
                    except Exception as e:
                        # Fallback local em caso de erro de conexão
                        texto_final = f"Desculpe — não foi possível conectar ao servidor ({e}). Resposta local: {pergunta}"
                        placeholder.empty()
                        st.write(texto_final)
                        st.session_state.historico_codex.append({"role": "assistant", "type": "text", "content": texto_final})
                        guardar_conversa()
                except Exception as e:
                    placeholder.write(f"❌ Erro de conexão: {e}")
