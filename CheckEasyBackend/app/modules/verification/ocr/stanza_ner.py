# File: app/modules/verification/ocr/stanza_ner.py

import stanza
import logging

logger = logging.getLogger("CheckEasyBackend.verification.ocr.stanza_ner")

# 初始化 Stanza 英语处理流水线（仅包含 tokenize 和 ner）
try:
    nlp = stanza.Pipeline('en', processors='tokenize,ner', verbose=False)
except Exception as e:
    logger.error("Error initializing Stanza pipeline: %s", str(e))
    nlp = None

def extract_dates(text: str):
    """
    使用 Stanza 识别文本中的日期实体，返回日期列表。
    """
    if not nlp:
        raise Exception("Stanza pipeline is not initialized.")
    doc = nlp(text)
    dates = [ent.text for sentence in doc.sentences for ent in sentence.ents if ent.type == "DATE"]
    return dates