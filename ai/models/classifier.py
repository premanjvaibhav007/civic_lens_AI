import os
import io
import re
import math
import logging
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, List, Optional
from backend.app.models.entities import SeverityLevel, PriorityLevel, AIStatus

logger = logging.getLogger("civiclens.ai.classifier")


class ImageEmbeddingExtractor:
    """
    Extracts dense visual feature embeddings from complaint photos.
    Uses Torchvision MobileNetV3 when PyTorch & weights are available,
    otherwise uses a fast multi-scale color & edge texture descriptor (128-dim).
    """

    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.torch_model = None
        self._init_torch_if_available()

    def _init_torch_if_available(self):
        try:
            import torch
            import torchvision.models as models
            import torchvision.transforms as transforms
            # MobileNetV3-Small feature extractor
            mobilenet = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
            mobilenet.classifier = torch.nn.Identity()
            mobilenet.eval()
            self.torch_model = mobilenet
            self.transform = transforms.Compose([
                transforms.Resize((128, 128)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            logger.info("MobileNetV3 feature extractor loaded successfully.")
        except Exception:
            self.torch_model = None

    def extract_embedding(self, image_source: Any) -> Optional[List[float]]:
        """Extract a normalized 128-dim embedding from an image source."""
        try:
            if isinstance(image_source, bytes):
                img = Image.open(io.BytesIO(image_source)).convert("RGB")
            elif isinstance(image_source, str) and os.path.exists(image_source):
                img = Image.open(image_source).convert("RGB")
            elif hasattr(image_source, "read"):
                img = Image.open(image_source).convert("RGB")
            else:
                return None

            if self.torch_model is not None:
                try:
                    import torch
                    with torch.no_grad():
                        tensor = self.transform(img).unsqueeze(0)
                        features = self.torch_model(tensor).squeeze().numpy()
                        # Project/slice to embedding_dim and L2 normalize
                        vec = features[:self.embedding_dim]
                        norm = np.linalg.norm(vec)
                        if norm > 0:
                            vec = vec / norm
                        return [float(x) for x in vec]
                except Exception as e:
                    logger.debug(f"Torch extraction failed, using fallback: {e}")

            # Deterministic multi-scale visual descriptor fallback
            img_res = img.resize((32, 32))
            arr = np.array(img_res, dtype=np.float32) / 255.0
            # Color histograms (3 channels x 16 bins = 48 dims)
            h_r, _ = np.histogram(arr[:, :, 0], bins=16, range=(0, 1))
            h_g, _ = np.histogram(arr[:, :, 1], bins=16, range=(0, 1))
            h_b, _ = np.histogram(arr[:, :, 2], bins=16, range=(0, 1))

            # Spatial block averages (4x4 blocks x 3 channels = 48 dims)
            blocks = []
            for bi in range(4):
                for bj in range(4):
                    blk = arr[bi * 8:(bi + 1) * 8, bj * 8:(bj + 1) * 8]
                    blocks.extend([float(blk[:, :, 0].mean()), float(blk[:, :, 1].mean()), float(blk[:, :, 2].mean())])

            # Gradient texture features (32 dims)
            gray = 0.2989 * arr[:, :, 0] + 0.5870 * arr[:, :, 1] + 0.1140 * arr[:, :, 2]
            gx = np.abs(gray[:, 1:] - gray[:, :-1])
            gy = np.abs(gray[1:, :] - gray[:-1, :])
            gx_pooled = [float(gx[i*8:(i+1)*8, :].mean()) for i in range(4)]
            gy_pooled = [float(gy[:, j*8:(j+1)*8].mean()) for j in range(4)]
            texture = (gx_pooled + gy_pooled) * 4

            combined = np.concatenate([h_r, h_g, h_b, blocks, texture[:32]])
            combined = combined[:self.embedding_dim].astype(np.float32)
            norm = np.linalg.norm(combined)
            if norm > 0:
                combined = combined / norm
            return [float(x) for x in combined]

        except Exception as err:
            logger.warning(f"Error extracting visual embedding: {err}")
            return None


class MultimodalIssueClassifier:
    """
    Multimodal Issue Classifier combining visual feature extraction,
    PyTorch transfer learning hooks, confidence tier routing,
    and natural language token analysis.
    """
    CATEGORIES = [
        "POTHOLE",
        "DAMAGED_ROAD",
        "STREETLIGHT",
        "GARBAGE",
        "DRAINAGE",
        "WATER_LEAKAGE",
        "DAMAGED_SIGN",
        "FOOTPATH",
        "OPEN_MANHOLE",
        "ILLEGAL_DUMPING",
        "PUBLIC_FACILITY"
    ]

    CATEGORY_DEPARTMENTS = {
        "POTHOLE": "Municipal Roads Department",
        "DAMAGED_ROAD": "Municipal Roads Department",
        "STREETLIGHT": "Electrical & Public Lighting Department",
        "GARBAGE": "Solid Waste & Sanitation Department",
        "ILLEGAL_DUMPING": "Solid Waste & Sanitation Department",
        "DRAINAGE": "Stormwater & Drainage Department",
        "WATER_LEAKAGE": "Water Supply & Sewerage Board",
        "DAMAGED_SIGN": "Traffic & Road Safety Cell",
        "FOOTPATH": "Civil Infrastructure & Footpath Division",
        "OPEN_MANHOLE": "Underground Drainage & Safety Department",
        "PUBLIC_FACILITY": "Public Works Department"
    }

    KEYWORD_MAPPINGS = {
        "POTHOLE": ["pothole", "crater", "hole in road", "road pit", "tarmac hole", "asphalt hole", "gadda"],
        "DAMAGED_ROAD": ["broken road", "cracked road", "rough road", "pavement damaged", "road eroded", "tar peeling", "tar", "road"],
        "STREETLIGHT": ["streetlight", "lamp", "dark street", "light pole", "blinking light", "light not working", "street lamp", "bulb"],
        "GARBAGE": ["garbage", "trash", "waste", "dustbin", "litter", "overflowing bin", "rubbish", "kachra"],
        "ILLEGAL_DUMPING": ["dumping", "debris", "construction waste", "illegal dump", "malba", "scrap"],
        "DRAINAGE": ["drain", "drainage", "sewer", "clogged drain", "nalah", "waterlogging", "gutters", "gutter"],
        "WATER_LEAKAGE": ["water leak", "pipeline burst", "leaking pipe", "drinking water", "tap broken", "water supply", "spill"],
        "DAMAGED_SIGN": ["signboard", "traffic sign", "stop sign", "direction board", "broken board", "signal", "traffic light"],
        "FOOTPATH": ["footpath", "sidewalk", "paver blocks", "pedestrian walk", "broken curb", "walkway"],
        "OPEN_MANHOLE": ["open manhole", "missing cover", "chamber open", "manhole lid", "drain cover", "sewer hole", "open pit"],
        "PUBLIC_FACILITY": ["public toilet", "park bench", "broken gate", "bus stand", "bus stop", "playground", "park"]
    }

    def __init__(self, model_version: str = "2.0.0", weights_path: Optional[str] = None):
        self.model_name = "civiclens-multimodal-classifier"
        self.model_version = model_version
        self.weights_path = weights_path or "./ai/weights/mobilenet_civic_v1.pt"
        self.embedding_extractor = ImageEmbeddingExtractor()
        self.torch_classifier = self._try_load_torchvision_model()

    def _try_load_torchvision_model(self):
        """Attempts to load a fine-tuned MobileNetV3 civic classifier if weights exist."""
        if not os.path.exists(self.weights_path):
            return None
        try:
            import torch
            import torchvision.models as models
            model = models.mobilenet_v3_small(num_classes=len(self.CATEGORIES))
            state = torch.load(self.weights_path, map_location="cpu")
            model.load_state_dict(state)
            model.eval()
            logger.info(f"Loaded civic vision weights from {self.weights_path}")
            return model
        except Exception as e:
            logger.debug(f"Could not load torch weights ({e}); using heuristic multimodal engine.")
            return None

    def _extract_image_visual_features(self, image_path_or_bytes: Any) -> Dict[str, float]:
        """
        Extract deterministic visual feature signals:
        - Texture variance (roughness for potholes/roads/rubbish)
        - Color channel histograms (dark tarmac, water blue/green, garbage multicolored)
        - Contrast & edge density
        """
        try:
            if isinstance(image_path_or_bytes, bytes):
                img = Image.open(io.BytesIO(image_path_or_bytes)).convert("RGB")
            elif isinstance(image_path_or_bytes, str) and os.path.exists(image_path_or_bytes):
                img = Image.open(image_path_or_bytes).convert("RGB")
            elif hasattr(image_path_or_bytes, "read"):
                img = Image.open(image_path_or_bytes).convert("RGB")
            else:
                return {"valid": False}

            img_resized = img.resize((128, 128))
            np_img = np.array(img_resized, dtype=np.float32) / 255.0

            # Channel means
            r_mean = float(np.mean(np_img[:, :, 0]))
            g_mean = float(np.mean(np_img[:, :, 1]))
            b_mean = float(np.mean(np_img[:, :, 2]))

            # Gray conversion for edge & texture variance
            gray = 0.2989 * np_img[:, :, 0] + 0.5870 * np_img[:, :, 1] + 0.1140 * np_img[:, :, 2]
            variance = float(np.var(gray))

            # Simple gradient edge magnitude
            gx = np.abs(gray[:, 1:] - gray[:, :-1])
            gy = np.abs(gray[1:, :] - gray[:-1, :])
            edge_density = float(np.mean(gx) + np.mean(gy))

            return {
                "valid": True,
                "r_mean": r_mean,
                "g_mean": g_mean,
                "b_mean": b_mean,
                "variance": variance,
                "edge_density": edge_density
            }
        except Exception:
            return {"valid": False}

    def _score_text_tokens(self, text: str) -> Dict[str, float]:
        text_lower = text.lower() if text else ""
        scores = {cat: 0.05 for cat in self.CATEGORIES}

        for category, keywords in self.KEYWORD_MAPPINGS.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    scores[category] += 0.45
                elif kw in text_lower:
                    scores[category] += 0.25
        return scores

    def classify_with_confidence_tiers(
        self, text: str, image_source: Optional[Any] = None
    ) -> Tuple[str, float, str, Dict[str, float], Dict[str, Any]]:
        """
        Classifies issue and returns explicit confidence tier:
        - HIGH (>= 0.75): automated routing directly to field officer
        - MEDIUM (0.65 – 0.74): routed to department queue
        - LOW (< 0.65): flagged for human reviewer triage
        """
        detected_category, confidence, probabilities, features = self.classify(text, image_source)

        if confidence >= 0.75:
            confidence_tier = "HIGH"
        elif confidence >= 0.65:
            confidence_tier = "MEDIUM"
        else:
            confidence_tier = "LOW"

        features["confidence_tier"] = confidence_tier
        features["requires_manual_triage"] = (confidence_tier == "LOW")

        return detected_category, confidence, confidence_tier, probabilities, features

    def classify(self, text: str, image_source: Optional[Any] = None) -> Tuple[str, float, Dict[str, float], Dict[str, Any]]:
        """
        Classifies issue using multimodal fusion.
        Returns: (detected_category, confidence, all_probabilities, explanation_features)
        """
        text_scores = self._score_text_tokens(text)
        visual_features = self._extract_image_visual_features(image_source) if image_source else {"valid": False}

        combined_scores = {}
        for cat in self.CATEGORIES:
            base_score = text_scores.get(cat, 0.05)

            # Visual feature modulation
            if visual_features.get("valid"):
                edge_d = visual_features.get("edge_density", 0.0)
                var = visual_features.get("variance", 0.0)
                r_m = visual_features.get("r_mean", 0.5)
                b_m = visual_features.get("b_mean", 0.5)

                if cat in ("POTHOLE", "DAMAGED_ROAD") and edge_d > 0.08:
                    base_score += 0.25
                elif cat in ("GARBAGE", "ILLEGAL_DUMPING") and var > 0.04:
                    base_score += 0.20
                elif cat in ("WATER_LEAKAGE", "DRAINAGE") and (b_m > r_m or edge_d > 0.06):
                    base_score += 0.20
                elif cat == "STREETLIGHT" and (r_m < 0.35 and b_m < 0.35): # Dark / Night scene
                    base_score += 0.25
                elif cat == "OPEN_MANHOLE" and edge_d > 0.10:
                    base_score += 0.25

            combined_scores[cat] = base_score

        # Softmax normalization
        exp_scores = {k: math.exp(v * 2.5) for k, v in combined_scores.items()}
        sum_exp = sum(exp_scores.values())
        probabilities = {k: round(v / sum_exp, 4) for k, v in exp_scores.items()}

        # Top category & confidence
        top_category = max(probabilities.items(), key=lambda x: x[1])
        detected_category = top_category[0]
        confidence = float(top_category[1])

        # Suggested department
        suggested_department = self.CATEGORY_DEPARTMENTS.get(detected_category, "Municipal Administration")

        features_summary = {
            "visual_valid": visual_features.get("valid", False),
            "edge_density": round(visual_features.get("edge_density", 0.0), 4),
            "texture_variance": round(visual_features.get("variance", 0.0), 4),
            "text_match_strength": round(text_scores.get(detected_category, 0.0), 2),
            "suggested_department": suggested_department
        }

        return detected_category, confidence, probabilities, features_summary


issue_classifier = MultimodalIssueClassifier()
