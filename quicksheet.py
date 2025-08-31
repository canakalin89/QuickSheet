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
import random # Çeşitlilik için eklendi

# -----------------------------
# SAYFA YAPISI VE BAŞLANGIÇ AYARLARI
# -----------------------------
st.set_page_config(page_title="QuickSheet v2.0", page_icon="⚡", layout="wide")
st.title("⚡ QuickSheet v2.0: Gelişmiş MEB İngilizce Öğretmen Asistanı")
st.markdown("9. Sınıf (B1.1) 'Century of Türkiye' (Maarif Modeli) müfredatına uygun çalışma kağıtları, ders planları, dinleme etkinlikleri ve daha fazlasını üretin.")

# Session State Başlatma (Oturum durumunu korumak için)
if 'ai_content' not in st.session_state:
    st.session_state.ai_content = ""
if 'last_tool' not in st.session_state:
    st.session_state.last_tool = ""
if 'final_prompt' not in st.session_state:
    st.session_state.final_prompt = ""


# Gemini API anahtarı (streamlit secrets'tan alınıyor) - HATA DÜZELTİLDİ
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except (KeyError, AttributeError):
    st.error("Gemini API anahtarı bulunamadı veya geçersiz. Lütfen Streamlit Cloud secrets'a 'GEMINI_API_KEY' ekleyin. Anahtarınızı https://ai.google.dev adresinden alabilirsiniz.")
    st.stop()


# -----------------------------
# FONT (PDF için Türkçe karakter desteği)
# -----------------------------
@st.cache_resource
def load_font():
    """
    PDF üretimi için DejaVuSans normal ve kalın fontlarını indirir ve kaydeder.
    Tekrar indirmeyi önlemek için bu kaynak önbelleğe alınır.
    """
    font_dir = "fonts"
    if not os.path.exists(font_dir):
        os.makedirs(font_dir)

    # İndirilecek font dosyaları ve URL'leri
    font_files = {
        "DejaVuSans": "https://github.com/googlefonts/dejavu-fonts/raw/main/ttf/DejaVuSans.ttf",
        "DejaVuSans-Bold": "https://github.com/googlefonts/dejavu-fonts/raw/main/ttf/DejaVuSans-Bold.ttf"
    }

    try:
        for name, url in font_files.items():
            font_path = os.path.join(font_dir, f"{name}.ttf")
            # Eğer font dosyası mevcut değilse indir
            if not os.path.exists(font_path):
                response = requests.get(url, timeout=20)
                response.raise_for_status()  # İndirme başarısız olursa (404 vb.) hata verir.
                with open(font_path, "wb") as f:
                    f.write(response.content)
            # Fontu reportlab kütüphanesine kaydet
            pdfmetrics.registerFont(TTFont(name, font_path))
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Font indirilirken bir ağ hatası oluştu: {e}. Lütfen internet bağlantınızı kontrol edin.")
        return False
    except Exception as e:
        st.error(f"Font yüklenirken bir hata oluştu: {e}. İndirilen dosya bozuk olabilir veya GitHub erişim sorunu yaşanıyor.")
        return False

font_loaded = load_font()

