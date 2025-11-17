"""Quick test script for API."""
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

print("Testing API imports...")

try:
    from api.main import app
    print("✅ API imports successful")
    
    # Test basic endpoint
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    print("\nTesting endpoints...")
    
    # Test root
    response = client.get("/")
    assert response.status_code == 200
    print(f"✅ GET / - {response.json()['status']}")
    
    # Test health
    response = client.get("/api/health")
    assert response.status_code == 200
    print(f"✅ GET /api/health - {response.json()['status']}")
    
    # Test stats
    response = client.get("/api/stats")
    assert response.status_code == 200
    print(f"✅ GET /api/stats - {response.json()}")
    
    # Test transcripts
    response = client.get("/api/transcripts")
    assert response.status_code == 200
    print(f"✅ GET /api/transcripts - {len(response.json())} transcripts")
    
    # Test reports
    response = client.get("/api/reports")
    assert response.status_code == 200
    print(f"✅ GET /api/reports - {len(response.json())} reports")
    
    print("\n🎉 All API tests passed!")
    print("\nTo start the API server, run:")
    print("  python api/main.py")
    print("\nThen visit:")
    print("  http://localhost:8000/docs (Swagger UI)")
    print("  http://localhost:8000 (API status)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
