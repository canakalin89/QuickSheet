import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os
import base64
import requests

# --- API ve Ayarlar ---
# ÖNEMLİ: Kendi Gemini API anahtarınızı buraya ekleyin
# (Örnek: genai.configure(api_key="AIzaSyA..."))
# API anahtarınız doğrudan kodun içine yazılacak, bu yüzden GitHub'a yüklerken dikkatli olun.
genai.configure(api_key="AIzaSyBSaZUaZPNMbqRyVp1uxOfibUh6y19ww5U")

# Türkçe karakterler için font ayarı
try:
    if not os.path.exists("fonts"):
        os.makedirs("fonts")
    font_path = "fonts/DejaVuSans.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/googlefonts/dejavu-fonts/raw/main/ttf/DejaVuSans.ttf"
        r = requests.get(url, allow_redirects=True)
        with open(font_path, 'wb') as f:
            f.write(r.content)
    
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_path))
except Exception as e:
    st.error(f"Font yüklenirken hata oluştu: {e}. Lütfen `fonts` klasörünü ve içindeki `DejaVuSans.ttf` dosyasını kontrol edin.")

# Sayfa başlığı
st.set_page_config(page_title="QuickSheet", page_icon="⚡")
st.title("⚡ QuickSheet: Akıllı Öğretmen Asistanı")

# --- Müfredat Bilgileri ---
meb_curriculum = {
    "9. Sınıf": {
        "Theme 1: School Life": {
            "Grammar": "Modal 'can' for ability and possibility, Simple Present Tense (to be), Simple Past Tense.",
            "Vocabulary": "Countries, nationalities, languages, tourist attractions, and school-related words.",
            "Reading": "Reading comprehension on texts about school life and cultural exchange."
        },
        "Theme 2: Classroom Life": {
            "Grammar": "Simple Present Tense and Present Continuous for routines and current activities.",
            "Vocabulary": "Daily routines, study habits, and classroom activities.",
            "Reading": "Reading comprehension on texts comparing daily routines."
        },
        "Theme 3: Personal Life": {
            "Grammar": "Adjectives and adverbs with 'too' and 'enough'.",
            "Vocabulary": "Physical appearance and personality traits.",
            "Reading": "Reading comprehension on texts about personal descriptions and stories."
        },
        "Theme 4: Family Life": {
            "Grammar": "Simple Present Tense for jobs, prepositions of place (in/on/at), relative clauses.",
            "Vocabulary": "Jobs, workplaces, and family members.",
            "Reading": "Reading comprehension on texts about family jobs and routines."
        },
        "Theme 5: Life in the House & Neighbourhood": {
            "Grammar": "Present Continuous for activities at home, possessive adjectives.",
            "Vocabulary": "Types of houses, rooms, furniture, and household chores.",
            "Reading": "Reading comprehension on texts about different living spaces."
        },
        "Theme 6: Life in the City & Country": {
            "Grammar": "Present Simple vs. Present Continuous for comparing lifestyles, 'or' for options.",
            "Vocabulary": "Food, festivals, and adjectives to describe taste.",
            "Reading": "Reading comprehension on texts about local food and festivals."
        },
        "Theme 7: Life in the World & Nature": {
            "Grammar": "Past Simple with 'was/were', modal 'should' for advice.",
            "Vocabulary": "Endangered animals, habitats, and environmental issues.",
            "Reading": "Reading comprehension on texts about nature conservation and animals."
        },
        "Theme 8: Life in the Universe & Future": {
            "Grammar": "Simple Future Tense with 'will' for predictions and beliefs.",
            "Vocabulary": "Film genres, technology, and futuristic concepts.",
            "Reading": "Reading comprehension on texts about future technology and films."
        }
    }
}

# --- Kullanıcı Arayüzü ---
with st.sidebar:
    st.header("Seçenekler")
    selected_grade = st.selectbox("📚 MEB Sınıfı", list(meb_curriculum.keys()))
    
    units = list(meb_curriculum[selected_grade].keys())
    selected_unit = st.selectbox("Ünite Seç", units)

    selected_tool = st.radio(
        "Üretim Modu Seç",
        ["Çalışma Sayfası", "Ders Planı", "Değerlendirme Rubriği", "Diferansiye İçerik"]
    )

    if selected_tool == "Çalışma Sayfası" or selected_tool == "Diferansiye İçerik":
        skill_options = list(meb_curriculum[selected_grade][selected_unit].keys())
        selected_skill = st.selectbox("Beceri", skill_options)
        num_questions = st.slider("Soru Sayısı", 1, 15, 5)

    if selected_tool == "Diferansiye İçerik":
        differentiation_type = st.radio("İçerik Tipi", ["Destekleyici (Supporting)", "Genişletici (Expansion)"])


