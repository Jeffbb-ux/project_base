# File: app/modules/verification/ocr/nlp/entity_extraction.py

import stanza
import logging

logger = logging.getLogger("CheckEasyBackend.verification.ocr.nlp.entity_extraction")

def extract_dates(text: str):
    """
    使用 Stanza 处理文本并抽取 DATE 实体
    """
    try:
        nlp = stanza.Pipeline('en', processors='tokenize,ner', verbose=False)
        doc = nlp(text)
        dates = []
        for sentence in doc.sentences:
            for ent in sentence.ents:
                if ent.type == "DATE":
                    dates.append(ent.text)
        return dates
    except Exception as e:
        logger.error("Error in extract_dates: %s", str(e), exc_info=True)
        return []