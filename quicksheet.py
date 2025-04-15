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
    "Vocabulary": ["Matching", "Word Formation", "Synonym/Antonym", "Fill in the Blanks"],
    "Pronunciation": ["Stress Practice", "Intonation Pattern", "Minimal Pairs", "Sound Matching"]

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
    selected_unit = st.selectbox("Ünite Seç", units_by_grade.get(meb_grade, []))
    skill = st.selectbox("Beceri", list(question_type_by_skill.keys()), key="meb_skill")
    question_type = st.selectbox("Soru Türü", question_type_by_skill[skill], key="meb_qtype")

meb_unit_prompts = {
    # 9. Sınıf
    "Theme 1: Studying Abroad": {
        "functions": "Introducing yourself and others, talking about possessions, asking for and giving directions",
        "vocab": "countries, nationalities, family members, places, directions",
        "grammar": "verb to be, possessives, there is/are, prepositions"
    },
    "Theme 2: My Environment": {
        "functions": "Describing environment, asking locations, making comparisons",
        "vocab": "places in town, adjectives, environment-related words",
        "grammar": "comparatives, superlatives, prepositions of place"
    },
    "Theme 3: Movies": {
        "functions": "Talking about movies, giving opinions, making preferences",
        "vocab": "film genres, adjectives, cinema vocabulary",
        "grammar": "simple present, like/love/hate + gerund"
    },
    "Theme 4: Human In Nature": {
        "functions": "Talking about daily routines, abilities, natural disasters",
        "vocab": "nature, abilities, weather, disasters",
        "grammar": "can/can’t, adverbs of frequency, present simple"
    },
    "Theme 5: Inspirational People": {
        "functions": "Describing people, expressing opinions, comparisons",
        "vocab": "personality traits, professions, appearances",
        "grammar": "present continuous, comparatives, superlatives"
    },
    "Theme 6: Bridging Cultures": {
        "functions": "Describing cities, discussing cultural differences",
        "vocab": "food, travel, holiday expressions",
        "grammar": "there is/are, imperatives, should"
    },
    "Theme 7: World Heritage": {
        "functions": "Describing historical places, talking about past events",
        "vocab": "history, culture, heritage-related words",
        "grammar": "simple past, wh- questions"
    },
    "Theme 8: Emergency and Health Problems": {
        "functions": "Giving advice, talking about emergencies, expressing obligations",
        "vocab": "illnesses, accidents, hospital items",
        "grammar": "should/shouldn’t, must/mustn’t"
    },
    "Theme 9: Invitations and Celebrations": {
        "functions": "Making and refusing invitations, talking about celebrations",
        "vocab": "party items, dates, invitation phrases",
        "grammar": "going to, future plans, can/may"
    },
    "Theme 10: Television and Social Media": {
        "functions": "Giving opinions, discussing media habits, interrupting",
        "vocab": "TV programs, social media terms, internet slang",
        "grammar": "will, modals for opinion"
    },

    # 10. Sınıf
    "Theme 1: School Life": {
        "functions": "Exchanging personal information in both formal and informal language, taking part in a conversation in everyday life situations",
        "vocab": "school subjects, daily routines, classroom items, club activities",
        "grammar": "simple present tense, wh- questions, adverbs of frequency"
    },
    "Theme 2: Plans": {
        "functions": "Describing future plans and arrangements, expressing unplanned situations",
        "vocab": "future time expressions, calendar terms, appointments",
        "grammar": "be going to, will, present continuous"
    },
    "Theme 3: Legendary Figure": {
        "functions": "Describing past activities and events, telling life stories",
        "vocab": "biographical words, historical figures, character traits",
        "grammar": "simple past, past continuous, time clauses"
    },
    "Theme 4: Traditions": {
        "functions": "Describing cultural elements, talking about routines in the past",
        "vocab": "festivals, cultural practices, traditional activities",
        "grammar": "used to, past simple, comparatives"
    },
    "Theme 5: Travel": {
        "functions": "Talking about travel experiences, making and confirming travel plans",
        "vocab": "transportation, accommodation, itinerary",
        "grammar": "present perfect, past simple, modals"
    },
    "Theme 6: Helpful Tips": {
        "functions": "Giving and receiving advice, talking about consequences and obligations",
        "vocab": "rules, tips, warning expressions",
        "grammar": "modals (should, must), conditionals (type 1)"
    },
    "Theme 7: Food and Festivals": {
        "functions": "Describing cooking processes, talking about national/international festivals",
        "vocab": "recipes, ingredients, cultural celebrations",
        "grammar": "passive voice, sequencing adverbs"
    },
    "Theme 8: Digital Era": {
        "functions": "Stating preferences and opinions, discussing technology’s impact",
        "vocab": "digital tools, online habits, social media",
        "grammar": "present perfect, comparatives, cause-effect conjunctions"
    },
    "Theme 9: Modern Heroes and Heroines": {
        "functions": "Talking about imaginary situations, expressing wishes and desires",
        "vocab": "heroic traits, inspirational people, hypothetical scenarios",
        "grammar": "second conditional, wish / if only"
    },
    "Theme 10: Shopping": {
        "functions": "Making comparisons, shopping dialogs, describing objects",
        "vocab": "clothing, stores, product descriptions",
        "grammar": "comparatives, too/enough, present continuous"
    },

    # 11. Sınıf
    "Theme 1: Future Jobs": {
        "functions": "Talking about future career preferences and qualifications",
        "vocab": "professions, workplace vocabulary, job skills",
        "grammar": "will, be going to, modals (can, must)"
    },
    "Theme 2: Hobbies and Skills": {
        "functions": "Describing hobbies, skills and abilities",
        "vocab": "leisure activities, talents, personal preferences",
        "grammar": "can, could, be able to, present perfect"
    },
    "Theme 3: Hard Times": {
        "functions": "Describing past events, talking about difficulties and natural disasters",
        "vocab": "disasters, accidents, emergency vocabulary",
        "grammar": "past continuous, simple past"
    },
    "Theme 4: What a Life": {
        "functions": "Narrating life events, giving biographical details",
        "vocab": "life stages, biography vocabulary",
        "grammar": "past perfect, time clauses"
    },
    "Theme 5: Back to the Past": {
        "functions": "Describing historical events and figures",
        "vocab": "history, important dates, national figures",
        "grammar": "past simple, passive voice"
    },
    "Theme 6: Open Your Heart": {
        "functions": "Expressing feelings, giving advice about emotional problems",
        "vocab": "feelings, mental health, personal issues",
        "grammar": "wish / if only, second conditional"
    },
    "Theme 7: Facts about Turkiye": {
        "functions": "Giving information about Türkiye's geography, culture and traditions",
        "vocab": "geographical terms, cities, landmarks",
        "grammar": "relative clauses, present simple"
    },
    "Theme 8: Sports": {
        "functions": "Talking about sports preferences, achievements and competitions",
        "vocab": "sports types, equipment, medals",
        "grammar": "simple present, adverbs of manner"
    },
    "Theme 9: My Friends": {
        "functions": "Describing friendships and social relationships",
        "vocab": "character traits, social behaviors",
        "grammar": "present simple, comparative adjectives"
    },
    "Theme 10: Values and Norms": {
        "functions": "Discussing moral values and cultural norms",
        "vocab": "respect, honesty, social behavior",
        "grammar": "modals (should/must), conditionals"
    },

    # 12. Sınıf
    "Theme 1: Music": {
        "functions": "Expressing musical preferences, talking about genres",
        "vocab": "music types, instruments, moods",
        "grammar": "gerunds and infinitives, adjective clauses"
    },
    "Theme 2: Friendship": {
        "functions": "Describing friendships, evaluating personal qualities",
        "vocab": "personality, friendship qualities",
        "grammar": "modals of deduction, cause/effect connectors"
    },
    "Theme 3: Human Rights": {
        "functions": "Discussing rights, equality and responsibilities",
        "vocab": "rights, freedoms, social issues",
        "grammar": "passive voice, relative clauses"
    },
    "Theme 4: Coming Soon": {
        "functions": "Making predictions about future technologies and media",
        "vocab": "film/media terms, tech tools",
        "grammar": "future tense, sequencing adverbs"
    },
    "Theme 5: Psychology": {
        "functions": "Describing emotions, giving advice about well-being",
        "vocab": "mental health, emotional states",
        "grammar": "present perfect continuous, modals of advice"
    },
    "Theme 6: Favors": {
        "functions": "Making polite requests, offering help",
        "vocab": "favor expressions, polite phrases",
        "grammar": "would you mind / could you / would you"
    },
    "Theme 7: News Stories": {
        "functions": "Reporting past events, understanding headlines",
        "vocab": "journalistic terms, reporting phrases",
        "grammar": "past perfect, reported speech"
    },
    "Theme 8: Alternative Energy": {
        "functions": "Discussing environment and energy sources",
        "vocab": "renewable sources, pollution, global warming",
        "grammar": "comparatives, passive voice"
    },
    "Theme 9: Technology": {
        "functions": "Describing modern technology and its effects",
        "vocab": "gadgets, artificial intelligence, internet tools",
        "grammar": "future continuous, if-clauses (type 1)"
    },
    "Theme 10: Manners": {
        "functions": "Talking about manners and social rules",
        "vocab": "etiquette, behavior norms, politeness",
        "grammar": "wish / if only, modals for past"
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

# AI çıktısını satır satır temizle
cleaned_lines = []
in_answer_section = False

for line in content.splitlines():
    lower = line.strip().lower()

    # Cevap anahtarı başladığı anda sonrasını alma
    if any(lower.startswith(key) for key in ["answer key", "answers:", "correct answers", "answer:"]):
        in_answer_section = True
        continue

    # Cevap satırları: 1) A 2) B vs. → atla
    if in_answer_section or lower[:3] in ["1)", "2)", "3)", "4)", "5)"]:
        continue

    # "Answer:" gibi inline ifadeleri kaldır
    if "answer:" in lower:
        continue

    cleaned_lines.append(line)
                    
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
if mode == "Otomatik Üret":
    if skill == "Reading":
        prompt = f"""
Create a reading comprehension worksheet for a {level} level English learner on the topic "{topic}".
Include:
- a short engaging reading text,
- 4–6 comprehension questions (multiple choice or open-ended),
- vocabulary support if necessary.
"""

    elif skill == "Grammar":
        prompt = f"""
Create a grammar-focused worksheet for a {level} level learner on the topic "{topic}".
Include:
- a brief rule or example,
- 5–6 fill-in-the-blank or sentence transformation exercises.
"""

    elif skill == "Vocabulary":
        prompt = f"""
Create a vocabulary-building worksheet on the topic "{topic}" for {level} level students.
Include:
- 6–8 topic-related words or phrases,
- matching, fill-in-the-blank or sentence completion activities.
"""

    elif skill == "Writing":
        prompt = f"""
Create a writing activity on the topic "{topic}" suitable for {level} level students.
Include:
- a model paragraph or writing prompt,
- guiding questions or outline support.
"""

    elif skill == "Speaking":
        prompt = f"""
Prepare a speaking activity for {level} level learners around the topic "{topic}".
Include:
- discussion questions,
- pair/group speaking tasks,
- short role-plays or interviews.
"""

    elif skill == "Listening":
        prompt = f"""
Create a listening activity for {level} level learners on the topic "{topic}".
Simulate a short dialogue or monologue and prepare:
- 4–6 comprehension questions,
- vocabulary focus (optional).
Transcript must be included.
"""

    elif skill == "Pronunciation":
        prompt = f"""
Design a pronunciation-focused worksheet on the topic "{topic}" for {level} level learners.
Include:
- stress pattern practice,
- intonation tasks,
- minimal pairs or sound distinction exercises.
"""

    else:
        prompt = f"""
Create a general English activity for {level} level learners on the topic "{topic}".
Include a short task that improves overall language use.
"""

elif mode == "Kendi Metnimden Test Üret" and custom_text.strip() != "":
    if skill == "Reading":
        prompt = f"""
You are an experienced English teacher.

Create a reading comprehension worksheet using the text below for {level} level learners.
Include:
- 4–6 comprehension questions,
- vocabulary focus if needed.

Text:
{custom_text}
"""

    elif skill == "Grammar":
        prompt = f"""
Using the text below, identify a grammar structure suitable for {level} learners.
Create:
- 4–5 fill-in-the-blank or transformation questions using real sentences from the text.

Text:
{custom_text}
"""

    elif skill == "Vocabulary":
        prompt = f"""
Use the text below to create a vocabulary activity for {level} level learners.
Include:
- 6–8 key words or phrases,
- matching, fill-in-the-blank or short definitions.

Text:
{custom_text}
"""

    elif skill == "Writing":
        prompt = f"""
Create a writing prompt inspired by the following text for {level} level students.
Include:
- one main writing question,
- outline support or hints.

Text:
{custom_text}
"""

    elif skill == "Speaking":
        prompt = f"""
Use the text below to create a speaking task for {level} level learners.
Include:
- 3–5 discussion questions,
- one pair-work or short role-play task.

Text:
{custom_text}
"""

    elif skill == "Listening":
        prompt = f"""
Use the following text as an audio transcript and create a listening task.
For {level} level learners:
- write 4–6 listening questions,
- optionally include a vocabulary match-up.

Transcript:
{custom_text}
"""

    elif skill == "Pronunciation":
        prompt = f"""
Use the text below to create a pronunciation-based worksheet for {level} level learners.
Include:
- word stress identification,
- sentence intonation,
- minimal pairs or confusing sounds (if relevant).

Text:
{custom_text}
"""

    else:
        prompt = f"""
Use this text to prepare a general classroom task suitable for {level} learners.

Text:
{custom_text}
"""
else:
    st.warning("Lütfen geçerli bir metin girin.")
    st.stop()

if st.button("✨ Testi Üret"):

    # Gerekli alanlar boşsa uyarı ver
    if not topic and mode == "Otomatik Üret":
        st.warning("Lütfen bir konu girin.")
        st.stop()

    if not level and mode == "Otomatik Üret":
        st.warning("Lütfen bir dil seviyesi seçin.")
        st.stop()

    if mode == "Otomatik Üret":
        if skill == "Reading":
            prompt = f"""
Create a reading comprehension worksheet for a {level} level English learner on the topic "{topic}".
Include:
- a short engaging reading text,
- 4–6 comprehension questions,
- vocabulary support if necessary.
"""
        elif skill == "Grammar":
            prompt = f"""
Create a grammar-focused worksheet for a {level} level learner on the topic "{topic}".
Include:
- a brief explanation or rule,
- 5–6 exercises like fill-in-the-blanks or error correction.
"""
        elif skill == "Vocabulary":
            prompt = f"""
Create a vocabulary activity on the topic "{topic}" for {level} level students.
Include:
- 6–8 topic-related words or expressions,
- matching or fill-in-the-blank tasks.
"""
        elif skill == "Writing":
            prompt = f"""
Create a writing task on the topic "{topic}" for {level} learners.
Include:
- a prompt or outline,
- optional guiding questions.
"""
        elif skill == "Speaking":
            prompt = f"""
Create a speaking activity for {level} learners on the topic "{topic}".
Include:
- discussion questions,
- a pair or group speaking task.
"""
        elif skill == "Listening":
            prompt = f"""
Simulate a short listening transcript on the topic "{topic}" for {level} level learners.
Then create:
- 4–6 comprehension questions,
- one vocabulary-related task.
"""
        elif skill == "Pronunciation":
            prompt = f"""
Create a pronunciation-focused worksheet for {level} learners on the topic "{topic}".
Include:
- word/sentence stress,
- intonation practice,
- minimal pairs or sound confusion tasks.
"""
        else:
            prompt = f"""
Create a general language worksheet for {level} level learners on the topic "{topic}".
"""

    elif mode == "Kendi Metnimden Test Üret" and custom_text.strip() != "":
        if skill == "Reading":
            prompt = f"""
Create a reading comprehension worksheet for {level} level learners using the text below.
Include:
- 4–6 comprehension questions,
- vocabulary or phrase focus if needed.

Text:
{custom_text}
"""
        elif skill == "Grammar":
            prompt = f"""
Using the text below, create grammar-focused questions for {level} level learners.
Focus on any relevant grammar structure from the text.
Include 4–5 fill-in-the-blank or transformation items.

Text:
{custom_text}
"""
        elif skill == "Vocabulary":
            prompt = f"""
Create a vocabulary activity based on the text below for {level} learners.
Include:
- 6–8 target words,
- matching or sentence completion exercises.

Text:
{custom_text}
"""
        elif skill == "Writing":
            prompt = f"""
Create a writing task inspired by the following text for {level} learners.
Include:
- a writing prompt,
- optional outline or hints.

Text:
{custom_text}
"""
        elif skill == "Speaking":
            prompt = f"""
Use the following text to create a speaking task for {level} learners.
Include:
- 3–5 discussion questions,
- short role-play or opinion-based speaking task.

Text:
{custom_text}
"""
        elif skill == "Listening":
            prompt = f"""
Treat the following text as a listening transcript for {level} learners.
Create:
- 4–6 comprehension questions,
- optionally, a vocabulary task.

Transcript:
{custom_text}
"""
        elif skill == "Pronunciation":
            prompt = f"""
Use the text below to create a pronunciation worksheet for {level} learners.
Include:
- word stress identification,
- intonation pattern practice,
- minimal pair matching (if applicable).

Text:
{custom_text}
"""
        else:
            prompt = f"""
Create a language activity based on the text below for {level} learners.

Text:
{custom_text}
"""
    else:
        st.warning("Lütfen geçerli bir metin girin.")
        st.stop()

    # AI'dan içerik alma
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

