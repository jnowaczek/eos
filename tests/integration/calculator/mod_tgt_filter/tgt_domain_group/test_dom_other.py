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


import logging

from eos import *
from eos.const.eos import ModDomain, ModOperator, ModTgtFilter
from eos.const.eve import EffectCategoryId
from tests.integration.calculator.calculator_testcase import CalculatorTestCase


class TestTgtDomainGroupDomainOther(CalculatorTestCase):

    def test_error(self):
        tgt_attr = self.mkattr()
        src_attr = self.mkattr()
        modifier = self.mkmod(
            tgt_filter=ModTgtFilter.domain_group,
            tgt_domain=ModDomain.other,
            tgt_filter_extra_arg=35,
            tgt_attr_id=tgt_attr.id,
            operator=ModOperator.post_percent,
            src_attr_id=src_attr.id)
        effect = self.mkeffect(
            category_id=EffectCategoryId.passive,
            modifiers=[modifier])
        influence_src_type = self.mktype(
            attrs={src_attr.id: 20},
            effects=[effect])
        influence_src = Rig(influence_src_type.id)
        # Action
        # Charge's container or module's charge can't be 'owner'of other items,
        # thus such modification type is unsupported
        self.fit.rigs.add(influence_src)
        # Verification
        log = self.get_log()
        self.assertEqual(len(log), 2)
        for log_record in log:
            self.assertEqual(log_record.name, 'eos.fit.calculator.register')
            self.assertEqual(log_record.levelno, logging.WARNING)
            self.assertEqual(
                log_record.msg,
                'malformed modifier on item type {}: unsupported target '
                'domain {}'.format(influence_src_type.id, ModDomain.other))
        # Cleanup
        self.assert_fit_buffers_empty(self.fit)
