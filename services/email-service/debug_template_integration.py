"""
Quick script to verify Template Service integration.

This script:
1. Checks if Template Service is running
2. Fetches a template by code
3. Shows the rendered output

Usage:
    python debug_template_integration.py
"""

import asyncio
import httpx
from jinja2 import Template


async def test_template_service():
    """Test Template Service connection and template rendering."""
    
    template_service_url = "http://localhost:8001"
    
    print("=" * 60)
    print("TESTING TEMPLATE SERVICE INTEGRATION")
    print("=" * 60)
    
    # Test 1: Check if Template Service is running
    print("\n1️⃣  Testing Template Service connection...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{template_service_url}/health")
            if response.status_code == 200:
                print("   ✅ Template Service is running!")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ❌ Template Service returned status {response.status_code}")
                return
    except Exception as e:
        print(f"   ❌ Cannot connect to Template Service: {e}")
        print(f"   Make sure Template Service is running on {template_service_url}")
        return
    
    # Test 2: List available templates
    print("\n2️⃣  Fetching available templates...")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{template_service_url}/api/v1/templates")
            data = response.json()
            
            if data.get("success") and data.get("data"):
                templates = data["data"]
                print(f"   ✅ Found {len(templates)} template(s):")
                for template in templates:
                    print(f"      • {template['code']} - {template['name']} [{template['language']}]")
                    
                # Test 3: Fetch and render first template
                if templates:
                    first_template = templates[0]
                    print(f"\n3️⃣  Testing template rendering with '{first_template['code']}'...")
                    
                    # Fetch template by code
                    response = await client.get(
                        f"{template_service_url}/api/v1/templates/code/{first_template['code']}",
                        params={"language": first_template['language']}
                    )
                    template_data = response.json()
                    
                    if template_data.get("success"):
                        template_info = template_data["data"]
                        print(f"   ✅ Template fetched successfully!")
                        print(f"   Subject: {template_info.get('subject', 'N/A')}")
                        print(f"   Content Preview: {template_info.get('content', '')[:100]}...")
                        
                        # Render with sample variables
                        print("\n4️⃣  Rendering template with sample variables...")
                        sample_vars = {
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john@example.com",
                            "activation_link": "https://example.com/activate/abc123"
                        }
                        
                        # Render subject
                        if template_info.get('subject'):
                            subject_template = Template(template_info['subject'])
                            rendered_subject = subject_template.render(**sample_vars)
                            print(f"   📧 Rendered Subject: {rendered_subject}")
                        
                        # Render content
                        content_template = Template(template_info['content'])
                        rendered_content = content_template.render(**sample_vars)
                        print(f"   📄 Rendered Content (first 200 chars):")
                        print(f"      {rendered_content[:200]}...")
                        
                        print("\n✅ INTEGRATION TEST PASSED!")
                        print("   Email Service can successfully fetch and render templates.")
                    else:
                        print(f"   ❌ Failed to fetch template: {template_data.get('message')}")
                else:
                    print("   ⚠️  No templates found!")
                    print("   Create a template first in Template Service at:")
                    print(f"   {template_service_url}/docs")
            else:
                print(f"   ❌ Failed to list templates: {data.get('message')}")
                
    except Exception as e:
        print(f"   ❌ Error during template test: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_template_service())
