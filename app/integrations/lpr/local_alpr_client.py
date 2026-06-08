"""Cliente LPR local gratuito basado en OCR.

Esta implementación no depende de APIs externas. Para la primera fase del PoC
usa EasyOCR sobre el frame completo o una zona de interés fija configurada por
variables de entorno.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger

from app.core.errors import LprApiError, LprPlateNotDetectedError
from app.integrations.lpr.image_preprocessor import ImagePreprocessor, RoiConfig
from app.integrations.lpr.lpr_client import LprClient
from app.integrations.lpr.lpr_models import LprResult
from app.integrations.lpr.plate_text_normalizer import PlateTextNormalizer


@dataclass(frozen=True)
class OcrCandidate:
    text: str
    confidence: float


class LocalAlprClient(LprClient):
    """Reconoce placas usando OCR local gratuito."""

    def __init__(
        self,
        roi: RoiConfig | None,
        region: str,
        min_text_length: int,
        max_text_length: int,
        gpu: bool = False,
    ) -> None:
        self._reader = None
        self._gpu = gpu
        self._region = region
        self._preprocessor = ImagePreprocessor(roi=roi)
        self._normalizer = PlateTextNormalizer(
            min_length=min_text_length,
            max_length=max_text_length,
        )

    def recognize(self, image_bytes: bytes) -> LprResult:
        try:
            frame = self._preprocessor.decode_jpeg(image_bytes)
        except ValueError as exc:
            raise LprApiError(str(exc)) from exc

        candidates = self._extract_candidates(frame)
        best_candidate = self._select_best_candidate(candidates)

        if best_candidate is None:
            raise LprPlateNotDetectedError("OCR local no detectó una placa válida")

        return LprResult(
            plate=best_candidate.text,
            confidence=best_candidate.confidence,
            vehicle_type=None,
            region=self._region,
            timestamp=datetime.now(timezone.utc),
            status="OK",
        )

    def _extract_candidates(self, frame) -> list[OcrCandidate]:
        reader = self._get_reader()
        candidates: list[OcrCandidate] = []

        for image in self._preprocessor.build_ocr_images(frame):
            ocr_results = reader.readtext(image, detail=1, paragraph=False)
            for result in ocr_results:
                raw_text = str(result[1])
                confidence = float(result[2])
                normalized_text = self._normalizer.normalize(raw_text)

                if self._normalizer.is_candidate(normalized_text):
                    candidates.append(
                        OcrCandidate(text=normalized_text, confidence=confidence)
                    )

        logger.debug("OCR local generó {} candidatos", len(candidates))
        return candidates

    def _get_reader(self):
        if self._reader is not None:
            return self._reader

        try:
            import easyocr
        except ImportError as exc:
            raise LprApiError(
                "EasyOCR no está instalado. Ejecuta: pip install easyocr"
            ) from exc

        self._reader = easyocr.Reader(["en"], gpu=self._gpu)
        return self._reader

    def _select_best_candidate(self, candidates: list[OcrCandidate]) -> OcrCandidate | None:
        if not candidates:
            return None

        votes_by_text: dict[str, list[float]] = {}
        for candidate in candidates:
            votes_by_text.setdefault(candidate.text, []).append(candidate.confidence)

        best_text = max(
            votes_by_text,
            key=lambda text: (len(votes_by_text[text]), max(votes_by_text[text])),
        )
        return OcrCandidate(
            text=best_text,
            confidence=max(votes_by_text[best_text]),
        )