"""Tests for action_parser module."""

import pytest

from ..action_parser import parse_response, _extract_json, ActionParseError
from ...poker.hand_controller import HandState, HandPhase
from ...poker.betting import Action


class TestExtractJson:
    """Tests for JSON extraction from response text."""

    def test_extract_pure_json(self):
        """Should extract pure JSON."""
        text = '{"action": "fold"}'
        result = _extract_json(text)
        assert result == {"action": "fold"}

    def test_extract_json_with_whitespace(self):
        """Should handle whitespace around JSON."""
        text = '  {"action": "call"}  '
        result = _extract_json(text)
        assert result == {"action": "call"}

    def test_extract_json_with_text_before(self):
        """Should extract JSON with text before."""
        text = 'I will fold. {"action": "fold"}'
        result = _extract_json(text)
        assert result == {"action": "fold"}

    def test_extract_json_with_text_after(self):
        """Should extract JSON with text after."""
        text = '{"action": "call"} This is a call.'
        result = _extract_json(text)
        assert result == {"action": "call"}

    def test_extract_json_with_amount(self):
        """Should extract JSON with amount."""
        text = '{"action": "raise", "amount": 150}'
        result = _extract_json(text)
        assert result == {"action": "raise", "amount": 150}

    def test_extract_invalid_json_returns_none(self):
        """Should return None for invalid JSON."""
        text = "Just some text without JSON"
        result = _extract_json(text)
        assert result is None

    def test_extract_json_without_action_returns_none(self):
        """Should return None for JSON without action key."""
        text = '{"value": 123}'
        result = _extract_json(text)
        assert result is None


class TestParseResponse:
    """Tests for parse_response function."""

    @pytest.fixture
    def hand_state(self) -> HandState:
        """Create a basic hand state for testing."""
        return HandState(
            hand_id="test_hand",
            phase=HandPhase.FLOP,
            pot=300,
            community_cards=["Ah", "Kd", "7c"],
            current_bet=100,
            action_on="wallet_1",
            players=[
                {
                    "wallet": "wallet_1",
                    "stack": 1000,
                    "current_bet": 50,
                    "is_active": True,
                    "is_all_in": False,
                    "seat_position": 0,
                },
            ],
            valid_actions=["fold", "call", "raise"],
            min_raise_to=200,
        )

    def test_parse_fold(self, hand_state):
        """Should parse fold action."""
        response = '{"action": "fold"}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "fold"

    def test_parse_check_when_valid(self, hand_state):
        """Should parse check when no bet to call."""
        hand_state.current_bet = 50  # Equal to player's current bet
        response = '{"action": "check"}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "check"

    def test_parse_check_converts_to_call_when_invalid(self, hand_state):
        """Should convert check to call when there's a bet."""
        response = '{"action": "check"}'
        action = parse_response(response, hand_state, "wallet_1")
        # Can't check when current_bet (100) > player_bet (50)
        # Should convert to call since player can afford it
        assert action.action_type == "call"

    def test_parse_call(self, hand_state):
        """Should parse call action."""
        response = '{"action": "call"}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "call"

    def test_parse_call_converts_to_check_when_no_bet(self, hand_state):
        """Should convert call to check when nothing to call."""
        hand_state.current_bet = 50  # Equal to player's bet
        response = '{"action": "call"}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "check"

    def test_parse_raise_with_valid_amount(self, hand_state):
        """Should parse raise with valid amount."""
        response = '{"action": "raise", "amount": 250}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "raise"
        assert action.amount == 250

    def test_parse_bet_normalizes_to_raise(self, hand_state):
        """Should normalize 'bet' to 'raise'."""
        response = '{"action": "bet", "amount": 250}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "raise"
        assert action.amount == 250

    def test_parse_raise_clamps_to_min(self, hand_state):
        """Should clamp raise below min to min_raise_to."""
        response = '{"action": "raise", "amount": 120}'  # Below min_raise_to of 200
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "raise"
        assert action.amount == 200  # Clamped to min

    def test_parse_raise_allows_all_in(self, hand_state):
        """Should allow all-in even below min raise."""
        hand_state.players[0]["stack"] = 100  # Small stack
        response = '{"action": "raise", "amount": 200}'  # Would require more than stack
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "raise"
        # All-in should be total available: stack + current_bet
        assert action.amount == 150  # 100 stack + 50 current_bet

    def test_parse_invalid_action_falls_back(self, hand_state):
        """Should fall back on invalid action type."""
        response = '{"action": "allin"}'  # Invalid action
        action = parse_response(response, hand_state, "wallet_1")
        # Should fall back to fold since there's a bet to call
        assert action.action_type == "fold"

    def test_parse_invalid_json_falls_back(self, hand_state):
        """Should fall back on invalid JSON."""
        response = "Just some text"
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "fold"

    def test_parse_empty_response_falls_back(self, hand_state):
        """Should fall back on empty response."""
        response = ""
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "fold"

    def test_fallback_check_when_possible(self, hand_state):
        """Should fall back to check when no bet to call."""
        hand_state.current_bet = 50  # Equal to player's bet
        response = "invalid"
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "check"

    def test_parse_raise_without_amount_uses_min(self, hand_state):
        """Should use min raise when amount not specified."""
        response = '{"action": "raise"}'
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "raise"
        assert action.amount == 200  # min_raise_to

    def test_parse_raise_with_invalid_amount_falls_back(self, hand_state):
        """Should fall back when amount is invalid."""
        response = '{"action": "raise", "amount": "big"}'
        action = parse_response(response, hand_state, "wallet_1")
        # Invalid amount falls back to conservative action
        assert action.action_type == "fold"

    def test_player_not_found_raises_error(self, hand_state):
        """Should raise error if player not in hand state."""
        response = '{"action": "fold"}'
        with pytest.raises(ActionParseError):
            parse_response(response, hand_state, "unknown_wallet")

    def test_parse_json_embedded_in_explanation(self, hand_state):
        """Should parse JSON from explanatory response."""
        response = '''Looking at the board, I have a strong hand.
        I will raise to apply pressure.
        {"action": "raise", "amount": 300}'''
        action = parse_response(response, hand_state, "wallet_1")
        assert action.action_type == "raise"
        assert action.amount == 300
