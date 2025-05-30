# Remember to adjust your student ID in meta.xml
import numpy as np
import pickle
import random
import gym
from gym import spaces
import matplotlib.pyplot as plt
import copy
import random
import math
from board_2048 import board, learning, pattern  

class Game2048Env(gym.Env):
    def __init__(self):
        super(Game2048Env, self).__init__()

        self.size = 4  # 4x4 2048 board
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.score = 0

        # Action space: 0: up, 1: down, 2: left, 3: right
        self.action_space = spaces.Discrete(4)
        self.actions = ["up", "down", "left", "right"]

        self.last_move_valid = True  # Record if the last move was valid

        self.reset()

    def reset(self):
        """Reset the environment"""
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.score = 0
        self.add_random_tile()
        self.add_random_tile()
        return self.board

    def add_random_tile(self):
        """Add a random tile (2 or 4) to an empty cell"""
        empty_cells = list(zip(*np.where(self.board == 0)))
        if empty_cells:
            x, y = random.choice(empty_cells)
            self.board[x, y] = 2 if random.random() < 0.9 else 4

    def compress(self, row):
        """Compress the row: move non-zero values to the left"""
        new_row = row[row != 0]  # Remove zeros
        new_row = np.pad(new_row, (0, self.size - len(new_row)), mode='constant')  # Pad with zeros on the right
        return new_row

    def merge(self, row):
        """Merge adjacent equal numbers in the row"""
        for i in range(len(row) - 1):
            if row[i] == row[i + 1] and row[i] != 0:
                row[i] *= 2
                row[i + 1] = 0
                self.score += row[i]
        return row

    def move_left(self):
        """Move the board left"""
        moved = False
        for i in range(self.size):
            original_row = self.board[i].copy()
            new_row = self.compress(self.board[i])
            new_row = self.merge(new_row)
            new_row = self.compress(new_row)
            self.board[i] = new_row
            if not np.array_equal(original_row, self.board[i]):
                moved = True
        return moved

    def move_right(self):
        """Move the board right"""
        moved = False
        for i in range(self.size):
            original_row = self.board[i].copy()
            # Reverse the row, compress, merge, compress, then reverse back
            reversed_row = self.board[i][::-1]
            reversed_row = self.compress(reversed_row)
            reversed_row = self.merge(reversed_row)
            reversed_row = self.compress(reversed_row)
            self.board[i] = reversed_row[::-1]
            if not np.array_equal(original_row, self.board[i]):
                moved = True
        return moved

    def move_up(self):
        """Move the board up"""
        moved = False
        for j in range(self.size):
            original_col = self.board[:, j].copy()
            col = self.compress(self.board[:, j])
            col = self.merge(col)
            col = self.compress(col)
            self.board[:, j] = col
            if not np.array_equal(original_col, self.board[:, j]):
                moved = True
        return moved

    def move_down(self):
        """Move the board down"""
        moved = False
        for j in range(self.size):
            original_col = self.board[:, j].copy()
            # Reverse the column, compress, merge, compress, then reverse back
            reversed_col = self.board[:, j][::-1]
            reversed_col = self.compress(reversed_col)
            reversed_col = self.merge(reversed_col)
            reversed_col = self.compress(reversed_col)
            self.board[:, j] = reversed_col[::-1]
            if not np.array_equal(original_col, self.board[:, j]):
                moved = True
        return moved

    def is_game_over(self):
        """Check if there are no legal moves left"""
        # If there is any empty cell, the game is not over
        if np.any(self.board == 0):
            return False

        # Check horizontally
        for i in range(self.size):
            for j in range(self.size - 1):
                if self.board[i, j] == self.board[i, j+1]:
                    return False

        # Check vertically
        for j in range(self.size):
            for i in range(self.size - 1):
                if self.board[i, j] == self.board[i+1, j]:
                    return False

        return True

    def step(self, action, add_random=True):
        """Execute one action"""
        assert self.action_space.contains(action), "Invalid action"

        if action == 0:
            moved = self.move_up()
        elif action == 1:
            moved = self.move_down()
        elif action == 2:
            moved = self.move_left()
        elif action == 3:
            moved = self.move_right()
        else:
            moved = False

        self.last_move_valid = moved  # Record if the move was valid

        if moved and add_random:
            self.add_random_tile()

        done = self.is_game_over()

        return self.board, self.score, done, {}

    def render(self, mode="human", action=None):
        """
        Render the current board using Matplotlib.
        This function does not check if the action is valid and only displays the current board state.
        """
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(-0.5, self.size - 0.5)
        ax.set_ylim(-0.5, self.size - 0.5)

        for i in range(self.size):
            for j in range(self.size):
                value = self.board[i, j]
                color = COLOR_MAP.get(value, "#3c3a32")  # Default dark color
                text_color = TEXT_COLOR.get(value, "white")
                rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=color, edgecolor="black")
                ax.add_patch(rect)

                if value != 0:
                    ax.text(j, i, str(value), ha='center', va='center',
                            fontsize=16, fontweight='bold', color=text_color)
        title = f"score: {self.score}"
        if action is not None:
            title += f" | action: {self.actions[action]}"
        plt.title(title)
        plt.gca().invert_yaxis()
        plt.show()

    def simulate_row_move(self, row):
        """Simulate a left move for a single row"""
        # Compress: move non-zero numbers to the left
        new_row = row[row != 0]
        new_row = np.pad(new_row, (0, self.size - len(new_row)), mode='constant')
        # Merge: merge adjacent equal numbers (do not update score)
        for i in range(len(new_row) - 1):
            if new_row[i] == new_row[i + 1] and new_row[i] != 0:
                new_row[i] *= 2
                new_row[i + 1] = 0
        # Compress again
        new_row = new_row[new_row != 0]
        new_row = np.pad(new_row, (0, self.size - len(new_row)), mode='constant')
        return new_row

    def is_move_legal(self, action):
        """Check if the specified move is legal (i.e., changes the board)"""
        # Create a copy of the current board state
        temp_board = self.board.copy()

        if action == 0:  # Move up
            for j in range(self.size):
                col = temp_board[:, j]
                new_col = self.simulate_row_move(col)
                temp_board[:, j] = new_col
        elif action == 1:  # Move down
            for j in range(self.size):
                # Reverse the column, simulate, then reverse back
                col = temp_board[:, j][::-1]
                new_col = self.simulate_row_move(col)
                temp_board[:, j] = new_col[::-1]
        elif action == 2:  # Move left
            for i in range(self.size):
                row = temp_board[i]
                temp_board[i] = self.simulate_row_move(row)
        elif action == 3:  # Move right
            for i in range(self.size):
                row = temp_board[i][::-1]
                new_row = self.simulate_row_move(row)
                temp_board[i] = new_row[::-1]
        else:
            raise ValueError("Invalid action")

        # If the simulated board is different from the current board, the move is legal
        return not np.array_equal(self.board, temp_board)



