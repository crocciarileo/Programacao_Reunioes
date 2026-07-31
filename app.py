import re
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Gerador da Programação (S-140-T)", page_icon="📋", layout="wide"
)

st.title("📋 Gerador Automático de Programação (S-140-T)")
st.subheader(
    "Suba um ou mais arquivos .RTF das semanas do mês para gerar a programação."
)

# Permite subir MÚLTIPLOS arquivos RTF de uma vez
uploaded_files = st.file_uploader(
    "Escolha os arquivos .RTF das semanas (pode selecionar vários)",
    type=["rtf"],
    accept_multiple_files=True,
)


def decode_and_clean_rtf(rtf_bytes):
    text = rtf_bytes.decode("latin-1", errors="ignore")

    # 1. Remove tags de HYPERLINK e urls do RTF antes de extrair o texto
    text = re.sub(r"\{\\field\{\\\*\\fldinst\s*\{HYPERLINK[^\}]+\}\}\s*\{\\fldrslt\s*\{([^\}]+)\}\}\}", r"\1", text)
    text = re.sub(r"HYPERLINK\s+\"[^\"]+\"", "", text)

    # 2. Converte acentuação unicode do RTF (\u227? -> ã)
    def replace_unicode(match):
        code = int(match.group(1))
        return chr(code)

    text = re.sub(r"\\u(\d+)\?", replace_unicode, text)

    # 3. Limpa comandos e tags RTF (\par, \f0, \cf1, etc.)
    text = re.sub(r"\\[a-zA-Z0-9]+\b\s?", " ", text)
    text = re.sub(r"[{}]", "", text)

    # 4. Normaliza espaços múltiplos e remove códigos soltos
    text = " ".join(text.split())
    text = text.replace("*", "").strip()

    return text


def parse_rtf_week(clean_text):
    # Procura a data da semana (ex: 2 a 8 de novembro (Jeremias 49 a 50))
    week_match = re.search(
        r"(\d{1,2}\s+a\s+\d{1,2}\s+de\s+[a-zçáéíóúâêôãõ]+\s*\([^)]+\))",
        clean_text,
        re.IGNORECASE,
    )
    week_title = week_match.group(1).strip() if week_match else "Semana da Reunião"

    # Extração de Cânticos
    songs = re.findall(r"Cântico\s+\d+", clean_text, re.IGNORECASE)
    song_start = songs[0] if len(songs) > 0 else "Cântico"
    song_mid = songs[1] if len(songs) > 1 else "Cântico"
    song_end = songs[2] if len(songs) > 2 else "Cântico"

    # Captura todas as partes numeradas (ex: 1. Tema da parte (10 min))
    raw_parts = re.findall(
        r"(\d{1,2}\.\s*[^0-9\•\n\r]+?\(\d+\s*min\))", clean_text
    )

    seen_nums = set()
    clean_parts = []
    for p in raw_parts:
        p_str = " ".join(p.split())
        num_str = p_str.split(".")[0].strip()
        if num_str.isdigit() and num_str not in seen_nums:
            seen_nums.add(num_str)
            clean_parts.append((int(num_str), p_str))

    clean_parts.sort(key=lambda x: x[0])

    tesouros = [p[1] for p in clean_parts if 1 <= p[0] <= 3]
    ministerio = [p[1] for p in clean_parts if 4 <= p[0] <= 6]
    vida = [p[1] for p in clean_parts if p[0] >= 7]

    return {
        "title": week_title,
        "song_start": song_start,
        "song_mid": song_mid,
        "song_end": song_end,
        "tesouros": tesouros,
        "ministerio": ministerio,
        "vida": vida,
    }


