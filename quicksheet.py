import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import tempfile
import os

# ----- Font Ayarı -----
font_path = os.path.join("fonts", "times.ttf")
pdfmetrics.registerFont(TTFont("TNR", font_path))

# ----- API Ayarı -----
client = Groq(api_key="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")

# ----- Uygulama Başlığı -----
st.set_page_config(page_title="QuickSheet", page_icon="⚡")
st.title("⚡ QuickSheet: AI Destekli Worksheet Hazırlayıcı")

# ----- Giriş Alanları -----
tab1, tab2 = st.tabs(["🌍 Seviye Bazlı", "📘 MEB Müfredatlı"])

with tab1:
    level = st.selectbox("Dil Seviyesi", ["A1", "A2", "B1", "B2", "C1"])
    topic = st.text_input("Konu (örnek: 'Passive Voice')")
    skill = st.selectbox("Beceri", ["Reading", "Grammar", "Vocabulary", "Writing"])
    question_type = st.selectbox("Soru Türü", ["Multiple Choice", "Fill in the Blanks", "True / False"])level = st.selectbox("Dil Seviyesi", ["A1", "A2", "B1", "B2", "C1"])

with tab2:
    meb_grade = st.selectbox("📚 MEB Sınıfı", ["9. Sınıf", "10. Sınıf", "11. Sınıf", "12. Sınıf"])
    units_by_grade = {
        "9. Sınıf": ["Theme 1: Studying Abroad", ...]
    }
    selected_unit = st.selectbox("Ünite Seç", units_by_grade.get(meb_grade, []))

if skill == "Reading":
    question_options = ["Multiple Choice", "Fill in the Blanks", "True / False", "Open-ended (Short Answer)"]
else:
    question_options = ["Multiple Choice", "Fill in the Blanks", "True / False"]

question_type = st.selectbox("Soru Türü", question_options)

mode = st.radio("Test Tipi", ["Otomatik Üret", "Kendi Metnimden Test Üret"])
custom_text = ""
if mode == "Kendi Metnimden Test Üret":
    custom_text = st.text_area("📝 İngilizce metninizi buraya yapıştırın", height=200, key="user_input_text")

# ----- PDF Üretim Fonksiyonu -----

def save_to_pdf(content, level=None, skill=None, question_type=None, topic=None,
                meb_grade=None, selected_unit=None, custom_text=None):
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"/mnt/data/quicksheet_{now}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    margin_x = 40
    y = height - 80

    # Başlık
    c.setFont("Times-Bold", 14)
    c.drawString(margin_x, y, "QuickSheet Worksheet")
    y -= 30

    c.setFont("Times-Roman", 12)

    # MEB Bilgileri varsa
    if meb_grade and selected_unit:
        c.drawString(margin_x, y, f"Sınıf: {meb_grade}")
        y -= 20
        c.drawString(margin_x, y, f"Ünite: {selected_unit}")
        y -= 30
    # Seviye/Konu bilgisi varsa
    elif level and topic:
        c.drawString(margin_x, y, f"Dil Seviyesi: {level}")
        y -= 20
        c.drawString(margin_x, y, f"Konu: {topic}")
        y -= 30

    # Kendi metni eklenecekse
    if custom_text:
        c.setFont("Times-Bold", 12)
        c.drawString(margin_x, y, "Metin:")
        y -= 20

        c.setFont("Times-Roman", 11)
        for line in custom_text.split("\n"):
            for sub_line in line.splitlines():
                c.drawString(margin_x, y, sub_line)
                y -= 15
            y -= 10
        y -= 10

    # Materyal yazdır
    c.setFont("Times-Bold", 12)
    c.drawString(margin_x, y, "Alıştırma:")
    y -= 20

    c.setFont("Times-Roman", 11)
    for line in content.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Times-Roman", 11)
        c.drawString(margin_x, y, line.strip())
        y -= 15

    c.save()
    return filename

    # Cevap anahtarı ve başlık temizliği
    lower_text = material_text.lower()
    cut_keywords = ["answer key", "correct answers", "answers:"]
    cut_index = len(material_text)
    for keyword in cut_keywords:
        idx = lower_text.find(keyword)
        if idx != -1 and idx < cut_index:
            cut_index = idx
    material_cleaned = material_text[:cut_index]

    lines = material_cleaned.splitlines()
    cleaned_lines = []
    for line in lines:
        line_lower = line.strip().lower()
        if line_lower.startswith("activity title") or line_lower.startswith("objective") or line_lower.startswith("activity:"):
            continue
        cleaned_lines.append(line)

    c.setFont("TNR", 11)
    for line in cleaned_lines:
        wrapped = []
        while len(line) > 100:
            split_index = line[:100].rfind(" ")
            if split_index == -1:
                split_index = 100
            wrapped.append(line[:split_index])
            line = line[split_index:].strip()
        wrapped.append(line)
        for wrapped_line in wrapped:
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("TNR", 11)
            c.drawString(margin_x, y, wrapped_line)
            y -= 16

    c.save()
    return buffer.name

# ----- Materyal Üretme -----
if st.button("✨ Testi Üret"):
    if tab1:
        prompt = f"""
Create a {question_type} activity for a {level} level English learner about "{topic}", focused on {skill} skills.
Only include content related to the topic. Avoid mixing tenses or unrelated grammar structures.
Make it classroom-appropriate and ready for printout.
"""
    
    if tab2 and selected_unit in meb_unit_prompts:
        unit_info = meb_unit_prompts[selected_unit]
        prompt = f"""
You are an experienced English teacher creating worksheets aligned with the Turkish MEB {meb_grade} curriculum.
Create a worksheet for Unit: "{selected_unit}".
Functions: {unit_info['functions']}
Vocabulary: {unit_info['vocab']}
Grammar Focus: {unit_info['grammar']}
Only include content relevant to this unit. Do not mix unrelated topics. Format clearly for classroom use.
"""

if "prompt" in locals():
    with st.spinner("Yapay zekâ içerik üretiyor..."):
        try:
            chat_completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )

            result = chat_completion.choices[0].message.content
            st.text_area("Üretilen Materyal", result, height=400)
            st.session_state["material_result"] = result

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")

        elif mode == "Kendi Metnimden Test Üret" and custom_text.strip() != "":
            prompt = f"""
            Use the following text to create a {question_type} activity for a {level} level English learner, focused on {skill} skills.
            Only use this text as source material. Include a clear title, the activity itself, and an answer key.

            Text:
            {custom_text}
            """
        else:
            st.warning("Lütfen geçerli bir metin girin.")
            st.stop()

        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            st.session_state["material_result"] = response.choices[0].message.content
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

# ----- Sonuç Gösterme ve PDF Butonu -----
if "material_result" in st.session_state:
    st.markdown("### ✅ Üretilen Materyal:")
    st.text_area("Materyal", st.session_state["material_result"], height=400, key="material_output")

    if st.button("📄 PDF Olarak İndir"):
        pdf_path = save_to_pdf(
            st.session_state["material_result"],
            level=level,
            skill=skill,
            question_type=question_type,
            topic=topic,
            custom_text=custom_text if mode == "Kendi Metnimden Test Üret" else None
        )
        with open(pdf_path, "rb") as f:
            st.download_button("İndir (PDF)", f, file_name="quicksheet.pdf")
