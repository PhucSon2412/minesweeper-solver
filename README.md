# Advanced Minesweeper Solver

An intelligent automated Minesweeper solver that uses advanced logic algorithms to solve Minesweeper puzzles on https://minesweeper.online/. This solver employs multiple sophisticated techniques including constraint satisfaction problem (CSP) solving, probability analysis, pattern recognition, and intelligent guessing strategies to achieve high success rates.

## Features

- **Fully Automated Solving**: Plays continuously without user intervention, can be stopped with Ctrl+C
- **Advanced Algorithms**:
  - Basic rule-based solving
  - Pattern recognition (1-2-1, 2-3, 1-1-1 patterns, etc.)
  - Constraint Satisfaction Problem (CSP) solver
  - Advanced probability analysis for optimal guessing
- **Performance Optimized**:
  - Efficient board state analysis
  - Batch processing for improved speed
  - Reusable solver instances
- **Intelligent Guessing**: 
  - Uses probability calculations when no safe moves are available
  - Multiple fallback strategies
- **Stuck Detection & Resolution**:
  - Identifies oscillating cell patterns
  - Detects and resolves stuck situations
  - Multiple fallback strategies
- **Comprehensive Statistics**: Records performance metrics across games

## Requirements

- Python 3.8+
- Google Chrome browser
- Chrome WebDriver (automatically managed by selenium)
- Required Python packages:
  - selenium
  - numpy
  - typing (built-in)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/PhucSon2412/minesweeper-solver.git
cd minesweeper-solver
```

2. Install dependencies:
```bash
pip install selenium numpy
```

## Usage

### Prerequisites Setup

1. **Start Chrome with Remote Debugging**:
   - Close all Chrome instances
   - Open Command Prompt or Terminal
   - Run: `chrome.exe --remote-debugging-port=9222`
   - Keep this Chrome window open

2. **Open Minesweeper Game**:
   - Navigate to https://minesweeper.online/
   - Start a new game (any difficulty level)

### Running the Solver

1. **Run the main program**:
```bash
python main.py
```

2. The solver will start automatically and run indefinitely until you press Ctrl+C to stop it
3. Performance statistics will be displayed after each game

## How It Works

### Core Components

1. **ChromeConnector**: Establishes connection to Chrome browser
2. **BoardReader**: Reads and parses the current board state from the webpage
3. **MinesweeperSolver**: Implements the core solving algorithms
4. **ConstraintGroups**: Handles constraint-based problem solving
5. **AutoPlayer**: Orchestrates automated gameplay
6. **Logger**: Provides detailed logging and debugging information

### Solving Algorithms

#### 1. Basic Rules
- **Rule 1**: If all mines around a number are flagged, remaining cells are safe
- **Rule 2**: If remaining mines equal remaining cells, all are mines

#### 2. Pattern Recognition
- **1-2-1 Pattern**: Identifies safe cells in 1-2-1 sequences
- **2-3 Pattern**: Analyzes adjacent 2-3 number combinations
- **1-1-1 Pattern**: Handles triple 1 sequences
- **Corner/Edge Patterns**: Special logic for board boundaries
- **Overlapping Patterns**: Advanced constraint analysis

#### 3. Constraint Satisfaction
- Groups related constraints into independent clusters
- Uses Group and Cluster classes to track constraints
- Solves complex constraint networks
- Identifies certain mines and safe cells

#### 4. Advanced Probability Analysis
- Calculates exact mine probabilities for uncertain cells
- Considers global and local constraints
- Prioritizes moves with lowest risk
- Frontier analysis for unexplored areas

#### 5. Intelligent Guessing
- Multi-level fallback strategies when logic fails
- Detects and breaks out of oscillating patterns
- Edge/corner preference for safer guessing
- Safety probability estimation for uncertain moves

#### 6. Stuck Situation Detection
- Identifies when the solver is stuck in a loop
- Detects oscillating cells
- Monitors solving progress stagnation
- Resolves with specialized strategies

## Algorithm Performance

The solver demonstrates high success rates across different difficulty levels:

- **Beginner**: ~95% success rate
- **Intermediate**: ~85-90% success rate  
- **Expert**: ~70-75% success rate

Success rates have been improved from previous versions with advanced CSP implementation and better stuck situation handling.

## Troubleshooting

### Common Issues

1. **Chrome Connection Failed**:
   - Ensure Chrome is running with `--remote-debugging-port=9222`
   - Check that minesweeper.online is open in the Chrome window

2. **Board Reading Errors**:
   - Refresh the minesweeper page
   - Ensure the game has started
   - Check for any webpage layout changes

3. **Slow Performance**:
   - Close unnecessary browser tabs
   - Ensure stable internet connection
   - Consider reducing board size for testing

### Debug Mode

Enable detailed logging by modifying the logger configuration in `src/Logger.py`.

## Architecture

```
minesweeper-solver/
├── main.py                  # Main entry point
├── src/
│   ├── AutoPlayer.py        # Automated gameplay logic
│   ├── BoardReader.py       # Board state parsing
│   ├── ChromeConnector.py   # Browser connection
│   ├── Logger.py            # Logging utilities
│   ├── MinesweeperBoard.py  # Board representation
│   ├── MinesweeperSolver.py # Core solving algorithms
│   └── ConstraintGroups.py  # CSP implementation
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with detailed description

### Areas for Improvement

- Machine learning integration for better guessing
- Support for other Minesweeper implementations
- Performance optimizations for larger boards
- Additional pattern recognition algorithms

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built using Selenium for browser automation
- Inspired by various Minesweeper solving algorithms and research papers
- Special thanks to CSP-based solving approaches
