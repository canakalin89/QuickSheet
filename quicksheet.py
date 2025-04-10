import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import tempfile

# Font ayarı
font_path = os.path.join("fonts", "times.ttf")
pdfmetrics.registerFont(TTFont("TNR", font_path))

# Groq API
client = Groq(api_key="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")

# Sayfa başlığı
st.set_page_config(page_title="QuickSheet", page_icon="⚡")
st.title("⚡ QuickSheet: AI Destekli Worksheet Hazırlayıcı")

# Beceriye göre soru türleri
question_type_by_skill = {
    "Reading": ["Multiple Choice", "Fill in the Blanks", "True / False", "Open-ended (Short Answer)"],
    "Listening": ["Multiple Choice", "Fill in the Blanks (from audio)", "True / False", "Matching", "Ordering Events", "Sentence Completion"],
    "Writing": ["Picture Prompt", "Sentence Completion", "Paragraph Writing", "Reordering Sentences"],
    "Speaking": ["Role Play", "Guided Interview", "Picture Description", "Opinion Giving", "Storytelling"],
    "Grammar": ["Multiple Choice", "Fill in the Blanks", "Error Correction"],
    "Vocabulary": ["Matching", "Word Formation", "Synonym/Antonym", "Fill in the Blanks"]
}

# Mod seçimi
mode_selection = st.radio("Mod Seçimi", ["🌍 Seviye Bazlı", "📘 MEB Müfredatlı"], horizontal=True)

level = topic = meb_grade = selected_unit = skill = question_type = None

# Ortak metin alanı
mode = st.radio("Test Tipi", ["Otomatik Üret", "Kendi Metnimden Test Üret"])
custom_text = st.text_area("📝 İngilizce metninizi buraya yapıştırın", height=200) if mode == "Kendi Metnimden Test Üret" else ""

# SEVİYE BAZLI
if mode_selection == "🌍 Seviye Bazlı":
    level = st.selectbox("Dil Seviyesi", ["A1", "A2", "B1", "B2", "C1"])
    topic = st.text_input("Konu (örnek: 'Passive Voice')")
    skill = st.selectbox("Beceri", list(question_type_by_skill.keys()))
    question_type = st.selectbox("Soru Türü", question_type_by_skill[skill])

# MEB MÜFREDATLI
elif mode_selection == "📘 MEB Müfredatlı":
    meb_grade = st.selectbox("📚 MEB Sınıfı", ["9. Sınıf", "10. Sınıf", "11. Sınıf", "12. Sınıf"])
    units_by_grade = {
        "9. Sınıf": [
            "Theme 1: Studying Abroad",
            "Theme 2: My Environment",
            "Theme 3: Movies",
            "Theme 4: Human In Nature",
            "Theme 5: Inspirational People",
            "Theme 6: Bridging Cultures",
            "Theme 7: World Heritage",
            "Theme 8: Emergency and Health Problems",
            "Theme 9: Invitations and Celebrations",
            "Theme 10: Television and Social Media"
        ]
    }
    selected_unit = st.selectbox("Ünite Seç", units_by_grade.get(meb_grade, []))
    skill = st.selectbox("Beceri", list(question_type_by_skill.keys()), key="meb_skill")
    question_type = st.selectbox("Soru Türü", question_type_by_skill[skill], key="meb_qtype")

# MEB prompt verisi
meb_unit_prompts = {
    "Theme 1: Studying Abroad": {
        "vocab": "countries, nationalities, languages, family members, directions",
        "functions": "introducing oneself and family, talking about possessions, asking and giving directions",
        "grammar": "verb to be, have got, there is/are, prepositions of place, imperatives"
    }
}