# --- AI Prompt Fonksiyonları ---
def generate_ai_worksheet_prompt(grade, unit, skill, num_questions):
    topic_info = meb_curriculum[grade][unit].get(skill, "")
    return f"""
    You are a helpful and experienced English teacher.
    Your task is to create a customized worksheet for a {grade} class.

    **Instructions:**
    1.  **Curriculum:** The worksheet must be based on the MEB (Turkish Ministry of National Education) curriculum for Grade 9.
    2.  **Unit & Topic:** The content must be specifically about "{unit}".
    3.  **Skill Focus:** The questions should focus on the "{skill}" skill.
    4.  **Number of Questions:** Generate exactly {num_questions} questions.
    5.  **Question Type:** Use a mix of question types appropriate for the selected skill (e.g., multiple choice, fill in the blanks, true/false). For 'Reading', include a short, original text followed by questions.
    6.  **Output Format:**
        - Start with a clear title for the activity.
        - Write a simple, one-sentence instruction for the student.
        - List the questions with clear numbering.
        - After the questions, create a separate section titled "Answer Key".
        - In the "Answer Key" section, provide only the correct answers without extra explanations.
    7. **Topic Info:** The key topics for this skill in this unit are: {topic_info}.
    """

def generate_lesson_plan_prompt(grade, unit):
    topic_info = next(iter(meb_curriculum[grade][unit].values()))
    return f"""
    You are an English curriculum expert.
    Create a detailed lesson plan outline for a {grade} class based on the MEB (Turkish Ministry of National Education) curriculum for "{unit}".

    **Instructions:**
    1.  **Title:** Provide a clear title for the lesson plan.
    2.  **Objective:** Write a concise objective for the lesson.
    3.  **Stages:** Structure the plan into three clear stages:
        - **Warm-Up / Lead-In:** Suggest an engaging activity or question to introduce the topic.
        - **Main Activity:** Describe a primary activity that reinforces the key grammar and vocabulary of the unit.
        - **Wrap-Up / Consolidation:** Suggest a final activity to summarize the lesson and check for understanding.
    4.  **Vocabulary/Grammar:** List the key vocabulary and grammar points covered in the unit.
    5.  **Duration:** Suggest an approximate duration for each stage.
    6.  **Output Format:** Use clear headings and bullet points. The content should be a ready-to-use lesson plan outline.
    7. **Topic Info:** The key topics for this unit are: {topic_info}.
    """

def generate_rubric_prompt(grade, unit, skill):
    return f"""
    You are an assessment and evaluation specialist for English as a Foreign Language.
    Create a detailed grading rubric for a {skill} activity for a {grade} class.

    **Instructions:**
    1.  **Topic:** The rubric should be for an activity related to the unit "{unit}".
    2.  **Criteria:** The rubric must have at least three specific criteria relevant to the skill ({skill}). For example:
        - For 'Speaking': Fluency, Pronunciation, Grammar, and Vocabulary.
        - For 'Writing': Grammar, Vocabulary, Cohesion, and Content.
    3.  **Levels:** Define at least three performance levels (e.g., Excellent, Good, Needs Improvement) for each criterion.
    4.  **Descriptions:** Write a clear, concise description for each level, explaining what a student needs to do to achieve that score.
    5.  **Output Format:** Present the rubric in a structured, easy-to-read format. Do not use tables. Use clear headings and bullet points.
    """

def generate_differentiation_prompt(grade, unit, skill, diff_type):
    topic_info = meb_curriculum[grade][unit].get(skill, "")
    if diff_type == "Destekleyici (Supporting)":
        prompt_intro = f"Create a SUPPORTING activity for students who need extra help."
        prompt_details = "The activity should be simpler, focusing on foundational concepts (e.g., fill-in-the-blanks, matching) and basic vocabulary."
    else:
        prompt_intro = f"Create an EXPANSION activity for advanced students."
        prompt_details = "The activity should be more challenging, requiring critical thinking and a deeper understanding of the topic (e.g., short essay, debate prompts, project ideas)."

    return f"""
    You are an experienced English teacher who specializes in differentiated instruction.
    For the {grade} class, unit "{unit}", with a focus on "{skill}", {prompt_intro}.
    
    **Instructions:**
    1. **Task:** Describe the differentiated activity clearly.
    2. **Objective:** State the goal of the activity for the specific student group.
    3. **Implementation:** Explain how the teacher can use this activity in the classroom.
    4. **Content:** The activity must be relevant to the key topics: {topic_info}.
    5. **Output Format:** Provide the content in a clear and concise manner with headings for "Activity", "Objective", and "Implementation".
    """

