"""Orquestación de una lectura LPR.

Flujo:
1. Pide un frame a `CameraService.capture_current_frame` (reutiliza el último
   frame del stream si está activo; nunca abre la cámara directamente).
2. Guarda SIEMPRE el frame analizado como evidencia.
3. Decodifica y ejecuta el motor LPR.
4. Normaliza y valida la placa.
5. Decide el estado (PLATE_DETECTED / LOW_CONFIDENCE / NO_PLATE_DETECTED / ERROR).
6. Guarda el recorte de placa solo si hubo detección.
7. Devuelve un resultado estructurado con tiempos y URLs públicas.

Los errores de cámara (no existe / no entrega frame) se propagan para que la
capa HTTP los mapee a 404/503; no se transforman en evidencia.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from urllib.parse import urlsplit

import cv2
import numpy as np
from loguru import logger

from app.integrations.lpr.lpr_engine import LprEngine, LprEngineResult
from app.modules.camera.camera_service import CameraService
from app.modules.lpr.lpr_models import LprReadRequest, LprReadResponse, LprReadStatus
from app.modules.lpr.lpr_result_storage import LprResultStorage, StoredEvidence
from app.modules.lpr.plate_normalizer import PlateNormalizer
from app.modules.lpr.plate_validator import PlateValidator


@dataclass(frozen=True)
class _FrameObservation:
    index: int
    frame_bytes: bytes
    engine_result: LprEngineResult
    normalized: str
    format_valid: bool


class LprService:
    def __init__(
        self,
        camera_service: CameraService,
        engine: LprEngine,
        storage: LprResultStorage,
        normalizer: PlateNormalizer,
        validator: PlateValidator,
        min_confidence: float = 70.0,
        max_processing_ms: int = 5000,
        burst_frame_count: int = 1,
        burst_interval_ms: int = 200,
        consensus_min_votes: int = 2,
        early_consensus: bool = True,
        result_sink: Callable[[LprReadResponse], object] | None = None,
    ) -> None:
        self._camera = camera_service
        self._engine = engine
        self._storage = storage
        self._normalizer = normalizer
        self._validator = validator
        self._min_confidence = min_confidence
        self._max_processing_ms = max_processing_ms
        self._burst_frame_count = max(1, burst_frame_count)
        self._burst_interval_ms = max(0, burst_interval_ms)
        self._consensus_min_votes = max(1, consensus_min_votes)
        self._early_consensus = early_consensus
        self._result_sink = result_sink

    def read_plate(self, request: LprReadRequest) -> LprReadResponse:
        started = time.monotonic()
        detected_at = datetime.now(timezone.utc)
        event_id = request.event_id or f"LPR-{detected_at.strftime('%Y%m%d-%H%M%S')}"

        if self._burst_frame_count == 1:
            frames = [self._camera.capture_current_frame(request.camera_id)]
        else:
            frames = self._camera.capture_frame_burst(
                request.camera_id,
                count=self._burst_frame_count,
                interval_ms=self._burst_interval_ms,
            )

        config = self._camera.get_config(request.camera_id)
        observations: list[_FrameObservation] = []
        for index, frame_bytes in enumerate(frames):
            image = _decode_jpeg(frame_bytes)
            if image is None:
                continue
            if config.has_lpr_roi:
                height, width = image.shape[:2]
                x1 = max(0, min(config.roi_x, width))
                y1 = max(0, min(config.roi_y, height))
                x2 = max(x1, min(x1 + config.roi_width, width))
                y2 = max(y1, min(y1 + config.roi_height, height))
                cropped = image[y1:y2, x1:x2]
                if cropped.size:
                    image = cropped
            try:
                result = self._engine.read_plate(image)
            except Exception:  # noqa: BLE001
                logger.exception("LPR {}: fallo OCR en frame {}", event_id, index)
                continue
            normalized = (
                result.best_normalized_text
                or self._normalizer.normalize(result.best_raw_text)
            )
            observations.append(
                _FrameObservation(
                    index=index,
                    frame_bytes=frame_bytes,
                    engine_result=result,
                    normalized=normalized,
                    format_valid=self._validator.is_format_valid(normalized),
                )
            )
            if self._early_consensus and self._burst_frame_count > 1:
                matching = [
                    obs
                    for obs in observations
                    if obs.normalized == normalized and obs.format_valid
                ]
                average_confidence = (
                    sum(obs.engine_result.confidence for obs in matching)
                    / len(matching)
                    if matching
                    else 0.0
                )
                if (
                    len(matching) >= self._consensus_min_votes
                    and average_confidence >= self._min_confidence
                ):
                    logger.info(
                        "LPR {}: consenso temprano '{}' alcanzado en {}/{} frames",
                        event_id,
                        normalized,
                        len(observations),
                        len(frames),
                    )
                    break

        if not observations:
            stored = self._storage.save_frame(frames[0], detected_at)
            return self._respond(
                event_id=event_id,
                request=request,
                started=started,
                detected_at=detected_at,
                stored_frame=stored,
                status=LprReadStatus.ERROR,
                rejection_reason="no_processable_frames",
                frames_requested=self._burst_frame_count,
                frames_captured=len(frames),
                frames_processed=0,
            )

        valid_groups: dict[str, list[_FrameObservation]] = {}
        for observation in observations:
            if observation.normalized and observation.format_valid:
                valid_groups.setdefault(observation.normalized, []).append(observation)

        if valid_groups:
            winning_text, winning_group = max(
                valid_groups.items(),
                key=lambda item: (
                    len(item[1]),
                    sum(obs.engine_result.confidence for obs in item[1]) / len(item[1]),
                    max(obs.engine_result.confidence for obs in item[1]),
                ),
            )
            winner = max(
                winning_group, key=lambda obs: obs.engine_result.confidence
            )
        else:
            winner = max(
                observations, key=lambda obs: obs.engine_result.confidence
            )
            winning_text = winner.normalized
            winning_group = [
                obs for obs in observations if obs.normalized == winning_text
            ]

        votes = len(winning_group) if winning_text else 0
        consensus_total = len(observations)
        consensus_ratio = votes / consensus_total if consensus_total else 0.0
        confidence = (
            sum(obs.engine_result.confidence for obs in winning_group) / votes
            if votes
            else 0.0
        )
        engine_result = replace(
            winner.engine_result,
            candidate_count=sum(
                obs.engine_result.candidate_count for obs in observations
            ),
            ocr_attempt_count=sum(
                obs.engine_result.ocr_attempt_count for obs in observations
            ),
        )
        stored_frame = self._storage.save_frame(winner.frame_bytes, detected_at)
        frame_candidates = [
            {
                "frame_index": obs.index,
                "text": obs.normalized or None,
                "raw_text": obs.engine_result.best_raw_text,
                "confidence": obs.engine_result.confidence,
                "format_valid": obs.format_valid,
            }
            for obs in observations
        ]

        if engine_result.best_raw_text is None:
            return self._respond(
                event_id=event_id,
                request=request,
                started=started,
                detected_at=detected_at,
                stored_frame=stored_frame,
                status=LprReadStatus.NO_PLATE_DETECTED,
                rejection_reason="no_text",
                engine_result=engine_result,
                frames_requested=self._burst_frame_count,
                frames_captured=len(frames),
                frames_processed=len(observations),
                consensus_votes=votes,
                consensus_total=consensus_total,
                consensus_ratio=consensus_ratio,
                frame_candidates=frame_candidates,
            )

        stored_crop: StoredEvidence | None = None
        if engine_result.plate_crop_jpeg is not None:
            stored_crop = self._storage.save_crop(
                engine_result.plate_crop_jpeg, detected_at
            )

        format_valid = self._validator.is_format_valid(winning_text)
        if self._burst_frame_count > 1 and votes < self._consensus_min_votes:
            status = LprReadStatus.LOW_CONFIDENCE
            rejection_reason: str | None = "insufficient_consensus"
        elif confidence < self._min_confidence:
            status = LprReadStatus.LOW_CONFIDENCE
            rejection_reason = "low_confidence"
        elif not format_valid:
            status = LprReadStatus.FORMAT_MISMATCH
            rejection_reason = "format_mismatch"
        else:
            status = LprReadStatus.PLATE_DETECTED
            rejection_reason = None

        accepted = status is LprReadStatus.PLATE_DETECTED
        logger.info(
            "LPR {}: {} candidato='{}' votos={}/{} conf={:.1f}",
            event_id,
            status.value,
            winning_text,
            votes,
            consensus_total,
            confidence,
        )
        return self._respond(
            event_id=event_id,
            request=request,
            started=started,
            detected_at=detected_at,
            stored_frame=stored_frame,
            status=status,
            rejection_reason=rejection_reason,
            plate=winner.engine_result.best_raw_text if accepted else None,
            plate_normalized=winning_text if accepted else None,
            confidence=round(confidence, 1),
            stored_crop=stored_crop,
            format_valid=format_valid,
            engine_result=engine_result,
            frames_requested=self._burst_frame_count,
            frames_captured=len(frames),
            frames_processed=len(observations),
            consensus_votes=votes,
            consensus_total=consensus_total,
            consensus_ratio=consensus_ratio,
            frame_candidates=frame_candidates,
        )

    def _read_plate_single_legacy(self, request: LprReadRequest) -> LprReadResponse:
        started = time.monotonic()
        detected_at = datetime.now(timezone.utc)
        event_id = request.event_id or f"LPR-{detected_at.strftime('%Y%m%d-%H%M%S')}"

        # 1. Frame desde Camera. Propaga CameraNotFoundError (->404) y
        #    CameraError (->503): no se atrapan aquí a propósito.
        frame_bytes = self._camera.capture_current_frame(request.camera_id)

        # 2. El frame analizado siempre se guarda como evidencia.
        stored_frame = self._storage.save_frame(frame_bytes, detected_at)

        image = _decode_jpeg(frame_bytes)
        if image is None:
            logger.error("LPR {}: no se pudo decodificar el frame", event_id)
            return self._respond(
                event_id=event_id,
                request=request,
                started=started,
                detected_at=detected_at,
                stored_frame=stored_frame,
                status=LprReadStatus.ERROR,
                rejection_reason="decode_error",
            )

        camera_config = self._camera.get_config(request.camera_id)
        if camera_config.has_lpr_roi:
            height, width = image.shape[:2]
            x1 = max(0, min(camera_config.roi_x, width))
            y1 = max(0, min(camera_config.roi_y, height))
            x2 = max(x1, min(x1 + camera_config.roi_width, width))
            y2 = max(y1, min(y1 + camera_config.roi_height, height))
            cropped = image[y1:y2, x1:x2]
            if cropped.size:
                image = cropped
                logger.info(
                    "LPR {}: ROI de camara {} aplicado ({},{}) {}x{}",
                    event_id,
                    request.camera_id,
                    x1,
                    y1,
                    x2 - x1,
                    y2 - y1,
                )

        # 3. Motor LPR. Un fallo del motor (p.ej. EasyOCR ausente) no debe tumbar
        #    el endpoint: se devuelve estado ERROR con el frame ya guardado.
        try:
            engine_result = self._engine.read_plate(image)
        except Exception:  # noqa: BLE001 - el motor PoC puede fallar de varias formas
            logger.exception("LPR {}: el motor de lectura falló", event_id)
            return self._respond(
                event_id=event_id,
                request=request,
                started=started,
                detected_at=detected_at,
                stored_frame=stored_frame,
                status=LprReadStatus.ERROR,
                rejection_reason="engine_error",
            )

        # 4. Sin texto candidato -> NO_PLATE_DETECTED.
        if engine_result.best_raw_text is None:
            logger.info("LPR {}: sin placa detectada", event_id)
            return self._respond(
                event_id=event_id,
                request=request,
                started=started,
                detected_at=detected_at,
                stored_frame=stored_frame,
                status=LprReadStatus.NO_PLATE_DETECTED,
                rejection_reason="no_text",
                engine_result=engine_result,
            )

        # 5. Hay un candidato. Se guarda el crop usado para OCR (haya o no
        #    formato válido) porque hubo una región/lectura.
        normalized = (
            engine_result.best_normalized_text
            or self._normalizer.normalize(engine_result.best_raw_text)
        )
        format_valid = self._validator.is_format_valid(normalized)
        confidence = engine_result.confidence

        stored_crop: StoredEvidence | None = None
        if engine_result.plate_crop_jpeg is not None:
            stored_crop = self._storage.save_crop(
                engine_result.plate_crop_jpeg, detected_at
            )

        # 6. Decisión de aceptación: solo PLATE_DETECTED si confianza suficiente
        #    Y el formato es válido. El candidato rechazado NO se expone como
        #    `plate` (solo como best_raw_text/best_normalized_text de depuración);
        #    no se infiere ni autocompleta ningún carácter.
        #    Precedencia: la confianza se evalúa ANTES que el formato; si ambos
        #    fallan, el motivo reportado es "low_confidence".
        if confidence < self._min_confidence:
            status = LprReadStatus.LOW_CONFIDENCE
            rejection_reason: str | None = "low_confidence"
        elif not format_valid:
            status = LprReadStatus.FORMAT_MISMATCH
            rejection_reason = "format_mismatch"
        else:
            status = LprReadStatus.PLATE_DETECTED
            rejection_reason = None

        accepted = status is LprReadStatus.PLATE_DETECTED
        logger.info(
            "LPR {}: {} candidato='{}' conf={:.1f} format_valid={} [terminal={} lane={}]",
            event_id,
            status.value,
            normalized,
            confidence,
            format_valid,
            request.terminal,
            request.lane,
        )
        return self._respond(
            event_id=event_id,
            request=request,
            started=started,
            detected_at=detected_at,
            stored_frame=stored_frame,
            status=status,
            rejection_reason=rejection_reason,
            plate=engine_result.best_raw_text if accepted else None,
            plate_normalized=normalized if accepted else None,
            confidence=confidence,
            stored_crop=stored_crop,
            format_valid=format_valid,
            engine_result=engine_result,
        )

    def _respond(
        self,
        *,
        event_id: str,
        request: LprReadRequest,
        started: float,
        detected_at: datetime,
        stored_frame: StoredEvidence,
        status: LprReadStatus,
        rejection_reason: str | None,
        plate: str | None = None,
        plate_normalized: str | None = None,
        confidence: float = 0.0,
        stored_crop: StoredEvidence | None = None,
        format_valid: bool = False,
        engine_result: LprEngineResult | None = None,
        frames_requested: int = 1,
        frames_captured: int = 1,
        frames_processed: int = 1,
        consensus_votes: int = 0,
        consensus_total: int = 0,
        consensus_ratio: float = 0.0,
        frame_candidates: list[dict] | None = None,
    ) -> LprReadResponse:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if elapsed_ms > self._max_processing_ms:
            logger.warning(
                "LPR {}: procesamiento {}ms supera el máximo {}ms",
                event_id,
                elapsed_ms,
                self._max_processing_ms,
            )
        camera_config = self._camera.get_config(request.camera_id)
        camera_ip = ""
        if camera_config.source_type == "rtsp":
            camera_ip = urlsplit(camera_config.source).hostname or ""

        response = LprReadResponse(
            event_id=event_id,
            camera_id=request.camera_id,
            camera_name=camera_config.camera_name,
            camera_ip=camera_ip,
            status=status,
            plate=plate,
            plate_normalized=plate_normalized,
            confidence=confidence,
            source_frame_path=stored_frame.path,
            source_frame_url=stored_frame.url,
            plate_crop_path=stored_crop.path if stored_crop else None,
            plate_crop_url=stored_crop.url if stored_crop else None,
            processing_time_ms=elapsed_ms,
            detected_at=detected_at,
            engine=self._engine.name,
            candidate_count=engine_result.candidate_count if engine_result else 0,
            ocr_attempt_count=engine_result.ocr_attempt_count if engine_result else 0,
            best_raw_text=engine_result.best_raw_text if engine_result else None,
            best_normalized_text=(
                engine_result.best_normalized_text if engine_result else None
            ),
            expected_format=self._validator.expected_format,
            format_valid=format_valid,
            rejection_reason=rejection_reason,
            preprocessing_variant=(
                engine_result.preprocessing_variant if engine_result else None
            ),
            crop_saved=stored_crop is not None,
            selected_roi=engine_result.selected_roi if engine_result else None,
            digit_count=engine_result.digit_count if engine_result else 0,
            alpha_count=engine_result.alpha_count if engine_result else 0,
            candidate_rejections=(
                list(engine_result.candidate_rejections) if engine_result else []
            ),
            candidate_scores=(
                list(engine_result.candidate_scores) if engine_result else []
            ),
            frames_requested=frames_requested,
            frames_captured=frames_captured,
            frames_processed=frames_processed,
            consensus_votes=consensus_votes,
            consensus_total=consensus_total,
            consensus_ratio=round(consensus_ratio, 3),
            frame_candidates=frame_candidates or [],
        )
        if self._result_sink is not None:
            try:
                self._result_sink(response)
            except Exception:  # noqa: BLE001 - Ignition no debe tumbar la lectura LPR
                logger.exception("LPR {}: no se pudo publicar el resultado a Ignition", event_id)
        return response


def _decode_jpeg(frame_bytes: bytes) -> np.ndarray | None:
    array = np.frombuffer(frame_bytes, dtype=np.uint8)
    return cv2.imdecode(array, cv2.IMREAD_COLOR)
