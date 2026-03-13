import os
import requests
import json
import logging
import base64
import glob
from pathlib import Path
from .interfaces import ReportGeneratorInterface

from .prompts import PROMPTS

logger = logging.getLogger(__name__)


class RemoteOllamaReportGenerator(ReportGeneratorInterface):
    def __init__(self):
        self.api_key = "sk-1550d490e41a4fefa8ba15ba14790454"
        self.api_url = "http://10.4.16.84:9000/api/chat/completions"
        self.model_name = "qwen3-vl:latest"
        
        logger.info(f"Initialized RemoteOllamaReportGenerator with model: {self.model_name} at {self.api_url}")

    def _encode_image(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return None

    def _call_api_stream(self, messages: list) -> str:
        """Helper to call the remote (OpenAI-compatible) API and stream output."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "temperature": 0.2
        }
        
        output_text = ""
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, stream=True, timeout=120)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]":
                        break
                    try:
                        json_data = json.loads(line)
                        delta = json_data.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            content = delta["content"]
                            output_text += content
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"Error calling remote API: {e}")
            return f"\n[API Error: {str(e)}]"
            
        return output_text

    def _collect_visual_evidence(self, data: dict, evidence_dir: str = None, input_path: str = None):
        """
        Collect visual evidence files (GradCAM heatmaps + masks) from evidence directory.
        Returns ONLY frame_0 per model (1 frame per model rule).
        
        Returns list of (model_name, file_basename, file_path, evidence_type) tuples.
        """
        evidence_files = []
        seen_models = set()
        
        # 1. Scan evidence_dir for all .png files
        if evidence_dir and os.path.isdir(evidence_dir):
            for png_file in sorted(glob.glob(os.path.join(evidence_dir, "*.png"))):
                basename = os.path.basename(png_file)
                
                # Determine model name and type from filename
                if "_gradcam_frame_" in basename:
                    continue # Skip gradcams for v_demo
                elif "_mask_frame_" in basename:
                    model_name = basename.split("_mask_frame_")[0]
                    evidence_type = "mask"
                else:
                    continue
                
                # Only take frame_0 per model (1 frame per model)
                if model_name in seen_models:
                    continue
                
                # Prefer frame_0
                if "_frame_0" in basename:
                    seen_models.add(model_name)
                    evidence_files.append((model_name, basename, png_file, evidence_type))
            
            # If we found frame_0 for some, fill in others with their first available frame
            if evidence_dir and os.path.isdir(evidence_dir):
                for png_file in sorted(glob.glob(os.path.join(evidence_dir, "*.png"))):
                    basename = os.path.basename(png_file)
                    if "_gradcam_frame_" in basename:
                        continue # Skip gradcams for v_demo
                    elif "_mask_frame_" in basename:
                        model_name = basename.split("_mask_frame_")[0]
                        evidence_type = "mask"
                    else:
                        continue
                    if model_name not in seen_models:
                        seen_models.add(model_name)
                        evidence_files.append((model_name, basename, png_file, evidence_type))
            
            if evidence_files:
                return evidence_files
        
        # 2. Fallback: extract from model output JSON
        for model_name, result in data.items():
            if model_name in seen_models:
                continue
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    continue
            if not isinstance(result, dict):
                continue
            
            details = result.get('details', {})
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except json.JSONDecodeError:
                    details = {}
            if not isinstance(details, dict):
                details = {}
            
            # Ignore gradcam paths in details fallback for v_demo
            
            # Check for masks — only first one
            masks = details.get('masks', [])
            if masks and masks[0]:
                mask_file = masks[0]
                if evidence_dir:
                    full_path = os.path.join(evidence_dir, mask_file)
                elif input_path:
                    full_path = os.path.join(os.path.dirname(os.path.abspath(input_path)), mask_file)
                else:
                    continue
                if os.path.exists(full_path):
                    seen_models.add(model_name)
                    evidence_files.append((model_name, mask_file, full_path, "mask"))
        
        return evidence_files

    def _extract_prediction(self, result):
        """Extract score and label from a model's result dict."""
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                return 'N/A', 'N/A'
        if not isinstance(result, dict):
            return 'N/A', 'N/A'
        
        score = result.get('score', 'N/A')
        label = result.get('label', 'N/A')
        
        # Try to format score nicely
        if score != 'N/A':
            try:
                score = round(float(score), 4)
            except (ValueError, TypeError):
                pass
        
        return score, label

    def _extract_first_frame(self, input_path, evidence_dir):
        """Extracts the first frame of a video using ffmpeg or returns image path directly."""
        import subprocess
        
        if not input_path:
            return None
            
        if any(input_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif']):
            return input_path
            
        if not evidence_dir:
            return None
            
        frame_path = os.path.join(evidence_dir, "original_frame_0.jpg")
        if os.path.exists(frame_path):
            return frame_path
            
        try:
            cmd = ["ffmpeg", "-y", "-i", input_path, "-vframes", "1", "-f", "image2", frame_path]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(frame_path):
                return frame_path
        except Exception as e:
            logger.error(f"Failed to extract frame with ffmpeg: {e}")
            
        try:
            import cv2
            cap = cv2.VideoCapture(input_path)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(frame_path, frame)
            cap.release()
            if os.path.exists(frame_path):
                return frame_path
        except ImportError:
            pass
            
        logger.error("Could not extract frame from video for deepfake analysis")
        return None

    def generate(self, data: dict, input_path: str = None, evidence_dir: str = None) -> str:
        """
        Generate a per-model structured report.
        Returns JSON string containing a list of model cards.
        Each card: {model_number, prediction_label, prediction_score, 
                    evidence_basename, evidence_type, vlm_reasoning}
        """
        logger.info("🧠 [VLM] Starting per-model report generation...")
        
        # Collect visual evidence (1 frame per model)
        evidence_files = self._collect_visual_evidence(data, evidence_dir=evidence_dir, input_path=input_path)
        
        # Build a lookup: model_name -> (basename, file_path, evidence_type)
        evidence_lookup = {}
        for model_name, basename, file_path, evidence_type in evidence_files:
            evidence_lookup[model_name] = (basename, file_path, evidence_type)
        
        # Build per-model cards
        model_cards = []
        model_counter = 1
        
        for model_name, result in data.items():
            logger.info(f"📊 [VLM] Processing Model {model_counter} ({model_name})...")
            
            score, label = self._extract_prediction(result)
            
            card = {
                "model_number": model_counter,
                "prediction_label": str(label),
                "prediction_score": score,
                "evidence_basename": None,
                "evidence_type": None,
                "vlm_reasoning": None,
            }
            
            # Check if we have visual evidence for this model
            if model_name in evidence_lookup:
                basename, file_path, evidence_type = evidence_lookup[model_name]
                card["evidence_basename"] = basename
                card["evidence_type"] = evidence_type
                
                # Encode image and ask VLM for reasoning
                encoded_img = self._encode_image(file_path)
                if encoded_img:
                    prompt_text = PROMPTS["per_model_reasoning"].format(
                        label=label, score=score
                    )
                    
                    messages = [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_img}"}}
                            ]
                        }
                    ]
                    
                    print(f"[Model {model_counter}] Analyzing visual evidence:", end=" ", flush=True)
                    reasoning = self._call_api_stream(messages)
                    card["vlm_reasoning"] = reasoning
                    logger.info(f"✅ [VLM] Model {model_counter} reasoning complete.")
                else:
                    # Image encoding failed — use text-only prompt
                    prompt_text = PROMPTS["per_model_reasoning_no_image"].format(
                        label=label, score=score
                    )
                    messages = [
                        {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
                    ]
                    print(f"[Model {model_counter}] Generating reasoning (no image):", end=" ", flush=True)
                    reasoning = self._call_api_stream(messages)
                    card["vlm_reasoning"] = reasoning
            else:
                # No visual evidence — use text-only prompt
                prompt_text = PROMPTS["per_model_reasoning_no_image"].format(
                    label=label, score=score
                )
                messages = [
                    {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
                ]
                print(f"[Model {model_counter}] Generating reasoning (no image):", end=" ", flush=True)
                reasoning = self._call_api_stream(messages)
                card["vlm_reasoning"] = reasoning
            
            model_cards.append(card)
            model_counter += 1
            
        # Add a final VLM Deepfake Analysis card based on the original frame
        logger.info("🤖 [VLM] Generating final deepfake analysis card...")
        frame_path = self._extract_first_frame(input_path, evidence_dir)
        
        if frame_path:
            encoded_img = self._encode_image(frame_path)
            if encoded_img:
                prompt_text = PROMPTS.get("vlm_deepfake_analysis", "Review the attached media frame. Look closely at facial boundaries and potential signs of manipulation. Provide a deepfake analysis.")
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_img}"}}
                        ]
                    }
                ]
                print(f"[Model {model_counter}] VLM Deepfake Analysis:", end=" ", flush=True)
                reasoning = self._call_api_stream(messages)
                
                vlm_card = {
                    "model_number": model_counter,
                    "prediction_label": "VLM Deepfake Analysis",
                    "prediction_score": "N/A",
                    "evidence_basename": os.path.basename(frame_path) if evidence_dir else None,
                    "evidence_type": "original",
                    "vlm_reasoning": reasoning,
                }
                model_cards.append(vlm_card)
                logger.info("✅ [VLM] Final deepfake analysis complete.")
            else:
                logger.error("Could not encode frame for final VLM deepfake analysis.")
        else:
            logger.warning("No frame extracted for final VLM deepfake analysis.")
        
        logger.info(f"🏁 [VLM] Per-model report generated with {len(model_cards)} cards.")
        
        # Return as JSON string for storage in TextField
        return json.dumps(model_cards, indent=2)
