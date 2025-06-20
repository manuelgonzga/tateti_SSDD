import socket
import threading
import tkinter as tk
from tkinter import messagebox

SERVER_HOST = '127.0.0.1'  
SERVER_PORT = 12345

class ClientApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Cliente Tatetí")
        self.symbol = None       
        self.my_turn = False     
        self.game_window = None  
        self.wait_window = None  
        self.board_buttons = [[None]*3 for _ in range(3)]
        self.board_state = [[' ']*3 for _ in range(3)]

    
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_HOST, SERVER_PORT))
        except Exception as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar al servidor:\n{e}")
            master.destroy()
            return

        
        self.listener_thread = threading.Thread(target=self.listen_from_server, daemon=True)
        self.listener_thread.start()

       
        self.build_main_menu()

    def build_main_menu(self):
       
        self.clear_window()
        frame = tk.Frame(self.master, padx=20, pady=20)
        frame.pack()

        tk.Label(frame, text="Bienvenido a Tatetí", font=("Helvetica", 16)).pack(pady=(0,10))
        play_button = tk.Button(frame, text="Jugar", width=20, command=self.request_play)
        play_button.pack(pady=(0,5))
        exit_button = tk.Button(frame, text="Salir", width=20, command=self.exit_program)
        exit_button.pack()

    def request_play(self):
       
        try:
            self.sock.sendall("PLAY\n".encode())
        except Exception:
            messagebox.showerror("Error", "Error al enviar petición de juego.")
            return

        
        self.clear_window()
        self.build_wait_window()

    def build_wait_window(self):
       
        self.wait_window = tk.Frame(self.master, padx=20, pady=20)
        self.wait_window.pack()
        tk.Label(self.wait_window, text="Esperando a otro jugador...", font=("Helvetica", 14)).pack()

    def build_game_window(self):
       
        
        if self.wait_window:
            self.wait_window.destroy()
            self.wait_window = None

        self.game_window = tk.Frame(self.master, padx=10, pady=10)
        self.game_window.pack()

        info = f"Tú eres: {self.symbol}"
        self.status_label = tk.Label(self.game_window, text=info, font=("Helvetica", 12))
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0,10))

        
        for r in range(3):
            for c in range(3):
                btn = tk.Button(self.game_window, text=" ", width=6, height=3,
                                font=("Helvetica", 20),
                                command=lambda row=r, col=c: self.on_cell_click(row, col))
                btn.grid(row=r+1, column=c, padx=5, pady=5)
                self.board_buttons[r][c] = btn
                self.board_state[r][c] = ' '

    def on_cell_click(self, row, col):
       
        if not self.my_turn:
            return
        if self.board_state[row][col] != ' ':
            return

        
        self.my_turn = False
        try:
            self.sock.sendall(f"MOVE:{row},{col}\n".encode())
        except Exception:
            messagebox.showerror("Error", "Error al enviar movimiento.")

    def listen_from_server(self):
       
        buffer = b''
        while True:
            try:
                chunk = self.sock.recv(1024)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk
            while b'\n' in buffer:
                line, _, buffer = buffer.partition(b'\n')
                msg = line.decode().strip()
                
                self.master.after(0, lambda m=msg: self.handle_server_message(m))
        
        self.master.after(0, lambda: messagebox.showwarning("Conexión perdida", "El servidor se desconectó."))
        self.master.after(0, self.master.destroy)

    def handle_server_message(self, msg):
       
        if msg == 'WAIT':
            
            return

        if msg.startswith('START:'):
            
            _, sym = msg.split(':')
            self.symbol = sym
            
            self.build_game_window()
            return

        if msg == 'YOUR_TURN':
            
            self.my_turn = True
            self.status_label.config(text=f"Tú eres {self.symbol} - Es tu turno")
            return

        if msg == 'INVALID':
            
            return

        if msg.startswith('VALID:'):
            
            _, coords = msg.split(':')
            row, col = map(int, coords.split(','))
            
            self.board_state[row][col] = self.symbol
            self.board_buttons[row][col].config(text=self.symbol, state=tk.DISABLED)
            self.status_label.config(text="Esperando movimiento del oponente...")
            return

        if msg.startswith('OPPONENT_MOVE:'):
            
            _, coords = msg.split(':')
            row, col = map(int, coords.split(','))
            opp_sym = 'O' if self.symbol == 'X' else 'X'
            self.board_state[row][col] = opp_sym
            self.board_buttons[row][col].config(text=opp_sym, state=tk.DISABLED)
            
            self.my_turn = True
            self.status_label.config(text=f"Tu turno ({self.symbol})")
            return

        if msg.startswith('GAME_END:'):
            
            _, result = msg.split(':')
            if result == 'WIN':
                self.status_label.config(text="¡Ganaste! 😊")
            elif result == 'LOSE':
                self.status_label.config(text="Perdiste 😞")
            else:
                self.status_label.config(text="Empate 🤝")
            
            self.master.after(2000, self.end_game)
            return

    def end_game(self):
        
        if self.game_window:
            self.game_window.destroy()
            self.game_window = None
        
        self.build_main_menu()

    def exit_program(self):
    
        try:
            self.sock.sendall("EXIT\n".encode())
        except Exception:
            pass
        self.sock.close()
        self.master.destroy()

    def clear_window(self):
        
        for widget in self.master.winfo_children():
            widget.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = ClientApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_program)
    root.mainloop()