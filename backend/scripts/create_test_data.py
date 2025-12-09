"""
Script to create comprehensive test data for development
Run with: python -m scripts.create_test_data
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.school import School, SchoolSettings
from app.models.grade_level import GradeLevel
from app.models.class_group import ClassGroup
from app.models.subject import Subject, ClassSubjectAllocation
from app.models.teacher import Teacher, TeacherSubjectCapability
from app.models.classroom import Classroom
from datetime import time
from sqlalchemy import text, select

async def create_test_data():
    async with AsyncSessionLocal() as db:
        # Get or create school
        result = await db.execute(text("SELECT id FROM schools WHERE code = 'DEMO001'"))
        school_id_result = result.scalar_one_or_none()
        
        if not school_id_result:
            print("❌ School not found. Please run seed_data.py first to create the school.")
            return
        
        school_id = school_id_result
        
        # Check if test data already exists
        result = await db.execute(text("SELECT COUNT(*) FROM subjects WHERE school_id = :school_id"), {"school_id": school_id})
        subject_count = result.scalar_one()
        
        if subject_count > 0:
            print("⚠️  Test data already exists.")
            print("   Deleting existing test data...")
            
            # Delete in reverse order of dependencies
            # First delete timetable entries and timetables
            await db.execute(text("DELETE FROM timetable_entries WHERE timetable_id IN (SELECT id FROM timetables WHERE school_id = :school_id)"), {"school_id": school_id})
            await db.execute(text("DELETE FROM timetables WHERE school_id = :school_id"), {"school_id": school_id})
            # Delete allocations and capabilities
            await db.execute(text("DELETE FROM class_subject_allocations WHERE class_group_id IN (SELECT id FROM class_groups WHERE school_id = :school_id)"), {"school_id": school_id})
            await db.execute(text("DELETE FROM teacher_subject_capabilities WHERE teacher_id IN (SELECT id FROM teachers WHERE school_id = :school_id)"), {"school_id": school_id})
            await db.execute(text("DELETE FROM class_subject_allocations WHERE subject_id IN (SELECT id FROM subjects WHERE school_id = :school_id)"), {"school_id": school_id})
            # Delete main entities
            await db.execute(text("DELETE FROM subjects WHERE school_id = :school_id"), {"school_id": school_id})
            await db.execute(text("DELETE FROM teachers WHERE school_id = :school_id"), {"school_id": school_id})
            await db.execute(text("DELETE FROM classrooms WHERE school_id = :school_id"), {"school_id": school_id})
            await db.execute(text("DELETE FROM class_groups WHERE school_id = :school_id"), {"school_id": school_id})
            await db.execute(text("DELETE FROM grade_levels WHERE school_id = :school_id"), {"school_id": school_id})
            await db.commit()
            print("   ✓ Deleted existing test data")
        
        print(f"Creating test data for school ID: {school_id}")
        print("=" * 60)
        
        # Create Grade Levels
        print("\n📚 Creating Grade Levels...")
        grade_levels_data = [
            {"name": "1st Grade", "level": 1},
            {"name": "2nd Grade", "level": 2},
            {"name": "3rd Grade", "level": 3},
            {"name": "4th Grade", "level": 4},
        ]
        grade_levels = {}
        for gl_data in grade_levels_data:
            grade_level = GradeLevel(
                school_id=school_id,
                name=gl_data["name"],
                level=gl_data["level"]
            )
            db.add(grade_level)
            await db.flush()
            grade_levels[gl_data["level"]] = grade_level
            print(f"  ✓ Created {gl_data['name']} (ID: {grade_level.id})")
        
        await db.commit()
        
        # Create Class Groups
        print("\n👥 Creating Class Groups...")
        class_groups_data = [
            {"name": "1.A", "grade_level": 1},
            {"name": "1.B", "grade_level": 1},
            {"name": "1.C", "grade_level": 1},
            {"name": "2.A", "grade_level": 2},
            {"name": "2.B", "grade_level": 2},
            {"name": "2.C", "grade_level": 2},
            {"name": "3.A", "grade_level": 3},
            {"name": "3.B", "grade_level": 3},
            {"name": "4.A", "grade_level": 4},
            {"name": "4.B", "grade_level": 4},
        ]
        class_groups = {}
        for cg_data in class_groups_data:
            class_group = ClassGroup(
                school_id=school_id,
                grade_level_id=grade_levels[cg_data["grade_level"]].id,
                name=cg_data["name"]
            )
            db.add(class_group)
            await db.flush()
            class_groups[cg_data["name"]] = class_group
            print(f"  ✓ Created {cg_data['name']} (ID: {class_group.id})")
        
        await db.commit()
        
        # Create Subjects
        print("\n📖 Creating Subjects...")
        subjects_data = [
            {"name": "Mathematics", "is_lab": False, "requires_specialized": False},
            {"name": "Physics", "is_lab": True, "requires_specialized": True},
            {"name": "Chemistry", "is_lab": True, "requires_specialized": True},
            {"name": "Biology", "is_lab": True, "requires_specialized": True},
            {"name": "Computer Science", "is_lab": True, "requires_specialized": True},
            {"name": "English", "is_lab": False, "requires_specialized": False},
            {"name": "History", "is_lab": False, "requires_specialized": False},
            {"name": "Geography", "is_lab": False, "requires_specialized": False},
            {"name": "Physical Education", "is_lab": False, "requires_specialized": False},
            {"name": "Art", "is_lab": False, "requires_specialized": False},
        ]
        subjects = {}
        for subj_data in subjects_data:
            subject = Subject(
                school_id=school_id,
                name=subj_data["name"],
                allow_consecutive_hours=True,
                max_consecutive_hours=2 if subj_data["is_lab"] else None,
                allow_multiple_in_one_day=True,
                required_block_length=2 if subj_data["is_lab"] else None,
                is_laboratory=subj_data["is_lab"],
                requires_specialized_classroom=subj_data["requires_specialized"]
            )
            db.add(subject)
            await db.flush()
            subjects[subj_data["name"]] = subject
            print(f"  ✓ Created {subj_data['name']} (ID: {subject.id})")
        
        await db.commit()
        
        # Create Teachers (multiple teachers per subject for primary/substitute support)
        print("\n👨‍🏫 Creating Teachers...")
        teachers_data = [
            # Mathematics teachers (3 teachers)
            {"name": "John Smith", "hours": 20, "subjects": ["Mathematics", "Physics"]},
            {"name": "Robert Miller", "hours": 22, "subjects": ["Mathematics"]},
            {"name": "Sarah Johnson", "hours": 18, "subjects": ["Mathematics", "Physics"]},
            # Physics teachers (2 teachers)
            {"name": "Michael Chen", "hours": 20, "subjects": ["Physics", "Mathematics"]},
            # Chemistry teachers (2 teachers)
            {"name": "Jane Doe", "hours": 18, "subjects": ["Chemistry", "Biology"]},
            {"name": "Emily Watson", "hours": 20, "subjects": ["Chemistry"]},
            # Biology teachers (2 teachers)
            {"name": "David Lee", "hours": 18, "subjects": ["Biology", "Chemistry"]},
            # Computer Science teachers (2 teachers)
            {"name": "Bob Johnson", "hours": 22, "subjects": ["Computer Science", "Mathematics"]},
            {"name": "Alex Turner", "hours": 20, "subjects": ["Computer Science"]},
            # English teachers (3 teachers)
            {"name": "Alice Williams", "hours": 20, "subjects": ["English", "History"]},
            {"name": "Emma Thompson", "hours": 18, "subjects": ["English"]},
            {"name": "James Wilson", "hours": 20, "subjects": ["English", "History"]},
            # History teachers (2 teachers)
            {"name": "Charlie Brown", "hours": 16, "subjects": ["Geography", "History"]},
            {"name": "Olivia Martinez", "hours": 18, "subjects": ["History", "Geography"]},
            # Geography teachers (2 teachers)
            {"name": "Thomas Anderson", "hours": 16, "subjects": ["Geography"]},
            # Physical Education teachers (2 teachers)
            {"name": "Diana Prince", "hours": 18, "subjects": ["Physical Education"]},
            {"name": "Mark Taylor", "hours": 20, "subjects": ["Physical Education"]},
            # Art teachers (2 teachers)
            {"name": "Edward Norton", "hours": 20, "subjects": ["Art", "English"]},
            {"name": "Sophie Green", "hours": 18, "subjects": ["Art"]},
        ]
        teachers = {}
        for teacher_data in teachers_data:
            teacher = Teacher(
                school_id=school_id,
                full_name=teacher_data["name"],
                max_weekly_hours=teacher_data["hours"],
                availability=None
            )
            db.add(teacher)
            await db.flush()
            teachers[teacher_data["name"]] = teacher
            print(f"  ✓ Created {teacher_data['name']} (ID: {teacher.id})")
        
        await db.commit()
        
        # Create Teacher Capabilities (general capabilities for all grade levels)
        print("\n🎯 Creating Teacher Capabilities...")
        for teacher_name, teacher in teachers.items():
            teacher_data = next(t for t in teachers_data if t["name"] == teacher_name)
            for subject_name in teacher_data["subjects"]:
                subject = subjects[subject_name]
                capability = TeacherSubjectCapability(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    grade_level_id=None,
                    class_group_id=None,
                    is_primary=0  # Will be set as primary for specific classes below
                )
                db.add(capability)
            print(f"  ✓ Added general capabilities for {teacher_name}")
        
        await db.commit()
        
        # Assign primary teachers to specific class-subject combinations
        print("\n⭐ Assigning Primary Teachers to Classes...")
        primary_assignments = [
            # 1st Grade - 1.A
            {"class": "1.A", "subject": "Mathematics", "teacher": "John Smith"},
            {"class": "1.A", "subject": "English", "teacher": "Alice Williams"},
            {"class": "1.A", "subject": "History", "teacher": "Charlie Brown"},
            {"class": "1.A", "subject": "Geography", "teacher": "Charlie Brown"},
            {"class": "1.A", "subject": "Physical Education", "teacher": "Diana Prince"},
            {"class": "1.A", "subject": "Art", "teacher": "Edward Norton"},
            # 1st Grade - 1.B
            {"class": "1.B", "subject": "Mathematics", "teacher": "Robert Miller"},
            {"class": "1.B", "subject": "English", "teacher": "Emma Thompson"},
            {"class": "1.B", "subject": "History", "teacher": "Olivia Martinez"},
            {"class": "1.B", "subject": "Geography", "teacher": "Thomas Anderson"},
            {"class": "1.B", "subject": "Physical Education", "teacher": "Mark Taylor"},
            {"class": "1.B", "subject": "Art", "teacher": "Sophie Green"},
            # 1st Grade - 1.C
            {"class": "1.C", "subject": "Mathematics", "teacher": "Sarah Johnson"},
            {"class": "1.C", "subject": "English", "teacher": "James Wilson"},
            {"class": "1.C", "subject": "History", "teacher": "Olivia Martinez"},
            {"class": "1.C", "subject": "Geography", "teacher": "Thomas Anderson"},
            {"class": "1.C", "subject": "Physical Education", "teacher": "Diana Prince"},
            {"class": "1.C", "subject": "Art", "teacher": "Edward Norton"},
            # 2nd Grade - 2.A
            {"class": "2.A", "subject": "Mathematics", "teacher": "John Smith"},
            {"class": "2.A", "subject": "Physics", "teacher": "John Smith"},
            {"class": "2.A", "subject": "Chemistry", "teacher": "Jane Doe"},
            {"class": "2.A", "subject": "English", "teacher": "Alice Williams"},
            {"class": "2.A", "subject": "History", "teacher": "Charlie Brown"},
            {"class": "2.A", "subject": "Geography", "teacher": "Charlie Brown"},
            {"class": "2.A", "subject": "Physical Education", "teacher": "Diana Prince"},
            # 2nd Grade - 2.B
            {"class": "2.B", "subject": "Mathematics", "teacher": "Robert Miller"},
            {"class": "2.B", "subject": "Physics", "teacher": "Michael Chen"},
            {"class": "2.B", "subject": "Chemistry", "teacher": "Emily Watson"},
            {"class": "2.B", "subject": "English", "teacher": "Emma Thompson"},
            {"class": "2.B", "subject": "History", "teacher": "Olivia Martinez"},
            {"class": "2.B", "subject": "Geography", "teacher": "Thomas Anderson"},
            {"class": "2.B", "subject": "Physical Education", "teacher": "Mark Taylor"},
            # 2nd Grade - 2.C
            {"class": "2.C", "subject": "Mathematics", "teacher": "Sarah Johnson"},
            {"class": "2.C", "subject": "Physics", "teacher": "Sarah Johnson"},
            {"class": "2.C", "subject": "Chemistry", "teacher": "Jane Doe"},
            {"class": "2.C", "subject": "English", "teacher": "James Wilson"},
            {"class": "2.C", "subject": "History", "teacher": "Charlie Brown"},
            {"class": "2.C", "subject": "Geography", "teacher": "Thomas Anderson"},
            {"class": "2.C", "subject": "Physical Education", "teacher": "Diana Prince"},
            # 3rd Grade - 3.A
            {"class": "3.A", "subject": "Mathematics", "teacher": "John Smith"},
            {"class": "3.A", "subject": "Physics", "teacher": "Michael Chen"},
            {"class": "3.A", "subject": "Chemistry", "teacher": "Jane Doe"},
            {"class": "3.A", "subject": "Biology", "teacher": "Jane Doe"},
            {"class": "3.A", "subject": "Computer Science", "teacher": "Bob Johnson"},
            {"class": "3.A", "subject": "English", "teacher": "Alice Williams"},
            {"class": "3.A", "subject": "History", "teacher": "Charlie Brown"},
            {"class": "3.A", "subject": "Geography", "teacher": "Charlie Brown"},
            {"class": "3.A", "subject": "Physical Education", "teacher": "Diana Prince"},
            # 3rd Grade - 3.B
            {"class": "3.B", "subject": "Mathematics", "teacher": "Robert Miller"},
            {"class": "3.B", "subject": "Physics", "teacher": "Sarah Johnson"},
            {"class": "3.B", "subject": "Chemistry", "teacher": "Emily Watson"},
            {"class": "3.B", "subject": "Biology", "teacher": "David Lee"},
            {"class": "3.B", "subject": "Computer Science", "teacher": "Alex Turner"},
            {"class": "3.B", "subject": "English", "teacher": "Emma Thompson"},
            {"class": "3.B", "subject": "History", "teacher": "Olivia Martinez"},
            {"class": "3.B", "subject": "Geography", "teacher": "Thomas Anderson"},
            {"class": "3.B", "subject": "Physical Education", "teacher": "Mark Taylor"},
            # 4th Grade - 4.A
            {"class": "4.A", "subject": "Mathematics", "teacher": "Sarah Johnson"},
            {"class": "4.A", "subject": "Physics", "teacher": "Michael Chen"},
            {"class": "4.A", "subject": "Chemistry", "teacher": "Emily Watson"},
            {"class": "4.A", "subject": "Biology", "teacher": "David Lee"},
            {"class": "4.A", "subject": "Computer Science", "teacher": "Bob Johnson"},
            {"class": "4.A", "subject": "English", "teacher": "James Wilson"},
            {"class": "4.A", "subject": "History", "teacher": "Olivia Martinez"},
            {"class": "4.A", "subject": "Geography", "teacher": "Thomas Anderson"},
            {"class": "4.A", "subject": "Physical Education", "teacher": "Diana Prince"},
            # 4th Grade - 4.B
            {"class": "4.B", "subject": "Mathematics", "teacher": "Robert Miller"},
            {"class": "4.B", "subject": "Physics", "teacher": "John Smith"},
            {"class": "4.B", "subject": "Chemistry", "teacher": "Jane Doe"},
            {"class": "4.B", "subject": "Biology", "teacher": "Jane Doe"},
            {"class": "4.B", "subject": "Computer Science", "teacher": "Alex Turner"},
            {"class": "4.B", "subject": "English", "teacher": "Alice Williams"},
            {"class": "4.B", "subject": "History", "teacher": "Charlie Brown"},
            {"class": "4.B", "subject": "Geography", "teacher": "Charlie Brown"},
            {"class": "4.B", "subject": "Physical Education", "teacher": "Mark Taylor"},
        ]
        
        for assignment in primary_assignments:
            class_group = class_groups[assignment["class"]]
            subject = subjects[assignment["subject"]]
            teacher = teachers[assignment["teacher"]]
            
            # Create primary capability for this specific class-subject
            primary_capability = TeacherSubjectCapability(
                teacher_id=teacher.id,
                subject_id=subject.id,
                grade_level_id=None,
                class_group_id=class_group.id,
                is_primary=1  # This is the primary teacher
            )
            db.add(primary_capability)
        
        await db.commit()
        print(f"  ✓ Assigned {len(primary_assignments)} primary teachers to class-subject combinations")
        
        # Create Classrooms
        print("\n🏫 Creating Classrooms...")
        classrooms_data = [
            {"name": "Room 101", "capacity": 30, "specializations": []},
            {"name": "Room 102", "capacity": 30, "specializations": []},
            {"name": "Room 103", "capacity": 30, "specializations": []},
            {"name": "Room 104", "capacity": 30, "specializations": []},
            {"name": "Room 201", "capacity": 30, "specializations": []},
            {"name": "Room 202", "capacity": 30, "specializations": []},
            {"name": "Physics Lab 1", "capacity": 20, "specializations": ["Physics"]},
            {"name": "Physics Lab 2", "capacity": 20, "specializations": ["Physics"]},
            {"name": "Chemistry Lab 1", "capacity": 20, "specializations": ["Chemistry"]},
            {"name": "Chemistry Lab 2", "capacity": 20, "specializations": ["Chemistry"]},
            {"name": "Biology Lab 1", "capacity": 20, "specializations": ["Biology"]},
            {"name": "Biology Lab 2", "capacity": 20, "specializations": ["Biology"]},
            {"name": "Computer Lab 1", "capacity": 25, "specializations": ["Computer Science"]},
            {"name": "Computer Lab 2", "capacity": 25, "specializations": ["Computer Science"]},
            {"name": "Gym", "capacity": 40, "specializations": []},
            {"name": "Art Room 1", "capacity": 25, "specializations": []},
            {"name": "Art Room 2", "capacity": 25, "specializations": []},
        ]
        classrooms = {}
        for room_data in classrooms_data:
            # Convert subject names to IDs
            spec_ids = [subjects[s].id for s in room_data["specializations"]] if room_data["specializations"] else []
            classroom = Classroom(
                school_id=school_id,
                name=room_data["name"],
                capacity=room_data["capacity"],
                specializations=spec_ids if spec_ids else None,
                restrictions=None
            )
            db.add(classroom)
            await db.flush()
            classrooms[room_data["name"]] = classroom
            spec_str = f" (specializations: {room_data['specializations']})" if room_data["specializations"] else ""
            print(f"  ✓ Created {room_data['name']} (ID: {classroom.id}){spec_str}")
        
        await db.commit()
        
        # Create Class Subject Allocations
        print("\n📋 Creating Class Subject Allocations...")
        allocations_data = [
            # 1st Grade classes
            {"class": "1.A", "subject": "Mathematics", "hours": 4},
            {"class": "1.A", "subject": "English", "hours": 4},
            {"class": "1.A", "subject": "History", "hours": 2},
            {"class": "1.A", "subject": "Geography", "hours": 2},
            {"class": "1.A", "subject": "Physical Education", "hours": 2},
            {"class": "1.A", "subject": "Art", "hours": 2},
            {"class": "1.B", "subject": "Mathematics", "hours": 4},
            {"class": "1.B", "subject": "English", "hours": 4},
            {"class": "1.B", "subject": "History", "hours": 2},
            {"class": "1.B", "subject": "Geography", "hours": 2},
            {"class": "1.B", "subject": "Physical Education", "hours": 2},
            {"class": "1.B", "subject": "Art", "hours": 2},
            {"class": "1.C", "subject": "Mathematics", "hours": 4},
            {"class": "1.C", "subject": "English", "hours": 4},
            {"class": "1.C", "subject": "History", "hours": 2},
            {"class": "1.C", "subject": "Geography", "hours": 2},
            {"class": "1.C", "subject": "Physical Education", "hours": 2},
            {"class": "1.C", "subject": "Art", "hours": 2},
            # 2nd Grade classes
            {"class": "2.A", "subject": "Mathematics", "hours": 5},
            {"class": "2.A", "subject": "Physics", "hours": 3},
            {"class": "2.A", "subject": "Chemistry", "hours": 2},
            {"class": "2.A", "subject": "English", "hours": 4},
            {"class": "2.A", "subject": "History", "hours": 2},
            {"class": "2.A", "subject": "Geography", "hours": 2},
            {"class": "2.A", "subject": "Physical Education", "hours": 2},
            {"class": "2.B", "subject": "Mathematics", "hours": 5},
            {"class": "2.B", "subject": "Physics", "hours": 3},
            {"class": "2.B", "subject": "Chemistry", "hours": 2},
            {"class": "2.B", "subject": "English", "hours": 4},
            {"class": "2.B", "subject": "History", "hours": 2},
            {"class": "2.B", "subject": "Geography", "hours": 2},
            {"class": "2.B", "subject": "Physical Education", "hours": 2},
            {"class": "2.C", "subject": "Mathematics", "hours": 5},
            {"class": "2.C", "subject": "Physics", "hours": 3},
            {"class": "2.C", "subject": "Chemistry", "hours": 2},
            {"class": "2.C", "subject": "English", "hours": 4},
            {"class": "2.C", "subject": "History", "hours": 2},
            {"class": "2.C", "subject": "Geography", "hours": 2},
            {"class": "2.C", "subject": "Physical Education", "hours": 2},
            # 3rd Grade classes
            {"class": "3.A", "subject": "Mathematics", "hours": 5},
            {"class": "3.A", "subject": "Physics", "hours": 4},
            {"class": "3.A", "subject": "Chemistry", "hours": 3},
            {"class": "3.A", "subject": "Biology", "hours": 3},
            {"class": "3.A", "subject": "Computer Science", "hours": 3},
            {"class": "3.A", "subject": "English", "hours": 4},
            {"class": "3.A", "subject": "History", "hours": 2},
            {"class": "3.A", "subject": "Geography", "hours": 2},
            {"class": "3.A", "subject": "Physical Education", "hours": 2},
            {"class": "3.B", "subject": "Mathematics", "hours": 5},
            {"class": "3.B", "subject": "Physics", "hours": 4},
            {"class": "3.B", "subject": "Chemistry", "hours": 3},
            {"class": "3.B", "subject": "Biology", "hours": 3},
            {"class": "3.B", "subject": "Computer Science", "hours": 3},
            {"class": "3.B", "subject": "English", "hours": 4},
            {"class": "3.B", "subject": "History", "hours": 2},
            {"class": "3.B", "subject": "Geography", "hours": 2},
            {"class": "3.B", "subject": "Physical Education", "hours": 2},
            # 4th Grade classes
            {"class": "4.A", "subject": "Mathematics", "hours": 5},
            {"class": "4.A", "subject": "Physics", "hours": 4},
            {"class": "4.A", "subject": "Chemistry", "hours": 3},
            {"class": "4.A", "subject": "Biology", "hours": 3},
            {"class": "4.A", "subject": "Computer Science", "hours": 3},
            {"class": "4.A", "subject": "English", "hours": 4},
            {"class": "4.A", "subject": "History", "hours": 2},
            {"class": "4.A", "subject": "Geography", "hours": 2},
            {"class": "4.A", "subject": "Physical Education", "hours": 2},
            {"class": "4.B", "subject": "Mathematics", "hours": 5},
            {"class": "4.B", "subject": "Physics", "hours": 4},
            {"class": "4.B", "subject": "Chemistry", "hours": 3},
            {"class": "4.B", "subject": "Biology", "hours": 3},
            {"class": "4.B", "subject": "Computer Science", "hours": 3},
            {"class": "4.B", "subject": "English", "hours": 4},
            {"class": "4.B", "subject": "History", "hours": 2},
            {"class": "4.B", "subject": "Geography", "hours": 2},
            {"class": "4.B", "subject": "Physical Education", "hours": 2},
        ]
        
        for alloc_data in allocations_data:
            class_group = class_groups[alloc_data["class"]]
            subject = subjects[alloc_data["subject"]]
            allocation = ClassSubjectAllocation(
                class_group_id=class_group.id,
                subject_id=subject.id,
                weekly_hours=alloc_data["hours"]
            )
            db.add(allocation)
        
        await db.commit()
        print(f"  ✓ Created {len(allocations_data)} subject allocations")
        
        print("\n" + "=" * 60)
        print("✅ Test data created successfully!")
        print("\nSummary:")
        print(f"  • {len(grade_levels)} Grade Levels")
        print(f"  • {len(class_groups)} Class Groups")
        print(f"  • {len(subjects)} Subjects")
        print(f"  • {len(teachers)} Teachers")
        print(f"  • {len(classrooms)} Classrooms")
        print(f"  • {len(allocations_data)} Class Subject Allocations")
        print("\nYou can now use the admin panel to manage this data!")

if __name__ == "__main__":
    asyncio.run(create_test_data())

