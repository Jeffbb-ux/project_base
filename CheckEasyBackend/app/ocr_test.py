# File: app/ocr_test.py
import pytesseract
from PIL import Image

# 如果 Tesseract 不在系统 PATH 中，请取消下面这行的注释并设置正确的路径
# pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'

def main():
    # 图片路径设置为你的 Desktop 中的 passport_cjh.jpg
    image_path = "/Users/cjh/Desktop/passport_cjh.jpg"
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"无法打开图片: {e}")
        return

    text = pytesseract.image_to_string(image, lang='eng')
    print("OCR 识别结果:")
    print(text)

if __name__ == "__main__":
    main()