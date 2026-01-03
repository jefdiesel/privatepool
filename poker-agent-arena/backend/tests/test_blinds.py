"""Tests for blind structure management."""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from core.tournament.blinds import (
    BlindLevel,
    BlindStructure,
    BLIND_TEMPLATES,
    get_blind_structure,
)


class TestBlindLevel:
    """Tests for BlindLevel dataclass."""

    def test_blind_level_creation(self):
        """Test creating a blind level."""
        level = BlindLevel(
            level=1,
            small_blind=25,
            big_blind=50,
            ante=0,
            duration_minutes=10,
        )
        assert level.level == 1
        assert level.small_blind == 25
        assert level.big_blind == 50
        assert level.ante == 0
        assert level.duration_minutes == 10

    def test_total_bb_payment_no_ante(self):
        """Test BB payment with no ante."""
        level = BlindLevel(1, 25, 50, 0, 10)
        assert level.total_bb_payment() == 50

    def test_total_bb_payment_with_ante(self):
        """Test BB payment includes ante."""
        level = BlindLevel(4, 100, 200, 25, 10)
        assert level.total_bb_payment() == 225  # 200 + 25

    def test_total_bb_payment_large_ante(self):
        """Test BB payment with larger ante."""
        level = BlindLevel(12, 1500, 3000, 375, 6)
        assert level.total_bb_payment() == 3375  # 3000 + 375


class TestBlindStructure:
    """Tests for BlindStructure class."""

    @pytest.fixture
    def turbo_structure(self):
        """Create a turbo blind structure."""
        return get_blind_structure("turbo")

    @pytest.fixture
    def simple_structure(self):
        """Create a simple 2-level structure for testing."""
        levels = [
            BlindLevel(1, 25, 50, 0, 1),  # 1 minute for fast testing
            BlindLevel(2, 50, 100, 10, 1),
        ]
        return BlindStructure(levels)

    def test_empty_levels_raises(self):
        """Test that empty levels list raises ValueError."""
        with pytest.raises(ValueError, match="at least one level"):
            BlindStructure([])

    def test_initial_state(self, turbo_structure):
        """Test initial structure state."""
        assert turbo_structure.current_level_index == 0
        assert turbo_structure.level_start_time is None
        assert turbo_structure.current_level.level == 1

    def test_current_level_property(self, turbo_structure):
        """Test current_level returns correct level."""
        assert turbo_structure.current_level.small_blind == 25
        assert turbo_structure.current_level.big_blind == 50

    def test_start_level(self, turbo_structure):
        """Test starting the level timer."""
        turbo_structure.start_level()
        assert turbo_structure.level_start_time is not None
        assert isinstance(turbo_structure.level_start_time, datetime)

    def test_advance_level(self, simple_structure):
        """Test advancing to next level."""
        simple_structure.start_level()
        new_level = simple_structure.advance_level()

        assert new_level is not None
        assert new_level.level == 2
        assert simple_structure.current_level_index == 1
        assert simple_structure.current_level.small_blind == 50

    def test_advance_level_at_max(self, simple_structure):
        """Test advance_level returns None at final level."""
        simple_structure.current_level_index = 1  # At last level
        result = simple_structure.advance_level()
        assert result is None
        assert simple_structure.current_level_index == 1

    def test_is_final_level(self, simple_structure):
        """Test is_final_level check."""
        assert simple_structure.is_final_level() is False
        simple_structure.current_level_index = 1
        assert simple_structure.is_final_level() is True

    def test_time_remaining_not_started(self, simple_structure):
        """Test time_remaining when level not started."""
        # Returns full duration when not started
        assert simple_structure.time_remaining() == 60  # 1 minute in seconds

    def test_time_remaining_after_start(self, simple_structure):
        """Test time_remaining decreases after start."""
        simple_structure.start_level()
        remaining = simple_structure.time_remaining()
        assert remaining <= 60
        assert remaining > 55  # Should be close to 60

    def test_time_remaining_elapsed(self):
        """Test time_remaining after time has passed."""
        levels = [BlindLevel(1, 25, 50, 0, 1)]
        structure = BlindStructure(levels)

        # Mock datetime.now to simulate time passage
        start = datetime.now()
        with patch('core.tournament.blinds.datetime') as mock_dt:
            mock_dt.now.return_value = start
            structure.start_level()

            # Simulate 30 seconds passing
            mock_dt.now.return_value = start + timedelta(seconds=30)
            remaining = structure.time_remaining()
            assert remaining == 30

    def test_check_level_up_not_started(self, simple_structure):
        """Test check_level_up when not started."""
        assert simple_structure.check_level_up() is False

    def test_check_level_up_time_not_elapsed(self, simple_structure):
        """Test check_level_up before time expires."""
        simple_structure.start_level()
        assert simple_structure.check_level_up() is False
        assert simple_structure.current_level_index == 0

    def test_check_level_up_advances(self):
        """Test check_level_up advances when time expires."""
        levels = [
            BlindLevel(1, 25, 50, 0, 1),
            BlindLevel(2, 50, 100, 10, 1),
        ]
        structure = BlindStructure(levels)

        start = datetime.now()
        with patch('core.tournament.blinds.datetime') as mock_dt:
            mock_dt.now.return_value = start
            structure.start_level()

            # Simulate 61 seconds passing (more than 1 minute)
            mock_dt.now.return_value = start + timedelta(seconds=61)
            result = structure.check_level_up()

            assert result is True
            assert structure.current_level_index == 1

    def test_check_level_up_at_final_level(self):
        """Test check_level_up doesn't advance at final level."""
        levels = [BlindLevel(1, 25, 50, 0, 1)]
        structure = BlindStructure(levels)

        start = datetime.now()
        with patch('core.tournament.blinds.datetime') as mock_dt:
            mock_dt.now.return_value = start
            structure.start_level()

            mock_dt.now.return_value = start + timedelta(seconds=120)
            result = structure.check_level_up()

            assert result is False
            assert structure.current_level_index == 0


