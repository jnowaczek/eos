# ===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2017 Anton Vorobyov
#
# This file is part of Eos.
#
# Eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Eos. If not, see <http://www.gnu.org/licenses/>.
# ===============================================================================


from eos.const.eos import Restriction, State
from eos.fit.item import ModuleHigh
from tests.restriction.restriction_testcase import RestrictionTestCase


class TestState(RestrictionTestCase):
    """Check functionality of item state restriction"""

    def test_state_lower(self):
        eve_type = self.ch.type(type_id=1)
        eve_type.max_state = State.active
        item = self.make_item_mock(ModuleHigh, eve_type, state=State.online)
        self.fit._items.add(item)
        # Action
        restriction_error = self.get_restriction_error(item, Restriction.state)
        # Verification
        self.assertIsNone(restriction_error)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_restriction_buffers_empty()

    def test_state_equal(self):
        eve_type = self.ch.type(type_id=1)
        eve_type.max_state = State.active
        item = self.make_item_mock(ModuleHigh, eve_type, state=State.active)
        self.fit._items.add(item)
        # Action
        restriction_error = self.get_restriction_error(item, Restriction.state)
        # Verification
        self.assertIsNone(restriction_error)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_restriction_buffers_empty()

    def test_state_higher(self):
        eve_type = self.ch.type(type_id=1)
        eve_type.max_state = State.active
        item = self.make_item_mock(ModuleHigh, eve_type, state=State.overload)
        self.fit._items.add(item)
        # Action
        restriction_error = self.get_restriction_error(item, Restriction.state)
        # Verification
        self.assertIsNotNone(restriction_error)
        self.assertEqual(restriction_error.current_state, State.overload)
        self.assertCountEqual(restriction_error.allowed_states, (State.offline, State.online, State.active))
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_restriction_buffers_empty()