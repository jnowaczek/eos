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


from collections import namedtuple

from eos.const.eos import Restriction
from eos.const.eve import AttributeId
from eos.fit.item import ModuleHigh, ModuleLow, ModuleMed, Ship
from eos.fit.pubsub.message import InstrItemAdd, InstrItemRemove
from .base import BaseRestrictionRegister
from ..exception import RestrictionValidationError


TRACKED_ITEM_CLASSES = (ModuleHigh, ModuleMed, ModuleLow)
# Containers for attribute IDs which are used to restrict fitting
TYPE_RESTRICTION_ATTRS = (
    AttributeId.can_fit_ship_type_1,
    AttributeId.can_fit_ship_type_2,
    AttributeId.can_fit_ship_type_3,
    AttributeId.can_fit_ship_type_4,
    AttributeId.can_fit_ship_type_5,
    AttributeId.can_fit_ship_type_6,
    AttributeId.can_fit_ship_type_7,
    AttributeId.can_fit_ship_type_8,
    AttributeId.can_fit_ship_type_9,
    AttributeId.can_fit_ship_type_10,
    AttributeId.fits_to_shiptype)
GROUP_RESTRICTION_ATTRS = (
    AttributeId.can_fit_ship_group_1,
    AttributeId.can_fit_ship_group_2,
    AttributeId.can_fit_ship_group_3,
    AttributeId.can_fit_ship_group_4,
    AttributeId.can_fit_ship_group_5,
    AttributeId.can_fit_ship_group_6,
    AttributeId.can_fit_ship_group_7,
    AttributeId.can_fit_ship_group_8,
    AttributeId.can_fit_ship_group_9,
    AttributeId.can_fit_ship_group_10,
    AttributeId.can_fit_ship_group_11,
    AttributeId.can_fit_ship_group_12,
    AttributeId.can_fit_ship_group_13,
    AttributeId.can_fit_ship_group_14,
    AttributeId.can_fit_ship_group_15,
    AttributeId.can_fit_ship_group_16,
    AttributeId.can_fit_ship_group_17,
    AttributeId.can_fit_ship_group_18,
    AttributeId.can_fit_ship_group_19,
    AttributeId.can_fit_ship_group_20)


ShipTypeGroupErrorData = namedtuple(
    'ShipTypeGroupErrorData',
    ('ship_type', 'ship_group', 'allowed_types', 'allowed_groups'))


# Helper class-container for metadata regarding allowed types and groups
AllowedData = namedtuple('AllowedData', ('types', 'groups'))


class ShipTypeGroupRestrictionRegister(BaseRestrictionRegister):
    """Make sure that item fits only to ships it can be fitted to.

    Item can specify which ships are suitable via ship group or ship type.

    Details:
        Only modules  are restricted.
        It's enough to satisfy any of conditions to make item usable (e.g.
            ship's group may not satisfy canFitShipGroupX restriction, but its
            type may be suitable to use item).
        If item has at least one restriction attribute, it is enabled for
            tracking by this register.
        For validation, canFitShipTypeX and canFitShipGroupX attribute values of
            eve type are taken.
    """

    def __init__(self, msg_broker):
        self.__current_ship = None
        # Container for items which possess ship type/group restriction
        # Format: {item: allowed data}
        self.__restricted_items = {}
        msg_broker._subscribe(self, self._handler_map.keys())

    def _handle_item_addition(self, message):
        if isinstance(message.item, Ship):
            self.__current_ship = message.item
        elif not isinstance(message.item, TRACKED_ITEM_CLASSES):
            return
        # Containers for type IDs and group IDs of ships, to which item is
        # allowed to fit
        allowed_types = set()
        allowed_groups = set()
        for allowed_container, restriction_attrs in (
            (allowed_types, TYPE_RESTRICTION_ATTRS),
            (allowed_groups, GROUP_RESTRICTION_ATTRS)
        ):
            # Cycle through IDs of known restriction attributes
            for restriction_attr in restriction_attrs:
                try:
                    restriction_value = (
                        message.item._eve_type_attributes[restriction_attr])
                except KeyError:
                    continue
                else:
                    allowed_container.add(restriction_value)
        # Ignore non-restricted items
        if not allowed_types and not allowed_groups:
            return
        # Finally, register items which made it into here
        self.__restricted_items[message.item] = AllowedData(
            types=tuple(allowed_types),
            groups=tuple(allowed_groups))

    def _handle_item_removal(self, message):
        if message.item is self.__current_ship:
            self.__current_ship = None
        elif message.item in self.__restricted_items:
            del self.__restricted_items[message.item]

    _handler_map = {
        InstrItemAdd: _handle_item_addition,
        InstrItemRemove: _handle_item_removal}

    def validate(self):
        # Get type ID and group ID of ship, if no ship available, assume they're
        # None; it's safe to set them to None because our primary data container
        # with restricted items can't contain None in its values anyway
        try:
            ship_type_id = self.__current_ship._eve_type_id
            ship_group = self.__current_ship._eve_type.group
        except AttributeError:
            ship_type_id = None
            ship_group = None
        # Container for tainted items
        tainted_items = {}
        # Go through all known restricted items
        for item in self.__restricted_items:
            allowed_data = self.__restricted_items[item]
            # If ship's type isn't in allowed types and ship's group isn't in
            # allowed groups, item is tainted
            if (
                ship_type_id not in allowed_data.types and
                ship_group not in allowed_data.groups
            ):
                tainted_items[item] = ShipTypeGroupErrorData(
                    ship_type=ship_type_id,
                    ship_group=ship_group,
                    allowed_types=allowed_data.types,
                    allowed_groups=allowed_data.groups)
        # Raise error if there're any tainted items
        if tainted_items:
            raise RestrictionValidationError(tainted_items)

    @property
    def type(self):
        return Restriction.ship_type_group
