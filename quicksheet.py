import streamlit as st
import os
import requests
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from docx import Document
from docx.shared import Pt
import time
import google.generativeai as genai
import io
import re
import random
from datetime import date

# -----------------------------
# SAYFA YAPISI VE BAŞLANGIÇ AYARLARI (VERSİYON GÜNCELLENDİ)
# -----------------------------
st.set_page_config(page_title="QuickSheet v1.7: 9. Sınıf Asistanı", page_icon="⚡", layout="wide")
st.title("⚡ Quicksheet v1.7: 9. Sınıf İngilizce Öğretmeni Asistanı")
st.markdown("Türkiye Yüzyılı Maarif Modeli'ne uygun, **çok dilli ve düzenli formatta** materyaller üretin.")

# Session State Başlatma
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = ""
if 'last_tool' not in st.session_state:
    st.session_state.last_tool = ""
if 'final_prompt' not in st.session_state:
    st.session_state.final_prompt = ""

# Gemini API anahtarı
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except (KeyError, AttributeError):
    st.error("Gemini API anahtarı bulunamadı veya geçersiz. Lütfen Streamlit Cloud secrets'a 'GEMINI_API_KEY' ekleyin.")
    st.stop()

# -----------------------------
# FONT YÜKLEME
# -----------------------------
@st.cache_resource
def load_font():
    font_dir = "fonts"
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)
    font_files = {
        "DejaVuSans": "https://github.com/googlefonts/dejavu-fonts/raw/main/ttf/DejaVuSans.ttf",
        "DejaVuSans-Bold": "https://github.com/googlefonts/dejavu-fonts/raw/main/ttf/DejaVuSans-Bold.ttf"
    }
    try:
        for name, url in font_files.items():
            font_path = os.path.join(font_dir, f"{name}.ttf")
            if not os.path.exists(font_path):
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                with open(font_path, "wb") as f:
                    f.write(response.content)
            pdfmetrics.registerFont(TTFont(name, font_path))
        return True
    except Exception as e:
        st.error(f"Font yüklenirken hata oluştu: {e}")
        return False
font_loaded = load_font()

