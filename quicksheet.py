import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
level = st.selectbox("Dil Seviyesi", ["A1", "A2", "B1", "B2", "C1"])
topic = st.text_input("Konu (örnek: 'Passive Voice')")
skill = st.selectbox("Beceri", ["Reading", "Grammar", "Vocabulary", "Writing"])

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
def save_to_pdf(material_text, level, skill, question_type, topic, custom_text=None):
    buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(buffer.name, pagesize=A4)
    width, height = A4
    margin_x = 50
    y = height - 50

    c.setFont("TNR", 16)
    c.drawCentredString(width / 2, y, "⚡ QuickSheet Worksheet")
    y -= 30

    c.setFont("TNR", 12)
    c.drawString(margin_x, y, f"Topic: {topic}")
    y -= 20

    c.setFont("TNR", 11)
    c.drawString(margin_x, y, "Full Name / Class / Number: __________________________")
    c.drawRightString(width - margin_x, y, "Date: ____________")
    y -= 30

    if custom_text and custom_text.strip():
        c.setFont("TNR", 12)
        c.drawString(margin_x, y, "📘 Reading Text:")
        y -= 20
        c.setFont("TNR", 11)
        text_lines = custom_text.strip().splitlines()
        for line in text_lines:
            if y < 50:
                c.showPage()
                y = height - 50
                c.setFont("TNR", 11)
            wrapped = []
            while len(line) > 100:
                split_index = line[:100].rfind(" ")
                if split_index == -1:
                    split_index = 100
                wrapped.append(line[:split_index])
                line = line[split_index:].strip()
            wrapped.append(line)
            for wrapped_line in wrapped:
                c.drawString(margin_x, y, wrapped_line)
                y -= 16
        y -= 10
        c.setLineWidth(0.5)
        c.line(margin_x, y, width - margin_x, y)
        y -= 25

    c.setFont("TNR", 11)
    c.drawString(margin_x, y, "📌 Instructions: Answer the following questions.")
    y -= 25

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
    with st.spinner("İçerik üretiliyor..."):
        if mode == "Otomatik Üret":
            prompt = f"""
        You are an expert English teacher preparing worksheets for students.
        Create a {question_type} activity for a {level} level English learner.
        The topic is: "{topic}", and it should focus strictly on that.
        This worksheet must be suitable for {skill} skills.

        Do not include any other grammar structure, tense, or unrelated vocabulary.
        For example, if the topic is "irregular verbs in past tense", only use past simple forms like "went", "took", "ate".
        Avoid mixing tenses (e.g., present simple), and do not use content outside of the given topic.

        Provide only the activity and instructions. Format it for direct use in class.
        """
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
