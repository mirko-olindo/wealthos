from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Vehicle(Base):
    """Veicolo di investimento (fondo, società, conto, ecc.)"""
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    asset_class = Column(String)          # Private Equity, Real Estate, Hedge Fund, Bond, Equity, Cash
    manager = Column(String)
    vehicle_type = Column(String)         # fund, direct, bond, listed
    currency = Column(String, default="EUR")
    vintage_year = Column(Integer)
    commitment = Column(Float)            # capitale impegnato
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    positions = relationship("Position", back_populates="vehicle")
    documents = relationship("Document", back_populates="vehicle")
    nav_statements = relationship("NavStatement", back_populates="vehicle")
    distributions = relationship("Distribution", back_populates="vehicle")
    capital_calls = relationship("CapitalCall", back_populates="vehicle")


class Document(Base):
    """Documento finanziario caricato nel repository"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String)            # pdf, xlsx, csv, image
    doc_category = Column(String)         # nav_statement, capital_call, distribution, report, other
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    doc_date = Column(Date, nullable=True)
    extraction_status = Column(String, default="pending")  # pending, processing, done, failed
    extraction_raw = Column(JSON, nullable=True)           # JSON grezzo estratto da Claude
    extraction_error = Column(Text, nullable=True)
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    extracted_at = Column(DateTime, nullable=True)

    vehicle = relationship("Vehicle", back_populates="documents")


class NavStatement(Base):
    """NAV statement periodico di un veicolo"""
    __tablename__ = "nav_statements"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    nav_date = Column(Date, nullable=False)
    nav_value = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    shares_units = Column(Float, nullable=True)
    nav_per_unit = Column(Float, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="nav_statements")
    document = relationship("Document")


class Distribution(Base):
    """Distribuzione ricevuta da un veicolo"""
    __tablename__ = "distributions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    distribution_type = Column(String)    # income, return_of_capital, capital_gain
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="distributions")
    document = relationship("Document")


class CapitalCall(Base):
    """Capital call ricevuta da un fondo"""
    __tablename__ = "capital_calls"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    call_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    call_number = Column(Integer, nullable=True)
    purpose = Column(String, nullable=True)
    paid = Column(Integer, default=0)     # 0=no, 1=yes
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="capital_calls")
    document = relationship("Document")


class Position(Base):
    """Snapshot periodico della posizione in un veicolo"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    position_date = Column(Date, nullable=False)
    invested_capital = Column(Float)
    current_value = Column(Float)
    unrealized_gain = Column(Float)
    tvpi = Column(Float)
    dpi = Column(Float)
    irr = Column(Float)
    currency = Column(String, default="EUR")
    created_at = Column(DateTime, default=datetime.utcnow)

    vehicle = relationship("Vehicle", back_populates="positions")
    document = relationship("Document")
