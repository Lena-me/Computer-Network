import tkinter as tk
from tkinter import messagebox
import socket
import logging

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='atm_client.log',
    filemode='a'
)

client_socket = None


def send_login():
    global client_socket
    userid = userid_entry.get()
    password = password_entry.get()

    logging.info(f"Attempting to login with User ID: {userid}")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('192.168.138.161', 2525))
        client_socket.sendall(f"HELO {userid}".encode())
        response = client_socket.recv(1024).decode()

        if response == "500 AUTH REQUIRE":
            logging.info("Authentication required. Sending password.")
            client_socket.sendall(f"PASS {password}".encode())
            response = client_socket.recv(1024).decode()

            if response == "525 OK!":
                logging.info("Login successful.")
                messagebox.showinfo("Login", "Login successful!")
                show_operations()  # 显示操作界面
            else:
                logging.error("Invalid password.")
                messagebox.showerror("Login", "Invalid password!")
        else:
            logging.error("Invalid user ID.",response)
            messagebox.showerror("Login", "Invalid user ID!")
    except Exception as e:
        logging.error(f"Login failed: {e}")
        messagebox.showerror("Error", f"Connection error: {e}")

def show_operations():
    # 隐藏登录界面
    userid_label.grid_forget()
    userid_entry.grid_forget()
    password_label.grid_forget()
    password_entry.grid_forget()
    login_button.grid_forget()

    # 显示操作界面
    bala_button.grid(row=0, column=0, padx=10, pady=10)
    wdra_button.grid(row=0, column=1, padx=10, pady=10)
    amount_label.grid(row=1, column=0)
    amount_entry.grid(row=1, column=1)
    bye_button.grid(row=2, column=0, columnspan=2, pady=10)

def send_request(request):
    global client_socket
    if not client_socket:
        logging.error("No active connection.")
        messagebox.showerror("Error", "Not connected to server.")
        return

    logging.info(f"Sending request: {request}")
    try:
        if request == "BALA":
            client_socket.sendall(b"BALA")
            response = client_socket.recv(1024).decode()
            logging.info(f"Received balance response: {response}")
            messagebox.showinfo("Balance", response)
        elif request == "WDRA":
            amount = amount_entry.get()
            client_socket.sendall(f"WDRA {amount}".encode())
            response = client_socket.recv(1024).decode()
            if response.startswith("525 OK!"):

                logging.info(f"Withdrawal successful.")
                messagebox.showinfo("Withdrawal", f"取钱成功!\n")
            else:
                logging.error(f"Withdrawal failed: {response}")
                messagebox.showerror("Withdrawal", response)


        elif request == "BYE":
            client_socket.sendall(b"BYE")
            response = client_socket.recv(1024).decode()
            logging.info(f"Received exit response: {response}")
            messagebox.showinfo("Exit", response)
            client_socket.close()
            app.quit()
    except Exception as e:
        logging.error(f"Request failed: {e}")
        messagebox.showerror("Error", f"Request error: {e}")

app = tk.Tk()
app.title("ATM Client")

# 登录界面
userid_label = tk.Label(app, text="User ID:")
userid_label.grid(row=0, column=0, padx=10, pady=10)
userid_entry = tk.Entry(app)
userid_entry.grid(row=0, column=1, padx=10, pady=10)

password_label = tk.Label(app, text="Password:")
password_label.grid(row=1, column=0, padx=10, pady=10)
password_entry = tk.Entry(app, show="*")
password_entry.grid(row=1, column=1, padx=10, pady=10)

login_button = tk.Button(app, text="Login", command=send_login)
login_button.grid(row=2, column=0, columnspan=2, pady=10)

# 操作界面
bala_button = tk.Button(app, text="Check Balance", command=lambda: send_request("BALA"))
wdra_button = tk.Button(app, text="Withdraw", command=lambda: send_request("WDRA"))
amount_label = tk.Label(app, text="Amount:")
amount_entry = tk.Entry(app)
bye_button = tk.Button(app, text="Exit", command=lambda: send_request("BYE"))

app.mainloop()
