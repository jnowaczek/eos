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
from eos.const.eos import ModifierTargetFilter, ModifierDomain, ModifierOperator
from eos.const.eve import Attribute, EffectCategory
from eos.data.cache_object.modifier import DogmaModifier
from tests.integration.stats.stat_testcase import StatTestCase


class TestPowergrid(StatTestCase):
    """Check functionality of powergrid stats"""

    def setUp(self):
        super().setUp()
        self.ch.attribute(attribute_id=Attribute.power_output)
        self.ch.attribute(attribute_id=Attribute.power)

    def test_output(self):
        # Check that modified attribute of ship is used
        src_attr = self.ch.attribute()
        modifier = DogmaModifier(
            tgt_filter=ModifierTargetFilter.item,
            tgt_domain=ModifierDomain.self,
            tgt_attr=Attribute.power_output,
            operator=ModifierOperator.post_mul,
            src_attr=src_attr.id
        )
        effect = self.ch.effect(category=EffectCategory.passive, modifiers=[modifier])
        fit = Fit()
        fit.ship = Ship(self.ch.type(effects=[effect], attributes={Attribute.power_output: 200, src_attr.id: 2}).id)
        # Verification
        self.assertAlmostEqual(fit.stats.powergrid.output, 400)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_output_no_ship(self):
        # None for output when no ship
        fit = Fit()
        # Verification
        self.assertIsNone(fit.stats.powergrid.output)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_output_no_attr(self):
        # None for output when no attribute on ship
        fit = Fit()
        fit.ship = Ship(self.ch.type().id)
        # Verification
        self.assertIsNone(fit.stats.powergrid.output)
        # Cleanup
        # Log entry is due to inability to calculate requested attribute
        self.assertEqual(len(self.log), 1)
        self.assert_fit_buffers_empty(fit)

    def test_use_single(self):
        # Check that modified consumption attribute is used
        src_attr = self.ch.attribute()
        modifier = DogmaModifier(
            tgt_filter=ModifierTargetFilter.item,
            tgt_domain=ModifierDomain.self,
            tgt_attr=Attribute.power,
            operator=ModifierOperator.post_mul,
            src_attr=src_attr.id
        )
        effect = self.ch.effect(category=EffectCategory.passive, modifiers=[modifier])
        fit = Fit()
        fit.modules.high.append(ModuleHigh(self.ch.type(
            effects=[effect], attributes={Attribute.power: 100, src_attr.id: 0.5}
        ).id, state=State.online))
        # Verification
        self.assertAlmostEqual(fit.stats.powergrid.used, 50)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_use_single_rounding(self):
        fit = Fit()
        fit.modules.high.append(ModuleHigh(self.ch.type(
            attributes={Attribute.power: 55.5555555555}
        ).id, state=State.online))
        # Verification
        self.assertAlmostEqual(fit.stats.powergrid.used, 55.56)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_use_multiple(self):
        fit = Fit()
        fit.modules.high.append(ModuleHigh(self.ch.type(attributes={Attribute.power: 50}).id, state=State.online))
        fit.modules.high.append(ModuleHigh(self.ch.type(attributes={Attribute.power: 30}).id, state=State.online))
        # Verification
        self.assertAlmostEqual(fit.stats.powergrid.used, 80)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_use_state(self):
        fit = Fit()
        fit.modules.high.append(ModuleHigh(self.ch.type(attributes={Attribute.power: 50}).id, state=State.online))
        fit.modules.high.append(ModuleHigh(self.ch.type(attributes={Attribute.power: 30}).id, state=State.offline))
        # Verification
        self.assertAlmostEqual(fit.stats.powergrid.used, 50)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)

    def test_use_none(self):
        fit = Fit()
        # Verification
        self.assertAlmostEqual(fit.stats.powergrid.used, 0)
        # Cleanup
        self.assertEqual(len(self.log), 0)
        self.assert_fit_buffers_empty(fit)