if uploaded_files:
    try:
        weeks_data = []
        # Processa cada arquivo RTF enviado
        for file in uploaded_files:
            raw_bytes = file.read()
            clean_text = decode_and_clean_rtf(raw_bytes)
            week_info = parse_rtf_week(clean_text)
            weeks_data.append(week_info)

        st.success(f"{len(weeks_data)} semana(s) carregada(s) com sucesso!")

        st.markdown("---")
        st.header("Preencha apenas os Nomes dos Irmãos")

        tab_names = [f"Semana {i+1}" for i in range(len(weeks_data))]
        tabs = st.tabs(tab_names)

        form_data = []

        for idx, tab in enumerate(tabs):
            week = weeks_data[idx]
            with tab:
                st.markdown(f"### 🗓️ {week['title']}")

                col1, col2 = st.columns(2)
                with col1:
                    pres = st.text_input(
                        "Presidente",
                        key=f"pres_{idx}",
                        placeholder="Nome do irmão",
                    )
                with col2:
                    or_ini = st.text_input(
                        "Oração Inicial",
                        key=f"or_ini_{idx}",
                        placeholder="Nome do irmão",
                    )

                st.markdown("**TESOUROS DA PALAVRA DE DEUS**")
                t_des = []
                for p_idx, part_title in enumerate(week["tesouros"]):
                    val = st.text_input(
                        part_title,
                        key=f"t_{idx}_{p_idx}",
                        placeholder="Nome do irmão",
                    )
                    t_des.append((part_title, val))

                st.markdown("**FAÇA SEU MELHOR NO MINISTÉRIO**")
                m_des = []
                for p_idx, part_title in enumerate(week["ministerio"]):
                    val = st.text_input(
                        part_title,
                        key=f"m_{idx}_{p_idx}",
                        placeholder="Nome(s)",
                    )
                    m_des.append((part_title, val))

                st.markdown("**NOSSA VIDA CRISTÃ**")
                v_des = []
                for p_idx, part_title in enumerate(week["vida"]):
                    val = st.text_input(
                        part_title,
                        key=f"v_{idx}_{p_idx}",
                        placeholder="Nome / Dirigente e Leitor",
                    )
                    v_des.append((part_title, val))

                or_fim = st.text_input(
                    "Oração Final",
                    key=f"or_fim_{idx}",
                    placeholder="Nome do irmão",
                )

                form_data.append({
                    "week": week,
                    "pres": pres,
                    "or_ini": or_ini,
                    "or_fim": or_fim,
                    "t_des": t_des,
                    "m_des": m_des,
                    "v_des": v_des,
                })

        st.markdown("---")
        if st.button("🖨️ Visualizar e Salvar PDF Completo", type="primary"):
            html_pages = []

            for item in form_data:
                week = item["week"]

                def build_rows(des_list):
                    rows = ""
                    for part_title, val in des_list:
                        rows += f"<tr><td class='p-title'>{part_title}</td><td class='p-val'>{val}</td></tr>"
                    return rows

                page_html = f"""
                <div class="page-container">
                    <table class="header-table">
                        <tr>
                            <td class="cong-name">Ariranha</td>
                            <td class="week-info">{week['title']}</td>
                        </tr>
                    </table>
                    <div class="doc-title">Programação da reunião do meio de semana</div>
                    <table class="roles-bar">
                        <tr>
                            <td><b>Presidente:</b> {item['pres']}</td>
                            <td style="text-align:right;"><b>Oração:</b> {item['or_ini']}</td>
                        </tr>
                    </table>
                    <div class="song-row">• {week['song_start']} &nbsp;|&nbsp; • Comentários iniciais (1 min)</div>
                    
                    <div class="section-header tesouros">TESOUROS DA PALAVRA DE DEUS <span style="float:right; font-weight:normal;">Salão principal</span></div>
                    <table class="program-table">{build_rows(item['t_des'])}</table>
                    
                    <div class="section-header ministerio">FAÇA SEU MELHOR NO MINISTÉRIO <span style="float:right; font-weight:normal;">Salão principal</span></div>
                    <table class="program-table">{build_rows(item['m_des'])}</table>
                    
                    <div class="section-header vida">NOSSA VIDA CRISTÃ</div>
                    <div class="song-row">• {week['song_mid']}</div>
                    <table class="program-table">{build_rows(item['v_des'])}</table>
                    
                    <div class="song-row">• Comentários finais (3 min) &nbsp;|&nbsp; • {week['song_end']}</div>
                    <table class="footer-roles">
                        <tr>
                            <td><b>Oração:</b> {item['or_fim']}</td>
                            <td style="text-align:right; color:#64748b; font-size:8pt;">S-140-T 11/23</td>
                        </tr>
                    </table>
                </div>
                """
                html_pages.append(page_html)

            full_preview = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    @media print {{
                        button {{ display: none !important; }}
                        .page-container {{ page-break-after: always; }}
                        .page-container:last-child {{ page-break-after: avoid; }}
                    }}
                    body {{ font-family: Arial, sans-serif; font-size: 9.5pt; color: #000; margin: 10px; }}
                    .page-container {{ background: white; padding: 15px; margin-bottom: 20px; border: 1px solid #ccc; }}
                    .header-table {{ width: 100%; margin-bottom: 6px; }}
                    .cong-name {{ font-size: 13pt; font-weight: bold; }}
                    .week-info {{ font-size: 11pt; font-weight: bold; color: #2563eb; text-align: right; }}
                    .doc-title {{ font-size: 12pt; font-weight: bold; text-align: center; margin: 6px 0 10px 0; text-transform: uppercase; border-bottom: 2px solid #2563eb; padding-bottom: 4px; }}
                    .roles-bar {{ width: 100%; margin-bottom: 8px; background: #f8fafc; border: 1px solid #cbd5e1; padding: 4px 8px; }}
                    .section-header {{ color: #fff; font-weight: bold; padding: 4px 6px; margin-top: 8px; font-size: 9pt; }}
                    .tesouros {{ background: #52606d; }}
                    .ministerio {{ background: #c17d11; }}
                    .vida {{ background: #962525; }}
                    .program-table {{ width: 100%; border-collapse: collapse; }}
                    .program-table td {{ padding: 5px 6px; border-bottom: 1px solid #f1f5f9; }}
                    .p-title {{ text-align: left; }}
                    .p-val {{ text-align: right; font-weight: bold; width: 38%; }}
                    .song-row {{ font-weight: bold; background: #f8fafc; padding: 4px 6px; font-size: 8.5pt; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; margin: 5px 0; }}
                    .footer-roles {{ width: 100%; margin-top: 12px; border-top: 1px solid #cbd5e1; padding-top: 4px; }}
                    .print-btn {{
                        background: #2563eb; color: white; border: none; padding: 12px 20px;
                        font-size: 14px; font-weight: bold; border-radius: 6px; cursor: pointer;
                        margin-bottom: 15px; width: 100%;
                    }}
                </style>
            </head>
            <body>
                <button class="print-btn" onclick="window.print()">🖨️ CLIQUE AQUI PARA SALVAR EM PDF / IMPRIMIR</button>
                {"".join(html_pages)}
            </body>
            </html>
            """

            components.html(full_preview, height=800, scrolling=True)
    except Exception as e:
        st.error(f"Erro ao processar os arquivos .RTF: {e}")