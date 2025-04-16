import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from datetime import datetime
import os
import tempfile

# Font ayarı
font_path = os.path.join("fonts", "times.ttf")
pdfmetrics.registerFont(TTFont("TNR", font_path))

# Groq API Anahtarı
client = Groq(api_key="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")

# Sayfa ayarı
st.set_page_config(page_title="QuickSheet", page_icon="⚡")
st.title("⚡ QuickSheet: AI Destekli Worksheet Hazırlayıcı")

# Beceri ve soru türleri eşleşmesi
question_type_by_skill = {
    "Reading": ["Multiple Choice", "Fill in the Blanks", "True / False", "Open-ended (Short Answer)"],
    "Listening": ["Multiple Choice", "Fill in the Blanks (from audio)", "True / False", "Matching", "Ordering Events", "Sentence Completion"],
    "Writing": ["Picture Prompt", "Sentence Completion", "Paragraph Writing", "Reordering Sentences"],
    "Speaking": ["Role Play", "Guided Interview", "Picture Description", "Opinion Giving", "Storytelling"],
    "Grammar": ["Multiple Choice", "Fill in the Blanks", "Error Correction"],
    "Vocabulary": ["Matching", "Word Formation", "Synonym/Antonym", "Fill in the Blanks"],
    "Pronunciation": ["Stress Practice", "Intonation Pattern", "Minimal Pairs", "Sound Matching"]
}

# Kullanıcıdan mod seçimi
mode_selection = st.radio("Mod Seçimi", ["🌍 Seviye Bazlı", "📘 MEB Müfredatlı"], horizontal=True)
mode = st.radio("Test Tipi", ["Otomatik Üret", "Kendi Metnimden Test Üret"])
custom_text = st.text_area("📝 İngilizce metninizi buraya yapıştırın", height=200) if mode == "Kendi Metnimden Test Üret" else ""

# Ortak değişkenler (ilk değer boş)
level = topic = meb_unit_prompts = selected_unit = skill = question_type = prompt = ""

# Seviye Bazlı Seçimler
if mode_selection == "🌍 Seviye Bazlı":
    level = st.selectbox("Dil Seviyesi", ["A1", "A2", "B1", "B2", "C1"])
    topic = st.text_input("Konu (örnek: 'Passive Voice')")
    skill = st.selectbox("Beceri", list(question_type_by_skill.keys()))
    question_type = st.selectbox("Soru Türü", question_type_by_skill[skill])

# MEB Müfredatı Seçimleri
elif mode_selection == "📘 MEB Müfredatlı":
    meb_unit_prompts: = st.selectbox("📚 MEB Sınıfı", ["9. Sınıf", "10. Sınıf", "11. Sınıf", "12. Sınıf"])
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
        ],
        "10. Sınıf": [
            "Theme 1: School Life",
            "Theme 2: Plans",
            "Theme 3: Legendary Figure",
            "Theme 4: Traditions",
            "Theme 5: Travel",
            "Theme 6: Helpful Tips",
            "Theme 7: Food and Festivals",
            "Theme 8: Digital Era",
            "Theme 9: Modern Heroes and Heroines",
            "Theme 10: Shopping"
        ],
        "11. Sınıf": [
            "Theme 1: Future Jobs",
            "Theme 2: Hobbies and Skills",
            "Theme 3: Hard Times",
            "Theme 4: What a Life",
            "Theme 5: Back to the Past",
            "Theme 6: Open Your Heart",
            "Theme 7: Facts about Turkiye",
            "Theme 8: Sports",
            "Theme 9: My Friends",
            "Theme 10: Values and Norms"
        ],
        "12. Sınıf": [
            "Theme 1: Music",
            "Theme 2: Friendship",
            "Theme 3: Human Rights",
            "Theme 4: Coming Soon",
            "Theme 5: Psychology",
            "Theme 6: Favors",
            "Theme 7: News Stories",
            "Theme 8: Alternative Energy",
            "Theme 9: Technology",
            "Theme 10: Manners"
        ]
    }
    selected_unit = st.selectbox("Ünite Seç", units_by_grade.get(meb_unit_prompts, []))
    skill = st.selectbox("Beceri", list(question_type_by_skill.keys()), key="meb_skill")
    question_type = st.selectbox("Soru Türü", question_type_by_skill[skill], key="meb_qtype")

# Cevap Yasakları Politikası
no_answer_policy = """
❌ DO NOT include:
- answer keys
- correct answers
- example answers (e.g. “played”, “was doing”, etc.)
- explanations of grammar rules or how to answer
- “Note”, “Remember”, “Use the correct form of…” type of tips

✅ Format the worksheet clearly and make it printable for students.
"""
def save_to_pdf(content, level=None, skill=None, question_type=None, topic=None,
                meb_unit_prompts=None, selected_unit=None, custom_text=None):
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

    # Başlık
    c.setFont("TNR", 16)
    c.drawCentredString(width / 2, height - 60, "QuickSheet Worksheet")

    # Tarih
    c.setFont("TNR", 10)
    c.drawRightString(width - margin_x, height - 50, datetime.now().strftime("%d.%m.%Y - %H:%M"))

    # Öğrenci bilgisi
    y -= 70
    c.setFont("TNR", 12)
    c.drawString(margin_x, y, "Name & Surname: ..............................................   No: .............")
    y -= 30

    # Konu varsa ekle
    if topic:
        c.setFont("TNR", 12)
        c.drawString(margin_x, y, f"Topic: {topic}")
        y -= 20

    # Satırları ayır
    lines = content.splitlines()
    intro_lines = []
    exercise_lines = []
    in_intro = True

    for line in lines:
        lower = line.strip().lower()
        if any(k in lower for k in [
            "answer key", "answers:", "correct answers", "note:", "for example", "(e.g.", 
            "example answer", "sample answer", "answer:", "* answer", "** answer"
        ]):
            continue
        if in_intro and any(k in lower for k in ["exercise", "instruction", "questions", "worksheet"]):
            in_intro = False
        (intro_lines if in_intro else exercise_lines).append(line.strip())

    # Konu anlatımı
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

    # Alıştırmalar
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

    # Footer
    y = max(y - 20, 40)
    c.setFont("TNR", 9)
    c.drawCentredString(width / 2, y, "Prepared by using QuickSheet")

    c.save()
    return filename, os.path.basename(filename)
                    