# -----------------------------
# MÜFREDAT BİLGİSİ
# -----------------------------
meb_curriculum = {
    "9. Sınıf": {
        "Theme 1: School Life": {
            "Grammar": ["Simple Present (to be)", "Modal 'can' (possibility/ability)", "Simple Past (was/were)"],
            "Vocabulary": ["Countries and Nationalities", "Languages and Capitals", "Tourist Attractions", "School Rules"],
            "Reading": ["School Life Descriptions", "Cultural Exchange Texts"],
            "Speaking": ["Introducing Oneself", "Describing Countries", "Talking about Tourist Spots"],
            "Writing": ["Paragraph about School Rules", "Paragraph about a Travel Destination"],
            "Pronunciation": ["Long and short vowels (/æ/, /ɑː/, /eɪ/)", "Consonants (/b/, /k/, /d/)"]
        },
        "Theme 2: Classroom Life": {
            "Grammar": ["Simple Present (routines)", "Adverbs of Frequency", "Imperatives"],
            "Vocabulary": ["Daily Routines", "Study Habits", "Classroom Objects", "Instructions"],
            "Reading": ["Texts on Daily Routines", "Study Habits Articles"],
            "Speaking": ["Describing a Typical School Day", "Giving Instructions"],
            "Writing": ["Paragraph about Personal Study Habits"],
            "Pronunciation": ["Vowels (/e/, /æ/)", "Consonants (/f/, /g/, /dʒ/, /h/)"]
        },
        "Theme 3: Personal Life": {
            "Grammar": ["Adjectives (personality/appearance)", "'too' / 'enough'"],
            "Vocabulary": ["Physical Appearance", "Personality Traits", "Hobbies and Interests"],
            "Reading": ["Descriptions of People", "Personal Blogs about Hobbies"],
            "Speaking": ["Describing a Friend's Personality", "Talking about Hobbies"],
            "Writing": ["A Short Description of a Family Member"],
            "Pronunciation": ["Vowels (/iː/, /ɪ/, /aɪ/)", "Consonants (/ʒ/, /k/, /l/)"]
        },
        "Theme 4: Family Life": {
            "Grammar": ["Simple Present (jobs and work routines)", "Prepositions of place (in/on/at for workplaces)"],
            "Vocabulary": ["Family members", "Jobs and Occupations", "Workplaces", "Work Activities"],
            "Reading": ["Texts about different family members' jobs", "Daily routines of professionals"],
            "Speaking": ["Talking about family members' occupations", "Asking about jobs"],
            "Writing": ["A paragraph about a family member's job"],
            "Pronunciation": ["Vowels (/ɒ/, /ɔː/)", "Consonants (/m/, /n/, /p/)"]
        },
        "Theme 5: House & Neighbourhood": {
            "Grammar": ["Present Continuous", "There is/are", "Possessive adjectives"],
            "Vocabulary": ["Types of houses", "Rooms", "Furniture", "Household chores"],
            "Reading": ["Descriptions of houses or neighborhoods"],
            "Speaking": ["Describing your own house", "Describing a picture of a room"],
            "Writing": ["A short text about your dream house"],
            "Pronunciation": ["Consonants (/q/ as in quick, /r/, /s/, /ʃ/ as in shower)"]
        },
        "Theme 6: City & Country": {
            "Grammar": ["Present Simple vs. Present Continuous", "Wh- questions", "'or' for options"],
            "Vocabulary": ["Food culture", "Food festivals", "Ingredients", "Local and international dishes"],
            "Reading": ["Texts about food festivals or traditional cuisines"],
            "Speaking": ["Role-playing at a food festival", "Asking for options"],
            "Writing": ["A blog post about a food festival you attended"],
            "Pronunciation": ["Vowels (/uː/, /ʊ/)", "Consonants (/t/, /ð/, /θ/, /v/)"]
        },
        "Theme 7: World & Nature": {
            "Grammar": ["Simple Past (was/were, there was/were)", "Modal 'should' (advice)"],
            "Vocabulary": ["Endangered animals", "Habitats", "Environmental problems (habitat loss, pollution)"],
            "Reading": ["Texts about endangered species and conservation efforts"],
            "Speaking": ["Giving advice on how to protect nature", "Discussing environmental problems"],
            "Writing": ["A short paragraph about an endangered animal"],
            "Pronunciation": ["Diphthongs (/eə/ as in bear, /ɪə/ as in deer)", "Consonants (/w/, /ks/)"]
        },
        "Theme 8: Universe & Future": {
            "Grammar": ["Future Simple (will) for predictions and beliefs", "Simple Present for describing films"],
            "Vocabulary": ["Films and film genres", "Futuristic ideas (robots, space exploration)", "Technology"],
            "Reading": ["Film reviews", "Short texts about future technology"],
            "Speaking": ["Making predictions about the future", "Talking about favorite films"],
            "Writing": ["A short futuristic story", "A review of a sci-fi film"],
            "Pronunciation": ["Diphthong (/əʊ/ as in show)", "Consonants (/j/ as in year, /z/)"]
        }
    }
}

