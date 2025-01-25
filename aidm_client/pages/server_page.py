from PySide6.QtWidgets import QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt
from aidm_client.pages.base_page import BasePage
from aidm_client.app import AIDMWizardApp

class ServerPage(BasePage):
    """
    Page to connect to the AI-DM server.
    """
    def __init__(self, parent):
        super().__init__(parent, title="1. Connect to AI-DM Server")

        self.server_edit = QLineEdit(self)
        self.server_edit.setFont(AIDMWizardApp.INPUT_FONT)
        # IMPORTANT: Set the default server URL here
        self.server_edit.setText("http://localhost:5000")  

        self.button_next = QPushButton("Next")
        self.button_next.setFont(AIDMWizardApp.BUTTON_FONT)
        self.button_next.clicked.connect(self.next_step)

        # Layout
        label = QLabel("Enter your AI-DM Server URL:")
        label.setFont(AIDMWizardApp.LABEL_FONT)

        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.server_edit)
        vbox.addWidget(self.button_next, alignment=Qt.AlignCenter)

        self.content_layout.addLayout(vbox)
        self.content_layout.addStretch()

    def next_step(self):
        """
        Proceed to the next step after validating the server URL.
        """
        url = self.server_edit.text().strip()
        if not url:
            QMessageBox.critical(self, "Error", "Server URL cannot be empty.")
            return
        self.controller.server_url = url
        self.controller.show_frame("CampaignPage")
