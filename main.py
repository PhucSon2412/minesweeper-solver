from src.ChromeConnector import ChromeConnector
from src.BoardReader import BoardReader
from src.MinesweeperSolver import MinesweeperSolver
from src.AutoPlayer import AutoPlayer

def main():
    print("=== MINESWEEPER SOLVER (ADVANCED) ===")
    print("1. Suggest")
    print("2. Auto mode")

    choice = input("Choose mode (1-2): ").strip()

    # Connect to Chrome
    chrome = ChromeConnector()
    if not chrome.find_minesweeper_tab():
        return
    
    try:
        if choice == "1":
            # Manual mode
            board_reader = BoardReader(chrome.driver)
            board = board_reader.read_board_state()
            
            if board:
                solver = MinesweeperSolver(board)
                safe_moves = solver.find_safe_moves()

                print(f"\nFound {len(safe_moves)} safe moves:")
                for i, (x, y, action) in enumerate(safe_moves, 1):
                    action_text = "Click" if action == "click" else "Flag"
                    print(f"{i}. {action_text} cell ({x}, {y})")
                
                # Show probabilities if no safe moves found
                if not safe_moves:
                    probabilities = solver.find_probability_moves()
                    if probabilities:
                        print(f"\nMine probabilities for cells (top 10):")
                        for i, (x, y, prob) in enumerate(probabilities[:10], 1):
                            print(f"{i}. Cell ({x}, {y}): {prob:.1%}")

        elif choice == "2":
            # Advanced auto mode
            player = AutoPlayer(chrome.driver)
            player.auto_solve_advanced()
    finally:
        chrome.close()

if __name__ == "__main__":
    main()