# -----------------------------
# SIDEBAR - KULLANICI ARAYÜZÜ
# -----------------------------
with st.sidebar:
    st.header("1. Adım: Seçimlerinizi Yapın")
    selected_grade = "9. Sınıf"
    units = list(meb_curriculum[selected_grade].keys())
    selected_unit = st.selectbox("Ünite Seçin", units)
    
    selected_tool = st.radio(
        "Materyal Türü Seçin",
        ["Günlük Ders Planı", "Çalışma Sayfası", "Ders Planı (Genel)", "Dinleme Aktivitesi Senaryosu", "Ünite Tekrar Testi", "Değerlendirme Rubriği", "Ek Çalışma (Farklılaştırılmış)"],
        captions=["Belirli bir konu için 40dk'lık plan", "Alıştırma kağıdı üretir", "Ünite geneli için ders planı", "Dinleme metni ve soruları yazar", "Üniteyi özetleyen test hazırlar", "Puanlama anahtarı oluşturur", "Destekleyici veya ileri düzey aktivite"]
    )
    
    plan_language = "İngilizce"
    if selected_tool in ["Günlük Ders Planı", "Ders Planı (Genel)"]:
        plan_language = st.selectbox("Plan Dili", ["Türkçe", "İngilizce"])

    if selected_tool == "Günlük Ders Planı":
        st.date_input("Ders Tarihi", value=date.today(), key="lesson_date")
        st.text_input("Bugünkü Dersin Konusu / Odak Noktası", placeholder="Örn: Kelime tekrarı, Sayfa 28, Alıştırma 3", key="lesson_context")

    skill_needed = selected_tool in ["Çalışma Sayfası", "Değerlendirme Rubriği", "Ek Çalışma (Farklılaştırılmış)", "Ünite Tekrar Testi"]
    if skill_needed:
        skill_options = list(meb_curriculum[selected_grade][selected_unit].keys())
        selected_skill = st.selectbox("Odaklanılacak Beceriyi Seçin", skill_options)
        
        topic_options = meb_curriculum[selected_grade][selected_unit].get(selected_skill, [])
        if topic_options:
            selected_topics = st.multiselect(
                "Hangi Konulara Odaklanılsın?",
                topic_options,
                default=topic_options[0] if topic_options else []
            )
        else:
            selected_topics = []
            
    else:
        selected_skill = "Genel"
        selected_topics = []

    with st.expander("Gelişmiş Ayarlar"):
        include_clil = st.checkbox("CLIL İçeriği Ekle (Teknoloji, Bilim vb.)")
        include_reflection = st.checkbox("Yansıtma Aktivitesi Ekle (Öz değerlendirme)")
        
        if selected_tool in ["Çalışma Sayfası", "Ünite Tekrar Testi"]:
            num_questions = st.slider("Soru Sayısı", 3, 10, 6)
        
        if selected_tool == "Ek Çalışma (Farklılaştırılmış)":
            differentiation_type = st.radio("Aktivite Düzeyi", ["Destekleyici (Supporting)", "İleri Düzey (Expansion)"])

# -----------------------------
# PROMPT OLUŞTURMA FONKSİYONLARI
# -----------------------------
def get_activity_suggestions(skill):
    suggestions = {
        "Grammar": ["a sentence transformation task", "a correct-the-mistake exercise", "a sentence building task from jumbled words"],
        "Vocabulary": ["a matching exercise (word to definition)", "a fill-in-the-blanks story using a word bank", "an odd-one-out task"],
        "Reading": ["a short text with True/False questions", "a text where students match paragraphs to headings"],
        "Speaking": ["a role-play scenario", "a set of discussion questions", "a picture description task"],
        "Writing": ["a guided paragraph writing task with prompts", "an email writing task based on a scenario"],
        "Pronunciation": ["a minimal pairs discrimination exercise", "a tongue twister", "a 'find the sound' activity"]
    }
    return random.choice(suggestions.get(skill, ["a multiple-choice exercise"]))

