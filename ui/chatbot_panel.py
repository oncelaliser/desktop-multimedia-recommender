from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.constants import AI_MODES, MEDIA_TYPES


class ChatbotPanel(QWidget):
    submitted = pyqtSignal(str, str, str)

    def __init__(self) -> None:
        super().__init__()

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Chatbot konuşması burada görünecek...")

        self.ai_mode = QComboBox()
        self.ai_mode.addItems(AI_MODES)

        self.media_type = QComboBox()
        self.media_type.addItems(MEDIA_TYPES)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Örn: 90'lar Amerika'sında geçen Twin Peaks tarzı suç dizisi")
        self.input.returnPressed.connect(self._submit)

        self.send_button = QPushButton("Recommend")
        self.send_button.clicked.connect(self._submit)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("AI Mode"))
        top_row.addWidget(self.ai_mode)
        top_row.addWidget(QLabel("Media"))
        top_row.addWidget(self.media_type)

        input_row = QHBoxLayout()
        input_row.addWidget(self.input)
        input_row.addWidget(self.send_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addLayout(top_row)
        layout.addWidget(self.chat_history)
        layout.addLayout(input_row)

    def append_user_message(self, text: str) -> None:
        self.chat_history.append(f"<b>You:</b> {text}")

    def append_assistant_message(self, text: str, provider_name: str) -> None:
        safe_text = text.replace("\n", "<br>")
        self.chat_history.append(f"<b>Assistant [{provider_name}]:</b> {safe_text}")

    def _submit(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.submitted.emit(text, self.ai_mode.currentText(), self.media_type.currentText())
