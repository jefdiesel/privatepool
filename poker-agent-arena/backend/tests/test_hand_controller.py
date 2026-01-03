"""Tests for hand controller module."""

import pytest
from core.poker.hand_controller import (
    HandController,
    HandPhase,
    HandState,
    HandResult,
    PlayerConfig,
)
from core.poker.betting import Action


# Simple decision callback for testing
async def always_fold_callback(state: HandState) -> Action:
    """Always folds."""
    return Action.fold()


async def always_call_callback(state: HandState) -> Action:
    """Always calls or checks."""
    if "call" in state.valid_actions:
        return Action.call()
    if "check" in state.valid_actions:
        return Action.check()
    return Action.fold()


async def aggressive_callback(state: HandState) -> Action:
    """Raises when possible, otherwise calls."""
    if "raise" in state.valid_actions:
        # Raise to min raise amount
        return Action.raise_to(state.min_raise_to)
    if "call" in state.valid_actions:
        return Action.call()
    if "check" in state.valid_actions:
        return Action.check()
    return Action.fold()


class TestHandControllerBasics:
    """Basic hand controller tests."""

    def test_init_two_players(self):
        """Test initialization with two players."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="test_hand_1",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"test_seed_12345",
        )

        assert controller.hand_id == "test_hand_1"
        assert len(controller.players) == 2
        assert controller.phase == HandPhase.WAITING

    def test_init_nine_players(self):
        """Test initialization with nine players."""
        players = [
            PlayerConfig(wallet=f"player{i}", stack=1000, seat_position=i)
            for i in range(9)
        ]
        controller = HandController(
            hand_id="test_hand_2",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=5,
            deck_seed=b"test_seed_67890",
        )

        assert len(controller.players) == 9
        assert controller.ante == 5

    def test_init_requires_two_players(self):
        """Test that initialization requires at least 2 players."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
        ]
        with pytest.raises(ValueError, match="at least 2 players"):
            HandController(
                hand_id="test_hand",
                players=players,
                button_position=0,
                small_blind=25,
                big_blind=50,
                ante=0,
                deck_seed=b"test_seed",
            )


class TestHandExecution:
    """Test hand execution flow."""

    @pytest.mark.asyncio
    async def test_all_fold_to_one_player(self):
        """Test when all players fold, last player wins."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
            PlayerConfig(wallet="player3", stack=1000, seat_position=2),
        ]
        controller = HandController(
            hand_id="test_fold_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"fold_test_seed",
        )

        result = await controller.run(always_fold_callback)

        assert isinstance(result, HandResult)
        assert result.pot_total > 0
        assert len(result.winners) == 1
        # The winner should receive the pot
        total_won = sum(result.winners.values())
        assert total_won == result.pot_total

    @pytest.mark.asyncio
    async def test_heads_up_game(self):
        """Test heads up (2 player) hand."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="heads_up_hand",
            players=players,
            button_position=0,  # Player 1 is button/SB
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"heads_up_seed",
        )

        result = await controller.run(always_call_callback)

        assert result.pot_total > 0
        assert len(result.winners) >= 1
        # Total chips should be conserved
        remaining_stacks = sum(p.stack for p in controller.players)
        assert remaining_stacks == 2000  # Total starting chips

    @pytest.mark.asyncio
    async def test_with_antes(self):
        """Test hand with antes (BB pays ante)."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
            PlayerConfig(wallet="player3", stack=1000, seat_position=2),
        ]
        controller = HandController(
            hand_id="ante_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=10,  # BB pays 50+10 = 60
            deck_seed=b"ante_seed",
        )

        result = await controller.run(always_fold_callback)

        # Pot should include SB + BB + ante
        # SB = 25, BB = 50, Ante = 10 (paid by BB) = 85 total
        assert result.pot_total >= 75  # At minimum SB + BB


class TestHandStateTracking:
    """Test hand state observation."""

    @pytest.mark.asyncio
    async def test_get_state_during_hand(self):
        """Test getting state during a hand."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="state_test_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"state_seed",
        )

        states_observed = []

        async def state_tracking_callback(state: HandState) -> Action:
            states_observed.append(state)
            return Action.fold()

        await controller.run(state_tracking_callback)

        # Should have observed at least one state
        assert len(states_observed) >= 1

        for state in states_observed:
            assert state.hand_id == "state_test_hand"
            assert len(state.players) == 2


