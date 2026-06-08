"""Tests de las reglas de cruce.

Las reglas viven en una función pura (`evaluate_crossing`), así que
podemos cubrirlas sin levantar servicios ni mockear nada.
"""

from datetime import date, datetime, timezone

from app.integrations.biostar.biostar_models import (
    BioStarUser,
    BioStarVerificationResult,
)
from app.integrations.lpr.lpr_models import LprResult
from app.integrations.rntt.rntt_models import RnttPolicy, RnttResult, RnttVehicle
from app.modules.crossing.crossing_models import CrossingDecision
from app.modules.crossing.crossing_rules import evaluate_crossing


TODAY = date(2026, 6, 1)


def _lpr(plate: str = "A123456") -> LprResult:
    return LprResult(
        plate=plate,
        confidence=0.9,
        vehicle_type="Truck",
        region="do",
        timestamp=datetime.now(timezone.utc),
        status="OK",
    )


def _rntt_ok(plate: str = "A123456") -> RnttResult:
    return RnttResult(
        plate=plate,
        status="ACTIVE",
        vehicle=RnttVehicle(plate=plate, brand="Daihatsu", model="Hijet"),
        policies=[
            RnttPolicy(name="Seguro", expires_at=date(2027, 1, 1), is_valid=True),
        ],
        queried_at=datetime.now(timezone.utc),
    )


def _biostar(found: bool = True, active: bool = True) -> BioStarVerificationResult:
    user = (
        BioStarUser(user_id="42", name="Juan", is_active=active)
        if found else None
    )
    return BioStarVerificationResult(
        found=found,
        is_active=active if found else False,
        user=user,
        reason=None if (found and active) else "test",
        checked_at=datetime.now(timezone.utc),
    )


def test_no_plate_returns_manual_review() -> None:
    decision, _ = evaluate_crossing(lpr=None, rntt=None, biostar=None, today=TODAY)
    assert decision == CrossingDecision.NEEDS_MANUAL_REVIEW


def test_plate_without_rntt_returns_manual_review() -> None:
    decision, reason = evaluate_crossing(
        lpr=_lpr(), rntt=None, biostar=None, today=TODAY,
    )
    assert decision == CrossingDecision.NEEDS_MANUAL_REVIEW
    assert "RNTT" in reason


def test_plate_with_rntt_not_found_returns_manual_review() -> None:
    rntt = RnttResult(plate="A999X", status="NOT_FOUND", queried_at=datetime.now(timezone.utc))
    decision, _ = evaluate_crossing(lpr=_lpr("A999X"), rntt=rntt, biostar=None, today=TODAY)
    assert decision == CrossingDecision.NEEDS_MANUAL_REVIEW


def test_rntt_inactive_rejects() -> None:
    rntt = RnttResult(plate="A1", status="INACTIVE", queried_at=datetime.now(timezone.utc))
    decision, _ = evaluate_crossing(lpr=_lpr("A1"), rntt=rntt, biostar=None, today=TODAY)
    assert decision == CrossingDecision.REJECTED


def test_expired_policy_rejects() -> None:
    rntt = RnttResult(
        plate="A1",
        status="ACTIVE",
        policies=[RnttPolicy(name="Seguro", expires_at=date(2024, 1, 1), is_valid=True)],
        queried_at=datetime.now(timezone.utc),
    )
    decision, reason = evaluate_crossing(lpr=_lpr(), rntt=rntt, biostar=None, today=TODAY)
    assert decision == CrossingDecision.REJECTED
    assert "Seguro" in reason


def test_biostar_not_found_rejects() -> None:
    decision, _ = evaluate_crossing(
        lpr=_lpr(), rntt=_rntt_ok(), biostar=_biostar(found=False), today=TODAY,
    )
    assert decision == CrossingDecision.REJECTED


def test_biostar_inactive_rejects() -> None:
    decision, _ = evaluate_crossing(
        lpr=_lpr(), rntt=_rntt_ok(), biostar=_biostar(found=True, active=False), today=TODAY,
    )
    assert decision == CrossingDecision.REJECTED


def test_everything_valid_authorizes() -> None:
    decision, _ = evaluate_crossing(
        lpr=_lpr(), rntt=_rntt_ok(), biostar=_biostar(), today=TODAY,
    )
    assert decision == CrossingDecision.AUTHORIZED


def test_no_biostar_is_optional_when_other_checks_pass() -> None:
    decision, _ = evaluate_crossing(
        lpr=_lpr(), rntt=_rntt_ok(), biostar=None, today=TODAY,
    )
    assert decision == CrossingDecision.AUTHORIZED
