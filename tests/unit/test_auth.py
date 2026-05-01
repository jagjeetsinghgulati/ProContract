from __future__ import annotations

from data_model.persistence import authenticate_user, create_user


def test_create_and_authenticate_user():
    user = create_user("alice", "StrongPassword123")
    assert user.username == "alice"
    assert user.password_hash != "StrongPassword123"

    assert authenticate_user("alice", "StrongPassword123") is not None
    assert authenticate_user("alice", "wrong") is None