class BoardAdapter:
    def __init__(self, game_env):
        self.game_env = game_env
        self.board_obj = board()  # The new bit-based board
        self.sync_to_board()
    
    def sync_to_board(self):
        """Convert Game2048Env board to bit-based board"""
        self.board_obj = board(0)  # Reset board
        for i in range(4):
            for j in range(4):
                # Convert values like 0, 2, 4, 8... to 0, 1, 2, 3...
                val = self.game_env.board[i, j]
                if val > 0:
                    index = int(math.log2(val))
                else:
                    index = 0
                self.board_obj.set(i * 4 + j, index)
        return self.board_obj
    
    def sync_from_board(self):
        """Convert bit-based board to Game2048Env board"""
        for i in range(4):
            for j in range(4):
                # Convert values like 0, 1, 2, 3... to 0, 2, 4, 8...
                index = self.board_obj.at(i * 4 + j)
                if index > 0:
                    val = 2 ** index
                else:
                    val = 0
                self.game_env.board[i, j] = val








# Node for TD-MCTS using the TD-trained value approximator
class TD_MCTS_Node:
    def __init__(self,env, state, score, parent=None, action=None):
        """
        state: current board state (numpy array)
        score: cumulative score at this node
        parent: parent node (None for root)
        action: action taken from parent to reach this node
        """
        self.state = state
        self.score = score
        self.parent = parent
        self.action = action
        self.children = {}
        self.visits = 0
        self.total_reward = 0.0
        # List of untried actions based on the current state's legal moves
        self.untried_actions = [a for a in range(4) if env.is_move_legal(a)]

    def fully_expanded(self):
        # A node is fully expanded if no legal actions remain untried.
        return len(self.untried_actions) == 0


