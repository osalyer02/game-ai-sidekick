import time
import json

from pathlib import Path

from classes.GameState import GameState, Status
from classes.LetterCell import Feedback
from constants import LLM_MODEL, MAX_LLM_CONTINUOUS_CALLS

LOG_DIR = Path("benchmarks/gemini_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

NUM_RUNS = 1


# Modify run_game to append per-game stats
def run_game(game: GameState, run_id: int, total_tries: int, total_success: int, total_bad_guesses: int, total_latency: float, results_dict=None):
    print(f"Starting run {run_id + 1}")
    game.reset()
    total_completion = 0
    completion = 0
    game_start_time = time.time()


    while game.status != Status.end:
        game.enter_word_from_ai()
        
        if game.ai_strikeout:
            print("AI failed to guess a valid word within 10 attempts. Ending game.")
            break
        
        if game.ai_timeout:
            print("AI request timed out. Ending game.")
            break
        # get the feedback
        offset = 0 if game.status == Status.end else 1
        feedback = game.words[game.current_word_index - offset].get_feedback()

        # check completion
        completion = 0
        for fdb in feedback:
            match fdb:
                case Feedback.incorrect:
                    completion += 0
                case Feedback.present:
                    completion += 0.5
                case Feedback.correct:
                    completion += 1

        if game.was_valid_guess:
            total_completion += completion
        else:
            total_bad_guesses += 1

    game_end_time = time.time()
    game_latency = game_end_time - game_start_time
    total_latency += game_latency

    avg_game_completion = total_completion / game.num_of_tries() if game.num_of_tries() > 0 else 0
    total_success += 1 if game.success else 0
    total_tries += game.num_of_tries()


    print(f"Average game completion: {avg_game_completion} / 5")
    print(f"Average tries: {total_tries / (run_id + 1)}")
    print(f"Average success: {total_success / (run_id + 1)}")
    print(f"Average latency: {total_latency / (run_id + 1):.2f}s")
    print(f"Total bad guesses: {total_bad_guesses}")
    print()
   
    if results_dict is not None:
        results_dict["games"].append({
            "run_id": run_id + 1,
            "average_game_completion": avg_game_completion,
            "tries": game.num_of_tries(),
            "success": game.success,
            "latency": game_latency,
            "bad_guesses": total_bad_guesses
        })

    return total_tries, total_success, total_bad_guesses, total_latency



def test_games(lies: int = 0):
    LOG_FILE = LOG_DIR / f"benchmark_llm_{LLM_MODEL.replace(':', '_')}_fibble{lies}.json"
    game = GameState(show_window=False, logging=False)
    game.num_lies = lies
    total_success = 0
    total_tries = 0
    total_bad_guesses = 0
    total_latency = 0.0

    results = {
        "num_runs": NUM_RUNS,
        "LLM_MODEL": LLM_MODEL,
        "MAX_LLM_CONTINUOUS_CALLS": MAX_LLM_CONTINUOUS_CALLS,
        "games": [],
        "lies": lies
    }

    print(f"Playing with {lies} lies...")

    for i in range(NUM_RUNS):
        total_tries, total_success, total_bad_guesses, total_latency = run_game(game, i, total_tries, total_success, total_bad_guesses, total_latency, results)
        if i < NUM_RUNS - 1:
            time.sleep(0.5)

    # Calculate final averages
    win_rate = total_success / NUM_RUNS
    avg_tries = total_tries / NUM_RUNS
    avg_latency = total_latency / NUM_RUNS

    # Save the results
    results["total_bad_guesses"] = total_bad_guesses
    results["win_rate"] = win_rate
    results["avg_tries"] = avg_tries
    results["avg_latency"] = avg_latency
   
    with open(LOG_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*50}")
    print(f"FINAL RESULTS:")
    print(f"{'='*50}")
    print(f"Win Rate: {win_rate:.2%} ({total_success}/{NUM_RUNS})")
    print(f"Average Tries: {avg_tries:.2f}")
    print(f"Average Latency: {avg_latency:.2f}s")
    print(f"Total Bad Guesses: {total_bad_guesses}")
    print(f"{'='*50}")
    print(f"\nSaved benchmark results to {LOG_FILE}")
    
def all_fibble_variants():
    test_games(lies=0)
    time.sleep(20)
    test_games(lies=1)
    time.sleep(20)
    test_games(lies=2)
    time.sleep(20)
    test_games(lies=3)
    time.sleep(20)
    test_games(lies=4)
    time.sleep(20)
    test_games(lies=5)


if __name__ == "__main__":
    all_fibble_variants()