def create_prompt(tool, **kwargs):
    language_instruction = f"The entire output for this plan MUST be in {kwargs.get('language')}."
    
    base_prompt = f"""
Act as an expert English teacher for the Turkish Ministry of Education's new 'Türkiye Yüzyılı Maarif Modeli'.
Create a high-quality, engaging material for a {kwargs.get('grade')} class (CEFR B1.1), aligned with the WAYMARK series.
The content must be entirely in English, unless a different language is specified for the output.
Unit: "{kwargs.get('unit')}"
"""
    
    topic_text = ""
    if kwargs.get('topics'):
        topic_text = f"**Strict Focus:** The material MUST ONLY focus on the following topic(s): {', '.join(kwargs.get('topics'))}."

    prompts = {
        "Günlük Ders Planı": f"""
        **Task:** Create a detailed 40-minute daily lesson plan for {kwargs.get('date')}.
        **Today's Specific Focus:** "{kwargs.get('context')}"
        {language_instruction}

        The plan MUST be well-structured, using clear headings (like **Objective:**, **Materials:**, **Warm-Up (5 min):** etc.) and bullet points.
        It must include:
        1.  **Objective(s):** Very specific goals for this single lesson.
        2.  **Materials:** A simple list.
        3.  **Lesson Stages (with exact timings):** Warm-Up (5 min), Presentation/Activity 1 (15 min), Practice/Activity 2 (15 min), Wrap-Up & Homework (5 min).
        - The plan must be practical and student-centered.
        """,
        "Çalışma Sayfası": f"""
        Focus Skill: "{kwargs.get('skill')}"
        {topic_text}
        
        Create a worksheet with exactly {kwargs.get('num_questions')} questions.
        - **Instruction for AI:** Ensure activities are diverse. Use a variety of task types like {get_activity_suggestions(kwargs.get('skill'))}.
        - **Strict Rule:** Do NOT include questions for any other skill.
        - Start with a title and a one-sentence instruction.
        - Use markdown for formatting (e.g., **bold** for headings).
        - End with a separate 'Answer Key' section.
        """,
        "Ders Planı (Genel)": f"""
        Create a 40-minute lesson plan for the selected unit.
        {language_instruction}
        - The plan must be well-structured with clear headings and bullet points.
        - Include: Objective, Key Language, Materials.
        - Structure in three stages: Warm-Up/Lead-In (5-10 min), Main Activity (25-30 min), and Wrap-Up/Consolidation (5 min).
        """,
        "Dinleme Aktivitesi Senaryosu": f"""
        Create a listening activity.
        - **Crucial Instruction for AI:** The audio script MUST be completely original and unique. Do NOT repeat scripts.
        - Write a short, natural-sounding audio script (100-150 words).
        - After the script, create 5 comprehension questions.
        - End with 'Audio Script' and 'Answer Key' sections.
        """,
        "Ünite Tekrar Testi": f"""
        Create a cumulative unit review test with {kwargs.get('num_questions')} questions.
        - The test must focus on the selected skill: {kwargs.get('skill')} and topics: {', '.join(kwargs.get('topics', []))}.
        - Include varied question formats.
        - End with an 'Answer Key' section.
        """,
        "Değerlendirme Rubriği": f"""
        Focus Skill: "{kwargs.get('skill')}"
        {topic_text}
        Create a simple assessment rubric.
        - Use 3 levels: 'Excellent', 'Good', 'Needs Improvement'.
        - Define 3 clear criteria.
        - Provide a brief descriptor for each level.
        """,
        "Ek Çalışma (Farklılaştırılmış)": f"""
        Focus Skill: "{kwargs.get('skill')}"
        Activity Level: "{kwargs.get('diff_type')}"
        {topic_text}
        
        Create a differentiated activity.
        - If 'Supporting', design a highly-structured task.
        - If 'Expansion', design a task requiring creative or critical thinking.
        - Include an objective and step-by-step instructions.
        """
    }
    
    final_prompt = base_prompt + prompts[tool]
    
    if kwargs.get('clil'):
        final_prompt += "\n- IMPORTANT: Integrate a CLIL component related to technology, science, or digital literacy."
    if kwargs.get('reflection'):
        final_prompt += "\n- IMPORTANT: Add a short, simple reflection question for students to think about their learning."
        
    return final_prompt.strip()

# -----------------------------
# GEMINI API ÇAĞRISI
# -----------------------------
@st.cache_data
def call_gemini_api(_prompt_text):
    try:
        response = model.generate_content(
            _prompt_text,
            generation_config={"max_output_tokens": 2048, "temperature": 0.9}
        )
        return response.text.strip()
    except Exception as e:
        return f"API Hatası: {e}"

# -----------------------------
# ÇIKTI OLUŞTURMA FONKSİYONLARI (PDF & DOCX - GÜNCELLENDİ)
# -----------------------------
def create_pdf(content, grade, unit):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    def draw_page_header_footer(page_number):
        p.saveState()
        p.setFont("DejaVuSans", 8)
        p.drawString(50, height - 40, f"{grade} - {unit}")
        p.drawRightString(width - 50, height - 40, "QuickSheet v1.7")
        p.drawCentredString(width / 2.0, 30, f"Sayfa {page_number}")
        p.restoreState()
        
    page_num = 1
    draw_page_header_footer(page_num)
    y = height - 70
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        
        if y < 60:
            p.showPage()
            page_num += 1
            draw_page_header_footer(page_num)
            y = height - 70
        
        x = 50
        if line.startswith('# '):
            p.setFont("DejaVuSans-Bold", 14)
            p.drawString(x, y, line[2:])
            y -= 25
        elif line.startswith('- '):
            p.drawString(x + 10, y, f"• {line[2:]}")
            y -= 20
        else:
            parts = re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    p.setFont("DejaVuSans-Bold", 10)
                    text_to_draw = part[2:-2]
                else:
                    p.setFont("DejaVuSans", 10)
                    text_to_draw = part
                
                # Word wrapping for long lines
                if x + p.stringWidth(text_to_draw, p._fontname, p._fontsize) > width - 50:
                    y -= 20
                    x = 50
                
                p.drawString(x, y, text_to_draw)
                x += p.stringWidth(text_to_draw, p._fontname, p._fontsize)
            y -= 20

    p.save()
    buffer.seek(0)
    return buffer

