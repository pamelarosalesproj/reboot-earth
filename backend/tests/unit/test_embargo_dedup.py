from app.services.car_service import alert_embargoes_count, dedupe_embargoes

CAR = "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0"


def emb(code, source="IBAMA", process="02001.000123/2020-11", area=10.0, desc="", reg="2020-05-01"):
    return {"code": code, "source": source, "processCode": process, "areaHa": area,
            "description": desc, "sourceRegisteredAt": reg, "sourceExpiredAt": None}


def test_same_process_is_one_embargo_with_descriptions():
    rps = [{"carCode": CAR, "embargoedAreas": [emb("1", desc="Desmatamento"), emb("2", desc="Queimada"),
                                                emb("3", desc="Desmatamento")]}]
    out = dedupe_embargoes(rps, CAR)
    assert len(out) == 1
    assert out[0].descriptions == ["Desmatamento", "Queimada"]
    assert out[0].area_ha == 10.0


def test_different_process_counts_twice_and_sorted():
    rps = [{"carCode": CAR, "embargoedAreas": [emb("1", process="B", reg="2021-01-01"),
                                                emb("2", process="A", reg="2019-01-01")]}]
    out = dedupe_embargoes(rps, CAR)
    assert [e.process_code for e in out] == ["A", "B"]


def test_other_car_ignored():
    rps = [{"carCode": "PE-0000000-00000000000000000000000000000000", "embargoedAreas": [emb("1")]}]
    assert dedupe_embargoes(rps, CAR) == []


def test_alert_count_from_ids_dedup():
    assert alert_embargoes_count({"crossedEmbargoesIds": [10, 10, 11]}) == 2


def test_alert_count_from_list_by_process():
    lst = [{"source": "IBAMA", "process_code": "X"}, {"source": "IBAMA", "process_code": "X"},
           {"source": "ICMBio", "process_code": "Y"}]
    assert alert_embargoes_count({"crossedEmbargoesList": lst, "crossedEmbargoesIds": [1, 2, 3]}) == 2


def test_alert_count_zero_and_unknown():
    assert alert_embargoes_count({"crossedEmbargoesIds": None, "crossedEmbargoesTotal": 0}) == 0
    assert alert_embargoes_count({}) is None
