from app.models import ApiKey, Application, AuditEvent, Base, User


def test_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "api_keys",
        "applications",
        "audit_events",
        "users",
    }


def test_audit_event_application_is_assigned_by_foreign_key() -> None:
    foreign_keys = AuditEvent.__table__.c.application_id.foreign_keys

    assert {key.target_fullname for key in foreign_keys} == {"applications.id"}


def test_actor_id_is_not_linked_to_panel_users() -> None:
    assert not AuditEvent.__table__.c.actor_id.foreign_keys


def test_sensitive_values_have_dedicated_storage_columns() -> None:
    assert User.__table__.c.password_hash.nullable is False
    assert ApiKey.__table__.c.key_hash.nullable is False
    assert "key" not in ApiKey.__table__.c


def test_application_relations_are_defined() -> None:
    assert Application.api_keys.property.mapper.class_ is ApiKey
    assert Application.audit_events.property.mapper.class_ is AuditEvent

