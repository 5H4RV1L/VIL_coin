# 🪙 VIL Coin — Decentralized Blockchain Network

VIL Coin is a **Python-based peer-to-peer blockchain simulation** that lets you create accounts, send virtual coins, mine blocks, and synchronize data between network peers — all in real time.  
It includes both a **command-line interface (CLI)** and a **modern GUI** built with `tkinter`.

---

## 🚀 Features

### 💻 Core Blockchain
- Fully functional blockchain implementation in Python  
- Proof-of-work mining with adjustable difficulty  
- Peer discovery and synchronization over LAN  
- Transaction verification and validation  
- Automatic consensus (longest valid chain rule)

### 🧑‍💻 User Management
- Secure account creation with SHA-256 password hashing  
- Persistent storage of users and blockchain data  
- Login/logout system with local session tracking  

### 🌐 Networking
- Auto peer discovery across subnetworks (`/24` and sampled `/16`)  
- TCP-based communication for blocks, transactions, and user sync  
- Real-time broadcast of new transactions and mined blocks  

### 🎨 GUI (VILcoin_gui.py)
- Beautiful dark-themed interface  
- Account creation and login screens  
- Live balance, transaction, and blockchain view  
- System console output within GUI  
- Mining and transaction dialogs  
- Fully responsive layout

---

## 🧩 Project Structure

📂 VILcoin/<br>
├── VILcoin.py # Core blockchain engine + CLI version<br>
├── VILcoin_gui.py # GUI frontend built with tkinter<br>
├── run.bat # Windows launcher for GUI<br>
└── blockchain_data.json # Pre-included local blockchain data and user info<br>

> The `blockchain_data.json` file contains:
> - Saved blockchain blocks  
> - User accounts and balances  
> - Any pending transactions  

---

## 🧰 Requirements

- **Python 3.8+**
- No external libraries needed — only standard Python modules
- On Linux, make sure `tkinter` is installed:
  ```bash
  sudo apt install python3-tk

## ⚙️ How to Run

There are two ways to use VIL Coin — GUI and CLI.

### 🖥️ GUI Version (Recommended for most users)

If you want the full graphical interface:

#### Windows

- Simply double-click:

- run.bat

- Or run manually:
  python VILcoin_gui.py
 
#### Linux / macOS
- python3 VILcoin_gui.py

### 💻 CLI Version (Command-Line Interface)

If you prefer terminal-based interaction:

#### Windows
- python VILcoin.py

#### Linux / macOS
- python3 VILcoin.py


### Once running, you can:

- Create a new account

- Log in to send or receive VIL Coins

- Mine new blocks for rewards

- View your balance, users, and network peers

- Automatically sync with other nodes on your LAN

## 🛡️ Security Notes

- Passwords are hashed using SHA-256 (never stored in plain text)

- Peer communication is local-only — no external servers involved

- This project is for educational and experimental use only
 (not a real cryptocurrency)

## 👤 Author

- Sharvil Sagalgile
- GitHub: @5H4RV1L

## 📜 License

Released under the MIT License — free to use, modify, and share.
