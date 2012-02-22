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


from itertools import chain

from .const import nulls, Attribute, Effect, EffectCategory
from eos.const import Slot, State
from eos.override.itemEffects import additionalEffects


class Type:
    """
    Type represents any EVE item. All characters, ships,
    incursion system-wide effects are actually items.
    """

    def __init__(self, typeId, groupId=None, categoryId=None, durationAttributeId=None, dischargeAttributeId=None,
                 rangeAttributeId=None, falloffAttributeId=None, trackingSpeedAttributeId=None, fittableNonSingleton=None,
                 attributes={}, effects=()):
        # The ID of the type
        self.id = int(typeId) if typeId is not None else None

        # The groupID of the type, integer
        self.groupId = int(groupId) if not groupId in nulls else None

        # The category ID of the type, integer
        self.categoryId = int(categoryId) if not categoryId in nulls else None

        # Defines cycle time
        self._durationAttributeId = int(durationAttributeId) if not durationAttributeId in nulls else None

        # Defines attribute, whose value will be used to drain ship's
        # capacitor each cycle
        self._dischargeAttributeId = int(dischargeAttributeId) if not dischargeAttributeId in nulls else None

        # Attribute with this ID defines optimal range of item
        self._rangeAttributeId = int(rangeAttributeId) if not rangeAttributeId in nulls else None

        # Defines falloff attribute
        self._falloffAttributeId = int(falloffAttributeId) if not falloffAttributeId in nulls else None

        # Defines tracking speed attribute
        self._trackingSpeedAttributeId = int(trackingSpeedAttributeId) if not trackingSpeedAttributeId in nulls else None

        # Defines if multiple items of this type can be added to fit without packaging.
        # We use it to see if charge can be loaded into anything or not.
        self._fittableNonSingleton = bool(fittableNonSingleton) if fittableNonSingleton is not None else None

        # The attributes of this type, used as base for calculation of modified
        # attributes, thus they should stay immutable
        # Format: {attributeId: attributeValue}
        self.attributes = attributes

        # Iterable with effects this type has, they describe modifications
        # which this type applies. If there're any additional effects specified
        # in overrides, add them too
        if additionalEffects.get(self.id) is None:
            self.effects = effects
        else:
            self.effects = tuple(chain(effects, additionalEffects[self.id]))

        # Stores required skill IDs and levels as dictionary once calculated
        self.__requiredSkills = None

        # Caches results of max allowed state as integer ID
        self.__maxState = None

        # Cache targeted flag
        self.__targeted = None

        # Cached set with slot types
        self.__slots = None

    def getInfos(self, eos):
        """
        Get all infos spawned by effects.

        Positional arguments:
        eos -- something belonging in this eos instance
        requests data

        Return value:
        Set with Info objects generated by type's effects
        """
        infos = set()
        for effect in self.effects:
            for info in effect.getInfos(eos):
                infos.add(info)
        return infos

    @property
    def requiredSkills(self):
        """
        Get skill requirements.

        Return value:
        Dictionary with IDs of skills and corresponding skill levels,
        which are required to use type
        """
        if self.__requiredSkills is None:
            skillRqAttrs = {Attribute.requiredSkill1: Attribute.requiredSkill1Level,
                            Attribute.requiredSkill2: Attribute.requiredSkill2Level,
                            Attribute.requiredSkill3: Attribute.requiredSkill3Level,
                            Attribute.requiredSkill4: Attribute.requiredSkill4Level,
                            Attribute.requiredSkill5: Attribute.requiredSkill5Level,
                            Attribute.requiredSkill6: Attribute.requiredSkill6Level}
            self.__requiredSkills = {}
            for srqAttrId in skillRqAttrs:
                srq = self.attributes.get(srqAttrId)
                if srq is not None:
                    srqLvl = self.attributes.get(skillRqAttrs[srqAttrId])
                    self.__requiredSkills[int(srq)] = int(srqLvl) if srqLvl is not None else None
        return self.__requiredSkills

    @property
    def maxState(self):
        """
        Get highest state this type is allowed to take.

        Return value:
        State class' attribute value, representing highest state
        """
        if self.__maxState is None:
            # All types can be at least offline,
            # even when they have no effects
            maxState = State.offline
            for effect in self.effects:
                # Convert effect category to state
                # Format: {effect category ID: state ID}
                conversionMap = {EffectCategory.passive: State.offline,
                                 EffectCategory.active: State.active,
                                 EffectCategory.target: State.active,
                                 EffectCategory.online: State.online,
                                 EffectCategory.overload: State.overload,
                                 EffectCategory.system: State.offline}
                state = conversionMap[effect.categoryId]
                maxState = max(maxState, state)
            self.__maxState = maxState
        return self.__maxState

    @property
    def isTargeted(self):
        """
        Report if type is targeted or not. Targeted types cannot be
        activated w/o target selection.

        Return value:
        Boolean targeted flag
        """
        if self.__targeted is None:
            # Assume type is not targeted by default
            targeted = False
            for effect in self.effects:
                # If any of effects is targeted, then type is targeted
                if effect.categoryId == EffectCategory.target:
                    targeted = True
            self.__targeted = targeted
        return self.__targeted

    @property
    def slots(self):
        """
        Get types of slots this type occupies.

        Return value:
        Set with slot types
        """
        if self.__slots is None:
            # Container for slot types item uses
            slots = set()
            for effect in self.effects:
                # Convert effect ID to slot type item takes
                # Format: {effect ID: slot ID}
                conversionMap = {Effect.loPower: Slot.moduleLow,
                                 Effect.hiPower: Slot.moduleHigh,
                                 Effect.medPower: Slot.moduleMed,
                                 Effect.launcherFitted: Slot.launcher,
                                 Effect.turretFitted: Slot.turret,
                                 Effect.rigSlot: Slot.rig,
                                 Effect.subSystem: Slot.subsystem}
                try:
                    slot = conversionMap[effect.id]
                # Silently skip effect if it's not in map
                except KeyError:
                    pass
                else:
                    slots.add(slot)
            self.__slots = slots
        return self.__slots
