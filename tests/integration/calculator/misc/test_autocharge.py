# ==============================================================================
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
# ==============================================================================


from eos import Charge
from eos import ModuleHigh
from eos import Ship
from eos import State
from eos.const.eos import ModDomain
from eos.const.eos import ModOperator
from eos.const.eos import ModTgtFilter
from eos.const.eve import AttrId
from eos.const.eve import EffectId
from eos.const.eve import EffectCategoryId
from tests.integration.calculator.testcase import CalculatorTestCase


class TestAutocharge(CalculatorTestCase):
    """Test how calculator processes autocharges."""

    def setUp(self):
        CalculatorTestCase.setUp(self)
        self.src_attr = self.mkattr()
        self.tgt_attr = self.mkattr()
        self.ammo_attr = self.mkattr(attr_id=AttrId.ammo_loaded)

    def mkmod_filter_item(self, domain):
        return self.mkmod(
            tgt_filter=ModTgtFilter.item,
            tgt_domain=domain,
            tgt_attr_id=self.tgt_attr.id,
            operator=ModOperator.post_percent,
            src_attr_id=self.src_attr.id)

    def test_influence_self(self):
        # Autocharge should be able to influence itself
        autocharge_modifier = self.mkmod_filter_item(ModDomain.self)
        autocharge_effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[autocharge_modifier])
        autocharge_type = self.mktype(
            attrs={self.src_attr.id: 50, self.tgt_attr.id: 10},
            effects=[autocharge_effect])
        container_effect = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={self.ammo_attr.id: autocharge_type.id},
                effects=[container_effect]).id,
            state=State.offline)
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertIn(container_effect.id, container_item.autocharges)
        autocharge_item = container_item.autocharges[container_effect.id]
        self.assertAlmostEqual(autocharge_item.attrs[self.tgt_attr.id], 15)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_influence_single_item_running(self):
        # Autocharge should be able to modify container when effect which
        # defines autocharge is running
        autocharge_modifier = self.mkmod_filter_item(ModDomain.ship)
        autocharge_effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[autocharge_modifier])
        autocharge_type = self.mktype(
            attrs={self.src_attr.id: 50},
            effects=[autocharge_effect])
        container_effect = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={self.ammo_attr.id: autocharge_type.id},
                effects=[container_effect]).id,
            state=State.active)
        influence_tgt = Ship(self.mktype(attrs={self.tgt_attr.id: 10}).id)
        self.fit.ship = influence_tgt
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertAlmostEqual(influence_tgt.attrs[self.tgt_attr.id], 15)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_influence_single_item_stopped(self):
        # Autocharge should be able to modify container item even when effect
        # which defines autocharge is stopped
        autocharge_modifier = self.mkmod_filter_item(ModDomain.ship)
        autocharge_effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[autocharge_modifier])
        autocharge_type = self.mktype(
            attrs={self.src_attr.id: 50},
            effects=[autocharge_effect])
        container_effect = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={self.ammo_attr.id: autocharge_type.id},
                effects=[container_effect]).id,
            state=State.offline)
        influence_tgt = Ship(self.mktype(attrs={self.tgt_attr.id: 10}).id)
        self.fit.ship = influence_tgt
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertAlmostEqual(influence_tgt.attrs[self.tgt_attr.id], 15)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_influence_on_container(self):
        # Autocharge should be able to affect container. Civilian gun ammo does
        # this, see effect ammoInfluenceEntityFlyRange
        autocharge_modifier = self.mkmod_filter_item(ModDomain.other)
        autocharge_effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[autocharge_modifier])
        autocharge_type = self.mktype(
            attrs={self.src_attr.id: 50},
            effects=[autocharge_effect])
        container_effect = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={
                    self.ammo_attr.id: autocharge_type.id,
                    self.tgt_attr.id: 10},
                effects=[container_effect]).id,
            state=State.active)
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertAlmostEqual(container_item.attrs[self.tgt_attr.id], 15)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_influence_from_container(self):
        # Container should be able to affect autocharge. So far I've seen no
        # effects which do this, but it makes sense.
        autocharge_type = self.mktype(attrs={self.tgt_attr.id: 10})
        container_modifier = self.mkmod_filter_item(ModDomain.other)
        container_effect_modifier = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[container_modifier])
        container_effect_autocharge = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={
                    self.ammo_attr.id: autocharge_type.id,
                    self.src_attr.id: 50},
                effects=[
                    container_effect_modifier,
                    container_effect_autocharge]).id,
            state=State.active)
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertIn(
            container_effect_autocharge.id, container_item.autocharges)
        autocharge_item = (
            container_item.autocharges[container_effect_autocharge.id])
        self.assertAlmostEqual(autocharge_item.attrs[self.tgt_attr.id], 15)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_influence_from_container_with_charge(self):
        # Container should be able to affect all charges, both normal and auto,
        # at the same time
        autocharge_type = self.mktype(attrs={self.tgt_attr.id: 10})
        charge_item = Charge(self.mktype(attrs={self.tgt_attr.id: 20}).id)
        container_modifier = self.mkmod_filter_item(ModDomain.other)
        container_effect_modifier = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[container_modifier])
        container_effect_autocharge = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={
                    self.ammo_attr.id: autocharge_type.id,
                    self.src_attr.id: 50},
                effects=[
                    container_effect_modifier,
                    container_effect_autocharge]).id,
            charge=charge_item,
            state=State.active)
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertIn(
            container_effect_autocharge.id, container_item.autocharges)
        autocharge_item = (
            container_item.autocharges[container_effect_autocharge.id])
        self.assertAlmostEqual(autocharge_item.attrs[self.tgt_attr.id], 15)
        self.assertAlmostEqual(charge_item.attrs[self.tgt_attr.id], 30)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_no_influence_to_charge(self):
        # Autocharge shouldn't be able to affect charge
        autocharge_modifier = self.mkmod_filter_item(ModDomain.other)
        autocharge_effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[autocharge_modifier])
        autocharge_type = self.mktype(
            attrs={self.src_attr.id: 50},
            effects=[autocharge_effect])
        charge_item = Charge(self.mktype(attrs={self.tgt_attr.id: 10}).id)
        container_effect = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={self.ammo_attr.id: autocharge_type.id},
                effects=[container_effect]).id,
            charge=charge_item,
            state=State.active)
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertAlmostEqual(charge_item.attrs[self.tgt_attr.id], 10)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)

    def test_no_influence_from_charge(self):
        # Charge shouldn't be able to affect autocharge
        autocharge_type = self.mktype(attrs={self.tgt_attr.id: 10})
        charge_modifier = self.mkmod_filter_item(ModDomain.other)
        charge_effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[charge_modifier])
        charge_item = Charge(self.mktype(
            attrs={self.src_attr.id: 50},
            effects=[charge_effect]).id)
        container_effect = self.mkeffect(
            effect_id=EffectId.tgt_attack,
            category_id=EffectCategoryId.target,
            customize=True)
        container_item = ModuleHigh(
            self.mktype(
                attrs={self.ammo_attr.id: autocharge_type.id},
                effects=[container_effect]).id,
            charge=charge_item,
            state=State.active)
        # Action
        self.fit.modules.high.append(container_item)
        # Verification
        self.assertIn(container_effect.id, container_item.autocharges)
        autocharge_item = container_item.autocharges[container_effect.id]
        self.assertAlmostEqual(autocharge_item.attrs[self.tgt_attr.id], 10)
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
        self.assertEqual(len(self.get_log()), 0)
