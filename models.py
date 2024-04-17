from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Service(Base):
    __tablename__ = 'services'
    ServiceID = Column(Integer, primary_key=True, autoincrement=True)
    ServiceName = Column(String(255))
    Description = Column(String(255))
    BasePrice = Column(Integer)
    PremiumPriceSaturday = Column(Integer)
    PremiumPriceSunday = Column(Integer)


class Customer(Base):
    __tablename__ = 'customers'
    CustomerID = Column(Integer, primary_key=True, autoincrement=True)
    FirstName = Column(String(50))
    LastName = Column(String(50))
    Email = Column(String(100))
    Phone = Column(String(15))
    pets = relationship("Pet", back_populates="owner")
    bookings = relationship("Booking", back_populates="customer")


class Pet(Base):
    __tablename__ = 'pets'
    PetID = Column(Integer, primary_key=True, autoincrement=True)
    CustomerID = Column(Integer, ForeignKey('customers.CustomerID'))
    PetName = Column(String(50))
    Breed = Column(String(50))
    Age = Column(Integer)
    Gender = Column(String(10))
    owner = relationship("Customer", back_populates="pets")


class Booking(Base):
    __tablename__ = 'bookings'
    BookingID = Column(Integer, primary_key=True, autoincrement=True)
    CustomerID = Column(Integer, ForeignKey('customers.CustomerID'))
    PetID = Column(Integer, ForeignKey('pets.PetID'))
    ServiceID = Column(Integer, ForeignKey('services.ServiceID'))
    BookingDate = Column(String(10))  # Assuming format YYYY-MM-DD
    IsPremium = Column(Boolean)
    TotalPrice = Column(Integer)
    customer = relationship("Customer", back_populates="bookings")
