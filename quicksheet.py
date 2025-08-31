import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import requests
import uuid
import time

# -----------------------------
# SAYFA YAPISI
# -----------------------------
st.set_page_config(page_title="QuickSheet", page_icon="⚡")
st.title("⚡ QuickSheet: Akıllı Öğretmen Asistanı")

# -----------------------------
# API ANAHTARI
# -----------------------------
API_KEY = st.secrets.get("GEMINI_API_KEY", st.text_input("Gemini API Anahtarınızı Girin", type="password"))
if not API_KEY:
    st.error("Lütfen bir Gemini API anahtarı girin.")
    st.stop()
genai.configure(api_key=API_KEY)

# -----------------------------
# FONT (Türkçe karakter desteği)
# -----------------------------
try:
    if not os.path.exists("fonts"):
        os.makedirs("fonts")
    font_path = "fonts/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/dejavu-fonts/raw/main/ttf/DejaVuSans.ttf"
        r = requests.get(url, allow_redirects=True, timeout=20)
        with open(font_path, 'wb') as f:
            f.write(r.content)

    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_path))
except Exception as e:
    st.error(f"Font yüklenirken hata: {e}. Gerekirse 'fonts/DejaVuSans.ttf' dosyasını elle ekleyin.")

# -----------------------------
# MÜFREDAT (8 ÜNİTE TAM)
# -----------------------------
meb_curriculum = {
    "9. Sınıf": {
        "Theme 1: School Life": {
            "Grammar": "Can/can't (yetenek/olasılık), Simple Present (to be), Simple Past (was/were, düzenli-düzensiz).",
            "Vocabulary": "Schools, subjects, clubs, rules, countries & nationalities, languages.",
            "Reading": "School life ve kültürel değişim üzerine kısa metinler; okul kuralları ve kulüp tanıtımları.",
            "Speaking": "Introducing oneself, describing countries and tourist attractions.",
            "Writing": "Short paragraphs about school rules or cultural exchange.",
            "Pronunciation": "Long and short vowels: /ae/, /a:/, /eɪ/, /ɔː/. Consonants: /b/, /c/, /d/."
        },
        "Theme 2: Classroom Life": {
            "Grammar": "Simple Present (routines), Present Continuous (şu an olanlar), Imperatives (talimatlar).",
            "Vocabulary": "Classroom objects, study habits, instructions, pair/group work ifadeleri.",
            "Reading": "Sınıf içi iletişim, ders çalışma alışkanlıkları, not alma üzerine metinler.",
            "Speaking": "Describing daily routines or classroom activities.",
            "Writing": "Writing about a typical school day or study habits.",
            "Pronunciation": "Vowels: /e/, /ae/. Consonants: /f/, /g/, /dʒ/, /h/."
        },
        "Theme 3: Personal Life": {
            "Grammar": "Adjectives & adverbs, 'too'/'enough', like/love/hate + -ing.",
            "Vocabulary": "Appearance & personality, hobbies, interests, daily routines.",
            "Reading": "Kişisel tanıtımlar, günlük yaşam, hobiler ve kısa anlatılar.",
            "Speaking": "Describing personality or hobbies.",
            "Writing": "Describing a friend’s appearance or personality.",
            "Pronunciation": "Vowels: /i:/, /ɪ/, /aɪ/. Consonants: /ʒ/, /k/, /l/."
        },
        "Theme 4: Family Life": {
            "Grammar": "Simple Present (jobs & routines), Prepositions of place (in/on/at), Relative clauses (who/which/that).",
            "Vocabulary": "Family members, jobs & workplaces, household roles.",
            "Reading": "Aile bireylerinin meslekleri ve günlük düzenleri üzerine metinler.",
            "Speaking": "Talking about family roles or jobs.",
            "Writing": "Writing about family routines or household chores.",
            "Pronunciation": "Vowels: /æ/, /ʌ/. Consonants: /m/, /n/."
        },
        "Theme 5: House & Neighbourhood": {
            "Grammar": "Present Continuous (ev içi etkinlikler), There is/are, Quantifiers (some/any/much/many).",
            "Vocabulary": "Types of houses, rooms, furniture, chores, places in the neighbourhood.",
            "Reading": "Ev tanıtımları, mahalle özellikleri, ev iş bölümüyle ilgili metinler.",
            "Speaking": "Describing one’s home or neighbourhood.",
            "Writing": "Writing about household chores or local places.",
            "Pronunciation": "Vowels: /oʊ/, /u:/. Consonants: /p/, /t/."
        },
        "Theme 6: City & Country": {
            "Grammar": "Present Simple vs Present Continuous (karşılaştırma), Comparative/Superlative adjectives, 'or' for options.",
            "Vocabulary": "City vs country life, transport, food & festivals, describing places.",
            "Reading": "Şehir-kır karşılaştırmaları, yer tanıtımları, yerel yemekler ve festivaller.",
            "Speaking": "Comparing city and country life.",
            "Writing": "Writing about a favorite place or festival.",
            "Pronunciation": "Vowels: /ɛ/, /ɔ/. Consonants: /r/, /s/."
        },
        "Theme 7: World & Nature": {
            "Grammar": "Past Simple (was/were), Modal 'should' (öneri), Must/mustn’t (kurallar).",
            "Vocabulary": "Endangered animals, habitats, environmental issues, weather & climate.",
            "Reading": "Doğa koruma, nesli tükenen türler ve çevre sorunlarına dair metinler.",
            "Speaking": "Discussing environmental issues or solutions.",
            "Writing": "Writing about protecting nature or climate change.",
            "Pronunciation": "Vowels: /ʊ/, /u/. Consonants: /v/, /w/."
        },
        "Theme 8: Universe & Future": {
            "Grammar": "Future Simple (will) – tahmin & inançlar, be going to (planlar), Conditionals Type 0–1 (temel).",
            "Vocabulary": "Technology, space, science fiction, film genres, future jobs.",
            "Reading": "Gelecek teknolojileri, uzay temalı kısa metinler ve film tanıtımları.",
            "Speaking": "Talking about future plans or technology.",
            "Writing": "Writing about future predictions or sci-fi scenarios.",
            "Pronunciation": "Vowels: /ɪə/, /eə/. Consonants: /j/, /z/."
        }
    }
}

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.header("Seçenekler")
    selected_grade = st.selectbox("📚 MEB Sınıfı", list(meb_curriculum.keys()))
    units = list(meb_curriculum[selected_grade].keys())
    selected_unit = st.selectbox("Ünite Seç", units)
    selected_tool = st.radio(
        "Üretim Modu Seç",
        ["Çalışma Sayfası", "Ders Planı", "Değerlendirme Rubriği", "Ek Çalışma"]
    )

    # Hangi araçlar beceri seçiyor?
    skill_needed = selected_tool in ["Çalışma Sayfası", "Değerlendirme Rubriği", "Ek Çalışma"]
    if skill_needed:
        skill_options = list(meb_curriculum[selected_grade][selected_unit].keys())
        selected_skill = st.selectbox("Beceri Seç (Dilbilgisi / Kelime / Okuma / Konuşma / Yazma / Telaffuz)", skill_options)
    
    include_clil = st.checkbox("CLIL İçeriği Ekle (ör. siber güvenlik, teknoloji)")
    include_reflection = st.checkbox("Yansıtma Aktivitesi Ekle (ör. öz değerlendirme)")
    
    if selected_tool in ["Çalışma Sayfası", "Ek Çalışma"]:
        num_questions = st.slider("Soru Sayısı", 1, 20, 6)
    
    if selected_tool == "Ek Çalışma":
        differentiation_type = st.radio("Çalışma Türü", ["Destekleyici", "İleri"])

