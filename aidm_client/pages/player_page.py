from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QLineEdit
from aidm_client.pages.base_page import BasePage

class PlayerPage(BasePage):
    """
    Page to choose or create a player.
    """
    def __init__(self, parent):
        super().__init__(parent, title="4. Choose or Create a Player")

        label = QLabel("Select or Create a Player:")
        label.setFont(self.controller.LABEL_FONT)

        self.player_combo = QComboBox()
        self.player_combo.setFont(self.controller.INPUT_FONT)

        self.button_load = QPushButton("Load Players")
        self.button_load.setFont(self.controller.BUTTON_FONT)
        self.button_load.clicked.connect(self.load_players)

        self.button_create = QPushButton("New Player")
        self.button_create.setFont(self.controller.BUTTON_FONT)
        self.button_create.clicked.connect(self.create_player_prompt)

        self.button_next = QPushButton("Next")
        self.button_next.setFont(self.controller.BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        self.content_layout.addWidget(label)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.player_combo)
        row_layout.addWidget(self.button_load)
        self.content_layout.addLayout(row_layout)

        row_layout2 = QHBoxLayout()
        row_layout2.addStretch()
        row_layout2.addWidget(self.button_create)
        row_layout2.addWidget(self.button_next)
        row_layout2.addStretch()
        self.content_layout.addLayout(row_layout2)

        self.content_layout.addStretch()

    def on_enter(self):
        """
        Load players when the page is entered.
        """
        self.load_players()

    def load_players(self):
        """
        Load players from the server.
        """
        if not self.controller.campaign_id:
            QMessageBox.critical(self, "Error", "No campaign selected.")
            return
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/players/campaigns/{self.controller.campaign_id}/players"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            players = resp.json() if resp.text else []
            if not isinstance(players, list):
                players = []

            self.player_combo.clear()
            for p in players:
                pid = p.get("player_id")
                cname = p.get("character_name")
                uname = p.get("name")
                text = f"{pid}: {cname} ({uname})"
                self.player_combo.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load players:\n{e}")

    def create_player_prompt(self):
        """
        Prompt to create a new player.
        """
        dialog = PlayerCreateDialog(self.controller)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Player created.")
            self.load_players()

    def next_step(self):
        """
        Proceed to the next step after selecting a player.
        """
        choice = self.player_combo.currentText().strip()
        if not choice:
            QMessageBox.information(self, "Info", "Select or create a player first.")
            return
        pid_str = choice.split(":", 1)[0].strip()
        if not pid_str.isdigit():
            return
        self.controller.player_id = int(pid_str)
        self.controller.show_frame("ChatPage")


class PlayerCreateDialog(QDialog):
    """
    Dialog to create a new player.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("New Player")
        self.setModal(True)
        layout = QFormLayout(self)

        self.name_edit       = QLineEdit(self)
        self.char_name_edit  = QLineEdit(self)
        self.race_edit       = QLineEdit(self)
        self.class_edit      = QLineEdit(self)
        self.level_edit      = QLineEdit(self)
        self.level_edit.setText("1")

        layout.addRow("User Name:", self.name_edit)
        layout.addRow("Character Name:", self.char_name_edit)
        layout.addRow("Race:", self.race_edit)
        layout.addRow("Class:", self.class_edit)
        layout.addRow("Level:", self.level_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self.do_create)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def do_create(self):
        """
        Create a new player on the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/campaigns/{self.controller.campaign_id}/players"
        data = {
            "name": self.name_edit.text().strip(),
            "character_name": self.char_name_edit.text().strip(),
            "race": self.race_edit.text().strip(),
            "char_class": self.class_edit.text().strip(),
        }
        lv_str = self.level_edit.text().strip()
        data["level"] = int(lv_str) if lv_str.isdigit() else 1
        try:
            r = requests.post(url, json=data, timeout=5)
            r.raise_for_status()
            pid = r.json().get("player_id")
            if pid:
                QMessageBox.information(self, "Success", f"Player created (ID={pid})")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "No player_id returned.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create player:\n{e}")
