#!/usr/bin/env python3
"""
debug_uploadedpassport.py

此脚本用于自动检测 User 模型中定义的 uploaded_passports 关系是否能正确找到 UploadedPassport 类，
从而诊断因导入路径错误导致的映射问题。

使用方法：
    python debug_uploadedpassport.py
"""

import importlib
import sys
import logging

from app.modules.auth.register.models import User

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_uploadedpassport")

def try_import_uploadedpassport():
    paths = [
        "app.modules.verification.upload.models",
        "app.modules.verification.upload.uploads.models"
    ]
    for module_path in paths:
        try:
            module = importlib.import_module(module_path)
            up_class = getattr(module, "UploadedPassport")
            logger.debug("UploadedPassport found in %s", module_path)
            return up_class, module_path
        except Exception as e:
            logger.debug("Failed to import UploadedPassport from %s: %s", module_path, e)
    return None, None

def check_user_mapping():
    # 检查 User 模型中是否存在 uploaded_passports 属性
    if hasattr(User, "uploaded_passports"):
        logger.debug("User model has attribute 'uploaded_passports'.")
    else:
        logger.error("User model does NOT have attribute 'uploaded_passports'.")
        sys.exit(1)

    # 通过映射检查 User.uploaded_passports 是否引用了正确的类
    try:
        mapper = User.__mapper__
        rel_prop = mapper.relationships.get("uploaded_passports")
        if rel_prop is None:
            logger.error("No 'uploaded_passports' relationship found in User mapper.")
            sys.exit(1)
        else:
            logger.debug("User.uploaded_passports relationship found: %s", rel_prop)
            target_class = rel_prop.mapper.class_
            logger.debug("The relationship target class is: %s.%s", target_class.__module__, target_class.__name__)
            return target_class
    except Exception as e:
        logger.exception("Error while checking User mapping: %s", e)
        sys.exit(1)

def main():
    up_class, module_path = try_import_uploadedpassport()
    if up_class is None:
        logger.error("Could not locate UploadedPassport class in expected paths.")
        sys.exit(1)
    else:
        logger.info("UploadedPassport class successfully imported from: %s", module_path)
    
    target_class = check_user_mapping()
    if target_class is up_class:
        logger.info("User.uploaded_passports is correctly mapped to UploadedPassport.")
    else:
        logger.error("User.uploaded_passports is mapped to %s.%s, which does not match the imported UploadedPassport from %s.",
                     target_class.__module__, target_class.__name__, module_path)
        sys.exit(1)

if __name__ == '__main__':
    main()