class TestBlindTemplates:
    """Tests for blind templates."""

    def test_turbo_template_exists(self):
        """Test turbo template is defined."""
        assert "turbo" in BLIND_TEMPLATES
        assert len(BLIND_TEMPLATES["turbo"]) == 12

    def test_standard_template_exists(self):
        """Test standard template is defined."""
        assert "standard" in BLIND_TEMPLATES
        assert len(BLIND_TEMPLATES["standard"]) == 8

    def test_deep_stack_template_exists(self):
        """Test deep_stack template is defined."""
        assert "deep_stack" in BLIND_TEMPLATES
        assert len(BLIND_TEMPLATES["deep_stack"]) == 8

    def test_turbo_has_shorter_levels(self):
        """Test turbo levels are 6 minutes."""
        for level in BLIND_TEMPLATES["turbo"]:
            assert level.duration_minutes == 6

    def test_standard_has_10_minute_levels(self):
        """Test standard levels are 10 minutes."""
        for level in BLIND_TEMPLATES["standard"]:
            assert level.duration_minutes == 10

    def test_deep_stack_has_15_minute_levels(self):
        """Test deep_stack levels are 15 minutes."""
        for level in BLIND_TEMPLATES["deep_stack"]:
            assert level.duration_minutes == 15

    def test_antes_start_at_level_4_turbo(self):
        """Test antes start at level 4 in turbo."""
        turbo = BLIND_TEMPLATES["turbo"]
        # Levels 1-3 have no ante
        for i in range(3):
            assert turbo[i].ante == 0
        # Level 4+ has ante
        assert turbo[3].ante == 25


class TestGetBlindStructure:
    """Tests for get_blind_structure function."""

    def test_get_turbo_structure(self):
        """Test getting turbo structure."""
        structure = get_blind_structure("turbo")
        assert isinstance(structure, BlindStructure)
        assert len(structure.levels) == 12

    def test_get_standard_structure(self):
        """Test getting standard structure."""
        structure = get_blind_structure("standard")
        assert isinstance(structure, BlindStructure)
        assert len(structure.levels) == 8

    def test_get_deep_stack_structure(self):
        """Test getting deep_stack structure."""
        structure = get_blind_structure("deep_stack")
        assert isinstance(structure, BlindStructure)
        assert len(structure.levels) == 8

    def test_unknown_template_raises(self):
        """Test unknown template raises ValueError."""
        with pytest.raises(ValueError, match="Unknown blind template"):
            get_blind_structure("unknown")

    def test_returned_structure_is_copy(self):
        """Test that modifying returned structure doesn't affect template."""
        structure1 = get_blind_structure("turbo")
        structure2 = get_blind_structure("turbo")

        structure1.current_level_index = 5
        assert structure2.current_level_index == 0
