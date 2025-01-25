from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QLineEdit, QPlainTextEdit, QMessageBox
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtCore import Qt, QTimer
import socketio
import random
import queue

from aidm_client.pages.base_page import BasePage

class ChatPage(BasePage):
    """
    Final step: Real-time chat with the AI DM via SocketIO.
    """
    # Add signal for real-time UI updates
    update_chat_signal = QtCore.Signal(str)

    def __init__(self, parent):
        super().__init__(parent, title="AI-DM")

        # Add QTextCursor enum import
        from PySide6.QtGui import QTextCursor

        # SocketIO client and a thread-safe queue for incoming messages
        self.sio = socketio.Client()
        self.msg_queue = queue.Queue()

        # Register socket.io event handlers
        @self.sio.event
        def connect():
            self.msg_queue.put("Connected to the server via SocketIO.")
            if self.controller.session_id:
                self.sio.emit('join_session', {'session_id': self.controller.session_id})

        @self.sio.event
        def connect_error(data):
            # If something goes wrong during connection, log it to the chat
            self.msg_queue.put(f"Connection failed: {data}")

        @self.sio.event
        def disconnect():
            self.msg_queue.put("Disconnected from the server.")

        @self.sio.on('new_message')
        def on_new_message(data):
            # Just like the old code, add extra line break
            message = data.get('message', '')
            self.msg_queue.put(f"\n--- NEW MESSAGE ---\n{message}\n")

        # NEW: Handle streaming chunks
        @self.sio.on('stream_chunk')
        def on_stream_chunk(data):
            chunk = data.get('chunk', '')
            self.msg_queue.put(chunk)  # Direct chunk streaming to chat

        # Main chat UI - with improved styling
        self.chat_display = QPlainTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(self.controller.LABEL_FONT)
        
        # More specific styling to ensure text visibility
        self.chat_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: #404040;
                selection-color: #FFFFFF;
                border: 1px solid #333333;
            }
        """)
        
        # Add test text to verify visibility
        self.chat_display.setPlainText("Chat initialized. If you can see this text, styling is working correctly.")

        self.input_line = QLineEdit()
        self.input_line.setFont(self.controller.INPUT_FONT)
        self.input_line.returnPressed.connect(self.send_message)

        self.btn_send = QPushButton("Send")
        self.btn_send.setFont(self.controller.BUTTON_FONT)
        self.btn_send.clicked.connect(self.send_message)

        self.btn_end = QPushButton("End Session")
        self.btn_end.setFont(self.controller.BUTTON_FONT)
        self.btn_end.clicked.connect(self.end_session)

        # Dice row with improved styling for macOS visibility
        self.dice_combo = QComboBox()
        self.dice_combo.setFont(self.controller.INPUT_FONT)
        self.dice_combo.addItems(["d4", "d6", "d8", "d10", "d12", "d20", "d100"])
        # Add specific styling for the combo box to ensure text visibility
        self.dice_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.9);
                color: black;
                padding: 5px;
                border: 1px solid #666666;
                border-radius: 3px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                width: 0;
                height: 0;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #0078d7;
                selection-color: white;
            }
        """)

        self.btn_roll = QPushButton("Roll")
        self.btn_roll.setFont(self.controller.BUTTON_FONT)
        self.btn_roll.clicked.connect(self.roll_die)

        self.label_roll_result = QLabel("")
        self.label_roll_result.setFont(QFont(self.controller.LABEL_FONT.family(), 12, QFont.Bold))

        # Update to use only the generic dice emoji
        self.dice_emojis = ["🎲"]  # Only use the generic dice emoji

        # Layout
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_display)

        send_layout = QHBoxLayout()
        send_layout.addWidget(self.input_line)
        send_layout.addWidget(self.btn_send)
        send_layout.addWidget(self.btn_end)
        chat_layout.addLayout(send_layout)

        dice_layout = QHBoxLayout()
        dice_layout.addWidget(self.dice_combo)
        dice_layout.addWidget(self.btn_roll)
        dice_layout.addWidget(self.label_roll_result)
        dice_layout.addStretch()
        chat_layout.addLayout(dice_layout)

        self.content_layout.addLayout(chat_layout)

        # Set up a QTimer to poll the msg_queue periodically
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self.poll_queue)
        self.poll_timer.start(100)  # poll every 100ms

        # Clear the initial test message from chat
        self.chat_display.clear()
        
        # Track if we're currently in a DM response
        self.in_dm_response = False
        self.current_message = []
        
        @self.sio.on('stream_chunk')
        def on_stream_chunk(data):
            chunk = data.get('chunk', '')
            if not self.in_dm_response:
                self.in_dm_response = True
                self.msg_queue.put("\nDM: ")  # Start new DM line
            self.current_message.append(chunk)
            self.msg_queue.put(chunk)  # Stream chunk directly
            
        @self.sio.on('new_message')
        def on_new_message(data):
            message = data.get('message', '')
            if "Player" in message or "You:" in message:
                # This is a player message, reset DM state
                self.in_dm_response = False
                self.current_message = []
            self.msg_queue.put(f"\n{message}")

        # Add state for tracking DM response
        self.current_dm_response = ""
        self.current_dm_session = None
        self.last_message_was_dm = False

        # ...existing socket event handlers...

        @self.sio.on('dm_response_start')
        def handle_dm_start(data):
            self.current_dm_session = data.get('session_id')
            self.current_dm_response = ""
            self.last_message_was_dm = True
            self.msg_queue.put("\nDM: ")

        @self.sio.on('dm_chunk')
        def handle_dm_chunk(data):
            if data.get('session_id') == self.current_dm_session:
                chunk = data.get('chunk', '')
                self.current_dm_response += chunk
                self.msg_queue.put(chunk)

        @self.sio.on('dm_response_end')
        def handle_dm_end(data):
            if data.get('session_id') == self.current_dm_session:
                self.msg_queue.put("\n")
                self.current_dm_response = ""
                self.current_dm_session = None
                self.last_message_was_dm = False

        # Connect the signal to the update_chat_display slot
        self.update_chat_signal.connect(self.update_chat_display)

        # State tracking for DM responses
        self.is_streaming = False
        self.current_response = []
        self.last_line = ""

        # Modify SocketIO event handlers
        @self.sio.on('dm_response_start')
        def handle_dm_start(data):
            self.is_streaming = True
            self.current_response = []
            self.msg_queue.put("\nDM: ")

        @self.sio.on('dm_chunk')
        def handle_dm_chunk(data):
            if self.is_streaming:
                chunk = data.get('chunk', '')
                if chunk:
                    self.current_response.append(chunk)
                    self.msg_queue.put(chunk)

        @self.sio.on('dm_response_end')
        def handle_dm_end(data):
            if self.is_streaming:
                self.msg_queue.put("\n")  # Add newline after response
                self.is_streaming = False
                self.current_response = []
                self.last_line = ""

        # Clean up old conflicting handlers
        if hasattr(self.sio, 'handlers'):
            self.sio.handlers = {
                k: v for k, v in self.sio.handlers.items() 
                if k not in ['stream_chunk', 'new_message']
            }

        @self.sio.on('new_message')
        def handle_new_message(data):
            message = data.get('message', '')
            if message and not self.is_streaming:
                self.msg_queue.put(f"\n{message}\n")

        # Modify the new_message handler to be inside __init__
        @self.sio.on('new_message')
        def handle_new_message(data):
            # Only process messages from the DM
            message = data.get('message', '')
            if not any(message.startswith(prefix) for prefix in ["You:", "Player:"]):
                # This is a DM message, so display it
                self.msg_queue.put(f"\n{message}")

        @self.sio.on('new_message')
        def handle_new_message(data):
            message = data.get('message', '')
            speaker = data.get('speaker', '')  # New: get speaker info
            
            if speaker and message:
                # Format: "Character: Message"
                display_text = f"\n{speaker}: {message}"
            else:
                # Fallback for system messages or DM responses
                display_text = f"\n{message}"
                
            self.msg_queue.put(display_text)

    def on_enter(self):
        """
        Connect to the SocketIO server when the page is entered.
        """
        # Connect socket if not connected
        if not self.sio.connected:
            server_url = self.controller.server_url.strip()
            self.log(f"Connecting to SocketIO server at {server_url}...")
            try:
                # Simplified connection parameters that are supported
                self.sio.connect(
                    server_url,
                    wait=True,
                    transports=["websocket"],
                    socketio_path="socket.io"
                )
            except Exception as e:
                self.log(f"Error connecting to SocketIO server:\n{e}")

    def poll_queue(self):
        """
        Poll the message queue for new messages.
        """
        try:
            while True:
                text = self.msg_queue.get_nowait()
                self.update_chat_signal.emit(text)
        except queue.Empty:
            pass

    def log(self, text):
        """
        Log a message to the chat display.
        """
        self.update_chat_signal.emit(text + "\n")

    def update_chat_display(self, text):
        """
        Update the chat display with new text.
        """
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        if self.is_streaming and text.startswith("DM: "):
            # Remove previous incomplete line if streaming
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()  # Remove newline
            
        cursor.insertText(text)
        
        # Auto-scroll
        scrollbar = self.chat_display.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum() - 4:
            scrollbar.setValue(scrollbar.maximum())
            self.chat_display.ensureCursorVisible()

    def send_message(self):
        """
        Send a message to the server.
        """
        msg = self.input_line.text().strip()
        if not msg:
            return
        self.input_line.clear()

        # Get player info to prefix the message
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/campaigns/{self.controller.campaign_id}/players"
        try:
            r = requests.get(url)
            if r.ok:
                players = r.json()
                player = next((p for p in players if p['player_id'] == self.controller.player_id), None)
                if player:
                    prefix = f"{player['character_name']}: "
                else:
                    prefix = "You: "
            else:
                prefix = "You: "
        except:
            prefix = "You: "

        # Update chat display with the prefixed message
        self.update_chat_signal.emit(f"\n{prefix}{msg}")
        QtWidgets.QApplication.processEvents()

        if not self.sio.connected:
            self.msg_queue.put("Not connected to SocketIO server.")
            return

        payload = {
            "session_id": self.controller.session_id,
            "campaign_id": self.controller.campaign_id,
            "world_id": self.controller.world_id,
            "player_id": self.controller.player_id,
            "message": msg
        }
        self.sio.emit('send_message', payload)

    def end_session(self):
        """
        End the current session.
        """
        if not self.controller.session_id:
            self.msg_queue.put("No session to end.")
            return
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/sessions/{self.controller.session_id}/end"
        try:
            r = requests.post(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            recap = data.get("recap", "No recap.")
            self.msg_queue.put("----- SESSION ENDED -----")
            self.msg_queue.put(f"Recap:\n{recap}")
            # Clear session ID
            self.controller.session_id = None
        except Exception as e:
            self.msg_queue.put(f"Error ending session:\n{e}")

    def roll_die(self):
        """
        Roll a die and display the result.
        """
        die_type = self.dice_combo.currentText()
        if not die_type.startswith("d"):
            return
        max_val = int(die_type[1:])
        result = random.randint(1, max_val)
        self.label_roll_result.setText(str(result))
        # Pick a random dice emoji
        emoji = random.choice(self.dice_emojis)
        self.msg_queue.put(f"{emoji} Roll {die_type}: {result}")

    def closeEvent(self, event: QtGui.QCloseEvent):
        """
        Clean up SocketIO on close if needed.
        """
        if self.sio and self.sio.connected:
            self.sio.disconnect()
        super().closeEvent(event)
