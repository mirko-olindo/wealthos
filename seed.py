"""
Script per popolare il database con dati di esempio.
Esegui con: python seed.py
"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from datetime import date
from backend.models.db import Base, Vehicle, NavStatement, Distribution, CapitalCall, Position

DATABASE_URL = "sqlite+aiosqlite:///./data/wealthos.db"

VEHICLES = [
    dict(name="KKR European Fund IV", asset_class="Private Equity", manager="KKR", vehicle_type="fund", currency="EUR", vintage_year=2018, commitment=5_000_000),
    dict(name="Ardian Real Estate III", asset_class="Real Estate", manager="Ardian", vehicle_type="fund", currency="EUR", vintage_year=2019, commitment=3_000_000),
    dict(name="Algebris Credit Opportunities", asset_class="Hedge Fund", manager="Algebris", vehicle_type="fund", currency="EUR", vintage_year=2020, commitment=2_000_000),
    dict(name="BNP RE Europe Fund", asset_class="Real Estate", manager="BNP Paribas AM", vehicle_type="fund", currency="EUR", vintage_year=2017, commitment=4_000_000),
    dict(name="iShares EM Bond ETF", asset_class="Bond", manager="BlackRock", vehicle_type="listed", currency="USD", vintage_year=2021, commitment=1_500_000),
]

NAV_DATA = {
    "KKR European Fund IV": [
        (date(2021,6,30), 4_200_000), (date(2021,12,31), 4_800_000),
        (date(2022,6,30), 5_500_000), (date(2022,12,31), 6_100_000),
        (date(2023,6,30), 7_200_000), (date(2023,12,31), 8_100_000),
        (date(2024,6,30), 9_000_000), (date(2024,9,30), 9_400_000),
    ],
    "Ardian Real Estate III": [
        (date(2021,6,30), 2_800_000), (date(2021,12,31), 3_100_000),
        (date(2022,12,31), 3_800_000), (date(2023,12,31), 5_200_000),
        (date(2024,9,30), 6_100_000),
    ],
    "Algebris Credit Opportunities": [
        (date(2021,12,31), 1_900_000), (date(2022,12,31), 2_100_000),
        (date(2023,12,31), 4_200_000), (date(2024,9,30), 5_300_000),
    ],
    "BNP RE Europe Fund": [
        (date(2020,12,31), 3_600_000), (date(2021,12,31), 3_800_000),
        (date(2022,12,31), 4_200_000), (date(2023,12,31), 4_600_000),
        (date(2024,9,30), 4_800_000),
    ],
    "iShares EM Bond ETF": [
        (date(2022,6,30), 1_300_000), (date(2022,12,31), 1_200_000),
        (date(2023,12,31), 1_400_000), (date(2024,9,30), 1_450_000),
    ],
}

DISTRIBUTIONS = {
    "KKR European Fund IV": [
        (date(2022,9,15), 300_000, "return_of_capital"),
        (date(2023,3,20), 500_000, "capital_gain"),
        (date(2024,1,10), 800_000, "capital_gain"),
    ],
    "Ardian Real Estate III": [
        (date(2022,12,15), 200_000, "income"),
        (date(2023,12,15), 350_000, "income"),
        (date(2024,6,15), 450_000, "income"),
    ],
    "Algebris Credit Opportunities": [
        (date(2023,6,30), 150_000, "income"),
        (date(2024,6,30), 250_000, "income"),
    ],
    "BNP RE Europe Fund": [
        (date(2021,12,31), 180_000, "income"),
        (date(2022,12,31), 220_000, "income"),
        (date(2023,12,31), 260_000, "income"),
    ],
}

CAPITAL_CALLS = {
    "KKR European Fund IV": [
        (date(2018,9,1), date(2018,9,20), 1_500_000, 1, "Initial investment"),
        (date(2019,3,1), date(2019,3,20), 1_500_000, 2, "Follow-on investments"),
        (date(2020,1,15), date(2020,2,1), 2_000_000, 3, "Portfolio companies"),
    ],
    "Ardian Real Estate III": [
        (date(2019,6,1), date(2019,6,20), 1_500_000, 1, "Acquisizioni immobiliari"),
        (date(2020,9,1), date(2020,9,15), 1_500_000, 2, "Asset repositioning"),
    ],
    "BNP RE Europe Fund": [
        (date(2017,10,1), date(2017,10,20), 2_000_000, 1, "First close investments"),
        (date(2018,6,1), date(2018,6,20), 2_000_000, 2, "Portfolio expansion"),
    ],
}

POSITIONS = {
    "KKR European Fund IV": (5_000_000, 9_400_000, 1.88, 0.32, 0.194),
    "Ardian Real Estate III": (3_000_000, 6_100_000, 2.03, 0.33, 0.147),
    "Algebris Credit Opportunities": (2_000_000, 5_300_000, 2.65, 0.20, 0.312),
    "BNP RE Europe Fund": (4_000_000, 4_800_000, 1.20, 0.17, 0.061),
    "iShares EM Bond ETF": (1_500_000, 1_450_000, 0.97, 0.0, -0.023),
}


async def seed():
    Path("./data").mkdir(exist_ok=True)
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        # Inserisci veicoli
        vehicle_ids = {}
        for vd in VEHICLES:
            v = Vehicle(**vd)
            db.add(v)
            await db.flush()
            vehicle_ids[vd["name"]] = v.id
        await db.commit()

        # NAV
        for vname, nav_list in NAV_DATA.items():
            vid = vehicle_ids.get(vname)
            if not vid: continue
            for nav_date, nav_val in nav_list:
                db.add(NavStatement(vehicle_id=vid, nav_date=nav_date, nav_value=nav_val, currency="EUR"))
        await db.commit()

        # Distributions
        for vname, dist_list in DISTRIBUTIONS.items():
            vid = vehicle_ids.get(vname)
            if not vid: continue
            for pdate, amount, dtype in dist_list:
                db.add(Distribution(vehicle_id=vid, payment_date=pdate, amount=amount, distribution_type=dtype, currency="EUR"))
        await db.commit()

        # Capital Calls
        for vname, cc_list in CAPITAL_CALLS.items():
            vid = vehicle_ids.get(vname)
            if not vid: continue
            for cdate, ddate, amount, num, purpose in cc_list:
                db.add(CapitalCall(vehicle_id=vid, call_date=cdate, due_date=ddate, amount=amount, call_number=num, purpose=purpose, paid=1, currency="EUR"))
        await db.commit()

        # Positions
        for vname, (invested, current, tvpi, dpi, irr) in POSITIONS.items():
            vid = vehicle_ids.get(vname)
            if not vid: continue
            db.add(Position(vehicle_id=vid, position_date=date(2024,9,30), invested_capital=invested, current_value=current, tvpi=tvpi, dpi=dpi, irr=irr, currency="EUR"))
        await db.commit()

    await engine.dispose()
    print("✅ Dati di esempio inseriti con successo!")
    print(f"   {len(VEHICLES)} veicoli, NAV storici, distribuzioni, capital calls, posizioni")

if __name__ == "__main__":
    asyncio.run(seed())
