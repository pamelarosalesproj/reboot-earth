"""Script para popular banco de dados com usuário fictício e múltiplos CARs para teste no Frontend."""

from sqlmodel import Session, select

from app.auth import hash_password
from app.db import create_db_and_tables, engine
from app.models import Producer, ProducerCar

MOCK_EMAIL = "produtor.florestal@rebootearth.com"
MOCK_PASSWORD = "senha_segura_123"
MOCK_CNPJ = "04654691000106"

# 8 CARs fictícios e reais para testar a detecção de evidência (5 com NFs vs 3 omitidos)
MOCK_CARS = [
    "PE-2607505-F2671DDFDA3D47CC917EB3E0DFEEB8B0",
    "PE-2600500-99E6E359827B460BAF346B15E27F602D",
    "PE-2606507-AC1BA1E9D7A24326A1FF97C58D37E146",
    "PA-1500107-11112222333344445555666677778888",
    "PA-1500206-AAAABBBBCCCCDDDDEEEEFFFF00001111",
    "MT-5100102-1234567890ABCDEF1234567890ABCDEF",  # CAR Omitido nas NFs
    "MT-5100201-FEDCBA0987654321FEDCBA0987654321",  # CAR Omitido nas NFs
    "RO-1100015-99887766554433221100AABBCCDDEEFF",  # CAR Omitido nas NFs
]


def seed_mock_producer():
    create_db_and_tables()

    with Session(engine) as db:
        existing = db.exec(select(Producer).where(Producer.email == MOCK_EMAIL)).first()
        if existing:
            print(f"Produtor fictício já existe: {MOCK_EMAIL} (ID: {existing.id})")
            producer = existing
        else:
            producer = Producer(
                email=MOCK_EMAIL,
                password_hash=hash_password(MOCK_PASSWORD),
                cnpj=MOCK_CNPJ,
            )
            db.add(producer)
            db.commit()
            db.refresh(producer)
            print(f"Produtor fictício criado com sucesso: {MOCK_EMAIL}")

        # Adiciona os 8 CARs se ainda não existirem
        existing_cars = {
            c.car_code
            for c in db.exec(
                select(ProducerCar).where(ProducerCar.producer_id == producer.id)
            ).all()
        }

        added = 0
        for code in MOCK_CARS:
            if code not in existing_cars:
                car = ProducerCar(producer_id=producer.id, car_code=code)
                db.add(car)
                added += 1

        db.commit()
        print(f"Total de {len(MOCK_CARS)} CARs vinculados ao CNPJ {MOCK_CNPJ} ({added} novos adicionados).")


if __name__ == "__main__":
    seed_mock_producer()
