import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
import uuid

from app.db.base import Base
from app.services.sync_engine import SyncEngine, MODEL_MAP
from app.models.patient import Patient
from app.models.sync import SyncQueue
from app.repositories.patient import patient_repo
from app.schemas.patient import PatientCreate, PatientUpdate

# Setup a secondary in-memory SQLite database to simulate the Cloud environment during tests
cloud_engine_test = create_engine(
    "sqlite:///:memory:", 
    connect_args={"check_same_thread": False}
)
CloudSessionLocalTest = sessionmaker(autocommit=False, autoflush=False, bind=cloud_engine_test)

@pytest.fixture(scope="function")
def cloud_db():
    """
    Fixtures to set up and tear down tables in the simulated cloud database.
    """
    Base.metadata.create_all(bind=cloud_engine_test)
    session = CloudSessionLocalTest()
    yield session
    session.close()
    Base.metadata.drop_all(bind=cloud_engine_test)

@pytest.fixture(scope="function")
def test_sync_engine(monkeypatch):
    """
    Returns an instance of SyncEngine, overriding the cloud engine with our mock.
    """
    engine = SyncEngine()
    # Mock connectivity checks and session makers to use the simulated cloud DB
    monkeypatch.setattr(engine, "check_cloud_connectivity", lambda: True)
    return engine

def test_sync_outbox_queue_logging(db):
    """Verify that writing to repositories automatically registers records in the local SyncQueue."""
    patient_in = PatientCreate(name="John Doe", age=30, gender="Male", phone="123456", address="PHC Area")
    patient = patient_repo.create(db, obj_in=patient_in)
    db.commit()
    
    # Query queue
    queue_item = db.query(SyncQueue).filter(SyncQueue.entity_id == patient.id).first()
    assert queue_item is not None
    assert queue_item.entity_type == "patient"
    assert queue_item.operation_type == "CREATE"
    assert queue_item.sync_status == "PENDING"

def test_sync_engine_lww_local_wins(db, cloud_db, test_sync_engine, monkeypatch):
    """Test Last Write Wins (LWW): Local update is newer -> Overwrite cloud."""
    # Mock session factory inside sync_engine
    monkeypatch.setattr("app.services.sync_engine.LocalSessionLocal", lambda: db)
    monkeypatch.setattr("app.services.sync_engine.CloudSessionLocal", lambda: cloud_db)
    # Prevent session close in sync engine from closing our test fixtures
    monkeypatch.setattr(db, "close", lambda: None)
    monkeypatch.setattr(cloud_db, "close", lambda: None)

    # 1. Create a patient locally (creates a CREATE queue entry)
    patient_id = uuid.uuid4()
    patient_in = PatientCreate(id=patient_id, name="John Doe", age=30, gender="Male")
    patient = patient_repo.create(db, obj_in=patient_in)
    db.commit()

    # 2. Run sync -> transfers creation to cloud
    stats = test_sync_engine.sync_local_to_cloud()
    assert stats["success"] == 1
    
    # Confirm it exists in cloud
    cloud_patient = cloud_db.get(Patient, patient_id)
    assert cloud_patient is not None
    assert cloud_patient.name == "John Doe"

    # 3. Simulate local update (new timestamp) and cloud update (older timestamp)
    # Perform local update
    patient_repo.update(db, db_obj=patient, obj_in=PatientUpdate(name="John Local Wins"))
    db.commit()

    # Manually adjust updated_at on cloud to represent an older update
    cloud_patient.name = "John Cloud Old"
    cloud_patient.updated_at = datetime.now(timezone.utc) - timedelta(hours=1)
    cloud_db.add(cloud_patient)
    cloud_db.commit()

    # 4. Trigger sync again
    stats = test_sync_engine.sync_local_to_cloud()
    assert stats["success"] == 1

    # Verify cloud was overwritten by local
    cloud_db.expire_all()
    cloud_patient_updated = cloud_db.get(Patient, patient_id)
    assert cloud_patient_updated.name == "John Local Wins"