# TEST ÜRET BUTONU
if st.button("✨ Testi Üret"):
    # Giriş kontrolleri
    if mode_selection == "🌍 Seviye Bazlı" and (not level or not topic):
        st.warning("Lütfen seviye ve konu giriniz.")
        st.stop()
    if mode_selection == "📘 MEB Müfredatlı" and (not selected_unit or not meb_unit_prompts):
        st.warning("Lütfen MEB sınıfı ve ünite seçiniz.")
        st.stop()

    # Ortak prompt uyarı politikası
    no_answer_policy = """
❌ DO NOT include:
- answer keys
- correct answers
- example answers (e.g. “played”, “was doing”, etc.)
- explanations of grammar rules or how to answer
- “Note”, “Remember”, “Use the correct form of…” type of tips

✅ Format the worksheet clearly and make it printable for students.
"""

    # Prompt Hazırlama
    if mode == "Otomatik Üret":
        # Seviye bazlı
        if mode_selection == "🌍 Seviye Bazlı":
            prompt = f"You are generating a classroom-ready English worksheet for {level} learners on the topic \"{topic}\", focused on the skill: {skill}.+ no_answer_policy \n"

        # MEB müfredatı bazlı
        elif mode_selection == "📘 MEB Müfredatlı" and selected_unit in meb_unit_prompts:
            unit_info = meb_unit_prompts[selected_unit]
            prompt = f"""You are preparing a worksheet aligned with the Turkish MEB {meb_unit_prompts} curriculum.\nUnit: {selected_unit} 
Functions: {unit_info['functions']}
Vocabulary: {unit_info['vocab']}
Grammar Focus: {unit_info['grammar']}\nSkill: {skill}\n"""

        # Beceriye özel detay
        skill_prompts = {
            "Reading": "- Activity Title\n- Objective\n- A short reading passage\n- 4–6 comprehension questions\n- Vocabulary help (optional)",
            "Grammar": "- Activity Title\n- Objective\n- Short grammar explanation\n- 5–6 exercises (fill-in-the-blank, sentence transformation)",
            "Vocabulary": "- Activity Title\n- Objective\n- 6–8 topic-related words\n- Matching, fill-in-the-blank or definitions",
            "Writing": "- Activity Title\n- Objective\n- Writing prompt\n- Guiding outline or questions",
            "Speaking": "- Activity Title\n- Objective\n- 3–5 speaking questions\n- Pair/group task or role-play",
            "Listening": "- Activity Title\n- Objective\n- A short transcript\n- 4–6 comprehension questions",
            "Pronunciation": "- Activity Title\n- Objective\n- Practice on stress, intonation or minimal pairs"
        }

        prompt += f"\nInclude:\n{skill_prompts.get(skill, '')}\n" + no_answer_policy

    elif mode == "Kendi Metnimden Test Üret" and custom_text.strip():
        base_prompt = f"Create a {skill} worksheet for {level} learners based on the following text:\n\nText:\n{custom_text}\n\n"
        skill_suffix = {
            "Reading": "- Activity Title\n- Objective\n- 4–6 comprehension questions\n- Vocabulary focus (optional)",
            "Grammar": "- Activity Title\n- Objective\n- 4–6 grammar-based fill-in-the-blanks or transformations",
            "Vocabulary": "- Activity Title\n- Objective\n- Word selection and fill-in-the-blanks or matching tasks",
            "Writing": "- Activity Title\n- Objective\n- Writing prompt + guiding outline",
            "Speaking": "- Activity Title\n- Objective\n- 3–5 discussion tasks or role-play",
            "Listening": "- Activity Title\n- Objective\n- Listening comprehension with questions",
            "Pronunciation": "- Activity Title\n- Objective\n- Intonation / stress / sound distinction tasks"
        }
        prompt = base_prompt + "Include:\n" + skill_suffix.get(skill, "") + "\n" + no_answer_policy

    else:
        st.warning("Lütfen geçerli bir metin veya seçim yapın.")
        st.stop()

    # Yapay zekâdan içerik alma
    with st.spinner("Yapay zekâ içerik üretiyor..."):
        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            result = response.choices[0].message.content
            st.session_state["material_result"] = result
            st.text_area("📄 Üretilen Materyal", result, height=400)
        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            
# PDF BUTONU
if "material_result" in st.session_state:
    st.markdown("### ✅ Çıktıya hazır:")
    st.text_area("Materyal", st.session_state["material_result"], height=400, key="material_output")

    if st.button("📄 PDF Olarak İndir"):
        pdf_path, file_name = save_to_pdf(
            content=st.session_state["material_result"],
            level=level if "level" in locals() else None,
            skill=skill if "skill" in locals() else None,
            question_type=question_type if "question_type" in locals() else None,
            topic=topic if "topic" in locals() else None,
            meb_unit_prompts=meb_unit_prompts if "meb_unit_prompts" in locals() else None,
            selected_unit=selected_unit if "selected_unit" in locals() else None,
            custom_text=custom_text if "custom_text" in locals() else None
        )

        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ PDF Dosyasını İndir", f, file_name=file_name, mime="application/pdf")
