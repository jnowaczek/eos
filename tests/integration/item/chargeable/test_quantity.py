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


from eos import *
from eos.const.eve import Attribute
from tests.integration.item.item_testcase import ItemMixinTestCase


class TestItemMixinChargeQuantity(ItemMixinTestCase):

    def setUp(self):
        super().setUp()
        self.ch.attribute(attribute_id=Attribute.capacity)
        self.ch.attribute(attribute_id=Attribute.volume)

    def test_generic(self):
        fit = Fit()
        item = ModuleHigh(self.ch.type(attributes={Attribute.capacity: 20.0}).id)
        item.charge = Charge(self.ch.type(attributes={Attribute.volume: 2.0}).id)
        fit.modules.high.append(item)
        # Verification
        self.assertEqual(item.charge_quantity, 10)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_float_error(self):
        fit = Fit()
        item = ModuleHigh(self.ch.type(attributes={Attribute.capacity: 2.3}).id)
        item.charge = Charge(self.ch.type(attributes={Attribute.volume: 0.1}).id)
        fit.modules.high.append(item)
        # Verification
        self.assertEqual(item.charge_quantity, 23)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_round_down(self):
        fit = Fit()
        item = ModuleHigh(self.ch.type(attributes={Attribute.capacity: 19.7}).id)
        item.charge = Charge(self.ch.type(attributes={Attribute.volume: 2.0}).id)
        fit.modules.high.append(item)
        # Verification
        self.assertEqual(item.charge_quantity, 9)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_no_volume(self):
        fit = Fit()
        item = ModuleHigh(self.ch.type(attributes={Attribute.capacity: 20.0}).id)
        item.charge = Charge(self.ch.type().id)
        fit.modules.high.append(item)
        # Verification
        self.assertIsNone(item.charge_quantity)
        # Cleanup
        self.assertEqual(len(self.log), 1)
        self.assert_fit_buffers_empty(fit)

    def test_no_capacity(self):
        fit = Fit()
        item = ModuleHigh(self.ch.type().id)
        item.charge = Charge(self.ch.type(attributes={Attribute.volume: 2.0}).id)
        fit.modules.high.append(item)
        # Verification
        self.assertIsNone(item.charge_quantity)
        # Cleanup
        self.assertEqual(len(self.log), 1)
        self.assert_fit_buffers_empty(fit)

    def test_no_charge(self):
        fit = Fit()
        item = ModuleHigh(self.ch.type(attributes={Attribute.capacity: 20.0}).id)
        fit.modules.high.append(item)
        # Verification
        self.assertIsNone(item.charge_quantity)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)