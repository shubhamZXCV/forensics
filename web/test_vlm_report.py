
import os
import sys
import json
import logging
from PIL import Image, ImageDraw

# Setup Django environment for imports (though we only need the class)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from analysis.report_generators import LocalVLMReportGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)

# Rest of imports...

def create_dummy_mask(path):
    # Create a 100x100 black image with a white square
    img = Image.new('RGB', (100, 100), color='black')
    d = ImageDraw.Draw(img)
    d.rectangle([25, 25, 75, 75], fill='white')
    img.save(path)
    print(f"Created dummy mask at {path}")

def test_vlm():
    # 1. Setup Data
    input_video_path = "test_video.mp4" # Dummy name
    mask_filename = "test_video_frame_0_mask.png"
    mask_path = os.path.abspath(mask_filename)
    
    create_dummy_mask(mask_path)
    
    # Mock AnalysisResult data
    data = {
        "trufor": {
            "score": 0.95,
            "label": "Fake",
            "details": {
                "masks": [mask_filename], # report_generators joins this with input_dir
                "score": 0.95
            }
        },
        "univfd": {
            "score": 0.1,
            "label": "Real"
        }
    }
    
    # 2. Run Generator
    print("Loading Local VLM (this may take time)...")
    generator = LocalVLMReportGenerator()
    
    # We pass the mask_path as input_path effectively so dirname works
    # report_generators uses dirname(input_path) to find masks
    # So if input_path is /foo/bar/video.mp4, it looks in /foo/bar/
    # Here our mask is in CWD. So we pass a dummy file in CWD.
    dummy_input_path = os.path.abspath(input_video_path)
    
    print("Generating report...")
    try:
        report = generator.generate(data, input_path=dummy_input_path)
        print("\n\n=== FINAL REPORT ===\n")
        print(report)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if os.path.exists(mask_path):
            os.remove(mask_path)

if __name__ == "__main__":
    test_vlm()
