import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "backend"))

from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as c:
        r = await c.execute(text("SELECT id, email, full_name, is_active FROM users;"))
        rows = r.fetchall()
        print("Users in DB:")
        for row in rows:
            print(f"  id: {row[0]}, email: {row[1]}, name: {row[2]}, active: {row[3]}")

if __name__ == "__main__":
    asyncio.run(check())
