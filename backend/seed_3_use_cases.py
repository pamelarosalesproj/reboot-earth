"""Script para popular banco de dados com 3 casos de uso:
1. Produtor OK / Excelente (Gold / Apto): 100% de conformidade, todos os CARs evidenciados, sem estouro, sem embargos.
2. Produtor Intermediário (Silver / Bom mas pode melhorar): Volume ok, mas alguns CARs omitidos nas NFs.
3. Produtor Crítico / Ruim (Bronze / Não Apto): CAR embargado, estouro de cota volumétrica e forte concentração ('CAR coringa').
"""

from sqlmodel import Session, select

from app.auth import hash_password
from app.db import create_db_and_tables, engine
from app.models import Producer, ProducerCar

MOCK_PRODUCERS = [
    {
        # Caso 1: OK / Excelente
        "email": "produtor.excelente@rebootearth.com",
        "password": "senha_segura_123",
        "cnpj": "04654691000106",  # 04.654.691/0001-06 (válido)
        "cars": [
            "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            "PE-2600500-99E6E359827B460BAF346B15E27F602D",
        ],
    },
    {
        # Caso 2: Bom, mas pode melhorar (Omissão de CARs)
        "email": "produtor.atencao@rebootearth.com",
        "password": "senha_segura_123",
        "cnpj": "11222333000181",  # 11.222.333/0001-81 (válido)
        "cars": [
            "PE-2606507-AC1BA1E9D7A24326A1FF97C58D37E146",
            "PA-1500107-11112222333344445555666677778888",
            "PA-1500206-AAAABBBBCCCCDDDDEEEEFFFF00001111",
            "MT-5100102-1234567890ABCDEF1234567890ABCDEF",
        ],
    },
    {
        # Caso 3: Ruim / Crítico (Estouro de cota + Embargo)
        "email": "produtor.critico@rebootearth.com",
        "password": "senha_segura_123",
        "cnpj": "33592510000154",  # 33.592.510/0001-54 (Vale S.A. - válido)
        "cars": [
            "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
            "MT-5100201-FEDCBA0987654321FEDCBA0987654321",
            "RO-1100015-99887766554433221100AABBCCDDEEFF",
            "AM-1300029-AABBCCDDEEFF00112233445566778899",
            "AC-1200013-11223344556677889900AABBCCDDEEFF",
        ],
    },
]


def seed_cases():
    create_db_and_tables()

    with Session(engine) as db:
        for case in MOCK_PRODUCERS:
            existing = db.exec(select(Producer).where(Producer.email == case["email"])).first()
            if existing:
                producer = existing
                print(f"[OK] Produtor já cadastrado: {case['email']} ({case['cnpj']})")
            else:
                producer = Producer(
                    email=case["email"],
                    password_hash=hash_password(case["password"]),
                    cnpj=case["cnpj"],
                )
                db.add(producer)
                db.commit()
                db.refresh(producer)
                print(f"[CRIADO] Novo produtor: {case['email']} ({case['cnpj']})")

            existing_cars = {
                c.car_code
                for c in db.exec(
                    select(ProducerCar).where(ProducerCar.producer_id == producer.id)
                ).all()
            }

            for code in case["cars"]:
                if code not in existing_cars:
                    db.add(ProducerCar(producer_id=producer.id, car_code=code))

            db.commit()

        print("\nTodos os 3 casos de uso foram provisionados com sucesso no banco de dados!")


if __name__ == "__main__":
    seed_cases()
