import socket
import threading
import logging
import json

# 配置日志
logging.basicConfig(filename='server.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 用户数据文件
USER_FILE = 'users.json'

# 加载用户数据
def load_users():
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果文件不存在，返回默认用户数据
        return {
            'user1': {'password': 'pass1', 'balance': 1000},
            'user2': {'password': 'pass2', 'balance': 2000}
        }

# 保存用户数据
def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# 初始化用户数据
users = load_users()

def handle_client(conn, addr):
    logging.info(f"Connected by {addr}")
    current_user = None

    try:
        # 接收客户端发送的 HELO 请求
        data = conn.recv(1024).decode().strip()
        if data.startswith("HELO"):
            userid = data.split()[1]  # 提取 user1
            logging.info(f"User ID received: {userid}")

            # 验证用户ID
            if userid in users:
                current_user = userid
                conn.sendall(b"500 sp AUTH REQUIRED\n")

                # 接收客户端发送的 PASS 请求
                data = conn.recv(1024).decode().strip()
                if data.startswith("PASS"):
                    password = data.split()[1]  # 提取 password
                    logging.info(f"Password received for user {userid}")

                    # 验证密码
                    if password == users[userid]['password']:
                        conn.sendall(b"525 sp OK!\n")
                        logging.info(f"User {userid} authenticated successfully")

                        # 处理客户端请求
                        while True:
                            data = conn.recv(1024).decode().strip()

                            if not data:  # 如果接收到空数据，表示客户端断开连接
                                logging.info(f"Client {addr} disconnected")
                                break
                            logging.info(f"Request received: {data}")

                            if data == "BALA":
                                # 查询余额
                                balance = users[userid]['balance']
                                conn.sendall(f"AMNT:{balance}\n".encode())
                                logging.info(f"Balance queried for user {userid}: {balance}")
                            elif data.startswith("WDRA"):
                                # 处理取款请求
                                try:
                                    amount = int(data.split()[1])
                                    if amount <= users[userid]['balance']:
                                        users[userid]['balance'] -= amount
                                        conn.sendall(b"525 sp OK!\n")
                                        logging.info(
                                            f"Withdrawal successful for user {userid}. Amount: {amount}, New Balance: {users[userid]['balance']}")
                                        save_users(users)  # 更新用户数据文件
                                    else:
                                        conn.sendall(b"401 sp ERROR!\n")
                                        logging.warning(
                                            f"Insufficient balance for user {userid}. Requested amount: {amount}")
                                except (IndexError, ValueError):
                                    conn.sendall(b"401 sp ERROR!\n")
                                    logging.warning(f"Invalid WDRA request format: {data}")
                            elif data == "BYE":
                                logging.info(f"User {userid} disconnected")
                                conn.sendall(b"BYE\n")

                                break
                            else:
                                conn.sendall(b"401 sp ERROR!\n")
                                logging.warning(f"Unknown request: {data}")
                    else:
                        conn.sendall(b"401 sp ERROR!\n")
                        logging.warning(f"Authentication failed for user {userid}")
                else:
                    conn.sendall(b"401 sp ERROR!\n")
                    logging.warning(f"Invalid password format for user {userid}")
            else:
                conn.sendall(b"401 sp ERROR!\n")
                logging.warning(f"Invalid user ID: {userid}")
    finally:
        conn.close()
        logging.info(f"Disconnected by {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 2525))
        s.listen()
        logging.info("Server started on port 2525")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()