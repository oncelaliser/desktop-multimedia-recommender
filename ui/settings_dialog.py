from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from app.config import AppConfig


def _status(value: str | None) -> str:
    return "<span style='color:#4caf50'>✓ set</span>" if value else "<span style='color:#e57373'>✗ not set</span>"


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.setWindowTitle("Provider Settings")
        self.setMinimumWidth(460)

        html = f"""
        <b>Media API Keys</b><br>
        TMDB &nbsp;&nbsp;&nbsp;{_status(config.tmdb_api_key)} — movie &amp; series recommendations<br>
        OMDb &nbsp;&nbsp;&nbsp;{_status(config.omdb_api_key)} — IMDb rating enrichment<br>
        Spotify &nbsp;{_status(config.spotify_client_id)} — music recommendations<br>
        <br>
        <b>AI Providers</b><br>
        OpenAI API key: {_status(config.openai_api_key)}<br>
        OpenAI base URL: {config.openai_base_url}<br>
        OpenAI model: {config.openai_model}<br>
        LM Studio URL: {config.lmstudio_base_url}<br>
        LM Studio model: {config.lmstudio_model}<br>
        <br>
        Keys are read from environment variables or a <b>.env</b> file in the project root.<br>
        See <b>.env.example</b> for all available options.
        """

        label = QLabel(html)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(label)
        layout.addWidget(close)
