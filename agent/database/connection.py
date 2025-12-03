import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager
from .models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1) if DATABASE_URL else ""

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True) if DATABASE_URL else None
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, pool_pre_ping=True) if ASYNC_DATABASE_URL else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
) if async_engine else None

def init_db():
    if engine:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    else:
        print("No database connection available")

async def init_db_async():
    if async_engine:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully (async)")
    else:
        print("No async database connection available")

@contextmanager
def get_db():
    if not SessionLocal:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

@asynccontextmanager
async def get_async_session():
    if not AsyncSessionLocal:
        yield None
        return
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
