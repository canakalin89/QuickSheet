import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from datetime import datetime
import tempfile
import os

# Font ayarı
pdfmetrics.registerFont(TTFont("TNR", "fonts/times.ttf"))

# API bağlantısı
client = Groq(api_key="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")

# Sayfa başlığı
st.set_page_config(page_title="QuickSheet", page_icon="⚡")
st.title("⚡ QuickSheet: AI Destekli Worksheet Hazırlayıcı")

question_type_by_skill = {
    "Reading": ["Multiple Choice", "Fill in the Blanks", "True / False", "Open-ended (Short Answer)"],
    "Listening": ["Fill in the Blanks (from audio)", "True / False", "Matching", "Ordering Events"],
    "Writing": ["Sentence Completion", "Paragraph Writing", "Picture Prompt"],
    "Speaking": ["Role Play", "Guided Interview", "Picture Description"],
    "Grammar": ["Fill in the Blanks", "Error Correction"],
    "Vocabulary": ["Matching", "Fill in the Blanks", "Word Formation"],
    "Pronunciation": ["Stress Practice", "Intonation Pattern", "Minimal Pairs"]
}

mode_selection = st.radio("Mod Seçimi", ["🌍 Seviye Bazlı", "📘 MEB Müfredatlı"], horizontal=True)
mode = st.radio("Test Tipi", ["Otomatik Üret", "Kendi Metnimden Test Üret"])

level = topic = meb_grade = selected_unit = skill = question_type = None
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
            "Theme 1: Studying Abroad", "Theme 2: My Environment", "Theme 3: Movies", "Theme 4: Human In Nature",
            "Theme 5: Inspirational People", "Theme 6: Bridging Cultures", "Theme 7: World Heritage",
            "Theme 8: Emergency and Health Problems", "Theme 9: Invitations and Celebrations", "Theme 10: Television and Social Media"
        ],
        "10. Sınıf": [
            "Theme 1: School Life", "Theme 2: Plans", "Theme 3: Legendary Figure", "Theme 4: Traditions",
            "Theme 5: Travel", "Theme 6: Helpful Tips", "Theme 7: Food and Festivals", "Theme 8: Digital Era",
            "Theme 9: Modern Heroes and Heroines", "Theme 10: Shopping"
        ],
        "11. Sınıf": [
            "Theme 1: Future Jobs", "Theme 2: Hobbies and Skills", "Theme 3: Hard Times", "Theme 4: What a Life",
            "Theme 5: Back to the Past", "Theme 6: Open Your Heart", "Theme 7: Facts about Turkiye",
            "Theme 8: Sports", "Theme 9: My Friends", "Theme 10: Values and Norms"
        ],
        "12. Sınıf": [
            "Theme 1: Music", "Theme 2: Friendship", "Theme 3: Human Rights", "Theme 4: Coming Soon",
            "Theme 5: Psychology", "Theme 6: Favors", "Theme 7: News Stories", "Theme 8: Alternative Energy",
            "Theme 9: Technology", "Theme 10: Manners"
        ]
    }

    selected_unit = st.selectbox("Ünite Seç", units_by_grade[meb_grade])
    skill = st.selectbox("Beceri", list(question_type_by_skill.keys()), key="meb_skill")
    question_type = st.selectbox("Soru Türü", question_type_by_skill[skill], key="meb_qtype")

no_answer_policy = """
❌ DO NOT include:
- answer keys
- correct answers
- example answers (e.g. “played”, “was doing”, etc.)
- explanations of grammar rules or how to answer
- “Note”, “Remember”, “Use the correct form of…” type of tips
- any phrases like “I hope this helps” or “Here is your worksheet”

✅ Format the worksheet clearly and make it printable for students.
✅ Use only the specified question type. Do NOT mix question types.
"""

def generate_prompt(level, skill, topic, question_type, custom_text=None, mode="Otomatik Üret"):
    base = f"""
You are generating a worksheet for {level} level learners.
The focus skill is: {skill.upper()}.
The topic is: "{topic}".
The exercise type must be: {question_type.upper()}.
"""

    if mode == "Kendi Metnimden Test Üret":
        base += f"\nUse ONLY the following text for content generation:\n\n{custom_text}\n"

    base += f"\nYour output must include:\n"
    base += "- A clear Activity Title\n"
    base += "- A 1-sentence Objective\n"
    base += f"- 5 to 7 questions or exercises in the style of: {question_type.upper()}\n\n"
    base += no_answer_policy
    return base


