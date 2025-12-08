"""
Seed script to create initial data for development
Run with: python -m scripts.seed_data
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.school import School, SchoolSettings
from app.models.user import User, UserRole
from app.services.user_service import UserService
from datetime import time
from sqlalchemy import text

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Check if admin user already exists
        result = await db.execute(text("SELECT id FROM users WHERE email = 'admin@rozvrhovac.dev'"))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("Users already exist. Skipping seed.")
            print("\nExisting login credentials:")
            print("  Admin:  admin@rozvrhovac.dev / admin123")
            print("  Teacher: teacher@rozvrhovac.dev / teacher123")
            print("  Scholar: scholar@rozvrhovac.dev / scholar123")
            return
        
        # Get or create school
        from app.repositories.school_repository import SchoolRepository, SchoolSettingsRepository
        school_repo = SchoolRepository(db)
        settings_repo = SchoolSettingsRepository(db)
        
        result = await db.execute(text("SELECT id FROM schools WHERE code = 'DEMO001'"))
        school_id_result = result.scalar_one_or_none()
        
        if school_id_result:
            school_id = school_id_result
            school = await school_repo.get_by_id(school_id)
            print(f"Using existing school: {school.name} (ID: {school.id})")
        else:
            # Create school
            school = School(
                name="Demo School",
                code="DEMO001"
            )
            school = await school_repo.create(school)
            print(f"Created school: {school.name} (ID: {school.id})")
            
            # Create school settings
            result = await db.execute(text("SELECT id FROM school_settings WHERE school_id = :school_id"), {"school_id": school.id})
            if not result.scalar_one_or_none():
                settings = SchoolSettings(
                    school_id=school.id,
                    start_time=time(8, 0),  # 08:00
                    end_time=time(16, 0),  # 16:00
                    class_hour_length_minutes=45,
                    break_duration_minutes=10,
                    possible_lunch_hours=[3, 4, 5],  # Lessons 3, 4, or 5
                    lunch_duration_minutes=30
                )
                settings = await settings_repo.create(settings)
                print(f"Created school settings for {school.name}")
        
        # Create admin user
        user_service = UserService(db)
        admin_user = await user_service.create_user(
            email="admin@rozvrhovac.dev",
            password="admin123",
            school_id=school.id,
            role=UserRole.ADMIN
        )
        print(f"Created admin user: {admin_user.email}")
        print(f"  Password: admin123")
        
        # Create a teacher user
        teacher_user = await user_service.create_user(
            email="teacher@rozvrhovac.dev",
            password="teacher123",
            school_id=school.id,
            role=UserRole.TEACHER
        )
        print(f"Created teacher user: {teacher_user.email}")
        print(f"  Password: teacher123")
        
        # Create a scholar user
        scholar_user = await user_service.create_user(
            email="scholar@rozvrhovac.dev",
            password="scholar123",
            school_id=school.id,
            role=UserRole.SCHOLAR
        )
        print(f"Created scholar user: {scholar_user.email}")
        print(f"  Password: scholar123")
        
        print("\n✅ Seed data created successfully!")
        print("\nLogin credentials:")
        print("  Admin:  admin@rozvrhovac.dev / admin123")
        print("  Teacher: teacher@rozvrhovac.dev / teacher123")
        print("  Scholar: scholar@rozvrhovac.dev / scholar123")

if __name__ == "__main__":
    asyncio.run(seed_data())