# -----------------------------
# MÜFREDAT BİLGİSİ (MEB 2025 - 9. SINIF)
# -----------------------------
meb_curriculum = {
    "9. Sınıf": {
        "Theme 1: School Life": {
            "Grammar": "Simple Present (to be), Modal 'can' (possibility/ability), Simple Past (was/were).",
            "Vocabulary": "Countries, nationalities, languages, capitals, tourist attractions, school rules.",
            "Reading": "Short texts about school life and cultural exchanges.",
            "Speaking": "Introducing oneself, describing countries and tourist spots.",
            "Writing": "A short paragraph about school rules or a travel destination.",
            "Pronunciation": "Long and short vowels: /æ/, /ɑː/, /eɪ/. Consonants: /b/, /k/, /d/."
        },
        "Theme 2: Classroom Life": {
            "Grammar": "Simple Present (routines), Adverbs of frequency, Imperatives.",
            "Vocabulary": "Daily and study routines, classroom objects, instructions.",
            "Reading": "Texts on daily routines and study habits.",
            "Speaking": "Describing daily routines or a typical school day.",
            "Writing": "A paragraph about personal study habits.",
            "Pronunciation": "Vowels: /e/, /æ/. Consonants: /f/, /g/, /dʒ/, /h/."
        },
        "Theme 3: Personal Life": {
            "Grammar": "Adjectives (personality/appearance), 'too'/'enough'.",
            "Vocabulary": "Physical appearance, personality traits, hobbies.",
            "Reading": "Descriptions of people, personal blogs about hobbies.",
            "Speaking": "Describing a friend's personality or appearance.",
            "Writing": "A short description of a family member or a famous person.",
            "Pronunciation": "Vowels: /iː/, /ɪ/, /aɪ/. Consonants: /ʒ/, /k/, /l/."
        },
        "Theme 4: Family Life": {
            "Grammar": "Simple Present (jobs and work routines), Prepositions of place (in/on/at for workplaces).",
            "Vocabulary": "Family members, jobs, workplaces, work activities.",
            "Reading": "Texts about different family members' jobs and their daily routines.",
            "Speaking": "Talking about family members' occupations.",
            "Writing": "A paragraph about a family member's job.",
            "Pronunciation": "Vowels: /ɒ/, /ɔː/. Consonants: /m/, /n/, /p/."
        },
         "Theme 5: House & Neighbourhood": {
            "Grammar": "Present Continuous, There is/are, Possessive adjectives.",
            "Vocabulary": "Types of houses, rooms, furniture, household chores.",
            "Reading": "Descriptions of houses or neighborhoods.",
            "Speaking": "Describing your own house or what people are doing in a picture.",
            "Writing": "A short text about your dream house.",
            "Pronunciation": "Consonants: /q/ (as in quick), /r/, /s/, /ʃ/ (as in shower)."
        },
        "Theme 6: City & Country": {
            "Grammar": "Present Simple vs. Present Continuous, Wh- questions, 'or' for options.",
            "Vocabulary": "Food culture, food festivals, ingredients, local and international dishes.",
            "Reading": "Texts about food festivals or traditional cuisines.",
            "Speaking": "Role-playing at a food festival, asking for options.",
            "Writing": "A blog post about a food festival you attended.",
            "Pronunciation": "Vowels: /uː/, /ʊ/. Consonants: /t/, /ð/, /θ/, /v/."
        },
        "Theme 7: World & Nature": {
            "Grammar": "Simple Past (was/were, there was/were), Modal 'should' (advice).",
            "Vocabulary": "Endangered animals, habitats, environmental problems (habitat loss, pollution).",
            "Reading": "Texts about endangered species and conservation efforts.",
            "Speaking": "Giving advice on how to protect nature.",
            "Writing": "A short paragraph about an endangered animal.",
            "Pronunciation": "Diphthongs: /eə/ (as in bear), /ɪə/ (as in deer). Consonants: /w/, /ks/."
        },
        "Theme 8: Universe & Future": {
            "Grammar": "Future Simple (will) for predictions and beliefs, Simple Present for describing films.",
            "Vocabulary": "Films, film genres, futuristic ideas (robots, space exploration), technology.",
            "Reading": "Film reviews or short texts about future technology.",
            "Speaking": "Making predictions about the future, talking about favorite films.",
            "Writing": "A short futuristic story or a review of a sci-fi film.",
            "Pronunciation": "Diphthong: /əʊ/ (as in show). Consonants: /j/ (as in year), /z/."
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
        ["Çalışma Sayfası", "Ders Planı", "Dinleme Aktivitesi Senaryosu", "Ünite Tekrar Testi", "Değerlendirme Rubriği", "Ek Çalışma (Farklılaştırılmış)"],
        captions=["Alıştırma kağıdı üretir", "40dk'lık ders planı oluşturur", "Dinleme metni ve soruları yazar", "Üniteyi özetleyen test hazırlar", "Puanlama anahtarı oluşturur", "Destekleyici veya ileri düzey aktivite"]
    )

    skill_needed = selected_tool in ["Çalışma Sayfası", "Değerlendirme Rubriği", "Ek Çalışma (Farklılaştırılmış)"]
    if skill_needed:
        skill_options = list(meb_curriculum[selected_grade][selected_unit].keys())
        selected_skill = st.selectbox("Odaklanılacak Beceriyi Seçin", skill_options)
    else:
        selected_skill = "Genel"

    with st.expander("Gelişmiş Ayarlar"):
        include_clil = st.checkbox("CLIL İçeriği Ekle (Teknoloji, Bilim vb.)")
        include_reflection = st.checkbox("Yansıtma Aktivitesi Ekle (Öz değerlendirme)")
        
        if selected_tool in ["Çalışma Sayfası", "Ünite Tekrar Testi"]:
            num_questions = st.slider("Soru Sayısı", 3, 10, 6)
        
        if selected_tool == "Ek Çalışma (Farklılaştırılmış)":
            differentiation_type = st.radio("Aktivite Düzeyi", ["Destekleyici (Supporting)", "İleri Düzey (Expansion)"])

# -----------------------------
# PROMPT OLUŞTURMA FONKSİYONLARI - GÜNCELLENDİ
# -----------------------------
def get_activity_suggestions(skill):
    """Belirli bir beceri için çeşitli aktivite türleri önerir."""
    suggestions = {
        "Grammar": [
            "a sentence transformation task (e.g., affirmative to negative)",
            "a correct-the-mistake exercise",
            "a multiple-choice question set focusing on common errors",
            "a fill-in-the-blanks exercise for verb forms",
            "a sentence building task from jumbled words"
        ],
        "Vocabulary": [
            "a matching exercise (word to definition or picture)",
            "a fill-in-the-blanks story using a word bank",
            "an odd-one-out task where students find the word that doesn't belong",
            "a sentence creation task for 3 key words",
            "an unscramble the letters activity for key vocabulary"
        ],
        "Reading": [
            "a short original text (100-150 words) with True/False and comprehension questions",
            "a text with headings where students match paragraphs to headings",
            "a text with gaps where students choose the best sentence to fill each gap"
        ],
        "Speaking": [
            "a role-play scenario with specific roles and goals",
            "a set of discussion questions for pair work",
            "a picture description task"
        ],
        "Writing": [
            "a guided paragraph writing task with prompts",
            "an email or message writing task based on a scenario",
            "a picture-based short story prompt"
        ],
        "Pronunciation": [
            "a minimal pairs discrimination exercise (e.g., ship vs. sheep)",
            "a tongue twister focusing on the target sounds",
            "a 'find the sound' activity in a short text"
        ]
    }
    return random.sample(suggestions.get(skill, []), 2) # Rastgele 2 öneri seçer

def create_prompt(tool, **kwargs):
    base_prompt = f"""
Act as an expert English teacher and material developer for the Turkish Ministry of Education's new 'Century of Türkiye' model.
Your task is to create a high-quality, practical, and engaging material for a {kwargs.get('grade')} class (CEFR B1.1), fully aligned with the WAYMARK series.
The content must be entirely in English, including instructions for students.
Unit: "{kwargs.get('unit')}"
"""
    
    # Aktivite çeşitliliği için öneri oluşturma
    activity_suggestion_text = ""
    if kwargs.get('skill') in ['Grammar', 'Vocabulary', 'Reading', 'Speaking', 'Writing', 'Pronunciation']:
        suggestions = get_activity_suggestions(kwargs.get('skill'))
        if suggestions:
            activity_suggestion_text = f"Please include a creative and diverse mix of activity types. For inspiration, you can use some of the following formats: {', '.join(suggestions)}."

    prompts = {
        "Çalışma Sayfası": f"""
        Focus Skill: "{kwargs.get('skill')}"
        Topic: "{meb_curriculum[kwargs.get('grade')][kwargs.get('unit')].get(kwargs.get('skill'), '')}"
        
        Create a worksheet with exactly {kwargs.get('num_questions')} questions.
        {activity_suggestion_text}
        - Start with a clear title (e.g., 'Theme 1: Grammar Worksheet') and a one-sentence instruction for students.
        - Ensure variety in tasks. Avoid using only one type of question.
        - End with a separate 'Answer Key' section listing only the correct answers.
        """,
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
        - The test must cover at least 3 different skills from the unit (e.g., Grammar, Vocabulary, Reading).
        - Include a variety of question formats as suggested for worksheets.
        - End with a separate 'Answer Key' section.
        """,
        "Değerlendirme Rubriği": f"""
        Focus Skill: "{kwargs.get('skill')}"
        Create a simple and clear assessment rubric for a speaking or writing task.
        - Use 3 performance levels: 'Excellent (4 pts)', 'Good (3 pts)', 'Needs Improvement (1-2 pts)'.
        - Define 3 clear criteria relevant to the skill (e.g., for Speaking: Fluency, Accuracy, Content).
        - Provide a brief, clear descriptor for each level under each criterion.
        """,
        "Ek Çalışma (Farklılaştırılmış)": f"""
        Focus Skill: "{kwargs.get('skill')}"
        Activity Level: "{kwargs.get('diff_type')}"
        
        Create a differentiated activity.
        - If 'Supporting', design a highly-structured, scaffolded task (e.g., matching with pictures, guided sentence completion).
        - If 'Expansion', design a task that requires more creative or critical thinking (e.g., a short role-play scenario, a problem-solving task, an opinion paragraph).
        - Include a clear objective and step-by-step implementation instructions for the teacher.
        """
    }
    
    final_prompt = base_prompt + prompts[tool]
    
    if kwargs.get('clil'):
        final_prompt += "\n- IMPORTANT: Integrate a CLIL (Content and Language Integrated Learning) component related to technology, science, or digital literacy."
    if kwargs.get('reflection'):
        final_prompt += "\n- IMPORTANT: Add a short, simple reflection question at the end for students to think about their learning (e.g., 'What was the most difficult part for you?')."
        
    return final_prompt.strip()

# -----------------------------
# GEMINI API ÇAĞRISI (CACHING İLE)
# -----------------------------
@st.cache_data
def call_gemini_api(_prompt_text):
    try:
        response = model.generate_content(
            _prompt_text,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.75 # Yaratıcılığı artırmak için sıcaklık biraz yükseltildi
            }
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
        p.drawRightString(width - 50, height - 40, "QuickSheet v2.0")
        p.line(50, height - 50, width - 50, height - 50)
        p.drawCentredString(width / 2.0, 30, f"Sayfa {page_number}")
        
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
        
        y -= 18 # Satır aralığını artır
        if is_heading:
            y -= 5 # Başlıktan sonra ekstra boşluk

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
            p = doc.add_paragraph(line[2:], style='Heading 1')
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
# Adım 1: Prompt'u oluştur ve session state'e kaydet
if st.button("✨ 1. Adım: Materyal Taslağını Oluştur", type="primary", use_container_width=True):
    prompt_args = {
        "grade": selected_grade,
        "unit": selected_unit,
        "skill": selected_skill,
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

# Adım 2: Prompt'u göster, düzenleme imkanı sağla ve yapay zekaya gönder
if 'final_prompt' in st.session_state and st.session_state.final_prompt:
    st.subheader("2. Adım: Komutu Gözden Geçirin ve Geliştirin (İsteğe Bağlı)")
    st.info("Aşağıdaki komut (prompt) yapay zekaya gönderilecektir. Daha spesifik sonuçlar için üzerinde değişiklik yapabilirsiniz.")
    
    edited_prompt = st.text_area(
        "Yapay Zeka Komutu (Prompt)",
        value=st.session_state.final_prompt,
        height=200,
        key="prompt_editor"
    )

    if st.button("🚀 3. Adım: Yapay Zeka ile İçeriği Üret", use_container_width=True):
         with st.spinner(f"{st.session_state.last_tool} üretiliyor... Bu işlem 30 saniye kadar sürebilir."):
            st.session_state.ai_content = call_gemini_api(edited_prompt)
            st.session_state.final_prompt = ""


# Adım 3: Üretilen içeriği göster ve indirme butonlarını sun
if st.session_state.ai_content:
    st.subheader(f"Üretilen İçerik: {st.session_state.last_tool}")
    
    edited_content = st.text_area(
        "İçeriği Düzenleyin (İndirmeden önce değişiklik yapabilirsiniz)",
        value=st.session_state.ai_content,
        height=400,
        key="edited_content"
    )
    
    st.subheader("Son Adım: İndirin")
    col1, col2 = st.columns(2)

    with col1:
        try:
            docx_buffer = create_docx(edited_content)
            st.download_button(
                label="📄 Word Olarak İndir (.docx)",
                data=docx_buffer,
                file_name=f"{st.session_state.last_tool.replace(' ', '_').lower()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Word dosyası oluşturulurken hata: {e}")

    with col2:
        if font_loaded:
            try:
                pdf_buffer = create_pdf(edited_content, selected_grade, selected_unit)
                st.download_button(
                    label="📑 PDF Olarak İndir",
                    data=pdf_buffer,
                    file_name=f"{st.session_state.last_tool.replace(' ', '_').lower()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF dosyası oluşturulurken hata: {e}")
        else:
            st.warning("Font yüklenemediği için PDF çıktısı devre dışı.")


# -----------------------------
# ALT BİLGİ VE NOTLAR
# -----------------------------
st.divider()
st.caption("⚡ **QuickSheet v2.0** | Google Gemini API ile güçlendirilmiştir. | MEB 'Yüzyılın Türkiye'si Eğitim Modeli' (2025) 9. Sınıf İngilizce müfredatına uygundur.")
st.caption("**Not:** En iyi sonuçlar için spesifik ve net seçimler yapın. Üretilen içeriği indirmeden önce mutlaka kontrol edin ve düzenleyin.")

