from rapid_videocr import RapidVideOCR, RapidVideOCRInput
import os
import tempfile

def test():
    try:
        params = RapidVideOCRInput()
        extractor = RapidVideOCR(params)
        print("Initialized")
        # Just check if it errors on a fake path
        # extractor("fake.mp4", ".", "test")
    except Exception as e:
        print(f"Error: {e}")

test()
