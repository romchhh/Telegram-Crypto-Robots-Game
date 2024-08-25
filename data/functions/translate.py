from googletrans import Translator
from data.functions.db import check_user_language

def translate_text(text, user_id):
    user_language = check_user_language(user_id)
    
    if user_language == 'ru' or user_language is None:
        return text
    
    translator = Translator()
    result = translator.translate(text, dest=user_language)
    return result.text



