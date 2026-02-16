from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, Float, Text
from flask_login import UserMixin

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user")  # 'admin' or 'user'


class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    models = relationship("PhoneModel", back_populates="brand")


class PhoneModel(Base):
    __tablename__ = "phone_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    ram: Mapped[str] = mapped_column(String(32))
    storage: Mapped[str] = mapped_column(String(32))
    camera: Mapped[str] = mapped_column(String(64))
    battery: Mapped[str] = mapped_column(String(64))
    processor: Mapped[str] = mapped_column(String(128))
    os: Mapped[str] = mapped_column(String(64))
    display_size: Mapped[str] = mapped_column(String(32))
    launch_year: Mapped[int] = mapped_column(Integer)

    brand = relationship("Brand", back_populates="models")
    sales = relationship("Sale", back_populates="phone_model")


class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("phone_models.id"), nullable=False)
    units_sold: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    average_price: Mapped[float] = mapped_column(Float, default=0.0)
    region: Mapped[str] = mapped_column(String(100))
    channel: Mapped[str] = mapped_column(String(50))  # Online/Retail/Wholesale
    year: Mapped[int] = mapped_column(Integer)

    phone_model = relationship("PhoneModel", back_populates="sales")