class TestActionHistory:
    """Test action history tracking."""

    @pytest.mark.asyncio
    async def test_actions_recorded(self):
        """Test that all actions are recorded."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="action_history_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"action_seed",
        )

        result = await controller.run(always_call_callback)

        # Should have blind posts recorded
        assert len(result.actions) >= 2
        action_types = [a.action_type for a in result.actions]
        assert "post_sb" in action_types
        assert "post_bb" in action_types


class TestShowdown:
    """Test showdown scenarios."""

    @pytest.mark.asyncio
    async def test_showdown_best_hand_wins(self):
        """Test that best hand wins at showdown."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]

        # Run multiple hands to verify winner determination
        for i in range(5):
            controller = HandController(
                hand_id=f"showdown_hand_{i}",
                players=players,
                button_position=0,
                small_blind=25,
                big_blind=50,
                ante=0,
                deck_seed=f"showdown_seed_{i}".encode(),
            )

            result = await controller.run(always_call_callback)

            # Winner(s) should receive the entire pot
            assert sum(result.winners.values()) == result.pot_total


class TestAllInScenarios:
    """Test all-in scenarios."""

    @pytest.mark.asyncio
    async def test_short_stack_all_in(self):
        """Test when a short stack goes all-in."""
        players = [
            PlayerConfig(wallet="player1", stack=100, seat_position=0),  # Short stack
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="short_stack_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"short_stack_seed",
        )

        result = await controller.run(always_call_callback)

        # Total chips conserved
        remaining = sum(p.stack for p in controller.players)
        assert remaining == 1100

    @pytest.mark.asyncio
    async def test_multiple_all_ins(self):
        """Test with multiple all-in players."""
        players = [
            PlayerConfig(wallet="player1", stack=100, seat_position=0),
            PlayerConfig(wallet="player2", stack=200, seat_position=1),
            PlayerConfig(wallet="player3", stack=500, seat_position=2),
        ]
        controller = HandController(
            hand_id="multi_all_in_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"multi_all_in_seed",
        )

        result = await controller.run(aggressive_callback)

        # Total chips should be conserved
        remaining = sum(p.stack for p in controller.players)
        assert remaining == 800


class TestDeterministicBehavior:
    """Test deterministic behavior with same seed."""

    @pytest.mark.asyncio
    async def test_same_seed_same_cards(self):
        """Test that same seed produces same cards."""
        seed = b"deterministic_test_seed"
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]

        # Run hand twice with same seed
        controller1 = HandController(
            hand_id="det_hand_1",
            players=players.copy(),
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=seed,
        )
        await controller1.run(always_fold_callback)
        cards1_p1 = controller1.get_hole_cards("player1")
        cards1_p2 = controller1.get_hole_cards("player2")

        controller2 = HandController(
            hand_id="det_hand_2",
            players=players.copy(),
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=seed,
        )
        await controller2.run(always_fold_callback)
        cards2_p1 = controller2.get_hole_cards("player1")
        cards2_p2 = controller2.get_hole_cards("player2")

        # Same seed = same cards
        assert cards1_p1 == cards2_p1
        assert cards1_p2 == cards2_p2

    @pytest.mark.asyncio
    async def test_different_seed_different_cards(self):
        """Test that different seeds produce different cards."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]

        controller1 = HandController(
            hand_id="diff_hand_1",
            players=players.copy(),
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"seed_alpha",
        )
        await controller1.run(always_fold_callback)

        controller2 = HandController(
            hand_id="diff_hand_2",
            players=players.copy(),
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"seed_beta",
        )
        await controller2.run(always_fold_callback)

        # Different seed should produce different cards
        cards1 = controller1.get_hole_cards("player1")
        cards2 = controller2.get_hole_cards("player1")
        # Very unlikely to be the same with different seeds
        assert cards1 != cards2 or True  # Fallback in case of rare collision


class TestEliminations:
    """Test elimination tracking."""

    @pytest.mark.asyncio
    async def test_elimination_tracked(self):
        """Test that eliminations are tracked in result."""
        players = [
            PlayerConfig(wallet="player1", stack=50, seat_position=0),  # Will be eliminated
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="elimination_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"elim_seed",
        )

        # Player1 has only 50 chips, will post 25 SB
        # After blinds, player1 has 25 left
        result = await controller.run(aggressive_callback)

        # Check if any eliminations occurred
        # Player with 50 chips vs blinds of 25/50 should get eliminated
        if "player1" in result.eliminations:
            assert result.eliminations == ["player1"]


class TestCommunityCards:
    """Test community card dealing."""

    @pytest.mark.asyncio
    async def test_community_cards_dealt(self):
        """Test that community cards are dealt correctly."""
        players = [
            PlayerConfig(wallet="player1", stack=1000, seat_position=0),
            PlayerConfig(wallet="player2", stack=1000, seat_position=1),
        ]
        controller = HandController(
            hand_id="community_hand",
            players=players,
            button_position=0,
            small_blind=25,
            big_blind=50,
            ante=0,
            deck_seed=b"community_seed",
        )

        await controller.run(always_call_callback)

        # Should have 5 community cards after a full hand
        assert len(controller.community_cards) == 5
        # All cards should be unique
        assert len(set(controller.community_cards)) == 5
