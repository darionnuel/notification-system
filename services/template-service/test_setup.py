"""Quick test script to verify the template service is working."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import init_db, SessionLocal
from app.models.template import Template, TemplateType, TemplateStatus


def test_database_connection():
    """Test database initialization and basic operations."""
    print("🧪 Testing Template Service Setup...\n")
    
    # Initialize database
    print("1️⃣ Initializing database...")
    init_db()
    print("   ✅ Database initialized\n")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Test create
        print("2️⃣ Testing template creation...")
        test_template = Template(
            template_code="test_template",
            template_type=TemplateType.EMAIL,
            language="en",
            subject="Test Subject {{name}}",
            content="<p>Hello {{name}}, this is a test.</p>",
            description="Test template",
            required_variables=["name"],
            status=TemplateStatus.DRAFT,
            version=1
        )
        db.add(test_template)
        db.commit()
        db.refresh(test_template)
        print(f"   ✅ Template created with ID: {test_template.id}\n")
        
        # Test read
        print("3️⃣ Testing template retrieval...")
        retrieved = db.query(Template).filter(Template.template_code == "test_template").first()
        if retrieved:
            print(f"   ✅ Template retrieved: {retrieved.template_code}")
            print(f"      - Type: {retrieved.template_type.value}")
            print(f"      - Subject: {retrieved.subject}")
            print(f"      - Variables: {retrieved.required_variables}\n")
        
        # Test update
        print("4️⃣ Testing template update...")
        retrieved.status = TemplateStatus.ACTIVE
        retrieved.version = 2
        db.commit()
        print(f"   ✅ Template updated to version {retrieved.version}\n")
        
        # Clean up
        print("5️⃣ Cleaning up test data...")
        db.delete(retrieved)
        db.commit()
        print("   ✅ Test template deleted\n")
        
        print("🎉 All tests passed! Template Service is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Run: python seed_templates.py (to add predefined templates)")
        print("   2. Run: uvicorn app.main:app --reload --port 8001")
        print("   3. Visit: http://localhost:8001/docs")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_database_connection()
