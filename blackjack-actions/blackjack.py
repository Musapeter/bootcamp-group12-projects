# blackjack.py


RANK_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11,
}


def hand_value(cards):
    """
    Compute the best total for a hand, counting Aces as 11 or 1.

  
    Sum values with every Ace = 11, count Aces, and while total > 21
          lower an Ace from 11 to 1 (subtract 10) until safe or no Aces left.
    
    """
    total = sum(RANK_VALUES[card] for card in cards)
    aces = cards.count("A")
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def parse_state(text):
    """
    Parse a decision-point string into a dict with hand, dealer, first, total, busted.

    
    Split on '|', parse the hand by commas, normalize the 'first' flag, compute total.
    
    """
    parts = [part.strip() for part in text.split("|")]
    if len(parts) != 3:
        raise ValueError("Expected format 'card1,card2[,...] | dealer_upcard | first|later'")
    hand_str, dealer_upcard, flag = parts
    hand = [rank.strip() for rank in hand_str.split(",") if rank.strip() != ""]
    dealer = dealer_upcard.strip()
    flag_clean = flag.strip().lower()
    if flag_clean not in ("first", "later"):
        raise ValueError("Last field must be 'first' or 'later'")
    first = (flag_clean == "first")
    total = hand_value(hand)
    busted = total > 21
    return {"hand": hand, "dealer": dealer, "first": first, "total": total, "busted": busted}


def generate_actions(state):
    """
    Return legal action names for the given state.

    
    Always include 'hit' and 'stand'. If state['first'] add 'double' and 'surrender'.
          If dealer == 'A' add 'insurance'. If hand length == 2 and hand[0] == hand[1] add 'split'.
    
    """
    actions = ["hit", "stand"]
    if state.get("first"):
        actions.append("double")
        actions.append("surrender")
        if state.get("dealer") == "A":
            actions.append("insurance")
        hand = state.get("hand", [])
        if len(hand) == 2 and hand[0] == hand[1]:
            actions.append("split")
    return actions


def apply_action(state, action, next_card=None):
    """
    Apply an action and return the resulting state(s).

    
    Teen: Provide next_card for draw actions. Returns one state dict or a tuple of two for split.
    
    """
    action = action.lower()

    def make_state_from_hand(hand_list, dealer=state.get("dealer"), first=False, extra=None):
        if extra is None:
            extra = {}
        total = hand_value(hand_list)
        base = {"hand": list(hand_list), "dealer": dealer, "first": first, "total": total, "busted": total > 21}
        base.update(extra)
        return base

    if action == "hit":
        if not next_card:
            raise ValueError("Hit action requires next_card argument (the drawn card).")
        return make_state_from_hand(list(state["hand"]) + [next_card], dealer=state["dealer"], first=False)

    if action == "double":
        if not state.get("first"):
            raise ValueError("Double action only allowed on the first decision.")
        if not next_card:
            raise ValueError("Double action requires next_card argument (the drawn card).")
        return make_state_from_hand(list(state["hand"]) + [next_card], dealer=state["dealer"], first=False, extra={"doubled": True, "stood": True})

    if action == "stand":
        return make_state_from_hand(state["hand"], dealer=state["dealer"], first=False, extra={"stood": True})

    if action == "surrender":
        if not state.get("first"):
            raise ValueError("Surrender action only allowed on the first decision.")
        return make_state_from_hand(state["hand"], dealer=state["dealer"], first=False, extra={"surrendered": True})

    if action == "insurance":
        if not state.get("first"):
            raise ValueError("Insurance only allowed on the first decision.")
        if state.get("dealer") != "A":
            raise ValueError("Insurance only allowed if dealer upcard is Ace.")
        return make_state_from_hand(state["hand"], dealer=state["dealer"], first=True, extra={"insurance_taken": True})

    if action == "split":
        hand = state.get("hand", [])
        if not state.get("first"):
            raise ValueError("Split only allowed on the first decision.")
        if len(hand) != 2 or hand[0] != hand[1]:
            raise ValueError("Split only allowed when the first two cards have the same rank string.")
        hand_a = make_state_from_hand([hand[0]], dealer=state["dealer"], first=True)
        hand_b = make_state_from_hand([hand[1]], dealer=state["dealer"], first=True)
        return hand_a, hand_b

    raise ValueError(f"Unknown action: {action}")



import unittest


class TestBlackjackActions(unittest.TestCase):
    def test_hit_and_stand_always_legal(self):
        state = parse_state("10,6 | 9 | later")
        actions = generate_actions(state)
        self.assertIn("hit", actions)
        self.assertIn("stand", actions)
        self.assertNotIn("double", actions)
        self.assertNotIn("surrender", actions)

    def test_double_and_surrender_only_on_first_decision(self):
        state = parse_state("10,6 | 9 | first")
        actions = generate_actions(state)
        self.assertIn("double", actions)
        self.assertIn("surrender", actions)
        self.assertNotIn("split", actions)

    def test_split_requires_matching_rank(self):
        pair_state = parse_state("8,8 | 5 | first")
        self.assertIn("split", generate_actions(pair_state))

        mismatched_state = parse_state("10,K | 5 | first")
        self.assertNotIn("split", generate_actions(mismatched_state))

    def test_insurance_only_against_ace_upcard(self):
        vs_ace = parse_state("10,9 | A | first")
        self.assertIn("insurance", generate_actions(vs_ace))

        vs_six = parse_state("10,9 | 6 | first")
        self.assertNotIn("insurance", generate_actions(vs_six))

    def test_apply_hit_can_bust(self):
        state = parse_state("10,6 | 9 | first")
        new_state = apply_action(state, "hit", next_card="K")
        self.assertEqual(new_state["total"], 26)
        self.assertTrue(new_state["busted"])

    def test_apply_split_returns_two_hands(self):
        state = parse_state("8,8 | 5 | first")
        hand_a, hand_b = apply_action(state, "split")
        self.assertEqual(hand_a["hand"], ["8"])
        self.assertEqual(hand_b["hand"], ["8"])


if __name__ == "__main__":
    unittest.main()
