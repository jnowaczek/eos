#===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2012 Anton Vorobyov
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
#===============================================================================


from eos.const import State, Location, Context, RunTime, Operator, SourceType
from eos.eve.attribute import Attribute
from eos.eve.const import EffectCategory
from eos.eve.effect import Effect
from eos.eve.type import Type
from eos.fit.attributeCalculator.info.info import Info
from eos.tests.attributeCalculator.environment import Logger, Fit, IndependentItem
from eos.tests.eosTestCase import EosTestCase


class TestSourceValueNone(EosTestCase):
    """Test how calculator reacts to source attribute which is set to None"""

    def setUp(self):
        EosTestCase.setUp(self)
        self.tgtAttr = tgtAttr = Attribute(1)
        self.srcAttr = srcAttr = Attribute(2)
        self.invalidInfo = invalidInfo = Info()
        invalidInfo.state = State.offline
        invalidInfo.context = Context.local
        invalidInfo.runTime = RunTime.duration
        invalidInfo.gang = False
        invalidInfo.location = Location.self_
        invalidInfo.filterType = None
        invalidInfo.filterValue = None
        invalidInfo.operator = Operator.postPercent
        invalidInfo.targetAttributeId = tgtAttr.id
        invalidInfo.sourceType = SourceType.value
        invalidInfo.sourceValue = None
        self.effect = Effect(None, EffectCategory.passive)
        self.fit = Fit({tgtAttr.id: tgtAttr, srcAttr.id: srcAttr})

    def testLog(self):
        self.effect._infos = (self.invalidInfo,)
        holder = IndependentItem(Type(529, effects=(self.effect,), attributes={self.srcAttr.id: 20, self.tgtAttr.id: 100}))
        self.fit._addHolder(holder)
        self.assertAlmostEqual(holder.attributes[self.tgtAttr.id], 100)
        self.assertEqual(len(self.log), 1)
        logRecord = self.log[0]
        self.assertEqual(logRecord.name, "eos_test.attributeCalculator")
        self.assertEqual(logRecord.levelno, Logger.WARNING)
        self.assertEqual(logRecord.msg, "malformed source value None on item 529")

    def testCombination(self):
        validInfo = Info()
        validInfo.state = State.offline
        validInfo.context = Context.local
        validInfo.runTime = RunTime.duration
        validInfo.gang = False
        validInfo.location = Location.self_
        validInfo.filterType = None
        validInfo.filterValue = None
        validInfo.operator = Operator.postMul
        validInfo.targetAttributeId = self.tgtAttr.id
        validInfo.sourceType = SourceType.attribute
        validInfo.sourceValue = self.srcAttr.id
        self.effect._infos = (self.invalidInfo, validInfo)
        holder = IndependentItem(Type(None, effects=(self.effect,), attributes={self.srcAttr.id: 1.5, self.tgtAttr.id: 100}))
        self.fit._addHolder(holder)
        # Invalid source value shouldn't screw whole calculation process
        self.assertNotAlmostEqual(holder.attributes[self.tgtAttr.id], 100)