if st.button("✨ Testi Üret"):
    if (mode_selection == "🌍 Seviye Bazlı" and not topic) and mode == "Otomatik Üret":
        st.warning("Lütfen bir konu girin.")
        st.stop()

    target_level = level if mode_selection == "🌍 Seviye Bazlı" else meb_grade
    target_topic = topic if mode_selection == "🌍 Seviye Bazlı" else selected_unit

    prompt = generate_prompt(
        level=target_level,
        skill=skill,
        topic=target_topic,
        question_type=question_type,
        custom_text=custom_text,
        mode=mode
    )

    with st.spinner("Yapay zekâ içerik üretiyor..."):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            result = response.choices[0].message.content.strip()
            st.session_state["material_result"] = result
            st.text_area("Üretilen Materyal", result, height=400)
        except Exception as e:
            st.error(f"Hata oluştu: {e}")

def save_to_pdf(content, level=None, skill=None, question_type=None, topic=None,
                meb_grade=None, selected_unit=None, custom_text=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filename = temp_file.name
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin_x = 50
    y = height - 80

    pdfmetrics.registerFont(TTFont("TNR", "fonts/times.ttf"))
    c.setFont("TNR", 11)

    # Logo
    logo_path = "assets/quicksheet_logo.png"
    if os.path.exists(logo_path):
        logo = ImageReader(logo_path)
        c.drawImage(logo, margin_x, height - 70, width=40, height=40, mask='auto')

    # Başlık ve tarih
    c.setFont("TNR", 16)
    c.drawCentredString(width / 2, height - 60, "QuickSheet Worksheet")
    c.setFont("TNR", 10)
    c.drawRightString(width - margin_x, height - 50, datetime.now().strftime("%d.%m.%Y - %H:%M"))

    # Öğrenci bilgisi
    y -= 70
    c.setFont("TNR", 12)
    c.drawString(margin_x, y, "Name & Surname: ..............................................   No: .............")
    y -= 30

    # Konu
    if topic:
        c.setFont("TNR", 12)
        c.drawString(margin_x, y, f"Topic: {topic}")
        y -= 20

    # Konu anlatımı ve egzersiz ayrımı
    lines = content.splitlines()
    intro_lines = []
    exercise_lines = []
    in_intro = True

    forbidden = [
        "answer key", "correct answer", "answers:", "note:", "for example", "(e.g.", "example answer", "sample answer",
        "i hope this helps", "use the correct form"
    ]

    for line in lines:
        lower = line.lower().strip()
        if any(k in lower for k in forbidden):
            continue
        if in_intro and ("exercise" in lower or "questions" in lower or "instruction" in lower):
            in_intro = False
        (intro_lines if in_intro else exercise_lines).append(line.strip())

    if intro_lines:
        c.setFont("TNR", 12)
        c.drawString(margin_x, y, "Topic Overview:")
        y -= 20
        c.setFont("TNR", 11)
        for line in intro_lines:
            if y < 60:
                c.showPage()
                y = height - 60
                c.setFont("TNR", 11)
            c.drawString(margin_x, y, line)
            y -= 14
        y -= 10

    if exercise_lines:
        c.setFont("TNR", 12)
        c.drawString(margin_x, y, "Instructions & Exercises:")
        y -= 20
        c.setFont("TNR", 11)
        for line in exercise_lines:
            if y < 60:
                c.showPage()
                y = height - 60
                c.setFont("TNR", 11)
            c.drawString(margin_x, y, line)
            y -= 14

    c.setFont("TNR", 9)
    c.drawCentredString(width / 2, 40, "Prepared by using QuickSheet")
    c.save()

    # Dosya adı örnek: quicksheet_A2_Passive Voice_Grammar.pdf
    cleaned_topic = (topic or selected_unit or "worksheet").replace(" ", "_").replace(":", "")
    level_part = (level or meb_grade or "").replace(" ", "")
    filename_out = f"quicksheet_{level_part}_{cleaned_topic}_{skill}.pdf"
    return filename, filename_out

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