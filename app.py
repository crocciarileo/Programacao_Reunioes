import re
import pypdf
import streamlit as st
import weasyprint

st.set_page_config(
    page_title="Gerador da Programação (S-140-T)", page_icon="📋", layout="wide"
)

st.title("📋 Gerador de Programação da Reunião (S-140-T)")
st.subheader("Suba o PDF da Apostila do Mês para gerar as folhas de reunião.")

# 1. UPLOAD DO PDF DA APOSTILA
uploaded_file = st.file_uploader(
    "Escolha o PDF da Apostila do Mês (mwb_T_...pdf)", type=["pdf"]
)


def parse_pdf(file_bytes):
    reader = pypdf.PdfReader(file_bytes)
    full_text = ""
    for page in reader.pages:
        txt = page.extract_text() or ""
        full_text += txt + "\n"

    # Quebra o texto pelas datas das semanas
    weeks_raw = re.split(
        r"(\d{1,2}\s*[-–]\s*\d{1,2}\s+DE\s+[A-ZÇÁÉÍÓÚÂÊÔÃÕ]+)",
        full_text,
        flags=re.IGNORECASE,
    )

    weeks = []
    if len(weeks_raw) > 1:
        for i in range(1, len(weeks_raw), 2):
            header = weeks_raw[i].strip()
            content = weeks_raw[i + 1] if i + 1 < len(weeks_raw) else ""

            # Extrai texto de leitura bíblica
            line_match = re.search(r"\|\s*([A-Z0-9\s-–]+)", content)
            reading = line_match.group(1).strip() if line_match else ""

            # Extrai Cânticos
            songs = re.findall(r"Cântico\s+\d+", content, re.IGNORECASE)
            song_start = songs[0] if len(songs) > 0 else "Cântico"
            song_mid = songs[1] if len(songs) > 1 else "Cântico"
            song_end = songs[2] if len(songs) > 2 else "Cântico"

            # Extrai Partes
            parts = re.findall(
                r"(\d\.\s*[^0-9\n\•]+?\(\d+\s*min\))", content
            )

            tesouros = [p for p in parts if p.startswith(("1.", "2.", "3."))]
            ministerio = [p for p in parts if p.startswith(("4.", "5.", "6."))]
            vida = [p for p in parts if p.startswith(("7.", "8.", "9."))]

            weeks.append({
                "title": f"{header} | {reading}",
                "song_start": song_start,
                "song_mid": song_mid,
                "song_end": song_end,
                "tesouros": tesouros,
                "ministerio": ministerio,
                "vida": vida,
            })
    return weeks


if uploaded_file:
    weeks_data = parse_pdf(uploaded_file)
    st.success(f"{len(weeks_data)} semanas extraídas com sucesso!")

    # FORMULÁRIO DAS DESIGNAÇÕES POR SEMANA
    st.markdown("---")
    st.header("Preencha os Irmãos Designados")

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
                    f"Presidente", key=f"pres_{idx}", placeholder="Nome"
                )
            with col2:
                or_ini = st.text_input(
                    f"Oração Inicial", key=f"or_ini_{idx}", placeholder="Nome"
                )

            st.markdown("**TESOUROS DA PALAVRA DE DEUS**")
            t_designations = {}
            for p in week["tesouros"]:
                t_designations[p[0]] = st.text_input(
                    p, key=f"p_{idx}_{p[0]}", placeholder="Nome do irmão"
                )

            st.markdown("**FAÇA SEU MELHOR NO MINISTÉRIO**")
            m_designations = {}
            for p in week["ministerio"]:
                m_designations[p[0]] = st.text_input(
                    p, key=f"p_{idx}_{p[0]}", placeholder="Nome(s)"
                )

            st.markdown("**NOSSA VIDA CRISTÃ**")
            v_designations = {}
            for p in week["vida"]:
                label = (
                    f"{p} (Dirigente/Leitor)"
                    if "Estudo bíblico" in p
                    else p
                )
                v_designations[p[0]] = st.text_input(
                    label, key=f"p_{idx}_{p[0]}", placeholder="Nome(s)"
                )

            or_fim = st.text_input(
                f"Oração Final", key=f"or_fim_{idx}", placeholder="Nome"
            )

            form_data.append({
                "week": week,
                "pres": pres,
                "or_ini": or_ini,
                "or_fim": or_fim,
                "t_des": t_designations,
                "m_des": m_designations,
                "v_des": v_designations,
            })

    # GERAR O PDF FINAL
    st.markdown("---")
    if st.button("🖨️ Gerar PDF Completo do Mês", type="primary"):
        html_pages = []

        for item in form_data:
            week = item["week"]

            def build_rows(parts_list, des_dict):
                rows = ""
                for p in parts_list:
                    val = des_dict.get(p[0], "")
                    rows += f"<tr><td class='p-title'>{p}</td><td class='p-val'>{val}</td></tr>"
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
                <table class="program-table">{build_rows(week['tesouros'], item['t_des'])}</table>
                
                <div class="section-header ministerio">FAÇA SEU MELHOR NO MINISTÉRIO <span style="float:right; font-weight:normal;">Salão principal</span></div>
                <table class="program-table">{build_rows(week['ministerio'], item['m_des'])}</table>
                
                <div class="section-header vida">NOSSA VIDA CRISTÃ</div>
                <div class="song-row">• {week['song_mid']}</div>
                <table class="program-table">{build_rows(week['vida'], item['v_des'])}</table>
                
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

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4 portrait; margin: 10mm 12mm; }}
                body {{ font-family: Arial, sans-serif; font-size: 9.5pt; color: #000; margin: 0; }}
                .page-container {{ page-break-after: always; }}
                .page-container:last-child {{ page-break-after: avoid; }}
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
            </style>
        </head>
        <body>{"".join(html_pages)}</body>
        </html>
        """

        pdf_bytes = weasyprint.HTML(string=full_html).write_pdf()

        st.download_button(
            label="📥 Baixar Programação do Mês em PDF",
            data=pdf_bytes,
            file_name="Programacao_Reunioes.pdf",
            mime="application/pdf",
        )