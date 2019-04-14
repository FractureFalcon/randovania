import dataclasses
from unittest.mock import MagicMock, patch

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutElevators
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.resolver import base_patches_factory


def test_add_elevator_connections_to_patches_vanilla(echoes_game_data):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    permalink = Permalink.default()

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(permalink, GamePatches.with_game(game))

    # Assert
    assert result == GamePatches.with_game(game)


def test_add_elevator_connections_to_patches_random(echoes_game_data):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    permalink = dataclasses.replace(
        Permalink.default(),
        layout_configuration=dataclasses.replace(LayoutConfiguration.default(),
                                                 elevators=LayoutElevators.RANDOMIZED))
    expected = dataclasses.replace(GamePatches.with_game(game),
                                   elevator_connection={
                                       589851: AreaLocation(1039999561, 3479543630),
                                       1572998: AreaLocation(464164546, 3528156989),
                                       1966093: AreaLocation(1039999561, 1868895730),
                                       2097251: AreaLocation(1119434212, 2806956034),
                                       136970379: AreaLocation(2252328306, 2068511343),
                                       3342446: AreaLocation(2252328306, 2399252740),
                                       3538975: AreaLocation(2252328306, 408633584),
                                       152: AreaLocation(1006255871, 1345979968),
                                       393260: AreaLocation(1119434212, 3331021649),
                                       524321: AreaLocation(1006255871, 3455543403),
                                       589949: AreaLocation(1006255871, 2278776548),
                                       122: AreaLocation(464164546, 900285955),
                                       1245307: AreaLocation(1006255871, 1287880522),
                                       2949235: AreaLocation(2252328306, 2556480432),
                                       129: AreaLocation(1006255871, 2889020216),
                                       2162826: AreaLocation(1006255871, 2918020398),
                                       4522032: AreaLocation(464164546, 3145160350),
                                       38: AreaLocation(1006255871, 1660916974),
                                       1245332: AreaLocation(1119434212, 1473133138),
                                       1638535: AreaLocation(1039999561, 3205424168),
                                   })

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(permalink, GamePatches.with_game(game))

    # Assert
    assert result == expected


def test_gate_assignment_for_configuration_all_emerald(echoes_resource_database):
    # Setup
    emerald = find_resource_info_with_long_name(echoes_resource_database.item, "Emerald Translator")
    indices = [1, 15, 23]

    configuration = MagicMock()
    configuration.translator_configuration.translator_requirement = {
        TranslatorGate(index): LayoutTranslatorRequirement.EMERALD
        for index in indices
    }

    rng = MagicMock()

    # Run
    results = base_patches_factory.gate_assignment_for_configuration(configuration, echoes_resource_database, rng)

    # Assert
    assert results == {
        TranslatorGate(index): emerald
        for index in indices
    }


def test_gate_assignment_for_configuration_all_random(echoes_resource_database):
    # Setup
    violet = find_resource_info_with_long_name(echoes_resource_database.item, "Violet Translator")
    emerald = find_resource_info_with_long_name(echoes_resource_database.item, "Emerald Translator")

    configuration = MagicMock()
    configuration.translator_configuration.translator_requirement = {
        TranslatorGate(index): LayoutTranslatorRequirement.RANDOM
        for index in [1, 15, 23]
    }

    rng = MagicMock()
    rng.choice.side_effect = [
        LayoutTranslatorRequirement.EMERALD,
        LayoutTranslatorRequirement.VIOLET,
        LayoutTranslatorRequirement.EMERALD,
    ]

    # Run
    results = base_patches_factory.gate_assignment_for_configuration(configuration, echoes_resource_database, rng)

    # Assert
    assert results == {
        TranslatorGate(1): emerald,
        TranslatorGate(15): violet,
        TranslatorGate(23): emerald,
    }


def test_starting_location_for_configuration_ship():
    # Setup
    configuration = MagicMock()
    configuration.starting_location.configuration = StartingLocationConfiguration.SHIP
    game = MagicMock()
    rng = MagicMock()

    # Run
    result = base_patches_factory.starting_location_for_configuration(configuration, game, rng)

    # Assert
    assert result is game.starting_location


def test_starting_location_for_configuration_custom():
    # Setup
    configuration = MagicMock()
    configuration.starting_location.configuration = StartingLocationConfiguration.CUSTOM
    game = MagicMock()
    rng = MagicMock()

    # Run
    result = base_patches_factory.starting_location_for_configuration(configuration, game, rng)

    # Assert
    assert result is configuration.starting_location.custom_location


def test_starting_location_for_configuration_random_save_station():
    # Setup
    configuration = MagicMock()
    configuration.starting_location.configuration = StartingLocationConfiguration.RANDOM_SAVE_STATION
    game = MagicMock()
    save_1 = MagicMock()
    save_1.name = "Save Station"
    save_2 = MagicMock()
    save_2.name = "Save Station"
    game.world_list.all_nodes = [save_1, save_2, MagicMock()]
    rng = MagicMock()

    # Run
    result = base_patches_factory.starting_location_for_configuration(configuration, game, rng)

    # Assert
    rng.choice.assert_called_once_with([save_1, save_2])
    game.world_list.node_to_area_location.assert_called_once_with(rng.choice.return_value)
    assert result is game.world_list.node_to_area_location.return_value


@patch("randovania.resolver.base_patches_factory.starting_location_for_configuration", autospec=True)
@patch("randovania.resolver.base_patches_factory.gate_assignment_for_configuration", autospec=True)
@patch("randovania.resolver.base_patches_factory.add_elevator_connections_to_patches", autospec=True)
@patch("randovania.resolver.generator.GamePatches.with_game")
def test_create_base_patches(mock_with_game: MagicMock,
                             mock_add_elevator_connections_to_patches: MagicMock,
                             mock_gate_assignment_for_configuration: MagicMock,
                             mock_starting_location_for_config: MagicMock,
                             ):
    # Setup
    rng = MagicMock()
    game = MagicMock()
    permalink = MagicMock()

    first_patches = mock_with_game.return_value
    second_patches = mock_add_elevator_connections_to_patches.return_value
    third_patches = second_patches.assign_gate_assignment.return_value

    # Run
    result = base_patches_factory.create_base_patches(rng, game, permalink)

    # Assert
    mock_with_game.assert_called_once_with(game)
    mock_add_elevator_connections_to_patches.assert_called_once_with(permalink, first_patches)

    # Gate Assignment
    mock_gate_assignment_for_configuration.assert_called_once_with(
        permalink.layout_configuration, game.resource_database, rng)
    second_patches.assign_gate_assignment.assert_called_once_with(mock_gate_assignment_for_configuration.return_value)

    # Starting Location
    mock_starting_location_for_config.assert_called_once_with(permalink.layout_configuration, game, rng)
    third_patches.assign_starting_location.assert_called_once_with(mock_starting_location_for_config.return_value)

    assert result is third_patches.assign_starting_location.return_value