# PDF üretim fonksiyonu
def save_to_pdf(content, level=None, skill=None, question_type=None, topic=None,
                meb_grade=None, selected_unit=None, custom_text=None):
    now_display = datetime.now().strftime("%d.%m.%Y - %H:%M")
    
    # Dosya adı belirleme
    base_name = "quicksheet"
    if level and topic and skill:
        file_name = f"{base_name}_{level}_{topic.replace(' ', '')}_{skill}.pdf"
    elif meb_grade and selected_unit:
        file_name = f"{base_name}_{meb_grade.replace(' ', '')}_{selected_unit.replace(' ', '').replace(':', '')}_{skill}.pdf"
    else:
        file_name = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    # Geçici dosya
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filename = temp_file.name

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin_x = 40
    y = height - 80

    c.setFont("TNR", 10)
    c.drawRightString(width - margin_x, height - 50, f"Tarih: {now_display}")
    c.setFont("TNR", 14)
    c.drawString(margin_x, y, "QuickSheet Worksheet")
    y -= 30
    c.setFont("TNR", 12)

    if meb_grade and selected_unit:
        c.drawString(margin_x, y, f"Sınıf: {meb_grade}")
        y -= 20
        c.drawString(margin_x, y, f"Ünite: {selected_unit}")
        y -= 20
        c.drawString(margin_x, y, f"Beceri: {skill} / Soru Türü: {question_type}")
        y -= 30
    elif level and topic:
        c.drawString(margin_x, y, f"Dil Seviyesi: {level}")
        y -= 20
        c.drawString(margin_x, y, f"Konu: {topic}")
        y -= 20
        c.drawString(margin_x, y, f"Beceri: {skill} / Soru Türü: {question_type}")
        y -= 30

    if custom_text:
        c.setFont("TNR", 12)
        c.drawString(margin_x, y, "Metin:")
        y -= 20
        c.setFont("TNR", 11)
        for line in custom_text.split("\n"):
            c.drawString(margin_x, y, line.strip())
            y -= 15
        y -= 10

    c.setFont("TNR", 12)
    c.drawString(margin_x, y, "Alıştırma:")
    y -= 20
    c.setFont("TNR", 11)
    for line in content.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("TNR", 11)
        c.drawString(margin_x, y, line.strip())
        y -= 15

    c.save()
    return filename, file_name
                    
# TEST ÜRET
if st.button("✨ Testi Üret"):
    if mode == "Otomatik Üret":
        if mode_selection == "📘 MEB Müfredatlı" and selected_unit in meb_unit_prompts:
            unit_info = meb_unit_prompts[selected_unit]
            prompt = f"""
You are an experienced English teacher creating worksheets aligned with the Turkish MEB {meb_grade} curriculum.
Create a {question_type} activity for Unit: "{selected_unit}".
Functions: {unit_info['functions']}
Vocabulary: {unit_info['vocab']}
Grammar Focus: {unit_info['grammar']}
Skill: {skill}
Only include content relevant to this unit.
"""
        else:
            prompt = f"""
Create a {question_type} activity for a {level} level English learner about "{topic}", focused on {skill} skills.
Only include content related to the topic. Avoid mixing unrelated grammar structures.
Make it classroom-appropriate and ready for printout.
"""
    elif mode == "Kendi Metnimden Test Üret" and custom_text.strip() != "":
        prompt = f"""
Use the following text to create a {question_type} activity for a {level} level English learner, focused on {skill} skills.
Only use this text as source material. Do not include answer keys.

Text:
{custom_text}
"""
    else:
        st.warning("Lütfen geçerli bir seçim veya metin girin.")
        st.stop()

    with st.spinner("Yapay zekâ içerik üretiyor..."):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=800
            )
            result = response.choices[0].message.content
            st.text_area("Üretilen Materyal", result, height=400)
            st.session_state["material_result"] = result
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

# PDF BUTONU
if "material_result" in st.session_state:
    if st.button("📄 PDF Olarak İndir"):
        pdf_path, file_name = save_to_pdf(
            content=st.session_state["material_result"],
            level=level if "level" in locals() else None,
            skill=skill if "skill" in locals() else None,
            question_type=question_type if "question_type" in locals() else None,
            topic=topic if "topic" in locals() else None,
            meb_grade=meb_grade if "meb_grade" in locals() else None,
            selected_unit=selected_unit if "selected_unit" in locals() else None,
            custom_text=custom_text if "custom_text" in locals() else None
        )

        with open(pdf_path, "rb") as f:
            st.download_button("İndir (PDF)", f, file_name=file_name)

