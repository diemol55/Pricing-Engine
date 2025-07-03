import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, initialize_rrpp_table
from models import Base, PricedParts, RRPPMarkupTable
from pricing_engine import OzwidePricingEngine
import pandas as pd
import os
import io

# Setup the test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        initialize_rrpp_table(db)  # Initialize with default data
        yield db
    finally:
        db.close()
        # Drop the database tables after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def test_client():
    return client

# Test data
@pytest.fixture
def sample_excel_file(tmp_path):
    df = pd.DataFrame({
        "Part Number": ["PN1", "PN2"],
        "Description": ["Desc1", "Desc2"],
        "Qty": [10, 20],
        "Purchase Cost": [100, 200],
        "Category": ["Speciality", "Universal"]
    })
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)
    return file_path

# Tests
def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "app": "Ozwide Pricing Calculator"}

def test_upload_and_calculate(test_client, db_session, sample_excel_file):
    with open(sample_excel_file, "rb") as f:
        response = test_client.post(
            "/upload-and-calculate/",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={
                "currency": "AUD",
                "exchange_rate": 1.0,
                "freight_cost": 100.0,
                "freight_mode": "Auto"
            },
            auth=("admin", "pricing123")
        )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Successfully processed 2 records"
    assert len(data["processed_data"]) == 2

def test_get_rrpp_markup_table(test_client, db_session):
    response = test_client.get("/rrpp-markup-table/", auth=("admin", "pricing123"))
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_rrpp_markup_table(test_client, db_session):
    new_markup_data = [
        {"from_price": 0, "to_price": 10, "rrpp_markup": 2.5},
        {"from_price": 10.01, "to_price": 20, "rrpp_markup": 2.0}
    ]
    response = test_client.put("/rrpp-markup-table/", json=new_markup_data, auth=("admin", "pricing123"))
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["from_price"] == 0
    assert response_data[0]["to_price"] == 10
    assert response_data[0]["rrpp_markup"] == 2.5

    # Verify the update
    response = test_client.get("/rrpp-markup-table/", auth=("admin", "pricing123"))
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_priced_parts(test_client, db_session, sample_excel_file):
    # First, upload and calculate to populate the database
    with open(sample_excel_file, "rb") as f:
        test_client.post(
            "/upload-and-calculate/",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            auth=("admin", "pricing123")
        )
    
    response = test_client.get("/priced-parts/", auth=("admin", "pricing123"))
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_export_csv(test_client, db_session, sample_excel_file):
    # First, upload and calculate to populate the database
    with open(sample_excel_file, "rb") as f:
        test_client.post(
            "/upload-and-calculate/",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            auth=("admin", "pricing123")
        )

    response = test_client.get("/export-csv/", auth=("admin", "pricing123"))
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=priced_parts.csv" in response.headers["content-disposition"]
    # Check if the content is a valid CSV
    try:
        df = pd.read_csv(io.StringIO(response.text))
        assert len(df) > 0
    except Exception as e:
        pytest.fail(f"Failed to parse CSV: {e}")
