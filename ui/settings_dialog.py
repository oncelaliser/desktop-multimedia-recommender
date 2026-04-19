from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from app.config import AppConfig


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.setWindowTitle("Provider Settings")
        self.setMinimumWidth(420)

        text = (
            "Provider ayarları şu an ortam değişkenlerinden okunuyor.\n\n"
            f"OpenAI-compatible base URL: {config.openai_base_url}\n"
            f"OpenAI-compatible model: {config.openai_model}\n"
            f"LM Studio base URL: {config.lmstudio_base_url}\n"
            f"LM Studio model: {config.lmstudio_model}\n\n"
            ".env desteği ve editable settings ekranı bir sonraki iterasyonda eklenecek."
        )

        label = QLabel(text)
        label.setWordWrap(True)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(close)
