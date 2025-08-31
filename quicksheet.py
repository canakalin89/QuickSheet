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

# -----------------------------
# SAYFA YAPISI VE BAŞLANGIÇ AYARLARI
# -----------------------------
st.set_page_config(page_title="QuickSheet v2.1", page_icon="⚡", layout="wide")
st.title("⚡ QuickSheet v2.1: Akıllı MEB İngilizce Asistanı")
st.markdown("9. Sınıf (B1.1) 'Century of Türkiye' (Maarif Modeli) müfredatına uygun, **çeşitli ve odaklı** materyaller üretin.")

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
# MÜFREDAT BİLGİSİ (KONU SEÇİMİ İÇİN GÜNCELLENDİ)
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
        # Diğer üniteler de benzer şekilde listeye çevrilebilir
    }
}

# -----------------------------
# SIDEBAR - KULLANICI ARAYÜZÜ (KONU SEÇİMİ EKLENDİ)
# -----------------------------
with st.sidebar:
    st.header("1. Adım: Seçimlerinizi Yapın")
    selected_grade = "9. Sınıf"
    units = list(meb_curriculum[selected_grade].keys())
    selected_unit = st.selectbox("Ünite Seçin", units)
    
    selected_tool = st.radio(
        "Materyal Türü Seçin",
        ["Çalışma Sayfası", "Ders Planı", "Dinleme Aktivitesi Senaryosu", "Ünite Tekrar Testi", "Değerlendirme Rubriği", "Ek Çalışma (Farklılaştırılmış)"],
        captions=["Alıştırma kağıdı üretir", "40dk'lık ders planı oluşturur", "Dinleme metni ve soruları yazar", "Üniteyi özetleyen test hazırlar", "Puanlama anahtarı oluşturur", "Destekleyici veya ileri düzey aktivite"]
    )

    skill_needed = selected_tool in ["Çalışma Sayfası", "Değerlendirme Rubriği", "Ek Çalışma (Farklılaştırılmış)", "Ünite Tekrar Testi"]
    if skill_needed:
        skill_options = list(meb_curriculum[selected_grade][selected_unit].keys())
        selected_skill = st.selectbox("Odaklanılacak Beceriyi Seçin", skill_options)
        
        # YENİ ÖZELLİK: ALT KONU SEÇİMİ
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
# PROMPT OLUŞTURMA FONKSİYONLARI (ÇEŞİTLİLİK VE ODAKLANMA İÇİN GÜNCELLENDİ)
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
    base_prompt = f"""
Act as an expert English teacher for the Turkish Ministry of Education's new 'Century of Türkiye' model.
Create a high-quality, engaging material for a {kwargs.get('grade')} class (CEFR B1.1), aligned with the WAYMARK series.
The content must be entirely in English.
Unit: "{kwargs.get('unit')}"
"""
    
    topic_text = ""
    if kwargs.get('topics'):
        topic_text = f"**Strict Focus:** The material MUST ONLY focus on the following topic(s): {', '.join(kwargs.get('topics'))}."

    prompts = {
        "Çalışma Sayfası": f"""
        Focus Skill: "{kwargs.get('skill')}"
        {topic_text}
        
        Create a worksheet with exactly {kwargs.get('num_questions')} questions.
        - **Instruction for AI:** Ensure the activities are diverse and creative. Use a variety of task types like {get_activity_suggestions(kwargs.get('skill'))}. Do NOT use only one question format.
        - **Strict Rule:** Do NOT include questions for any other skill. If the focus is Vocabulary, there should be NO Grammar questions.
        - Start with a clear title and a one-sentence instruction for students.
        - End with a separate 'Answer Key' section.
        """,
        # ... (Diğer prompt'lar aynı kalabilir veya benzer şekilde güncellenebilir) ...
        "Ders Planı": f"""
        Create a 40-minute lesson plan.
        - Include: Objective, Key Language (Vocab & Grammar), Materials.
        - Structure in three stages with timings: Warm-Up/Lead-In (5-10 min), Main Activity (25-30 min), and Wrap-Up/Consolidation (5 min).
        - Activities must be communicative and interactive.
        """,
        "Dinleme Aktivitesi Senaryosu": f"""
        Create a listening activity.
        - Write a short, natural-sounding audio script (dialogue or monologue, 100-150 words) suitable for B1.1 level. The script must include vocabulary and grammar from the unit.
        - After the script, create 5 comprehension questions (e.g., multiple choice, True/False).
        - End with a separate 'Audio Script' section and an 'Answer Key' section.
        """,
        "Ünite Tekrar Testi": f"""
        Create a cumulative unit review test with {kwargs.get('num_questions')} questions.
        - The test must cover topics from the entire unit.
        - Include a variety of question formats.
        - End with a separate 'Answer Key' section.
        """,
        "Değerlendirme Rubriği": f"""
        Focus Skill: "{kwargs.get('skill')}"
        {topic_text}
        Create a simple assessment rubric for a task related to the selected topic.
        - Use 3 performance levels: 'Excellent', 'Good', 'Needs Improvement'.
        - Define 3 clear criteria relevant to the skill.
        - Provide a brief, clear descriptor for each level.
        """,
        "Ek Çalışma (Farklılaştırılmış)": f"""
        Focus Skill: "{kwargs.get('skill')}"
        Activity Level: "{kwargs.get('diff_type')}"
        {topic_text}
        
        Create a differentiated activity.
        - If 'Supporting', design a highly-structured, scaffolded task.
        - If 'Expansion', design a task that requires more creative or critical thinking.
        - Include a clear objective and step-by-step instructions for the teacher.
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
            generation_config={"max_output_tokens": 2048, "temperature": 0.8}
        )
        return response.text.strip()
    except Exception as e:
        return f"API Hatası: {e}"

# -----------------------------
# ÇIKTI OLUŞTURMA FONKSİYONLARI (PDF & DOCX)
# -----------------------------
def create_pdf(content, grade, unit):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    def draw_page_content(page_number):
        p.setFont("DejaVuSans-Bold", 10)
        p.drawString(50, height - 40, f"{grade} - {unit}")
        p.setFont("DejaVuSans", 8)
        p.drawRightString(width - 50, height - 40, "QuickSheet v2.1")
        p.line(50, height - 50, width - 50, height - 50)
        p.drawCentredString(width / 2.0, 30, f"Page {page_number}")
        
    page_num = 1
    draw_page_content(page_num)
    y = height - 70
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        
        is_heading = False
        font_name = "DejaVuSans"
        font_size = 10

        if line.startswith('# '):
            font_name = "DejaVuSans-Bold"
            font_size = 14
            line = line[2:]
            is_heading = True
        elif line.startswith('**') and line.endswith('**'):
             font_name = "DejaVuSans-Bold"
             line = line[2:-2]

        if y < 60:
            p.showPage()
            page_num += 1
            draw_page_content(page_num)
            y = height - 70

        p.setFont(font_name, font_size)
        p.drawString(50, y, line)
        
        y -= 18
        if is_heading:
            y -= 5

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
        if line.startswith('# '):
            doc.add_paragraph(line[2:], style='Heading 1')
        elif '**' in line:
            p = doc.add_paragraph()
            parts = re.split(r'(\*\*.*?\*\*)', line)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    p.add_run(part[2:-2]).bold = True
                else:
                    p.add_run(part)
        else:
            doc.add_paragraph(line)
            
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# -----------------------------
# ANA UYGULAMA AKIŞI
# -----------------------------
if st.button("✨ 1. Adım: Materyal Taslağını Oluştur", type="primary", use_container_width=True):
    prompt_args = {
        "grade": selected_grade,
        "unit": selected_unit,
        "skill": selected_skill,
        "topics": selected_topics,
        "clil": include_clil,
        "reflection": include_reflection,
    }
    if selected_tool in ["Çalışma Sayfası", "Ünite Tekrar Testi"]:
        prompt_args["num_questions"] = num_questions
    if selected_tool == "Ek Çalışma (Farklılaştırılmış)":
        prompt_args["diff_type"] = differentiation_type.split(" ")[0]

    st.session_state.final_prompt = create_prompt(selected_tool, **prompt_args)
    st.session_state.last_tool = selected_tool
    st.session_state.ai_content = "" 

if 'final_prompt' in st.session_state and st.session_state.final_prompt:
    st.subheader("2. Adım: Komutu Gözden Geçirin ve Geliştirin (İsteğe Bağlı)")
    st.info("Aşağıdaki komut yapay zekaya gönderilecektir. Daha spesifik sonuçlar için üzerinde değişiklik yapabilirsiniz.")
    
    edited_prompt = st.text_area(
        "Yapay Zeka Komutu (Prompt)",
        value=st.session_state.final_prompt,
        height=250,
        key="prompt_editor"
    )

    if st.button("🚀 3. Adım: Yapay Zeka ile İçeriği Üret", use_container_width=True):
         with st.spinner(f"{st.session_state.last_tool} üretiliyor..."):
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
st.caption("⚡ **QuickSheet v2.1** | Google Gemini API ile güçlendirilmiştir. | MEB 'Yüzyılın Türkiye'si Eğitim Modeli' (2025) 9. Sınıf İngilizce müfredatına uygundur.")