# -----------------------------
# PROMPT FONKSİYONLARI
# -----------------------------
def generate_ai_worksheet_prompt(grade, unit, skill, num_questions):
    topic_info = meb_curriculum[grade][unit].get(skill, "")
    prompt = f"""
You are an experienced English teacher. Create a worksheet for a {grade} class (CEFR B1.1).
Requirements:
- Unit: "{unit}"
- Focus skill: "{skill}"
- Number of questions: exactly {num_questions}
- Question types: a sensible mix (multiple choice, fill-in-the-blanks, true/false). For 'Reading', include a short original text and then questions. For 'Speaking', include role-play or discussion prompts. For 'Writing', include short writing tasks. For 'Pronunciation', include drills for specific sounds.
- Start with a clear activity title and one-sentence instruction for students.
- At the end, include an "Answer Key" section listing only the correct answers (no explanations).
Topics to cover: {topic_info}
"""
    if include_clil:
        prompt += "\n- Include a CLIL component related to cybersecurity or digital technology."
    if include_reflection:
        prompt += "\n- Include a reflection question for students to evaluate their learning."
    return prompt.strip()

def generate_lesson_plan_prompt(grade, unit):
    unit_data = meb_curriculum[grade][unit]
    topic_info = " | ".join([f"{k}: {v}" for k, v in unit_data.items()])
    prompt = f"""
You are an English curriculum expert. Create a detailed lesson plan for a {grade} class (CEFR B1.1).
Unit: "{unit}"
Include:
- Title
- Objective (1-2 sentences)
- Stages with durations:
  * Warm-Up / Lead-In (engaging opener, 5-10 min)
  * Main Activity (grammar, vocabulary, speaking, writing, or pronunciation practice, 30-35 min)
  * Wrap-Up / Consolidation (quick check, 5-10 min)
- Key vocabulary, grammar, and pronunciation list
- Materials (simple list)
Key topics: {topic_info}
"""
    if include_clil:
        prompt += "\n- Include a CLIL activity related to cybersecurity or digital technology."
    if include_reflection:
        prompt += "\n- Include a reflection activity for students to evaluate their learning process."
    return prompt.strip()

