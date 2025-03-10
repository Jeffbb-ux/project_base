# File: app/nlp_test.py
from transformers import pipeline

def main():
    # 初始化NER pipeline，这里使用一个预训练的英文NER模型
    ner_pipeline = pipeline(
        "ner",
        model="dbmdz/bert-large-cased-finetuned-conll03-english",
        aggregation_strategy="simple"
    )
    
    # 这里的文本可以换成你 OCR 测试中识别到的文本
    text = (
        "PEARSE PRPS DE |, FLU IT AG RAF VAIAT OF RA Fords 1 KVM) ,\n"
        "The Ministry of Foreign Affairs of the People's Republic of China "
        "requests all civil and military authorities of foreign countries to "
        "allow the bearer of this passport to pass freely and afford assistance in case of need.\n"
        "PASSPORT P CHN EJ4391314\n"
        "CHEN, JIAHAO : sh Ht PE BI /Sex [i BF / Nationality {ACH IRL. Date of Linh .\n"
        "02 MAR 1995"
    )
    
    results = ner_pipeline(text)
    
    print("Named Entity Recognition Results:")
    for entity in results:
        print(entity)

if __name__ == "__main__":
    main()