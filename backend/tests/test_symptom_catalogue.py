"""Shipped symptom catalogue — data-quality contract.

``backend/seed/symptom_catalogue.py`` is data, and data can rot: a duplicate
code, a missing Bangla name, a synonym that quietly names a disease instead of a
symptom, a speciality hint that is not a speciality.  These assertions pin the
properties the booking UI and the ranking logic rely on, so editing the
catalogue cannot silently break bilingual search or the symptom/diagnosis line
this feature is required to keep.

No database is touched here: this is a pure data check, and it runs in the same
suite as the service tests.
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from seed.symptom_catalogue import (CATALOGUE_SOURCE, DEMO_SYMPTOMS,  # noqa: E402
                                    KNOWN_SPECIALTY_HINTS, REVIEW_STATUS,
                                    demo_symptom_rows)

BENGALI = re.compile(r"[\u0980-\u09FF]")

CATEGORIES = {
    "general", "neurological", "eye", "ent", "respiratory",
    "cardiovascular", "gastrointestinal", "urinary", "musculoskeletal",
    "skin", "mental_health", "womens_health", "pediatric",
}

#: Conditions a clinician diagnoses.  A catalogue entry must not be one of them:
#: the receptionist records what the patient reports, never a diagnosis.
DIAGNOSES = {
    "diabetes", "diabetic", "hypertension", "anaemia", "anemia", "typhoid",
    "asthma", "tuberculosis", "cancer", "stroke", "arthritis", "migraine",
    "pneumonia", "jaundice",
}


def codes():
    return [item["code"] for item in DEMO_SYMPTOMS]


def test_catalogue_is_a_curated_set_not_a_terminology_database():
    assert 40 <= len(DEMO_SYMPTOMS) <= 120, (
        "the initial catalogue is meant to be a careful selection, not an import")


def test_codes_are_unique_and_url_safe():
    assert len(codes()) == len(set(codes())), "duplicate symptom code"
    for code in codes():
        assert re.fullmatch(r"[a-z0-9_]+", code), f"unsafe code: {code}"


def test_every_entry_is_bilingual_in_both_scripts():
    for item in DEMO_SYMPTOMS:
        assert item["name_en"].strip(), f"{item['code']}: missing English name"
        assert BENGALI.search(item["name_bn"]), (
            f"{item['code']}: Bangla name is missing or not in Bengali script")


def test_every_entry_is_searchable_in_both_languages():
    for item in DEMO_SYMPTOMS:
        assert item["synonyms_en"], f"{item['code']}: no English synonym"
        assert item["synonyms_bn"], f"{item['code']}: no Bangla synonym"
        for synonym in item["synonyms_en"] + item["synonyms_bn"]:
            assert synonym.strip(), f"{item['code']}: empty synonym"
        assert len(set(item["synonyms_en"])) == len(item["synonyms_en"]), (
            f"{item['code']}: duplicate English synonym")
        assert len(set(item["synonyms_bn"])) == len(item["synonyms_bn"]), (
            f"{item['code']}: duplicate Bangla synonym")


def test_entries_name_symptoms_not_diagnoses():
    for item in DEMO_SYMPTOMS:
        haystack = " ".join([item["name_en"]] + list(item["synonyms_en"])).lower()
        for diagnosis in DIAGNOSES:
            assert diagnosis not in haystack, (
                f"{item['code']}: '{diagnosis}' is a diagnosis, not a reported symptom")


def test_categories_and_speciality_hints_are_known_values():
    for item in DEMO_SYMPTOMS:
        assert item["category"] in CATEGORIES, (
            f"{item['code']}: unknown category {item['category']}")
        for hint in item["specialty_hints"]:
            assert hint in KNOWN_SPECIALTY_HINTS, (
                f"{item['code']}: unknown speciality hint {hint}")


def test_sort_order_is_unique_so_ranking_is_deterministic():
    orders = [item["sort_order"] for item in DEMO_SYMPTOMS]
    assert len(orders) == len(set(orders)), "duplicate sort_order breaks tie-breaks"


def test_provenance_and_review_state_are_recorded():
    assert REVIEW_STATUS == "curated"
    assert "carehospitals.com" in CATALOGUE_SOURCE
    assert "Not clinically validated" in CATALOGUE_SOURCE
    rows = demo_symptom_rows("demo-org-001")
    assert len(rows) == len(DEMO_SYMPTOMS)
    for row in rows:
        assert row["organization_id"] == "demo-org-001"
        assert row["review_status"] == REVIEW_STATUS
        assert row["source"] == CATALOGUE_SOURCE
        assert row["status"] == "active"
        assert row["id"].startswith("demo-sym-")


def test_onset_vocabulary_is_closed_unique_and_bilingual():
    from appointment.symptoms import ONSET_CODES, ONSET_OPTIONS

    assert ONSET_CODES == ("TODAY", "YESTERDAY", "FEW_DAYS", "FEW_WEEKS",
                           "OVER_MONTH", "LONG_STANDING", "UNKNOWN")
    assert len(ONSET_OPTIONS) == len(ONSET_CODES)
    for code, name_en, name_bn in ONSET_OPTIONS:
        assert code in ONSET_CODES
        assert name_en.strip()
        assert BENGALI.search(name_bn), f"{code}: Bangla onset label missing"
