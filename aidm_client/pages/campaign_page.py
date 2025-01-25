from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QLineEdit
from aidm_client.pages.base_page import BasePage

class CampaignPage(BasePage):
    """
    Page to choose or create a campaign.
    """
    def __init__(self, parent):
        super().__init__(parent, title="2. Choose or Create a Campaign")

        label = QLabel("Select or Create a Campaign:")
        label.setFont(self.controller.LABEL_FONT)

        self.campaign_combo = QComboBox()
        self.campaign_combo.setFont(self.controller.INPUT_FONT)

        self.button_load = QPushButton("Load Campaigns")
        self.button_load.setFont(self.controller.BUTTON_FONT)
        self.button_load.clicked.connect(self.load_campaigns)

        self.button_create = QPushButton("Create New")
        self.button_create.setFont(self.controller.BUTTON_FONT)
        self.button_create.clicked.connect(self.create_campaign_prompt)

        self.button_next = QPushButton("Next")
        self.button_next.setFont(self.controller.BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        self.content_layout.addWidget(label)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.campaign_combo)
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
        Load campaigns when the page is entered.
        """
        self.load_campaigns()

    def load_campaigns(self):
        """
        Load campaigns from the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/campaigns"  # Add /api/ prefix
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            campaigns = resp.json() if resp.text else []
            if not isinstance(campaigns, list):
                campaigns = []

            self.campaign_combo.clear()
            for c in campaigns:
                c_id = c.get("campaign_id")
                c_title = c.get("title")
                text = f"{c_id}: {c_title}"
                self.campaign_combo.addItem(text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load campaigns:\n{e}")

    def create_campaign_prompt(self):
        """
        Prompt to create a new campaign.
        """
        dialog = CampaignCreateDialog(self.controller)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Campaign created.")
            self.load_campaigns()

    def next_step(self):
        """
        Proceed to the next step after selecting a campaign.
        """
        choice = self.campaign_combo.currentText().strip()
        if not choice:
            QMessageBox.information(self, "Info", "Select or create a campaign first.")
            return

        cid_str = choice.split(":", 1)[0].strip()
        if not cid_str.isdigit():
            return

        self.controller.campaign_id = int(cid_str)
        # Fetch campaign detail to get world_id
        base_url = self.controller.server_url.rstrip("/")
        c_url = f"{base_url}/api/campaigns/{self.controller.campaign_id}"  # Add /api/ prefix
        try:
            r = requests.get(c_url, timeout=5)
            r.raise_for_status()
            data = r.json()
            self.controller.world_id = data.get("world_id", 1)
        except:
            self.controller.world_id = 1

        self.controller.show_frame("SessionPage")


class CampaignCreateDialog(QDialog):
    """
    Dialog to create a new campaign.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("New Campaign")
        self.setModal(True)
        layout = QFormLayout(self)

        self.title_edit = QLineEdit(self)
        self.desc_edit = QLineEdit(self)
        self.world_edit = QLineEdit(self)
        self.world_edit.setText("1")

        layout.addRow("Campaign Title:", self.title_edit)
        layout.addRow("Description:", self.desc_edit)
        layout.addRow("World ID:", self.world_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        btn_box.accepted.connect(self.do_create)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def do_create(self):
        """
        Create a new campaign on the server.
        """
        base_url = self.controller.server_url.rstrip("/")
        url = f"{base_url}/api/campaigns"  # Add /api/ prefix
        data = {
            "title": self.title_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "world_id": int(self.world_edit.text() or "1"),
        }
        try:
            r = requests.post(url, json=data, timeout=5)
            r.raise_for_status()
            cid = r.json().get("campaign_id")
            if cid:
                QMessageBox.information(self, "Success", f"Created Campaign ID={cid}")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Response did not contain campaign_id.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create campaign:\n{e}")