# --- PDF Oluşturucu Fonksiyonu ---
def create_pdf(content, filename, is_teacher_copy=False, is_worksheet=False):
    pdf = canvas.Canvas(filename, pagesize=A4)
    pdf.setTitle("English Worksheet - Grade 9")
    pdf.setAuthor("QuickSheet AI Assistant")
    pdf.setCreator("QuickSheet AI Assistant")
    
    pdf.setFont("DejaVuSans", 10)
    
    lines = content.split('\n')
    y_position = 750
    
    pdf.setFont("DejaVuSans-Bold", 16)
    pdf.drawCentredString(A4[0] / 2.0, y_position + 20, "English Worksheet - Grade 9")
    y_position -= 20

    is_answer_key_section = False
    
    for line in lines:
        line_height = 12
        if "Answer Key" in line and is_worksheet:
            is_answer_key_section = True
            if is_teacher_copy:
                pdf.showPage()
                y_position = 750
                pdf.setFont("DejaVuSans-Bold", 12)
                pdf.drawString(50, y_position, "Answer Key")
                y_position -= 20
                pdf.setFont("DejaVuSans", 10)
            else:
                continue
            
        if is_worksheet and not is_teacher_copy and is_answer_key_section:
            continue
            
        if y_position < 50:
            pdf.showPage()
            y_position = 800
            pdf.setFont("DejaVuSans", 10)

        pdf.drawString(50, y_position, line.strip())
        y_position -= line_height
    
    pdf.save()
    return filename

# --- Uygulama Mantığı ---
if st.button("✨ İçeriği Üret"):
    if "YOUR_GEMINI_API_KEY" in genai.api_key:
        st.error("Lütfen Gemini API anahtarınızı kodun içine ekleyin.")
    else:
        with st.spinner(f"{selected_tool} oluşturuluyor... Bu biraz zaman alabilir."):
            try:
                if selected_tool == "Çalışma Sayfası":
                    prompt_text = generate_ai_worksheet_prompt(selected_grade, selected_unit, selected_skill, num_questions)
                elif selected_tool == "Ders Planı":
                    prompt_text = generate_lesson_plan_prompt(selected_grade, selected_unit)
                elif selected_tool == "Değerlendirme Rubriği":
                    prompt_text = generate_rubric_prompt(selected_grade, selected_unit, selected_skill)
                elif selected_tool == "Diferansiye İçerik":
                    prompt_text = generate_differentiation_prompt(selected_grade, selected_unit, selected_skill, differentiation_type)
                
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt_text)
                ai_content = response.text.strip()
                st.session_state["ai_content"] = ai_content

                st.subheader(f"Oluşturulan {selected_tool}")
                st.text_area("İçerik", ai_content, height=500)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf_path = tmp_file.name
                
                if selected_tool == "Çalışma Sayfası":
                    student_pdf_path = create_pdf(ai_content, "ogrenci_calisma_sayfasi.pdf", is_teacher_copy=False, is_worksheet=True)
                    with open(student_pdf_path, "rb") as f:
                        st.download_button("📄 Öğrenci İçin PDF İndir", f, file_name="ogrenci_calisma_sayfasi.pdf")
                    
                    teacher_pdf_path = create_pdf(ai_content, "ogretmen_calisma_sayfasi.pdf", is_teacher_copy=True, is_worksheet=True)
                    with open(teacher_pdf_path, "rb") as f:
                        st.download_button("🔑 Öğretmen İçin Cevap Anahtarlı PDF İndir", f, file_name="ogretmen_calisma_sayfasi.pdf")
                else:
                    pdf_path_single = create_pdf(ai_content, f"{selected_tool.lower().replace(' ', '_')}.pdf")
                    with open(pdf_path_single, "rb") as f as f:
                        st.download_button(f"📄 PDF Olarak İndir", f, file_name=f"{selected_tool.lower().replace(' ', '_')}.pdf")
                
                st.success("İçerik başarıyla oluşturuldu!")
                
            except Exception as e:
                st.error(f"İçerik oluşturulurken bir hata oluştu: {e}")
