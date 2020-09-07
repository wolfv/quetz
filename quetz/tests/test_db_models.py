"""Tests for the database models"""
# Copyright 2020 QuantStack
# Distributed under the terms of the Modified BSD License.

import uuid

from quetz.db_models import User, ApiKey, Channel, ChannelMember
from fastapi.testclient import TestClient
from quetz.main import app


def test_user(db):
    user = User(id=uuid.uuid4().bytes, username='paul')
    db.add(user)
    db.commit()

    assert len(db.query(User).all()) == 1

    found = User.find(db, 'paul')
    assert found.username == user.username
    found = User.find(db, 'dave')
    assert found is None


def test_api_key(db):
    usera = User(id=uuid.uuid4().bytes, username='usera')
    db.add(usera)
    userb = User(id=uuid.uuid4().bytes, username='userb')
    db.add(userb)
    db.commit()

    assert len(db.query(User).all()) >= 2

    keya = "akey"
    keyb = "bkey"
    db.add(ApiKey(key=keya, user_id=usera.id, owner_id=usera.id))
    db.add(ApiKey(key=keyb, user_id=userb.id, owner_id=userb.id))
    db.commit()

    channel1 = Channel(name="testchannel", private=False)
    channel2 = Channel(name="privatechannel", private=True)

    channel_member = ChannelMember(channel=channel2, user=usera, role='OWNER')
    for el in [channel1, channel2, channel_member]:
        db.add(el)
    db.commit()

    client = TestClient(app)

    response = client.get('/')
    assert (len(response.text))
    response = client.get('/api/channels')

    response = client.get('/api/channels', headers={"X-Api-Key": keya})
    assert (len(response.json()) == 2)
    response = client.get('/api/channels', headers={"X-Api-Key": keyb})
    assert (len(response.json()) == 1)

keya = "akey"
keyb = "bkey"

def test_api_key(db):
    usera = User(id=uuid.uuid4().bytes, username='usera')
    db.add(usera)
    userb = User(id=uuid.uuid4().bytes, username='userb')
    db.add(userb)
    db.commit()

    assert len(db.query(User).all()) >= 2

    db.add(ApiKey(key=keya, user_id=usera.id, owner_id=usera.id))
    db.add(ApiKey(key=keyb, user_id=userb.id, owner_id=userb.id))
    db.commit()

    channel1 = Channel(name="testchannel", private=False)
    channel2 = Channel(name="privatechannel", private=True)

    channel_member = ChannelMember(channel=channel2, user=usera, role='OWNER')
    for el in [channel1, channel2, channel_member]:
        db.add(el)
    db.commit()

    client = TestClient(app)

    response = client.get('/')
    assert (len(response.text))
    response = client.get('/api/channels')

    response = client.get('/api/channels', headers={"X-Api-Key": keya})
    assert (len(response.json()) == 2)
    response = client.get('/api/channels', headers={"X-Api-Key": keyb})
    assert (len(response.json()) == 1)

def test_api(db):
    client = TestClient(app)
    assert len(db.query(User).all()) >= 2

    response = client.get('/api/channels', headers={"X-Api-Key": keya})
    assert (len(response.json()) == 2)

    response = client.get('/api/channels', headers={"X-Api-Key": keya})
