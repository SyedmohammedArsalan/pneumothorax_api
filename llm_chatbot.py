# llm_chatbot.py - Local rule-based chatbot (no API, always works)
import re
from typing import Tuple

# Knowledge base: keywords and responses
KNOWLEDGE_BASE = [
    {
        "keywords": ["what is", "definition", "pneumothorax", "collapsed lung", "explain"],
        "response": "🫁 Pneumothorax (collapsed lung) occurs when air leaks into the space between your lung and chest wall, causing the lung to collapse partially or fully."
    },
    {
        "keywords": ["symptom", "signs", "feel", "pain", "shortness of breath", "breathless", "chest pain"],
        "response": "⚠️ Common symptoms: sudden sharp chest pain (on one side), shortness of breath, rapid heart rate, dry cough, fatigue. Severe cases may cause bluish skin (cyanosis)."
    },
    {
        "keywords": ["cause", "why", "risk factor", "what causes"],
        "response": "🔍 Causes: chest injury (rib fracture), lung diseases (COPD, asthma, cystic fibrosis), smoking, mechanical ventilation, or sometimes spontaneous rupture of small air blisters (blebs)."
    },
    {
        "keywords": ["treatment", "cure", "fix", "how to treat", "therapy", "chest tube", "aspiration"],
        "response": "💊 Treatment depends on size: small cases → observation & oxygen; moderate → needle aspiration; large → chest tube insertion; recurrent → surgery (pleurodesis)."
    },
    {
        "keywords": ["diagnosis", "detect", "x-ray", "ct scan", "how to diagnose"],
        "response": "🩻 Diagnosis: Chest X‑ray is the primary method. CT scan provides more detail. Ultrasound can also be used in emergencies."
    },
    {
        "keywords": ["prevent", "prevention", "avoid", "stop", "reduce risk"],
        "response": "🛡️ Prevention: quit smoking, avoid rapid pressure changes (scuba diving/flying if at risk), treat underlying lung diseases, and follow up with your doctor."
    },
    {
        "keywords": ["recovery", "heal", "after treatment", "prognosis"],
        "response": "📈 Recovery: Most patients recover fully within 2–4 weeks. Avoid strenuous activity and air travel until cleared by your doctor."
    },
    {
        "keywords": ["emergency", "urgent", "when to go to hospital", "serious"],
        "response": "🚨 Seek emergency care if: sudden severe chest pain, difficulty breathing, rapid heart rate, fainting, or bluish lips/skin."
    },
    {
        "keywords": ["risk", "who gets", "likely", "prone"],
        "response": "👥 At higher risk: tall thin young men (spontaneous), smokers, people with family history, patients with COPD or asthma."
    },
    {
        "keywords": ["recurrent", "come back", "again", "second time"],
        "response": "🔄 Recurrence happens in 20–40% of cases. Prevent with surgery (pleurodesis) or chemical pleurodesis after second episode."
    },
    {
        "keywords": ["hi", "hello", "hey", "thanks", "thank you"],
        "response": "👋 Hello! I'm PneumoAI Assistant. Ask me anything about pneumothorax, lung health, or our AI detection tool."
    },
    {
        "keywords": ["how accurate", "reliable", "trust", "ai model", "your model"],
        "response": "🤖 Our AI model (EfficientNet-B0 + U-Net) achieves ~79% Dice score on validation. It's for research assistance only – always confirm with a radiologist."
    },
    {
        "keywords": ["how to use", "upload", "predict", "analyse", "get result"],
        "response": "📤 Go to 'Detect' section, upload a chest X‑ray (JPEG/PNG). Our AI will classify and show segmentation overlay if pneumothorax is detected."
    },
    {
        "keywords": ["affect", "complication", "dangerous", "serious"],
        "response": "⚠️ If untreated, a large pneumothorax can lead to tension pneumothorax – a life‑threatening condition that compresses the heart and other lung."
    },
    {
        "keywords": ["living with", "daily life", "exercise", "activity"],
        "response": "🏃‍♂️ After recovery, most normal activities resume. Avoid smoking, scuba diving, and high altitudes if you've had a spontaneous pneumothorax."
    }
]

DEFAULT_RESPONSE = "💡 I'm still learning! Please ask about pneumothorax symptoms, causes, treatment, prevention, or how our AI works. Try: 'What is pneumothorax?' or 'How to treat collapsed lung?'"

def get_llm_response(user_message: str) -> Tuple[str, bool]:
    """
    Local rule-based response (no API, always works).
    Returns (response_text, found_match).
    """
    if not user_message or not user_message.strip():
        return "Please type a question.", False

    message_lower = user_message.lower().strip()
    best_score = 0
    best_response = None

    for item in KNOWLEDGE_BASE:
        score = sum(1 for kw in item["keywords"] if kw in message_lower)
        if score > best_score:
            best_score = score
            best_response = item["response"]

    if best_response and best_score > 0:
        return best_response, True
    else:
        return DEFAULT_RESPONSE, False