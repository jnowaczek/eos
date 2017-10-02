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


from eos.util.frozen_dict import FrozenDict
from .cleaner import Cleaner
from .converter import Converter
from .normalizer import Normalizer
from .validator_preclean import ValidatorPreCleanup
from .validator_preconvert import ValidatorPreConversion


class CachableBuilder:
    """Builds Eos-specific cachable objects from passed data."""

    @staticmethod
    def run(data_handler):
        """Run cache building process.

        Use data provided by passed cache handler to compose various objects
        with the help of which eos will oeprate. As building process is quite
        complex and can take time, objects are cachable, and are intended to be
        cached later,

        Args:
            data_handler: data handler instance, which should provide access
                to raw eve data.

        Returns:
            Tuple with 3 dictionaries, which contain types, attributes and
            effects, keyed against their representative IDs.
        """
        # Put all the data we need into single dictionary Format, as usual,
        # {table name: table}, where table is set of rows, which are
        # represented by frozendicts {fieldName: fieldValue}. Combination of
        # sets and frozendicts is used to speed up several stages of the
        # builder.
        data = {}
        tables = {
            'evetypes': data_handler.get_evetypes,
            'evegroups': data_handler.get_evegroups,
            'dgmattribs': data_handler.get_dgmattribs,
            'dgmtypeattribs': data_handler.get_dgmtypeattribs,
            'dgmeffects': data_handler.get_dgmeffects,
            'dgmtypeeffects': data_handler.get_dgmtypeeffects,
            'dgmexpressions': data_handler.get_dgmexpressions,
            'typefighterabils': data_handler.get_typefighterabils
        }

        for tablename, method in tables.items():
            table_pos = 0
            table = set()
            for row in method():
                # During further builder stages. some of rows may fall in risk
                # groups, where all rows but one need to be removed. To
                # deterministically remove rows based on position in original
                # data, write position to each row
                row['table_pos'] = table_pos
                table_pos += 1
                table.add(FrozenDict(row))
            data[tablename] = table

        # Run pre-cleanup checks, as cleanup stage and further stages rely on
        # some assumptions about the data
        ValidatorPreCleanup.run(data)

        # Normalize the data to make data structure more consistent, making it
        # easier to clean properly
        Normalizer.run(data)

        # Remove unwanted data
        Cleaner().clean(data)

        # Verify that our data is ready for conversion
        ValidatorPreConversion.run(data)

        # Convert data into Eos-specific objects, stored in several
        # dictionaries, with object IDs being dictionary keys
        types, attributes, effects = Converter.run(data)

        return types, attributes, effects