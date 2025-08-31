import streamlit as st
import os
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from transformers import pipeline
import time

# -----------------------------
# SAYFA YAPISI
# -----------------------------
st.set_page_config(page_title="QuickSheet", page_icon="⚡", layout="wide")
st.title("⚡ QuickSheet: MEB İngilizce Öğretmen Asistanı")
st.markdown("9. Sınıf (B1.1) müfredatına uygun çalışma kağıtları, ders planları, rubricler ve ek aktiviteler üretin.")

# Hugging Face modelini başlat (DistilGPT-2, hafif ve bulut dostu)
generator = pipeline("text-generation", model="distilgpt2")

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
    st.error(f"Font yüklenirken hata: {e}. 'fonts/DejaVuSans.ttf' dosyasını elle ekleyin.")

# -----------------------------
# MÜFREDAT (MEB 2025 9. SINIF, 8 TEMA)
# -----------------------------
meb_curriculum = {
    "9. Sınıf": {
        "Theme 1: School Life": {
            "Grammar": "Can/can't (yetenek/olasılık), Simple Present (to be), Simple Past (was/were, düzenli-düzensiz).",
            "Vocabulary": "Okullar, dersler, kulüpler, kurallar, ülkeler ve milletler, diller.",
            "Reading": "Okul hayatı ve kültürel değişim üzerine kısa metinler; okul kuralları ve kulüp tanıtımları.",
            "Speaking": "Kendini tanıtma, ülkeler ve turistik yerleri tarif etme.",
            "Writing": "Okul kuralları veya kültürel değişim hakkında kısa paragraflar.",
            "Pronunciation": "Uzun ve kısa ünlüler: /ae/, /a:/, /eɪ/, /ɔː/. Ünsüzler: /b/, /c/, /d/."
        },
        "Theme 2: Classroom Life": {
            "Grammar": "Simple Present (rutinler), Present Continuous (şimdiki zaman), Imperatives (talimatlar).",
            "Vocabulary": "Sınıf eşyaları, ders çalışma alışkanlıkları, talimatlar, çift/grup çalışması ifadeleri.",
            "Reading": "Sınıf içi iletişim, ders çalışma alışkanlıkları, not alma üzerine metinler.",
            "Speaking": "Günlük rutinleri veya sınıf aktivitelerini tarif etme.",
            "Writing": "Tipik bir okul günü veya ders çalışma alışkanlıkları hakkında yazma.",
            "Pronunciation": "Ünlüler: /e/, /ae/. Ünsüzler: /f/, /g/, /dʒ/, /h/."
        },
        "Theme 3: Personal Life": {
            "Grammar": "Sıfatlar ve zarflar, 'too'/'enough', like/love/hate + -ing.",
            "Vocabulary": "Görünüş ve kişilik, hobiler, ilgi alanları, günlük rutinler.",
            "Reading": "Kişisel tanıtımlar, günlük yaşam, hobiler ve kısa anlatılar.",
            "Speaking": "Kişilik veya hobileri tarif etme.",
            "Writing": "Bir arkadaşın görünüşünü veya kişiliğini tarif etme.",
            "Pronunciation": "Ünlüler: /i:/, /ɪ/, /aɪ/. Ünsüzler: /ʒ/, /k/, /l/."
        },
        "Theme 4: Family Life": {
            "Grammar": "Simple Present (meslekler ve rutinler), Prepositions of place (in/on/at), Relative clauses (who/which/that).",
            "Vocabulary": "Aile bireyleri, meslekler ve iş yerleri, evdeki roller.",
            "Reading": "Aile bireylerinin meslekleri ve günlük düzenleri üzerine metinler.",
            "Speaking": "Aile rolleri veya meslekler hakkında konuşma.",
            "Writing": "Aile rutinleri veya ev işleri hakkında yazma.",
            "Pronunciation": "Ünlüler: /æ/, /ʌ/. Ünsüzler: /m/, /n/."
        },
        "Theme 5: House & Neighbourhood": {
            "Grammar": "Present Continuous (ev içi etkinlikler), There is/are, Quantifiers (some/any/much/many).",
            "Vocabulary": "Ev tipleri, odalar, mobilyalar, ev işleri, mahalledeki yerler.",
            "Reading": "Ev tanıtımları, mahalle özellikleri, ev iş bölümüyle ilgili metinler.",
            "Speaking": "Evini veya mahalleni tarif etme.",
            "Writing": "Ev işleri veya yerel yerler hakkında yazma.",
            "Pronunciation": "Ünlüler: /oʊ/, /u:/. Ünsüzler: /p/, /t/."
        },
        "Theme 6: City & Country": {
            "Grammar": "Present Simple vs Present Continuous (karşılaştırma), Comparative/Superlative adjectives, 'or' for options.",
            "Vocabulary": "Şehir ve kır hayatı, ulaşım, yemekler ve festivaller, yer tanımlama.",
            "Reading": "Şehir-kır karşılaştırmaları, yer tanıtımları, yerel yemekler ve festivaller.",
            "Speaking": "Şehir ve kır hayatını karşılaştırma.",
            "Writing": "Sevdiğin bir yer veya festival hakkında yazma.",
            "Pronunciation": "Ünlüler: /ɛ/, /ɔ/. Ünsüzler: /r/, /s/."
        },
        "Theme 7: World & Nature": {
            "Grammar": "Past Simple (was/were), Modal 'should' (öneri), Must/mustn't (kurallar).",
            "Vocabulary": "Nesli tükenen hayvanlar, yaşam alanları, çevre sorunları, hava ve iklim.",
            "Reading": "Doğa koruma, nesli tükenen türler ve çevre sorunlarına dair metinler.",
            "Speaking": "Çevre sorunları veya çözümleri tartışma.",
            "Writing": "Doğayı koruma veya iklim değişikliği hakkında yazma.",
            "Pronunciation": "Ünlüler: /ʊ/, /u/. Ünsüzler: /v/, /w/."
        },
        "Theme 8: Universe & Future": {
            "Grammar": "Future Simple (will) – tahmin ve inançlar, be going to (planlar), Conditionals Type 0–1 (temel).",
            "Vocabulary": "Teknoloji, uzay, bilimkurgu, film türleri, gelecekteki meslekler.",
            "Reading": "Gelecek teknolojileri, uzay temalı kısa metinler ve film tanıtımları.",
            "Speaking": "Gelecek planları veya teknoloji hakkında konuşma.",
            "Writing": "Gelecek tahminleri veya bilimkurgu senaryoları yazma.",
            "Pronunciation": "Ünlüler: /ɪə/, /eə/. Ünsüzler: /j/, /z/."
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

    # Beceri seçimi gereken araçlar
    skill_needed = selected_tool in ["Çalışma Sayfası", "Değerlendirme Rubriği", "Ek Çalışma"]
    if skill_needed:
        skill_options = list(meb_curriculum[selected_grade][selected_unit].keys())
        selected_skill = st.selectbox("Beceri Seç (Dilbilgisi / Kelime / Okuma / Konuşma / Yazma / Telaffuz)", skill_options)
    
    include_clil = st.checkbox("CLIL İçeriği Ekle (ör. siber güvenlik, teknoloji)")
    include_reflection = st.checkbox("Yansıtma Aktivitesi Ekle (ör. öz değerlendirme)")
    
    if selected_tool in ["Çalışma Sayfası", "Ek Çalışma"]:
        num_questions = st.slider("Soru Sayısı", 1, 10, 6)  # DistilGPT-2 için daha az soru
    
    if selected_tool == "Ek Çalışma":
        differentiation_type = st.radio("Çalışma Türü", ["Destekleyici", "İleri"])

# -----------------------------
# PROMPT FONKSİYONLARI
# -----------------------------
def generate_ai_worksheet_prompt(grade, unit, skill, num_questions):
    topic_info = meb_curriculum[grade][unit].get(skill, "")
    prompt = f"""
You are an expert English teacher creating materials for a {grade} class (CEFR B1.1, MEB 2025 Curriculum).
Requirements:
- Unit: "{unit}"
- Focus skill: "{skill}"
- Number of questions: exactly {num_questions}
- Question types: mix of multiple choice, fill-in-the-blanks, true/false. For 'Reading', include a short original text followed by questions. For 'Speaking', include role-play or discussion prompts. For 'Writing', include short writing tasks (e.g., 50-100 words). For 'Pronunciation', include drills for specific sounds listed in the curriculum.
- Start with a clear activity title and a one-sentence instruction for students.
- End with an "Answer Key" section listing only correct answers (no explanations).
- Keep output concise (under 500 tokens) to fit lightweight model capabilities.
- Ensure content aligns with the MEB 2025 English curriculum (Waymark series).
Topics to cover: {topic_info}
"""
    if include_clil:
        prompt += "\n- Include a CLIL component related to cybersecurity, digital technology, or interdisciplinary topics."
    if include_reflection:
        prompt += "\n- Include a reflection question for students to evaluate their learning process."
    return prompt.strip()

def generate_lesson_plan_prompt(grade, unit):
    unit_data = meb_curriculum[grade][unit]
    topic_info = " | ".join([f"{k}: {v}" for k, v in unit_data.items()])
    prompt = f"""
You are an English curriculum expert creating a lesson plan for a {grade} class (CEFR B1.1, MEB 2025 Curriculum).
Unit: "{unit}"
Include:
- Title
- Objective (1-2 sentences)
- Stages with durations:
  * Warm-Up / Lead-In (engaging activity, 5-10 min)
  * Main Activity (grammar, vocabulary, speaking, writing, or pronunciation practice, 30-35 min)
  * Wrap-Up / Consolidation (quick review or check, 5-10 min)
- Key vocabulary, grammar, and pronunciation list
- Materials (simple list, e.g., worksheets, whiteboard)
- Keep output concise (under 500 tokens) for lightweight model.
- Align with the MEB 2025 English curriculum (Waymark series).
Key topics: {topic_info}
"""
    if include_clil:
        prompt += "\n- Include a CLIL activity related to cybersecurity, digital technology, or interdisciplinary topics."
    if include_reflection:
        prompt += "\n- Include a reflection activity for students to evaluate their learning process."
    return prompt.strip()

def generate_rubric_prompt(grade, unit, skill):
    return f"""
You are an EFL assessment specialist creating a grading rubric for {skill} in {grade} (CEFR B1.1, MEB 2025 Curriculum).
Unit: "{unit}"
Include:
- At least 3 criteria relevant to {skill} (e.g., accuracy, fluency, content for Writing).
- 3 performance levels: Excellent, Good, Needs Improvement.
- Clear, concise descriptors for each level under each criterion.
- Use headings and bullet points (no tables).
- Keep output concise (under 300 tokens) for lightweight model.
- Align with the MEB 2025 English curriculum (Waymark series).
Topics: {meb_curriculum[grade][unit].get(skill, "")}
""".strip()

def generate_differentiation_prompt(grade, unit, skill, diff_type):
    topic_info = meb_curriculum[grade][unit].get(skill, "")
    if diff_type == "Destekleyici":
        intro = "Create a SUPPORTING activity for students who need extra help."
        detail = "Use simpler, scaffolded tasks (e.g., guided fill-in-the-blanks, matching, controlled practice)."
    else:
        intro = "Create an ADVANCED activity for students ready for more challenge."
        detail = "Require higher-order thinking (e.g., short opinion writing, problem-solving, mini project, debate prompts)."
    
    prompt = f"""
You are an expert English teacher creating differentiated materials for a {grade} class (CEFR B1.1, MEB 2025 Curriculum).
{intro}
Unit: "{unit}"
Focus: "{skill}"
Instructions:
- Activity: Provide a clear, classroom-ready task. {detail}
- Objective: State the learning goal for this group.
- Implementation: Step-by-step how the teacher runs it (timings optional).
- Keep output concise (under 300 tokens) for lightweight model.
- Align with the MEB 2025 English curriculum (Waymark series).
Topics: {topic_info}
"""
    if include_clil:
        prompt += "\n- Include a CLIL component related to cybersecurity, digital technology, or interdisciplinary topics."
    if include_reflection:
        prompt += "\n- Include a reflection question for students to evaluate their learning."
    return prompt.strip()

# -----------------------------
# PDF OLUŞTURUCU
# -----------------------------
def create_pdf(content, filename, is_teacher_copy=False, is_worksheet=False, grade="9. Sınıf", unit=""):
    pdf = canvas.Canvas(filename, pagesize=A4)
    pdf.setTitle(f"MEB English Material - {grade} - {unit}")
    pdf.setAuthor("QuickSheet AI Assistant (Powered by Hugging Face)")
    pdf.setCreator("QuickSheet AI Assistant")

    # Başlık ve üst bilgi
    y = 800
    pdf.setFont("DejaVuSans-Bold", 16)
    pdf.drawCentredString(A4[0] / 2.0, y, f"MEB English Material - {grade} - {unit}")
    y -= 30
    pdf.setFont("DejaVuSans", 10)
    pdf.drawString(50, y, f"Generated by QuickSheet AI Assistant (Powered by Hugging Face)")
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
        elif text.startswith("## "):
            pdf.setFont("DejaVuSans-Bold", 11)
            text = text[3:]
        else:
            pdf.setFont("DejaVuSans", 10)

        # Uzun satırları böl
        if len(text) > 80:
            words = text.split()
            current_line = ""
            for word in words:
                if pdf.stringWidth(current_line + word, "DejaVuSans", 10) < A4[0] - 100:
                    current_line += word + " "
                else:
                    pdf.drawString(50, y, current_line.strip())
                    y -= 14
                    current_line = word + " "
                    if y < 60:
                        pdf.showPage()
                        y = 800
                        pdf.setFont("DejaVuSans", 10)
                        pdf.drawString(50, y, f"MEB English Material - {grade} - {unit} (Continued)")
                        y -= 20
            text = current_line.strip()

        # Sayfa altına gelindiyse yeni sayfa
        if y < 60:
            pdf.showPage()
            y = 800
            pdf.setFont("DejaVuSans", 10)
            pdf.drawString(50, y, f"MEB English Material - {grade} - {unit} (Continued)")
            y -= 20

        pdf.drawString(50, y, text)
        y -= 14

    pdf.save()
    return filename

# -----------------------------
# ANA AKIŞ
# -----------------------------
if st.button("✨ İçeriği Üret", key="generate_content"):
    with st.spinner(f"{selected_tool} oluşturuluyor... (Hugging Face ile)"):
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
                st.error("Geçersiz üretim modu seçimi.")
                st.stop()

            # Hugging Face modeliyle içerik üret
            for attempt in range(3):  # 3 deneme
                try:
                    response = generator(
                        prompt_text,
                        max_length=500,  # DistilGPT-2 için uygun
                        num_return_sequences=1,
                        truncation=True,
                        pad_token_id=generator.tokenizer.eos_token_id
                    )
                    ai_content = response[0]["generated_text"].strip()
                    if ai_content:
                        break
                except Exception as model_error:
                    st.warning(f"Deneme {attempt+1} başarısız: {model_error}. Yeniden deneniyor...")
                    time.sleep(1)
            else:
                st.error("Modelden yanıt alınamadı. Daha az soru seçin veya tekrar deneyin.")
                st.stop()

            if not ai_content:
                st.error("Model boş içerik döndürdü. Promptu gözden geçirin veya tekrar deneyin.")
                st.stop()

            st.subheader(f"Oluşturulan: {selected_tool}")
            edited_content = st.text_area("İçeriği Düzenle", ai_content, height=500, key="edit_content")

            # PDF üretimi
            if selected_tool == "Çalışma Sayfası":
                student_pdf = create_pdf(
                    edited_content, "ogrenci_calisma_sayfasi.pdf",
                    is_teacher_copy=False, is_worksheet=True,
                    grade=selected_grade, unit=selected_unit
                )
                with open(student_pdf, "rb") as f:
                    st.download_button("📄 Öğrenci PDF İndir", f, file_name="ogrenci_calisma_sayfasi.pdf", key="student_pdf")

                teacher_pdf = create_pdf(
                    edited_content, "ogretmen_calisma_sayfasi.pdf",
                    is_teacher_copy=True, is_worksheet=True,
                    grade=selected_grade, unit=selected_unit
                )
                with open(teacher_pdf, "rb") as f:
                    st.download_button("🔑 Öğretmen PDF (Cevap Anahtarlı) İndir", f, file_name="ogretmen_calisma_sayfasi.pdf", key="teacher_pdf")

            else:
                out_name = f"{selected_tool.lower().replace(' ', '_')}.pdf"
                pdf_path = create_pdf(edited_content, out_name, is_teacher_copy=False, is_worksheet=False,
                                      grade=selected_grade, unit=selected_unit)
                with open(pdf_path, "rb") as f:
                    st.download_button("📄 PDF Olarak İndir", f, file_name=out_name, key="single_pdf")

            st.success("İçerik başarıyla oluşturuldu! (Hugging Face ile)")

        except Exception as e:
            st.error(f"Hata oluştu: {e}. Daha az soru seçin veya internet bağlantınızı kontrol edin.")

# -----------------------------
# İPUCU VE NOTLAR
# -----------------------------
st.caption("**İpucu**: İçerik zayıfsa soru sayısını azaltın (örn. 6), promptu düzenleyin veya tekrar deneyin. DistilGPT-2 hafif bir modeldir, daha güçlü model için premium bulut planı gerekebilir.")
st.markdown("**Not**: Bu uygulama Hugging Face Transformers (MIT lisansı) ile çalışır. MEB 2025 müfredatına uygundur.")
