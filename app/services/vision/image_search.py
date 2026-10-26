import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image

from app.config import settings
from app.core.logging import logger
from app.models.product import Product

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB


class ImageValidationError(ValueError):
    pass


class MultimodalImageSearchEngine:
    """Production-grade visual similarity engine with CLIP and CV feature fallback."""

    def __init__(self, model_name: str = "clip-ViT-B-32", cache_dir: Path | None = None):
        self.model_name = model_name
        self.cache_dir = cache_dir or settings.INDEX_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.products: list[Product] = []
        self.image_embeddings: np.ndarray | None = None
        self.valid_product_indices: list[int] = []
        self._clip_model = None
        self._clip_processor = None
        self._clip_attempted: bool = False
        self._encoder_type = "cv_color_spatial_histogram"

    def _init_clip(self):
        if self._clip_attempted:
            return
        self._clip_attempted = True

        cache_path = (
            Path.home() / ".cache" / "huggingface" / "hub" / "models--openai--clip-vit-base-patch32"
        )
        if cache_path.exists():
            try:
                from transformers import CLIPModel, CLIPProcessor

                model_id = "openai/clip-vit-base-patch32"
                self._clip_processor = CLIPProcessor.from_pretrained(
                    model_id, local_files_only=True
                )
                self._clip_model = CLIPModel.from_pretrained(model_id, local_files_only=True)
                self._encoder_type = "clip-vit-base-patch32"
                logger.info("Local CLIP vision model loaded successfully.")
                return
            except Exception:
                pass

        self._encoder_type = "cv_color_spatial_histogram"

    def _extract_cv_features(self, img: Image.Image) -> np.ndarray:
        """Extract deterministic visual features (RGB color histogram + 4x4 spatial grid color blocks)."""
        img_rgb = img.convert("RGB")

        # 1. 3D color histogram (8 bins per channel = 512 features)
        hist = img_rgb.histogram()  # 256 R, 256 G, 256 B
        # Sample down to 16 bins per channel = 48 features
        r_hist = np.array(hist[0:256]).reshape(16, 16).sum(axis=1)
        g_hist = np.array(hist[256:512]).reshape(16, 16).sum(axis=1)
        b_hist = np.array(hist[512:768]).reshape(16, 16).sum(axis=1)
        color_hist = np.concatenate([r_hist, g_hist, b_hist]).astype(np.float32)

        # 2. 4x4 spatial grid average colors (4x4x3 = 48 features)
        resized = img_rgb.resize((4, 4), Image.Resampling.BILINEAR)
        spatial_features = np.array(resized).flatten().astype(np.float32)

        combined = np.concatenate([color_hist, spatial_features])
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        return combined

    def extract_image_features(self, img: Image.Image) -> np.ndarray:
        self._init_clip()
        if (
            self._encoder_type.startswith("clip")
            and self._clip_model is not None
            and self._clip_processor is not None
        ):
            import torch

            inputs = self._clip_processor(images=img, return_tensors="pt")
            with torch.no_grad():
                features = self._clip_model.get_image_features(**inputs)
                features = features / features.norm(p=2, dim=-1, keepdim=True)
                return features.cpu().numpy()[0].astype(np.float32)
        else:
            return self._extract_cv_features(img)

    def fit(self, products: list[Product], force_refresh: bool = False):
        self.products = products
        self.valid_product_indices = []

        if not products:
            self.image_embeddings = None
            return

        cat_ids_str = "".join(f"{p.product_id}_{p.image_path}" for p in products)
        cat_hash = hashlib.md5(cat_ids_str.encode("utf-8")).hexdigest()
        emb_file = self.cache_dir / f"img_emb_{self._encoder_type}_{cat_hash}.npy"
        idx_file = self.cache_dir / f"img_idx_{self._encoder_type}_{cat_hash}.json"

        if not force_refresh and emb_file.exists() and idx_file.exists():
            try:
                self.image_embeddings = np.load(emb_file)
                with open(idx_file, "r") as f:
                    self.valid_product_indices = json.load(f)
                logger.info(
                    f"Loaded {len(self.image_embeddings)} cached image embeddings from {emb_file}"
                )
                return
            except Exception as e:
                logger.warning(f"Error reading image cache: {e}")

        embeddings_list = []
        valid_indices = []

        for idx, p in enumerate(products):
            if not p.image_path:
                continue

            # Resolve local image path
            img_path = Path(p.image_path)
            if not img_path.is_absolute():
                img_path = settings.DATA_DIR.parent / p.image_path

            if not img_path.exists():
                continue

            try:
                with Image.open(img_path) as img:
                    feat = self.extract_image_features(img)
                    embeddings_list.append(feat)
                    valid_indices.append(idx)
            except Exception as e:
                logger.warning(f"Could not process image {img_path}: {e}")

        if embeddings_list:
            self.image_embeddings = np.array(embeddings_list, dtype=np.float32)
            self.valid_product_indices = valid_indices
            try:
                np.save(emb_file, self.image_embeddings)
                with open(idx_file, "w") as f:
                    json.dump(valid_indices, f)
                logger.info(f"Saved {len(self.image_embeddings)} image embeddings to {emb_file}")
            except Exception as e:
                logger.warning(f"Failed writing image cache: {e}")
        else:
            self.image_embeddings = None
            self.valid_product_indices = []

    def validate_upload(self, content_bytes: bytes, filename: str | None = None) -> Image.Image:
        if not content_bytes or len(content_bytes) == 0:
            raise ImageValidationError("Uploaded image file is empty.")

        if len(content_bytes) > MAX_IMAGE_BYTES:
            raise ImageValidationError(
                f"Image file size ({len(content_bytes) / 1024 / 1024:.2f}MB) exceeds limit of 5MB."
            )

        if filename:
            ext = Path(filename).suffix.lower()
            if ext and ext not in ALLOWED_EXTENSIONS:
                raise ImageValidationError(
                    f"Invalid image extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
                )

        try:
            img = Image.open(io.BytesIO(content_bytes))
            img.verify()  # Verify valid image header
        except Exception as e:
            raise ImageValidationError(f"File is not a valid or readable image: {e!s}")

        # Reopen after verify (verify closes file pointer)
        img = Image.open(io.BytesIO(content_bytes))

        # Check dimensions
        w, h = img.size
        if w < 10 or h < 10:
            raise ImageValidationError(
                f"Image dimensions ({w}x{h}) are too small. Minimum is 10x10."
            )
        if w > 6000 or h > 6000:
            raise ImageValidationError(
                f"Image dimensions ({w}x{h}) exceed maximum allowed of 6000x6000."
            )

        return img

    def search_by_image(self, img: Image.Image, top_k: int = 6) -> list[tuple[Product, float]]:
        if self.image_embeddings is None or len(self.image_embeddings) == 0:
            return []

        q_feat = self.extract_image_features(img)
        # Cosine similarity
        sims = np.dot(self.image_embeddings, q_feat)
        sims = np.clip(sims, 0.0, 1.0)

        top_local_idx = np.argsort(sims)[::-1][:top_k]

        results = []
        for l_idx in top_local_idx:
            orig_p_idx = self.valid_product_indices[l_idx]
            prod = self.products[orig_p_idx]
            score = float(sims[l_idx])
            results.append((prod, score))

        return results

    @property
    def encoder_name(self) -> str:
        return self._encoder_type
