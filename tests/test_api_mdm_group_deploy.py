"""test_api_group_deploy.py: Tests for group deployment API."""

__author__ = "Phil Weir <phil.weir@flaxandteal.co.uk>"

import sys
import pytest
import json
import sqlalchemy
import sqlalchemy.orm
import uuid
from commandment import database as cdatabase
from commandment.models import Profile, MDMGroup, ProfileStatus, Device
from pytest_flask.fixtures import client
from flask import url_for

from fixtures import app, profile, device, mdm_group


class TestAPIProfile:
    @staticmethod
    def assert_success(response):
        if response.status_code != 200:
            raise AssertionError("Response status code is %d != 200" % response.status_code)
        return True

    @staticmethod
    def assert_json(headers):
        if 'Content-Type' not in headers:
            raise AssertionError("Response header did not have Content-Type")

        if headers['Content-Type'] != 'application/json':
            raise AssertionError("Response was not JSON")

        return True

    def test_can_switch_membership_of_an_inactive_profile(self, client, profile, mdm_group):
        profile = Profile(**profile)
        profile.status = ProfileStatus.INACTIVE
        mdm_group = MDMGroup(**mdm_group)

        cdatabase.db_session.add(profile)
        cdatabase.db_session.add(mdm_group)
        cdatabase.db_session.commit()

        res = client.put(url_for('api_app.mdmgroupresource_profile', id=mdm_group.id, profile_id=profile.id))

        assert self.assert_json(res.headers)
        assert self.assert_success(res)
        data = json.loads(res.data)
        assert data['message'] == "Success"

        res = client.delete(url_for('api_app.mdmgroupresource_profile', id=mdm_group.id, profile_id=profile.id))

        assert self.assert_json(res.headers)
        assert self.assert_success(res)
        data = json.loads(res.data)
        assert data['message'] == "Success"

    def test_cannot_switch_profile_membership_if_its_not_inactive(self, client, profile, mdm_group):
        profile = Profile(**profile)
        mdm_group = MDMGroup(**mdm_group)

        cdatabase.db_session.add(profile)
        cdatabase.db_session.add(mdm_group)
        cdatabase.db_session.commit()

        for status in list(ProfileStatus):
            if status == ProfileStatus.INACTIVE:
                continue

            profile.status = status
            cdatabase.db_session.commit()
            res = client.put(url_for('api_app.mdmgroupresource_profile', id=mdm_group.id, profile_id=profile.id))

            assert self.assert_json(res.headers)
            data = json.loads(res.data)

            assert res.status_code == 400
            assert data['message'] == "Cannot change groups while profile is not inactive"

    def test_switching_profile_membership_is_idempotent(self, client, profile, mdm_group):
        profile = Profile(**profile)
        mdm_group = MDMGroup(**mdm_group)

        cdatabase.db_session.add(profile)
        cdatabase.db_session.add(mdm_group)
        profile.mdm_groups.append(mdm_group)
        cdatabase.db_session.commit()

        res = client.put(url_for('api_app.mdmgroupresource_profile', id=mdm_group.id, profile_id=profile.id))

        assert self.assert_json(res.headers)
        assert self.assert_success(res)
        data = json.loads(res.data)

        assert data['message'] == "Already in group"
