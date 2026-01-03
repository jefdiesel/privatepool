"""Tests for game_state_formatter module."""

import pytest

from ..game_state_formatter import format_game_state, _get_position_labels
from ...poker.hand_controller import HandState, HandPhase


class TestGetPositionLabels:
    """Tests for position label generation."""

    def test_heads_up_positions(self):
        """Heads up should have BTN and BB."""
        labels = _get_position_labels(2)
        assert labels == ["BTN", "BB"]

    def test_three_player_positions(self):
        """3 players should have BTN, SB, BB."""
        labels = _get_position_labels(3)
        assert labels == ["BTN", "SB", "BB"]

    def test_six_player_positions(self):
        """6 players should have full 6-max positions."""
        labels = _get_position_labels(6)
        assert "UTG" in labels
        assert "BTN" in labels
        assert "BB" in labels
        assert len(labels) == 6

    def test_nine_player_positions(self):
        """9 players should have full 9-max positions."""
        labels = _get_position_labels(9)
        assert "UTG" in labels
        assert "UTG+1" in labels
        assert "HJ" in labels
        assert "CO" in labels
        assert "BTN" in labels
        assert len(labels) == 9


class TestFormatGameState:
    """Tests for game state formatting."""

    @pytest.fixture
    def basic_hand_state(self) -> HandState:
        """Create a basic hand state for testing."""
        return HandState(
            hand_id="test_hand_1",
            phase=HandPhase.FLOP,
            pot=450,
            community_cards=["Ah", "Kd", "7c"],
            current_bet=150,
            action_on="wallet_1",
            players=[
                {
                    "wallet": "wallet_1",
                    "stack": 4850,
                    "current_bet": 0,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 3,
                },
                {
                    "wallet": "wallet_2",
                    "stack": 5100,
                    "current_bet": 150,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 1,
                },
                {
                    "wallet": "wallet_3",
                    "stack": 2800,
                    "current_bet": 150,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 2,
                },
            ],
            valid_actions=["fold", "call", "raise"],
            min_raise_to=300,
        )

    def test_format_includes_hand_header(self, basic_hand_state):
        """Format should include hand number and phase."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
            hand_number=1847,
        )

        assert "HAND #1847" in result
        assert "FLOP" in result
        assert "Pot: 450" in result

    def test_format_includes_board(self, basic_hand_state):
        """Format should include community cards."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "Board:" in result
        assert "Ah" in result
        assert "Kd" in result
        assert "7c" in result

    def test_format_includes_hole_cards(self, basic_hand_state):
        """Format should include player's hole cards."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "Your Cards: Qs Qd" in result

    def test_format_includes_player_position(self, basic_hand_state):
        """Format should include player's position."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "Your Position:" in result

    def test_format_includes_player_stack(self, basic_hand_state):
        """Format should include player's stack."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "Your Stack: 4,850" in result

    def test_format_includes_all_players(self, basic_hand_state):
        """Format should list all players."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "Players:" in result
        assert "YOU" in result
        assert "(to act)" in result

    def test_format_includes_to_call(self, basic_hand_state):
        """Format should show amount to call."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "To Call: 150" in result

    def test_format_shows_folded_players(self, basic_hand_state):
        """Format should indicate folded players."""
        basic_hand_state.players[1]["is_active"] = False

        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "(folded)" in result

    def test_format_shows_all_in_players(self, basic_hand_state):
        """Format should indicate all-in players."""
        basic_hand_state.players[2]["is_all_in"] = True

        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert "(all-in)" in result

    def test_format_shows_ante(self, basic_hand_state):
        """Format should show ante for BB."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
            ante=25,
        )

        assert "posted ante:" in result

    def test_format_ends_with_action_prompt(self, basic_hand_state):
        """Format should end with action prompt."""
        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
        )

        assert result.strip().endswith("Your Action?")

    def test_format_preflop_no_board(self):
        """Preflop format should not show board."""
        hand_state = HandState(
            hand_id="test_hand_1",
            phase=HandPhase.PREFLOP,
            pot=75,
            community_cards=[],
            current_bet=50,
            action_on="wallet_1",
            players=[
                {
                    "wallet": "wallet_1",
                    "stack": 4950,
                    "current_bet": 0,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 0,
                },
                {
                    "wallet": "wallet_2",
                    "stack": 4950,
                    "current_bet": 50,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 1,
                },
            ],
            valid_actions=["fold", "call", "raise"],
            min_raise_to=100,
        )

        result = format_game_state(
            hand_state=hand_state,
            player_wallet="wallet_1",
            hole_cards=["As", "Ks"],
            button_seat=0,
        )

        assert "PREFLOP" in result
        assert "Board:" not in result

    def test_format_with_action_history(self, basic_hand_state):
        """Format should include action history when provided."""
        action_history = [
            {"player_wallet": "wallet_1", "phase": "PREFLOP", "action_type": "raise", "amount": 100},
            {"player_wallet": "wallet_2", "phase": "PREFLOP", "action_type": "call", "amount": 100},
        ]

        result = format_game_state(
            hand_state=basic_hand_state,
            player_wallet="wallet_1",
            hole_cards=["Qs", "Qd"],
            button_seat=3,
            action_history=action_history,
        )

        assert "Action History" in result

    def test_player_not_found_raises_error(self, basic_hand_state):
        """Should raise error if player not in hand state."""
        with pytest.raises(ValueError):
            format_game_state(
                hand_state=basic_hand_state,
                player_wallet="unknown_wallet",
                hole_cards=["Qs", "Qd"],
                button_seat=3,
            )