def create_docx(content):
    buffer = io.BytesIO()
    doc = Document()
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            doc.add_paragraph()
            continue

        if line.startswith('# '):
            p = doc.add_paragraph(line[2:])
            p.style = 'Heading 1'
        elif line.startswith('- '):
            p = doc.add_paragraph(line[2:], style='List Bullet')
        else:
            p = doc.add_paragraph()
            parts = re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    p.add_run(part[2:-2]).bold = True
                else:
                    p.add_run(part)
            
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# -----------------------------
# ANA UYGULAMA AKIŞI
# -----------------------------
if st.button("✨ 1. Adım: Materyal Taslağını Oluştur", type="primary", use_container_width=True):
    if skill_needed and not selected_topics:
        st.warning("Lütfen en az bir alt konu seçin.")
        st.stop()
    if selected_tool == "Günlük Ders Planı" and not st.session_state.lesson_context:
        st.warning("Lütfen 'Bugünkü Dersin Konusu' alanını doldurun.")
        st.stop()

    prompt_args = {
        "grade": selected_grade, "unit": selected_unit, "skill": selected_skill,
        "topics": selected_topics, "clil": include_clil, "reflection": include_reflection,
        "language": plan_language
    }
    if selected_tool in ["Çalışma Sayfası", "Ünite Tekrar Testi"]:
        prompt_args["num_questions"] = num_questions
    if selected_tool == "Ek Çalışma (Farklılaştırılmış)":
        prompt_args["diff_type"] = differentiation_type.split(" ")[0]
    if selected_tool == "Günlük Ders Planı":
        prompt_args["date"] = st.session_state.lesson_date
        prompt_args["context"] = st.session_state.lesson_context

    st.session_state.final_prompt = create_prompt(selected_tool, **prompt_args)
    st.session_state.last_tool = selected_tool
    st.session_state.ai_content = "" 

if 'final_prompt' in st.session_state and st.session_state.final_prompt:
    st.subheader("2. Adım: Komutu Gözden Geçirin (İsteğe Bağlı)")
    edited_prompt = st.text_area("Yapay Zeka Komutu", value=st.session_state.final_prompt, height=250)

    if st.button("🚀 3. Adım: Yapay Zeka ile İçeriği Üret", use_container_width=True):
         with st.spinner(f"{st.session_state.last_tool} üretiliyor..."):
            call_gemini_api.clear()
            st.session_state.ai_content = call_gemini_api(edited_prompt)
            st.session_state.final_prompt = ""

if st.session_state.ai_content:
    st.subheader(f"Üretilen İçerik: {st.session_state.last_tool}")
    edited_content = st.text_area("İçeriği Düzenleyin", value=st.session_state.ai_content, height=400)
    
    st.subheader("Son Adım: İndirin")
    col1, col2 = st.columns(2)
    with col1:
        docx_buffer = create_docx(edited_content)
        st.download_button(
            label="📄 Word Olarak İndir (.docx)", data=docx_buffer,
            file_name=f"{st.session_state.last_tool.replace(' ', '_').lower()}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True
        )
    with col2:
        if font_loaded:
            pdf_buffer = create_pdf(edited_content, selected_grade, selected_unit)
            st.download_button(
                label="📑 PDF Olarak İndir", data=pdf_buffer,
                file_name=f"{st.session_state.last_tool.replace(' ', '_').lower()}.pdf",
                mime="application/pdf", use_container_width=True
            )
        else:
            st.warning("Font yüklenemediği için PDF çıktısı devre dışı.")

st.divider()
st.caption("⚡ **Quicksheet v1.7** | Google Gemini API ile güçlendirilmiştir. | MEB 'Türkiye Yüzyılı Maarif Modeli' (2025) 9. Sınıf İngilizce müfredatına uygundur.")
st.caption(f"Geliştirici: Can AKALIN | İletişim: canakalin59@gmail.com | [Instagram](https://instagram.com/can_akalin)")

