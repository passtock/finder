for pkg in ['rapidocr_onnxruntime', 'easyocr', 'pytesseract', 'cv2', 'torch', 'paddleocr']:
    try:
        __import__(pkg)
        print(pkg, 'AVAILABLE')
    except ImportError:
        print(pkg, 'NOT AVAILABLE')