# TD-MCTS class utilizing a trained approximator for leaf evaluation
class TD_MCTS:
    def __init__(self, env, approximator, iterations=500, exploration_constant=1.41, rollout_depth=10, gamma=0.99):
        self.env = env
        self.approximator = approximator
        self.iterations = iterations
        self.c = exploration_constant
        self.rollout_depth = rollout_depth
        self.gamma = gamma

    def create_env_from_state(self, state, score):
        # Create a deep copy of the environment with the given state and score.
        new_env = copy.deepcopy(self.env)
        new_env.board = state.copy()
        new_env.score = score
        return new_env

    def select_child(self, node):
        # TODO: Use the UCT formula: Q + c * sqrt(log(parent.visits)/child.visits) to select the best child.
        best_val = -float("inf")
        best_child = None
        parent = node
        for child in node.children.values():
            if child.visits == 0:
                UCT_val = float("inf")
            else:
                Q = child.total_reward / child.visits
                UCT_val = Q + self.c * math.sqrt(math.log(parent.visits) / child.visits)
            if UCT_val > best_val:
                best_child = child
                best_val = UCT_val
        return best_child


    def evaluate_afterstate(self, env):
        legal_actions = [a for a in range(4) if env.is_move_legal(a)]
        if not legal_actions:
            return 0

        max_value = float('-inf')
        for action in legal_actions:
            env_copy = copy.deepcopy(env)
            afterstate, _, _, _ = env_copy.step(action, add_random=False)

            adapter = BoardAdapter(env_copy)
            bit_board = adapter.sync_to_board()

            if self.approximator.estimate(bit_board) is not None:
              value = self.approximator.estimate(bit_board)
            if value >= max_value:
                max_value = value

        return max_value


    def rollout(self, sim_env, depth):
        # TODO: Perform a random rollout until reaching the maximum depth or a terminal state.
        # TODO: Use the approximator to evaluate the final state.
        total_reward = 0
        cur_deteriorate_rate = 1
        cur_depth = 0
        while cur_depth < depth:
            legal_moves = [a for a in range(4) if sim_env.is_move_legal(a)]
            if not legal_moves:
                break
            selected_action = random.choice(legal_moves)
            previous_score = sim_env.score
            _, _, is_terminal, _ = sim_env.step(selected_action)
            total_reward += cur_deteriorate_rate * (sim_env.score - previous_score)
            cur_deteriorate_rate *= self.gamma
            cur_depth += 1 
            if is_terminal:
                return total_reward

        estimated_value = self.evaluate_afterstate(sim_env)
        total_reward = total_reward + cur_deteriorate_rate * estimated_value

        return total_reward





    def backpropagate(self, node, reward):
        # TODO: Propagate the obtained reward back up the tree.
        while node is not None:
            node.visits += 1
            node.total_reward += (reward - node.total_reward) / node.visits
            node = node.parent


    def run_simulation(self, root):
        node = root
        sim_env = self.create_env_from_state(node.state, node.score)

        # TODO: Selection: Traverse the tree until reaching an unexpanded node.

        while node.fully_expanded() == True and node.children:
            node = self.select_child(node)
            sim_env.step(node.action)

        # TODO: Expansion: If the node is not terminal, expand an untried action.

        if node.fully_expanded() == False:
            selected_action = random.choice(node.untried_actions)
            sim_env.step(selected_action)
            newNode = TD_MCTS_Node(sim_env, sim_env.board.copy(), sim_env.score, parent=node, action=selected_action)
            node.children[selected_action] = newNode
            node.untried_actions.remove(selected_action)
            node = newNode


        # Rollout: Simulate a random game from the expanded node.
        rollout_reward = self.rollout(sim_env, self.rollout_depth)
        # Backpropagate the obtained reward.
        self.backpropagate(node, rollout_reward)

    def best_action_distribution(self, root):
        # Compute the normalized visit count distribution for each child of the root.
        total_visits = sum(child.visits for child in root.children.values())
        distribution = np.zeros(4)
        best_visits = -1
        best_action = None
        for action, child in root.children.items():
            distribution[action] = child.visits / total_visits if total_visits > 0 else 0
            if child.visits > best_visits:
                best_visits = child.visits
                best_action = action
        return best_action, distribution


def np_to_board(np_board: np.ndarray) -> board:
    b = board()
    for i in range(4):
        for j in range(4):
            val = np_board[i, j]
            b.set(i * 4 + j, int(np.log2(val)) if val != 0 else 0)
    return b

def load_approximator_from_bin(filename='2048.bin'):
    print("loading...")
    board.lookup.init()
    approximator = learning()
    approximator.add_feature(pattern([0, 1, 2, 3, 4, 5]))
    approximator.add_feature(pattern([4, 5, 6, 7, 8, 9]))
    approximator.add_feature(pattern([0, 1, 2, 4, 5, 6]))
    approximator.add_feature(pattern([4, 5, 6, 8, 9, 10]))
    approximator.load(filename)
    if approximator is not None:
        print("loaded!!!")
    return approximator



approximator = load_approximator_from_bin()

def get_action(state, score):
    """
    Choose the best action based on the N-Tuple Approximator
    
    Args:
        state: Current board state (4x4 numpy array)
        score: Current game score
        
    Returns:
        action: 0 (up), 1 (down), 2 (left), or 3 (right)
    """
    
    global approximator
    #approximator = load_approximator()
    
    # Load the approximator if not already loaded
    if approximator is None:
        return random.choice([0, 1, 2, 3])
    
    # Create a temporary environment to simulate actions
    env = Game2048Env()
    env.board = state.copy()
    env.score = score
    
    td_mcts = TD_MCTS(env, approximator, iterations=200, exploration_constant=1.41, rollout_depth=0, gamma=0.99) #1.41
    
    root = TD_MCTS_Node(env,state, env.score)

    # Run multiple simulations to build the MCTS tree
    for _ in range(td_mcts.iterations):
        td_mcts.run_simulation(root)

    # Select the best action (based on highest visit count)
    best_act, _ = td_mcts.best_action_distribution(root)
    
    
    # return_act = -1
    # if best_act == 0: #up
    #     return_act = 0
    # elif best_act == 1: #right
    #     return_act = 3
    # elif best_act == 2: # down
    #     return_act = 1
    # elif best_act == 3: #left
    #     return_act = 2
    # else:
    #     print("error act:",best_act)
    




  #  print("TD-MCTS selected action:", best_act)

    return  best_act


