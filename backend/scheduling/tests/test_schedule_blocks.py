"""Blocked periods — BR §15 / MP-16.

The gap audit recorded this capability as **absent** (GAP-12 / F-20): no table,
no route, no enforcement.  These tests state the contract that now exists, and
they deliberately cover the negative paths — a block that cannot be created, a
block that must not leak across tenants or branches, a block that is cancelled,
and a stored block whose window cannot be parsed (it must degrade the read, never
500 it).

Availability assertions read the **real** appointment and block rows, so "the
blocked slot is published as unavailable" is checked against the same arithmetic
the booking guard uses.
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from amsdp_test_support import (db_session, ensure_branch, ensure_doctor,
                               ensure_org, ensure_user, headers, load_app,
                               purge_org)
from common.models import AuditEvent, Schedule, ScheduleBlock

ORG = "mp16-org"
BR = "mp16-br"
BR2 = "mp16-br2"
OTHER_ORG = "mp16-other-org"
OTHER_BR = "mp16-other-br"
DOC = "mp16-doc"
DOC2 = "mp16-doc2"
OTHER_DOC = "mp16-other-doc"
ADMIN = "mp16_admin"
ADMIN2 = "mp16_admin2"
ORG_ADMIN = "mp16_org_admin"
OTHER_ADMIN = "mp16_other_admin"
RECP = "mp16_recp"
DOC_USER = "mp16_doc_user"

#: 2026-04-20 is a Monday — the weekday the MORNING template publishes on.
MONDAY = "2026-04-20"
TUESDAY = "2026-04-21"

MORNING = [{"day_of_week": 0, "start_time": "09:00", "end_time": "10:00",
            "slot_duration_minutes": 15, "max_patients": 2}]
AFTERNOON = [{"day_of_week": 0, "start_time": "14:00", "end_time": "15:00",
              "slot_duration_minutes": 15, "max_patients": 2}]


@pytest.fixture(scope="module")
def client():
    return TestClient(load_app("scheduling"))


@pytest.fixture(autouse=True)
def _world(client):
    purge_org(ORG)
    purge_org(OTHER_ORG)
    ensure_org(ORG)
    ensure_org(OTHER_ORG)
    ensure_branch(BR, ORG)
    ensure_branch(BR2, ORG)
    ensure_branch(OTHER_BR, OTHER_ORG)
    ensure_doctor(DOC, ORG, name="Dr. Blocked")
    ensure_doctor(DOC2, ORG, name="Dr. Second", mobile="01700000002")
    ensure_doctor(OTHER_DOC, OTHER_ORG, name="Dr. Other", mobile="01700000001")
    ensure_user(ADMIN, "branch_admin", ORG, BR)
    ensure_user(ADMIN2, "branch_admin", ORG, BR2)
    ensure_user(ORG_ADMIN, "org_admin", ORG, None)
    ensure_user(OTHER_ADMIN, "branch_admin", OTHER_ORG, OTHER_BR)
    ensure_user(RECP, "receptionist", ORG, BR)
    ensure_user(DOC_USER, "doctor", ORG, BR)
    yield
    purge_org(ORG)
    purge_org(OTHER_ORG)


def _schedule(client, user=ADMIN, doctor_id=DOC, templates=None,
              branch_id=BR) -> str:
    body = {"doctor_id": doctor_id, "organization_id": ORG,
            "branch_id": branch_id,
            "effective_from": "2026-01-01",
            "slot_templates": MORNING if templates is None else templates}
    r = client.post("/api/v1/schedules", headers=headers(user), json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _block(client, schedule_id, user=ADMIN, **body):
    payload = {"start_date": MONDAY, "reason": "medical leave"}
    payload.update(body)
    return client.post(f"/api/v1/schedules/{schedule_id}/blocks",
                       headers=headers(user), json=payload)


def _slots(client, schedule_id, day=MONDAY, user=ADMIN):
    r = client.get(f"/api/v1/schedules/{schedule_id}/available-slots",
                   params={"date_str": day}, headers=headers(user))
    assert r.status_code == 200, r.text
    return r.json()


class TestBlockCreate:
    def test_whole_day_block(self, client):
        sid = _schedule(client)
        r = _block(client, sid)
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["schedule_id"] == sid
        assert body["doctor_id"] == DOC
        assert body["branch_id"] == BR
        assert body["start_date"] == MONDAY
        assert body["end_date"] == MONDAY, "end_date defaults to start_date"
        assert body["whole_day"] is True
        assert body["window_label"] == "all day"
        assert body["status"] == "active"
        assert body["created_by"]
        with db_session() as s:
            row = s.query(ScheduleBlock).filter(
                ScheduleBlock.id == body["id"]).first()
            assert row is not None and row.reason == "medical leave"

    def test_windowed_block(self, client):
        sid = _schedule(client)
        r = _block(client, sid, start_time="09:00", end_time="09:30")
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["whole_day"] is False
        assert body["window_label"] == "09:00–09:30"
        assert (body["start_time"], body["end_time"]) == ("09:00", "09:30")

    def test_multi_day_range(self, client):
        sid = _schedule(client)
        r = _block(client, sid, end_date="2026-04-24")
        assert r.status_code == 201, r.text
        body = r.json()
        assert (body["start_date"], body["end_date"]) == (MONDAY, "2026-04-24")

    def test_creation_is_audited_with_the_full_record(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid).json()["id"]
        with db_session() as s:
            row = s.query(AuditEvent).filter(
                AuditEvent.action == "schedule.blocked",
                AuditEvent.target_id == block_id).first()
            assert row is not None
            assert row.organization_id == ORG
            assert row.branch_id == BR
            assert row.actor_id, "the actor is recorded"
            assert row.after["id"] == block_id
            assert row.after["reason"] == "medical leave"

    def test_reason_is_required(self, client):
        sid = _schedule(client)
        assert _block(client, sid, reason="").status_code == 422
        assert _block(client, sid, reason="  ").status_code == 422

    def test_reason_must_be_meaningful(self, client):
        sid = _schedule(client)
        assert _block(client, sid, reason="ab").status_code == 422

    def test_half_a_window_is_refused(self, client):
        sid = _schedule(client)
        assert _block(client, sid, start_time="09:00").status_code == 422
        assert _block(client, sid, end_time="09:30").status_code == 422

    def test_inverted_window_is_refused(self, client):
        sid = _schedule(client)
        assert _block(client, sid, start_time="10:00",
                      end_time="09:00").status_code == 422
        assert _block(client, sid, start_time="09:00",
                      end_time="09:00").status_code == 422

    def test_unpadded_clock_is_refused(self, client):
        sid = _schedule(client)
        assert _block(client, sid, start_time="9:00",
                      end_time="10:00").status_code == 422

    def test_inverted_date_range_is_refused(self, client):
        sid = _schedule(client)
        r = _block(client, sid, end_date="2026-04-19")
        assert r.status_code == 422
        assert "earlier" in r.text

    def test_bad_date_is_refused(self, client):
        sid = _schedule(client)
        assert _block(client, sid, start_date="20-04-2026").status_code == 422
        assert _block(client, sid, start_date="2026-02-30").status_code == 422

    def test_range_is_bounded(self, client):
        sid = _schedule(client)
        r = _block(client, sid, end_date="2027-04-21")   # 367 days
        assert r.status_code == 422
        assert "366" in r.text

    def test_another_tenant_schedule_is_a_non_disclosing_404(self, client):
        other = _schedule(client, user=OTHER_ADMIN, doctor_id=OTHER_DOC,
                          branch_id=OTHER_BR)
        r = _block(client, other)
        assert r.status_code == 404, "cross-tenant access fails closed"
        assert "not found" in r.text
        with db_session() as s:
            assert s.query(ScheduleBlock).filter(
                ScheduleBlock.schedule_id == other).count() == 0

    def test_another_branch_administrator_gets_a_404(self, client):
        sid = _schedule(client)                       # BR
        r = _block(client, sid, user=ADMIN2)          # branch_admin of BR2
        assert r.status_code == 404
        with db_session() as s:
            assert s.query(ScheduleBlock).filter(
                ScheduleBlock.schedule_id == sid).count() == 0

    def test_org_admin_may_block_any_branch_in_the_organization(self, client):
        sid = _schedule(client)
        assert _block(client, sid, user=ORG_ADMIN).status_code == 201

    def test_receptionist_cannot_block(self, client):
        sid = _schedule(client)
        assert _block(client, sid, user=RECP).status_code == 403

    def test_doctor_cannot_block(self, client):
        sid = _schedule(client)
        assert _block(client, sid, user=DOC_USER).status_code == 403

    def test_unknown_schedule_is_a_404(self, client):
        assert _block(client, "no-such-schedule").status_code == 404



class TestBlockList:
    def test_lists_active_blocks_ordered(self, client):
        sid = _schedule(client)
        _block(client, sid, start_time="14:00", end_time="14:30")
        _block(client, sid)                        # whole day, same date
        _block(client, sid, start_date=TUESDAY, end_date=TUESDAY)
        r = client.get(f"/api/v1/schedules/{sid}/blocks",
                       headers=headers(ADMIN))
        assert r.status_code == 200, r.text
        rows = r.json()
        assert len(rows) == 3
        assert rows[0]["start_date"] == MONDAY and rows[0]["whole_day"] is True
        assert rows[1]["start_date"] == MONDAY and rows[1]["whole_day"] is False
        assert rows[2]["start_date"] == TUESDAY

    def test_date_range_filters_by_overlap(self, client):
        sid = _schedule(client)
        _block(client, sid, start_date="2026-04-20", end_date="2026-04-30")
        _block(client, sid, start_date="2026-06-01", end_date="2026-06-01")
        rows = client.get(f"/api/v1/schedules/{sid}/blocks",
                          params={"date_from": "2026-04-25",
                                  "date_to": "2026-04-26"},
                          headers=headers(ADMIN)).json()
        assert len(rows) == 1, "a block spanning the window is still reported"
        assert rows[0]["start_date"] == "2026-04-20"

    def test_inverted_query_range_is_refused(self, client):
        sid = _schedule(client)
        r = client.get(f"/api/v1/schedules/{sid}/blocks",
                       params={"date_from": "2026-04-25",
                               "date_to": "2026-04-24"},
                       headers=headers(ADMIN))
        assert r.status_code == 422

    def test_cancelled_blocks_are_hidden_unless_requested(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid).json()["id"]
        client.delete(f"/api/v1/schedules/{sid}/blocks/{block_id}",
                      headers=headers(ADMIN))
        assert client.get(f"/api/v1/schedules/{sid}/blocks",
                          headers=headers(ADMIN)).json() == []
        rows = client.get(f"/api/v1/schedules/{sid}/blocks",
                          params={"include_cancelled": True},
                          headers=headers(ADMIN)).json()
        assert len(rows) == 1 and rows[0]["status"] == "cancelled"

    def test_other_tenant_cannot_list(self, client):
        other = _schedule(client, user=OTHER_ADMIN, doctor_id=OTHER_DOC,
                          branch_id=OTHER_BR)
        r = client.get(f"/api/v1/schedules/{other}/blocks",
                       headers=headers(ADMIN))
        assert r.status_code == 404


class TestBlockCancel:
    def test_cancel_keeps_the_row_and_audits(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid).json()["id"]
        r = client.delete(f"/api/v1/schedules/{sid}/blocks/{block_id}",
                          params={"reason": "doctor recovered"},
                          headers=headers(ADMIN))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "cancelled"
        assert body["cancelled_by"]
        assert body["cancel_reason"] == "doctor recovered"
        with db_session() as s:
            assert s.query(ScheduleBlock).filter(
                ScheduleBlock.id == block_id).count() == 1, "never deleted"
            row = s.query(AuditEvent).filter(
                AuditEvent.action == "schedule.block_cancelled",
                AuditEvent.target_id == block_id).first()
            assert row is not None
            assert row.before["status"] == "active"
            assert row.after["status"] == "cancelled"

    def test_cancelling_twice_is_refused(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid).json()["id"]
        assert client.delete(f"/api/v1/schedules/{sid}/blocks/{block_id}",
                             headers=headers(ADMIN)).status_code == 200
        assert client.delete(f"/api/v1/schedules/{sid}/blocks/{block_id}",
                             headers=headers(ADMIN)).status_code == 422

    def test_cancel_unknown_block_is_a_404(self, client):
        sid = _schedule(client)
        r = client.delete(f"/api/v1/schedules/{sid}/blocks/no-such-block",
                          headers=headers(ADMIN))
        assert r.status_code == 404

    def test_receptionist_cannot_cancel(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid).json()["id"]
        r = client.delete(f"/api/v1/schedules/{sid}/blocks/{block_id}",
                          headers=headers(RECP))
        assert r.status_code == 403
        with db_session() as s:
            assert s.query(ScheduleBlock).filter(
                ScheduleBlock.id == block_id).first().status == "active"



class TestAvailabilityWithBlocks:
    def test_blocked_slots_publish_zero_availability(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid, start_time="09:00",
                          end_time="09:30").json()["id"]
        body = _slots(client, sid)
        by_start = {s["start_time"]: s for s in body["slots"]}
        # 09:00–09:15 and 09:15–09:30 overlap the block; 09:30 onwards does not.
        assert by_start["09:00"]["blocked"] is True
        assert by_start["09:00"]["available"] == 0
        assert by_start["09:00"]["available_unreserved"] == 0
        assert by_start["09:15"]["blocked"] is True
        assert by_start["09:15"]["available"] == 0
        assert by_start["09:30"]["blocked"] is False
        assert by_start["09:30"]["available"] == 2
        assert body["blocked_slot_count"] == 2
        assert [p["block_id"] for p in body["blocked_periods"]] == [block_id]
        assert body["blocked_periods"][0]["window_label"] == "09:00–09:30"

    def test_whole_day_block_removes_all_availability(self, client):
        sid = _schedule(client)
        _block(client, sid)
        body = _slots(client, sid)
        assert body["slots"], "the grid still shows the slots it publishes"
        assert all(s["blocked"] and s["available"] == 0 for s in body["slots"])
        assert body["blocked_slot_count"] == len(body["slots"])
        assert body["blocked_periods"][0]["whole_day"] is True

    def test_block_on_another_day_does_not_affect_this_day(self, client):
        sid = _schedule(client)
        _block(client, sid, start_date=TUESDAY, end_date=TUESDAY)
        assert _slots(client, sid, MONDAY)["blocked_slot_count"] == 0
        tuesday = _slots(client, sid, TUESDAY)
        assert tuesday["blocked_slot_count"] == len(tuesday["slots"])

    def test_cancelled_block_does_not_affect_availability(self, client):
        sid = _schedule(client)
        block_id = _block(client, sid).json()["id"]
        client.delete(f"/api/v1/schedules/{sid}/blocks/{block_id}",
                      headers=headers(ADMIN))
        body = _slots(client, sid)
        assert body["blocked_slot_count"] == 0
        assert all(s["available"] == 2 for s in body["slots"])

    def test_block_covers_the_doctor_not_only_one_schedule(self, client):
        """A block means the doctor is unavailable, whichever schedule is read."""
        morning = _schedule(client)
        afternoon = _schedule(client, templates=AFTERNOON)
        _block(client, morning, start_time="14:00", end_time="14:15")
        body = _slots(client, afternoon)
        assert body["slots"][0]["start_time"] == "14:00"
        assert body["slots"][0]["blocked"] is True
        assert _slots(client, morning)["blocked_slot_count"] == 0

    def test_another_doctors_block_does_not_affect_this_doctor(self, client):
        sid = _schedule(client)
        second = _schedule(client, doctor_id=DOC2)
        _block(client, second)
        assert _slots(client, sid)["blocked_slot_count"] == 0

    def test_payload_shape_is_stable_on_an_out_of_range_day(self, client):
        """Every availability answer carries the MP-16 keys, even with no slots."""
        sid = _schedule(client)
        body = _slots(client, sid, "2025-12-31")     # before effective_from
        assert body["slots"] == []
        assert body["blocked_periods"] == []
        assert body["blocked_slot_count"] == 0

    def test_unreadable_window_degrades_without_error(self, client):
        """A stored row with an unpadded clock must not turn the read into a 500."""
        sid = _schedule(client)
        with db_session() as s:
            schedule = s.query(Schedule).filter(Schedule.id == sid).first()
            s.add(ScheduleBlock(
                organization_id=ORG, branch_id=BR, schedule_id=sid,
                doctor_id=schedule.doctor_id, start_date=date(2026, 4, 20),
                end_date=date(2026, 4, 20), start_time="9:00", end_time=None,
                reason="hand-edited row", status="active"))
            s.commit()
        body = _slots(client, sid)
        assert all(s["blocked"] for s in body["slots"]), "fail closed"
        assert body["blocked_periods"][0]["window_label"].startswith("all day")

