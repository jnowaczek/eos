# ==============================================================================
# Copyright (C) 2011 Diego Duclos
# Copyright (C) 2011-2018 Anton Vorobyov
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


from eos.util.keyed_storage import KeyedStorage


class ProjectionRegister:
    """Keeps track of various projection-related connections."""

    def __init__(self):
        # Format: {projectors}
        self.__projectors = set()

        # Projectors residing on solar system item
        # Format: {carrier item: {projectors}}
        self.__carrier_projectors = KeyedStorage()

        # Projectors whose carrying solar system item is not present
        # Format: {projectors}
        self.__carrierless_projectors = set()

        # Solar system items affected by projector
        # Format: {projector: {target items}}
        self.__projector_targets = KeyedStorage()

        # Projectors affecting solar system item
        # Format: {target item: {projectors}}
        self.__target_projectors = KeyedStorage()

    def get_projector_tgts(self, projector):
        return self.__projector_targets.get(projector, ())

    def get_tgt_projectors(self, tgt_item):
        return self.__target_projectors.get(tgt_item, ())

    def get_carrier_projectors(self, carrier_item):
        return self.__carrier_projectors.get(carrier_item, ())

    def get_projectors(self):
        return self.__projectors

    def register_projector(self, projector):
        self.__projectors.add(projector)

    def unregister_projector(self, projector):
        self.__projectors.discard(projector)

    def apply_projector(self, projector, tgt_items):
        self.__projector_targets.add_data_set(projector, tgt_items)
        for tgt_item in tgt_items:
            self.__target_projectors.add_data_entry(tgt_item, projector)
        solsys_carrier_item = projector.carrier_item._solsys_carrier
        self.__carrier_projectors.add_data_entry(solsys_carrier_item, projector)

    def unapply_projector(self, projector, tgt_items):
        self.__projector_targets.rm_data_set(projector, tgt_items)
        for tgt_item in tgt_items:
            self.__target_projectors.rm_data_entry(tgt_item, projector)
        solsys_carrier_item = projector.carrier_item._solsys_carrier
        self.__carrier_projectors.rm_data_entry(solsys_carrier_item, projector)

    def register_solsys_item(self, solsys_item):
        pass

    def unregister_solsys_item(self, solsys_item):
        pass