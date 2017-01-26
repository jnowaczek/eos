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


from logging import getLogger

from eos.const.eos import ModifierType, ModifierDomain, EosEveTypes
from eos.util.keyed_set import KeyedSet
from ..exception import DirectDomainError, FilteredDomainError, FilteredSelfReferenceError, ModifierTypeError


logger = getLogger(__name__)


class DogmaRegister:
    """
    Keep track of connections between Affector objects and affectee
    holders, only for connections defined as regular modifiers. Having
    this data is hard requirement for efficient partial attribute
    recalculation.

    Required arguments:
    fit -- fit, to which this register is bound to
    """

    def __init__(self, fit):
        self._fit = fit

        # Holders belonging to certain domain
        # Format: {domain: set(target holders)}
        self.__affectee_domain = KeyedSet()

        # Holders belonging to certain domain and group
        # Format: {(domain, group): set(target holders)}
        self.__affectee_domain_group = KeyedSet()

        # Holders belonging to certain domain and having certain skill requirement
        # Format: {(domain, skill): set(target holders)}
        self.__affectee_domain_skillrq = KeyedSet()

        # Owner-modifiable holders which have certain skill requirement
        # Format: {skill: set(target holders)}
        self.__affectee_owner_skillrq = KeyedSet()

        # Affectors influencing holders directly
        # Format: {target holder: set(affectors)}
        self.__affector_direct_active = KeyedSet()

        # Affectors which influence something directly, but their target is not available
        # Format: {source holder: set(affectors)}
        self.__affector_direct_awaiting = KeyedSet()

        # Affectors influencing all holders belonging to certain domain
        # Format: {domain: set(affectors)}
        self.__affector_domain = KeyedSet()

        # Affectors influencing holders belonging to certain domain and group
        # Format: {(domain, group): set(affectors)}
        self.__affector_domain_group = KeyedSet()

        # Affectors influencing holders belonging to certain domain and having certain skill requirement
        # Format: {(domain, skill): set(affectors)}
        self.__affector_domain_skillrq = KeyedSet()

        # Affectors influencing owner-modifiable holders which have certain skill requirement
        # Format: {skill: set(affectors)}
        self.__affector_owner_skillrq = KeyedSet()

    def register_affectee(self, target_holder):
        """
        Add passed target holder to register's maps, so it can be affected by
        other holders properly.

        Required arguments:
        target_holder -- holder to register
        """
        for key, affectee_map in self.__get_affectee_maps(target_holder):
            # Add data to map
            affectee_map.add_data(key, target_holder)
        # Check if we have affectors which should directly influence passed holder,
        # but are disabled; enable them if there're any
        enable_direct = self.__get_holder_direct_domain(target_holder)
        if enable_direct is None:
            return
        if enable_direct == ModifierDomain.other:
            self.__enable_direct_other(target_holder)
        elif enable_direct in (ModifierDomain.character, ModifierDomain.ship):
            self.__enable_direct_spec(target_holder, enable_direct)

    def unregister_affectee(self, target_holder):
        """
        Remove passed target holder from register's maps, so holders affecting
        it "know" that its modification is no longer needed.

        Required arguments:
        target_holder -- holder to unregister
        """
        for key, affectee_map in self.__get_affectee_maps(target_holder):
            affectee_map.rm_data(key, target_holder)
        # When removing holder from register, make sure to move modifiers which
        # originate from 'other' holders and directly affect it to disabled map
        disable_direct = self.__get_holder_direct_domain(target_holder)
        if disable_direct is None:
            return
        if disable_direct == ModifierDomain.other:
            self.__disable_direct_other(target_holder)
        elif disable_direct in (ModifierDomain.character, ModifierDomain.ship):
            self.__disable_direct_spec(target_holder)

    def register_affector(self, affector):
        """
        Add passed affector to register's affector maps, so that new holders
        added to fit know that they should be affected by it.

        Required arguments:
        affector -- affector to register
        """
        try:
            key, affector_map = self.__get_affector_map(affector)
            # Actually add data to map
            affector_map.add_data(key, affector)
        except Exception as e:
            self.__handle_affector_errors(e, affector)

    def unregister_affector(self, affector):
        """
        Remove passed affector from register's affector maps, so that
        holders-affectees "know" that they're no longer affected by it.

        Required arguments:
        affector -- affector to unregister
        """
        try:
            key, affector_map = self.__get_affector_map(affector)
            affector_map.rm_data(key, affector)
        # Following block handles exceptions; all of them must be handled
        # when registering affector too
        except Exception as e:
            self.__handle_affector_errors(e, affector)

    def get_affectees(self, affector):
        """
        Get all holders influenced by passed affector.

        Required arguments:
        affector -- affector, for which we're seeking for affectees

        Return value:
        Set with holders, being influenced by affector
        """
        source_holder, modifier = affector
        affectees = set()
        try:
            # For direct modification, make set out of single target domain
            if modifier.type == ModifierType.item:
                if modifier.domain == ModifierDomain.self:
                    target = {source_holder}
                elif modifier.domain == ModifierDomain.character:
                    char = self._fit.character
                    target = {char} if char is not None else None
                elif modifier.domain == ModifierDomain.ship:
                    ship = self._fit.ship
                    target = {ship} if ship is not None else None
                elif modifier.domain == ModifierDomain.other:
                    other_holder = self.__get_other_linked_holder(source_holder)
                    target = {other_holder} if other_holder is not None else None
                else:
                    raise DirectDomainError(modifier.domain)
            # For filtered modifications, pick appropriate dictionary and get set
            # with target holders
            elif modifier.type == ModifierType.domain:
                key = self.__contextize_filter_domain(affector)
                target = self.__affectee_domain.get(key) or set()
            elif modifier.type == ModifierType.domain_group:
                domain = self.__contextize_filter_domain(affector)
                group = modifier.extra_arg
                key = (domain, group)
                target = self.__affectee_domain_group.get(key) or set()
            elif modifier.type == ModifierType.domain_skillrq:
                domain = self.__contextize_filter_domain(affector)
                skill = modifier.extra_arg
                if skill == EosEveTypes.current_self:
                    skill = affector.source_holder._eve_type_id
                key = (domain, skill)
                target = self.__affectee_domain_skillrq.get(key) or set()
            elif modifier.type == ModifierType.owner_skillrq:
                skill = modifier.extra_arg
                if skill == EosEveTypes.current_self:
                    skill = affector.source_holder._eve_type_id
                key = skill
                target = self.__affectee_owner_skillrq.get(key) or set()
            else:
                raise ModifierTypeError(modifier.type)
            # Add our set to affectees
            if target is not None:
                affectees.update(target)
        except Exception as e:
            self.__handle_affector_errors(e, affector)
        return affectees

    def get_affectors(self, target_holder):
        """
        Get all affectors, which influence passed holder.

        Required arguments:
        target_holder -- holder, for which we're seeking for affecting it
        affectors

        Return value:
        Set with affectors, incluencing target_holder
        """
        affectors = set()
        # Add all affectors which directly affect it
        affectors.update(self.__affector_direct_active.get(target_holder) or set())
        # Then all affectors which affect domain of passed holder
        domain = target_holder._domain
        affectors.update(self.__affector_domain.get(domain) or set())
        # All affectors which affect domain and group of passed holder
        group = target_holder._eve_type.group
        affectors.update(self.__affector_domain_group.get((domain, group)) or set())
        # Same, but for domain & skill requirement of passed holder
        for skill in target_holder._eve_type.required_skills:
            affectors.update(self.__affector_domain_skillrq.get((domain, skill)) or set())
            if target_holder._owner_modifiable is True:
                affectors.update(self.__affector_owner_skillrq.get(skill) or set())
        return affectors

    # General-purpose auxiliary methods
    def __get_affectee_maps(self, target_holder):
        """
        Helper for affectee register/unregister methods.

        Required arguments:
        target_holder -- holder, for which affectee maps are requested

        Return value:
        List of (key, affecteeMap) tuples, where key should be used to access
        data set (appropriate to passed target_holder) in affecteeMap
        """
        # Container which temporarily holds (key, map) tuples
        affectee_maps = []
        domain = target_holder._domain
        if domain is not None:
            affectee_maps.append((domain, self.__affectee_domain))
            group = target_holder._eve_type.group
            if group is not None:
                affectee_maps.append(((domain, group), self.__affectee_domain_group))
            for skill in target_holder._eve_type.required_skills:
                affectee_maps.append(((domain, skill), self.__affectee_domain_skillrq))
        if target_holder._owner_modifiable:
            for skill in target_holder._eve_type.required_skills:
                affectee_maps.append((skill, self.__affectee_owner_skillrq))
        return affectee_maps

    def __get_affector_map(self, affector):
        """
        Helper for affector register/unregister methods.

        Required arguments:
        affector -- affector, for which affector map are requested

        Return value:
        (key, affector_map) tuple, where key should be used to access
        data set (appropriate to passed affector) in affector_map

        Possible exceptions:
        FilteredSelfReferenceError -- raised if affector's modifier specifies
        filtered modification and target domain refers self, but affector's
        holder isn't in position to be target for filtered modifications
        DirectDomainError -- raised when affector's modifier target
        domain is not supported for direct modification
        FilteredDomainError -- raised when affector's modifier target
        domain is not supported for filtered modification
        ModifierTypeError -- raised when affector's modifier filter type is not
        supported
        """
        source_holder, modifier = affector
        # For each filter type, define affector map and key to use
        if modifier.type == ModifierType.item:
            # For direct modifications, we need to properly pick
            # target holder (it's key) based on domain
            if modifier.domain == ModifierDomain.self:
                affector_map = self.__affector_direct_active
                key = source_holder
            elif modifier.domain == ModifierDomain.character:
                char = self._fit.character
                if char is not None:
                    affector_map = self.__affector_direct_active
                    key = char
                else:
                    affector_map = self.__affector_direct_awaiting
                    key = source_holder
            elif modifier.domain == ModifierDomain.ship:
                ship = self._fit.ship
                if ship is not None:
                    affector_map = self.__affector_direct_active
                    key = ship
                else:
                    affector_map = self.__affector_direct_awaiting
                    key = source_holder
            # When other domain is referenced, it means direct reference to module's charge
            # or to charge's module-container
            elif modifier.domain == ModifierDomain.other:
                other_holder = self.__get_other_linked_holder(source_holder)
                if other_holder is not None:
                    affector_map = self.__affector_direct_active
                    key = other_holder
                # When no reference available, it means that e.g. charge may be
                # unavailable for now; use disabled affectors map for these
                else:
                    affector_map = self.__affector_direct_awaiting
                    key = source_holder
            else:
                raise DirectDomainError(modifier.domain)
        # For filtered modifications, compose key, making sure reference to self
        # is converted into appropriate real domain
        elif modifier.type == ModifierType.domain:
            affector_map = self.__affector_domain
            domain = self.__contextize_filter_domain(affector)
            key = domain
        elif modifier.type == ModifierType.domain_group:
            affector_map = self.__affector_domain_group
            domain = self.__contextize_filter_domain(affector)
            group = modifier.extra_arg
            key = (domain, group)
        elif modifier.type == ModifierType.domain_skillrq:
            affector_map = self.__affector_domain_skillrq
            domain = self.__contextize_filter_domain(affector)
            skill = modifier.extra_arg
            if skill == EosEveTypes.current_self:
                skill = affector.source_holder._eve_type_id
            key = (domain, skill)
        elif modifier.type == ModifierType.owner_skillrq:
            affector_map = self.__affector_owner_skillrq
            skill = modifier.extra_arg
            if skill == EosEveTypes.current_self:
                skill = affector.source_holder._eve_type_id
            key = skill
        else:
            raise ModifierTypeError(modifier.type)
        return key, affector_map

    def __handle_affector_errors(self, error, affector):
        """
        Multiple register methods which get data based on passed affector
        raise similar exception classes. To handle them in consistent fashion,
        it is done from centralized place - this method. If error cannot be
        handled by method, it is re-raised.

        Required arguments:
        error -- Exception instance which was caught and needs to be handled
        affector -- affector object, which was being processed when error occurred
        """
        if isinstance(error, DirectDomainError):
            msg = 'malformed modifier on EVE type {}: unsupported target domain {} for direct modification'.format(
                affector.source_holder._eve_type_id, error.args[0])
            logger.warning(msg)
        elif isinstance(error, FilteredDomainError):
            msg = 'malformed modifier on EVE type {}: unsupported target domain {} for filtered modification'.format(
                affector.source_holder._eve_type_id, error.args[0])
            logger.warning(msg)
        elif isinstance(error, FilteredSelfReferenceError):
            msg = 'malformed modifier on EVE type {}: invalid reference to self for filtered modification'.format(
                affector.source_holder._eve_type_id)
            logger.warning(msg)
        elif isinstance(error, ModifierTypeError):
            msg = 'malformed modifier on EVE type {}: invalid filter type {}'.format(
                affector.source_holder._eve_type_id, error.args[0])
            logger.warning(msg)
        else:
            raise error

    # Methods which help to process filtered modifications
    def __contextize_filter_domain(self, affector):
        """
        Convert domain self-reference to real domain, like
        character or ship. Used only in modifications of multiple
        filtered holders, direct modifications are processed out
        of the context of this method.

        Required arguments:
        affector -- affector, whose modifier refers domain in question

        Return value:
        Real contextized domain

        Possible exceptions:
        FilteredSelfReferenceError -- raised if affector's modifier
        refers self, but affector's holder isn't in position to be
        target for filtered modifications
        FilteredDomainError -- raised when affector's modifier
        target domain is not supported for filtered modification
        """
        source_holder = affector.source_holder
        domain = affector.modifier.domain
        # Reference to self is sparingly used in ship effects, so we must convert
        # it to real domain
        if domain == ModifierDomain.self:
            if source_holder is self._fit.ship:
                return ModifierDomain.ship
            elif source_holder is self._fit.character:
                return ModifierDomain.character
            else:
                raise FilteredSelfReferenceError
        # Just return untouched domain for all other valid cases
        elif domain in (ModifierDomain.character, ModifierDomain.ship):
            return domain
        # Raise error if domain is invalid
        else:
            raise FilteredDomainError(domain)

    # Methods which help to process direct modifications
    def __get_holder_direct_domain(self, holder):
        """
        Get domain which you need to target to apply
        direct modification to passed holder.

        Required arguments:
        holder -- holder in question

        Return value:
        Domain specification, if holder can be targeted directly
        from the outside, or None if it can't
        """
        # For ship and character it's easy, we're just picking
        # corresponding domain
        if holder is self._fit.ship:
            domain = ModifierDomain.ship
        elif holder is self._fit.character:
            domain = ModifierDomain.character
        # For "other" domain, we should've checked for presence
        # of other entity - charge's container or module's charge
        elif self.__get_other_linked_holder(holder) is not None:
            domain = ModifierDomain.other
        else:
            domain = None
        return domain

    def __enable_direct_spec(self, target_holder, domain):
        """
        Enable temporarily disabled affectors, directly targeting holder in
        specific domain.

        Required arguments:
        target_holder -- holder which is being registered
        domain -- domain, to which holder is being registered
        """
        # Format: {source_holder: [affectors]}
        affectors_to_enable = {}
        # Cycle through all disabled direct affectors
        for source_holder, affector_set in self.__affector_direct_awaiting.items():
            for affector in affector_set:
                modifier = affector.modifier
                # Mark affector as to-be-enabled only when it
                # targets passed target domain
                if modifier.domain == domain:
                    source_affectors = affectors_to_enable.setdefault(source_holder, [])
                    source_affectors.append(affector)
        # Bail if we have nothing to do
        if not affectors_to_enable:
            return
        # Move all of them to direct modification dictionary
        for source_holder, affectors in affectors_to_enable.items():
            self.__affector_direct_awaiting.rm_data_set(source_holder, affectors)
            self.__affector_direct_active.add_data_set(target_holder, affectors)

    def __disable_direct_spec(self, target_holder):
        """
        Disable affectors, directly targeting holder in specific domain.

        Required arguments:
        target_holder -- holder which is being unregistered
        """
        # Format: {source_holder: [affectors]}
        affectors_to_disable = {}
        # Check all affectors, targeting passed holder
        for affector in self.__affector_direct_active.get(target_holder) or ():
            # Mark them as to-be-disabled only if they originate from
            # other holder, else they should be removed with passed holder
            if affector.source_holder is not target_holder:
                source_affectors = affectors_to_disable.setdefault(affector.source_holder, [])
                source_affectors.append(affector)
        if not affectors_to_disable:
            return
        # Move data from map to map
        for source_holder, affectors in affectors_to_disable.items():
            self.__affector_direct_active.rm_data_set(target_holder, affectors)
            self.__affector_direct_awaiting.add_data_set(source_holder, affectors)

    def __enable_direct_other(self, target_holder):
        """
        Enable temporarily disabled affectors, directly targeting passed holder,
        originating from holder in "other" domain.

        Required arguments:
        target_holder -- holder which is being registered
        """
        other_holder = self.__get_other_linked_holder(target_holder)
        # If passed holder doesn't have other domain (charge's module
        # or module's charge), do nothing
        if other_holder is None:
            return
        # Get all disabled affectors which should influence our target_holder
        affectors_to_enable = set()
        for affector in self.__affector_direct_awaiting.get(other_holder) or ():
            modifier = affector.modifier
            if modifier.domain == ModifierDomain.other:
                affectors_to_enable.add(affector)
        # Bail if we have nothing to do
        if not affectors_to_enable:
            return
        # Move all of them to direct modification dictionary
        self.__affector_direct_active.add_data_set(target_holder, affectors_to_enable)
        self.__affector_direct_awaiting.rm_data_set(other_holder, affectors_to_enable)

    def __disable_direct_other(self, target_holder):
        """
        Disable affectors, directly targeting passed holder, originating from
        holder in "other" domain.

        Required arguments:
        target_holder -- holder which is being unregistered
        """
        other_holder = self.__get_other_linked_holder(target_holder)
        if other_holder is None:
            return
        affectors_to_disable = set()
        # Go through all affectors influencing holder being unregistered
        for affector in self.__affector_direct_active.get(target_holder) or ():
            # If affector originates from other_holder, mark it as
            # to-be-disabled
            if affector.source_holder is other_holder:
                affectors_to_disable.add(affector)
        # Do nothing if we have no such affectors
        if not affectors_to_disable:
            return
        # If we have, move them from map to map
        self.__affector_direct_awaiting.add_data_set(other_holder, affectors_to_disable)
        self.__affector_direct_active.rm_data_set(target_holder, affectors_to_disable)

    def __get_other_linked_holder(self, holder):
        """
        Attempt to get holder linked via 'other' link,
        like charge's module or module's charge, return
        None if nothing is found.
        """
        if hasattr(holder, 'charge'):
            return holder.charge
        elif hasattr(holder, 'container'):
            return holder.container
        else:
            return None