def generate_rubric_prompt(grade, unit, skill):
    return f"""
You are an EFL assessment specialist. Create a grading rubric for {skill} in {grade} (CEFR B1.1), Unit "{unit}".
Include:
- At least 3 criteria relevant to {skill}.
- 3 performance levels: Excellent, Good, Needs Improvement.
- Clear, concise descriptors for each level under each criterion.
- Use headings and bullet points. Do NOT use tables.
Topics: {meb_curriculum[grade][unit].get(skill, "")}
""".strip()

def generate_differentiation_prompt(grade, unit, skill, diff_type):
    topic_info = meb_curriculum[grade][unit].get(skill, "")
    if diff_type == "Destekleyici":
        intro = "Create a SUPPORTING activity for students who need extra help."
        detail = "Keep it simpler and scaffolded (e.g., guided fill-in-the-blanks, matching, controlled practice)."
    else:
        intro = "Create an ADVANCED activity for students who are ready for more challenge."
        detail = "Require higher-order thinking (e.g., short opinion writing, problem-solving, mini project, debate prompts)."
    
    prompt = f"""
You are an experienced English teacher. {intro}
Class: {grade} (CEFR B1.1)
Unit: "{unit}"
Focus: "{skill}"
Instructions:
- Activity: Provide a clear, classroom-ready task. {detail}
- Objective: State the learning goal for this group.
- Implementation: Step-by-step how the teacher runs it (timings optional).
- Keep it aligned with the unit topics: {topic_info}
- Output headings: "Activity", "Objective", "Implementation".
"""
    if include_clil:
        prompt += "\n- Include a CLIL component related to cybersecurity or digital technology."
    if include_reflection:
        prompt += "\n- Include a reflection question for students to evaluate their learning."
    return prompt.strip()

# -----------------------------
# PDF OLUŞTURUCU
# -----------------------------
def create_pdf(content, filename, is_teacher_copy=False, is_worksheet=False, grade="9. Sınıf", unit=""):
    pdf = canvas.Canvas(filename, pagesize=A4)
    pdf.setTitle(f"English Worksheet - {grade}")
    pdf.setAuthor("QuickSheet AI Assistant")
    pdf.setCreator("QuickSheet AI Assistant")

    # Başlık ve üst bilgi
    y = 800
    pdf.setFont("DejaVuSans-Bold", 16)
    pdf.drawCentredString(A4[0] / 2.0, y, f"English Worksheet - {grade} - {unit}")
    y -= 30
    pdf.setFont("DejaVuSans", 10)
    pdf.drawString(50, y, f"Generated by QuickSheet AI Assistant")
    y -= 20

    lines = content.split("\n")
    is_answer_key = False
    question_number = 1

    for line in lines:
        text = line.rstrip()

        # "Answer Key" bölümünü öğrenci kopyasında gizle
        if is_worksheet and "Answer Key" in text:
            is_answer_key = True
            if is_teacher_copy:
                pdf.showPage()
                y = 800
                pdf.setFont("DejaVuSans-Bold", 12)
                pdf.drawString(50, y, "Answer Key")
                y -= 20
                pdf.setFont("DejaVuSans", 10)
            else:
                continue

        if is_worksheet and not is_teacher_copy and is_answer_key:
            continue

        # Soru numaralandırma
        if is_worksheet and not is_answer_key and text.strip() and text[0].isdigit():
            text = f"{question_number}. {text.lstrip('0123456789. ')}"
            question_number += 1

        # Başlık için kalın font
        if text.startswith("# "):
            pdf.setFont("DejaVuSans-Bold", 12)
            text = text[2:]
        else:
            pdf.setFont("DejaVuSans", 10)

        # Sayfa altına gelindiyse yeni sayfa
        if y < 60:
            pdf.showPage()
            y = 800
            pdf.setFont("DejaVuSans", 10)
            pdf.drawString(50, y, f"English Worksheet - {grade} - {unit} (Continued)")
            y -= 20

        pdf.drawString(50, y, text)
        y -= 14

    pdf.save()
    return filename

