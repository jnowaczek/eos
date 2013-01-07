#===============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2013 Anton Vorobyov
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


from eos.tests.cacheUpdater.updaterTestCase import UpdaterTestCase


class TestConversionAttribute(UpdaterTestCase):
    """
    Appropriate data should be saved into appropriate
    indexes of object representing attribute.
    """

    def testFields(self):
        self.dh.data['invtypes'].append({'typeID': 1, 'groupID': 1})
        self.dh.data['dgmtypeattribs'].append({'typeID': 1, 'attributeID': 111, 'value': 8.2})
        self.dh.data['dgmattribs'].append({'maxAttributeID': 84, 'randomField': None, 'stackable': True, 'defaultValue': 0.0, 'attributeID': 111, 'highIsGood': False})
        data = self.updater.run(self.dh)
        self.assertEqual(len(self.log), 0)
        self.assertEqual(len(data['attributes']), 1)
        self.assertIn(111, data['attributes'])
        self.assertEqual(data['attributes'][111], (84, 0.0, False, True))
