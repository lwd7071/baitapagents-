import random

# Ma trận 4x4
room = [
    [1, 0, 1, 0],
    [0, 1, 0, 1],
    [1, 0, 0, 0],
    [0, 1, 1, 0]
]

# Vị trí ban đầu robot
x, y = 0, 0

# Tìm các hướng có thể đi
def possible_moves(x, y):
    moves = []

    if x > 0:
        moves.append('U')

    if x < 3:
        moves.append('D')

    if y > 0:
        moves.append('L')

    if y < 3:
        moves.append('R')

    return moves


# Chạy robot
for step in range(15):

    state = room[x][y]

    print(f"\nStep {step+1}")
    print(f"Position: ({x},{y})")
    print(f"State: {state}")

    # Nếu bẩn -> hút
    if state == 1:
        action = 'S'
        room[x][y] = 0
        print("Action: Suck")
    
    # Nếu sạch -> di chuyển ngẫu nhiên
    else:
        moves = possible_moves(x, y)
        action = random.choice(moves)

        print("Possible moves:", moves)
        print("Action:", action)

        # Cập nhật vị trí
        if action == 'U':
            x -= 1

        elif action == 'D':
            x += 1

        elif action == 'L':
            y -= 1

        elif action == 'R':
            y += 1

# In ma trận sau khi chạy
print("\nFinal room:")
for row in room:
    print(row)