def test_sync_engine_lww_cloud_wins_convergence(db, cloud_db, test_sync_engine, monkeypatch):
    """Test Last Write Wins (LWW): Cloud update is newer -> Converge local SQLite database."""
    # Mock session factory inside sync_engine
    monkeypatch.setattr("app.services.sync_engine.LocalSessionLocal", lambda: db)
    monkeypatch.setattr("app.services.sync_engine.CloudSessionLocal", lambda: cloud_db)
    # Prevent session close in sync engine from closing our test fixtures
    monkeypatch.setattr(db, "close", lambda: None)
    monkeypatch.setattr(cloud_db, "close", lambda: None)

    # 1. Create patient locally
    patient_id = uuid.uuid4()
    patient_in = PatientCreate(id=patient_id, name="Jane Doe", age=25, gender="Female")
    patient = patient_repo.create(db, obj_in=patient_in)
    db.commit()

    # Sync to Cloud
    test_sync_engine.sync_local_to_cloud()

    # 2. Trigger local update
    patient_repo.update(db, db_obj=patient, obj_in=PatientUpdate(name="Jane Local Old"))
    db.commit()
    
    # Manually set local updated_at to be OLDER
    patient.updated_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db.add(patient)
    db.commit()

    # 3. Trigger cloud update with NEWER timestamp
    cloud_patient = cloud_db.get(Patient, patient_id)
    cloud_patient.name = "Jane Cloud Wins"
    cloud_patient.updated_at = datetime.now(timezone.utc)  # Newer timestamp
    cloud_db.add(cloud_patient)
    cloud_db.commit()

    # 4. Sync
    stats = test_sync_engine.sync_local_to_cloud()
    assert stats["success"] == 1
    assert stats["converged"] == 1

    # Verify local SQLite record was updated to match Cloud values
    db.expire_all()
    local_patient_updated = db.get(Patient, patient_id)
    assert local_patient_updated.name == "Jane Cloud Wins"


def test_sync_priority_ordering_logic(db):
    """Verify that Patients are ordered before Consultations in the sync query queue."""
    import uuid
    from app.models.sync import SyncQueue
    from app.services.sync_engine import PRIORITY_ORDER

    # Insert a consultation log then a patient log to simulate out-of-order logging
    log_cons = SyncQueue(
        entity_type="consultation",
        entity_id=uuid.uuid4(),
        operation_type="CREATE",
        sync_status="PENDING",
        timestamp=datetime.now(timezone.utc)
    )
    log_pat = SyncQueue(
        entity_type="patient",
        entity_id=uuid.uuid4(),
        operation_type="CREATE",
        sync_status="PENDING",
        timestamp=datetime.now(timezone.utc) + timedelta(seconds=1)
    )
    db.add(log_cons)
    db.add(log_pat)
    db.commit()

    # Query pending logs sorted by PRIORITY_ORDER and timestamp
    items = (
        db.query(SyncQueue)
        .filter(SyncQueue.sync_status == "PENDING")
        .order_by(PRIORITY_ORDER, SyncQueue.timestamp.asc())
        .all()
    )

    # Patient (priority 1) must be first, Consultation (priority 2) must be second
    assert len(items) >= 2
    assert items[0].entity_type == "patient"
    assert items[1].entity_type == "consultation"


def test_sync_queue_pruning_logic(db, test_sync_engine):
    """Verify that successfully synced logs older than 24 hours are pruned, while keeping newer logs."""
    import uuid
    from app.models.sync import SyncQueue

    # Create logs with different updated_at times
    now = datetime.now(timezone.utc)
    
    # 1. Synced log older than 24 hours (should be pruned)
    old_synced = SyncQueue(
        entity_type="patient",
        entity_id=uuid.uuid4(),
        operation_type="CREATE",
        sync_status="SYNCED",
        created_at=now - timedelta(hours=30),
        updated_at=now - timedelta(hours=30)
    )
    
    # 2. Synced log newer than 24 hours (should be kept)
    new_synced = SyncQueue(
        entity_type="patient",
        entity_id=uuid.uuid4(),
        operation_type="CREATE",
        sync_status="SYNCED",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2)
    )
    
    # 3. Pending log older than 24 hours (should be kept because it is still pending!)
    old_pending = SyncQueue(
        entity_type="patient",
        entity_id=uuid.uuid4(),
        operation_type="CREATE",
        sync_status="PENDING",
        created_at=now - timedelta(hours=30),
        updated_at=now - timedelta(hours=30)
    )

    db.add(old_synced)
    db.add(new_synced)
    db.add(old_pending)
    db.commit()

    # Capture IDs before deletion/pruning to avoid ObjectDeletedError
    old_synced_id = old_synced.id
    new_synced_id = new_synced.id
    old_pending_id = old_pending.id

    # Run pruning
    pruned_count = test_sync_engine.prune_synced_records(db)
    assert pruned_count == 1

    # Verify what remains
    remaining = db.query(SyncQueue).all()
    remaining_ids = [r.id for r in remaining]
    
    assert old_synced_id not in remaining_ids
    assert new_synced_id in remaining_ids
    assert old_pending_id in remaining_ids

