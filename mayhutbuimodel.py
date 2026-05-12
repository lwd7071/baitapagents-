import random
import copy

# random ma trận 4x4 gồm 0 và 1
def tao_phong_random():

    room = []

    for i in range(4):

        row = []

        for j in range(4):

            # random 0 hoặc 1
            row.append(random.randint(0, 1))

        room.append(row)

    return room

# tạo ma trận random
room = tao_phong_random()

# vị trí robot random
x = random.randint(0, 3)
y = random.randint(0, 3)

# MODEL:
# lưu ô đã đi
visited = []

# in phòng
def print_room(room):

    for row in room:
        print(row)

# tìm hướng đi hợp lệ
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

# dự đoán vị trí mới
def next_position(x, y, move):

    new_x = x
    new_y = y

    if move == 'U':
        new_x -= 1

    elif move == 'D':
        new_x += 1

    elif move == 'L':
        new_y -= 1

    elif move == 'R':
        new_y += 1

    return new_x, new_y

# MODEL-BASED AGENT
def choose_action(room, x, y):

    # nếu ô hiện tại bẩn
    if room[x][y] == 1:
        return 'S'

    moves = possible_moves(x, y)

    best_move = None

    # ưu tiên ô chưa đi
    for move in moves:

        nx, ny = next_position(x, y, move)

        if (nx, ny) not in visited:

            # ưu tiên ô bẩn
            if room[nx][ny] == 1:
                return move

            if best_move is None:
                best_move = move

    # nếu bí thì random
    if best_move is None:
        best_move = random.choice(moves)

    return best_move

# chạy robot
for step in range(30):

    print(f"\nSTEP {step+1} ")

    print(f"Robot position: ({x},{y})")

    print("Current room:")
    print_room(room)

    # lưu bộ nhớ
    visited.append((x, y))

    action = choose_action(room, x, y)

    print("Action:", action)

    # hút bụi
    if action == 'S':

        room[x][y] = 0

        print("Cleaning dirt...")

    # di chuyển
    else:

        x, y = next_position(x, y, action)

# kết quả cuối
print("\nFINAL ROOM")

print_room(room)