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


__all__ = [
    'CalibrationStatRegister',
    'CpuStatRegister',
    'DmgDealerRegister',
    'DroneBandwidthStatRegister',
    'DronebayVolumeStatRegister',
    'HighSlotStatRegister',
    'LaunchedDroneStatRegister',
    'LauncherSlotStatRegister',
    'LowSlotStatRegister',
    'MediumSlotStatRegister',
    'PowergridStatRegister',
    'RigSlotStatRegister',
    'SubsystemSlotStatRegister',
    'TurretSlotStatRegister'
]


from .dmg_dealer import DmgDealerRegister
from .resource import CalibrationStatRegister
from .resource import CpuStatRegister
from .resource import DroneBandwidthStatRegister
from .resource import DronebayVolumeStatRegister
from .resource import PowergridStatRegister
from .slot import HighSlotStatRegister
from .slot import LaunchedDroneStatRegister
from .slot import LauncherSlotStatRegister
from .slot import LowSlotStatRegister
from .slot import MediumSlotStatRegister
from .slot import RigSlotStatRegister
from .slot import SubsystemSlotStatRegister
from .slot import TurretSlotStatRegister