# -----------------------------
# ANA AKIŞ
# -----------------------------
if st.button("✨ İçeriği Üret"):
    if not API_KEY:
        st.error("Lütfen Gemini API anahtarınızı girin.")
    else:
        with st.spinner(f"{selected_tool} oluşturuluyor..."):
            try:
                if selected_tool == "Çalışma Sayfası":
                    prompt_text = generate_ai_worksheet_prompt(
                        selected_grade, selected_unit, selected_skill, num_questions
                    )
                elif selected_tool == "Ders Planı":
                    prompt_text = generate_lesson_plan_prompt(
                        selected_grade, selected_unit
                    )
                elif selected_tool == "Değerlendirme Rubriği":
                    prompt_text = generate_rubric_prompt(
                        selected_grade, selected_unit, selected_skill
                    )
                elif selected_tool == "Ek Çalışma":
                    prompt_text = generate_differentiation_prompt(
                        selected_grade, selected_unit, selected_skill, differentiation_type
                    )
                else:
                    st.error("Geçersiz seçim.")
                    st.stop()

                model = genai.GenerativeModel("gemini-1.5-pro")
                for attempt in range(3):  # 3 deneme
                    try:
                        response = model.generate_content(prompt_text)
                        ai_content = (response.text or "").strip()
                        if ai_content:
                            break
                    except Exception as api_error:
                        if "404" in str(api_error):
                            st.error(f"Model bulunamadı: {api_error}. Desteklenen modeller için lütfen Google Gemini API dokümantasyonunu kontrol edin.")
                            st.stop()
                        time.sleep(1)  # Yeniden deneme öncesi bekleme
                else:
                    st.error("API'den yanıt alınamadı. Lütfen tekrar deneyin.")
                    st.stop()

                if not ai_content:
                    st.error("Model boş içerik döndürdü. Promptu gözden geçirin veya tekrar deneyin.")
                    st.stop()

                st.subheader(f"Oluşturulan: {selected_tool}")
                edited_content = st.text_area("İçeriği Düzenle", ai_content, height=500)

                # PDF üretimi
                if selected_tool == "Çalışma Sayfası":
                    student_pdf = create_pdf(
                        edited_content, "ogrenci_calisma_sayfasi.pdf",
                        is_teacher_copy=False, is_worksheet=True,
                        grade=selected_grade, unit=selected_unit
                    )
                    with open(student_pdf, "rb") as f:
                        st.download_button("📄 Öğrenci PDF İndir", f, file_name="ogrenci_calisma_sayfasi.pdf")

                    teacher_pdf = create_pdf(
                        edited_content, "ogretmen_calisma_sayfasi.pdf",
                        is_teacher_copy=True, is_worksheet=True,
                        grade=selected_grade, unit=selected_unit
                    )
                    with open(teacher_pdf, "rb") as f:
                        st.download_button("🔑 Öğretmen PDF (Cevap Anahtarlı) İndir", f, file_name="ogretmen_calisma_sayfasi.pdf")

                else:
                    out_name = f"{selected_tool.lower().replace(' ', '_')}.pdf"
                    pdf_path = create_pdf(edited_content, out_name, is_teacher_copy=False, is_worksheet=False,
                                          grade=selected_grade, unit=selected_unit)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📄 PDF Olarak İndir", f, file_name=out_name)

                st.success("İçerik başarıyla oluşturuldu!")

            except Exception as e:
                st.error(f"Hata oluştu: {e}")

# -----------------------------
# Küçük İpucu
# -----------------------------
st.caption("İpucu: İçerik zayıf geldiyse aynı promptu tekrar deneyin, soruları artırıp/azaltın veya içeriği düzenleyin.")
