import socket
import threading

HOST = '0.0.0.0'   
PORT = 12345       


waiting_clients = []
waiting_lock = threading.Lock()


def read_line(conn):
    
    data = b''
    while True:
        try:
            chunk = conn.recv(1024)
        except ConnectionResetError:
            return None
        if not chunk:
            return None
        data += chunk
        if b'\n' in data:
            break

    line, _, rest = data.partition(b'\n')
    return line.decode().strip()


def send_line(conn, msg):
    try:
        conn.sendall((msg + '\n').encode())
    except BrokenPipeError:
        pass


def check_winner(board):
   
    
    for i in range(3):
        if board[i][0] != ' ' and board[i][0] == board[i][1] == board[i][2]:
            return board[i][0]
        if board[0][i] != ' ' and board[0][i] == board[1][i] == board[2][i]:
            return board[0][i]
    
    if board[0][0] != ' ' and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != ' ' and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    
    for row in board:
        for cell in row:
            if cell == ' ':
                return None
    return 'DRAW'


def game_thread(conn1, conn2, event1, event2):
    
    symbol = {conn1: 'X', conn2: 'O'}
    
    send_line(conn1, 'START:X')
    send_line(conn2, 'START:O')

    
    board = [[' ' for _ in range(3)] for _ in range(3)]
    current = conn1  
    other = conn2

    while True:
        
        send_line(current, 'YOUR_TURN')
        
        move_msg = read_line(current)
        if move_msg is None:
            
            break

        if not move_msg.startswith('MOVE:'):
            
            continue

        
        try:
            _, coords = move_msg.split(':')
            row, col = map(int, coords.split(','))
        except Exception:
            send_line(current, 'INVALID')
            continue

        
        if row < 0 or row > 2 or col < 0 or col > 2 or board[row][col] != ' ':
            send_line(current, 'INVALID')
            continue

        
        board[row][col] = symbol[current]
        
        send_line(current, f'VALID:{row},{col}')
        send_line(other, f'OPPONENT_MOVE:{row},{col}')

        
        resultado = check_winner(board)
        if resultado:
            if resultado == 'DRAW':
                send_line(current, 'GAME_END:DRAW')
                send_line(other, 'GAME_END:DRAW')
            else:
                
                if symbol[current] == resultado:
                    
                    send_line(current, 'GAME_END:WIN')
                    send_line(other, 'GAME_END:LOSE')
                else:
                    
                    send_line(current, 'GAME_END:LOSE')
                    send_line(other, 'GAME_END:WIN')
            break

        current, other = other, current

    event1.set()
    event2.set()


def register_client(conn, event):
    
    with waiting_lock:
        if waiting_clients:
            other_conn, other_event = waiting_clients.pop(0)
            
            t = threading.Thread(target=game_thread, args=(conn, other_conn, event, other_event), daemon=True)
            t.start()
        else:
            
            waiting_clients.append((conn, event))
            send_line(conn, 'WAIT')


def handle_client(conn, addr):
   
    print(f'[SERVER] Cliente conectado: {addr}')
    try:
        while True:
            msg = read_line(conn)
            if msg is None:
                print(f'[SERVER] {addr} se desconectó.')
                break

            if msg == 'PLAY':
                
                event = threading.Event()
                register_client(conn, event)
                
                event.wait()
                
                continue

            elif msg == 'EXIT':
                print(f'[SERVER] {addr} solicitó salir.')
                break

            else:
                
                continue
    except Exception as e:
        print(f'[SERVER] Error con cliente {addr}: {e}')
    finally:
        conn.close()
        print(f'[SERVER] Conexión con {addr} cerrada.')

def main():
   
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f'[SERVER] Escuchando en {HOST}:{PORT} ...')

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print('\n[SERVER] Terminando servidor.')
    finally:
        server.close()

if __name__ == '__main__':
    main()