from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.config import AppConfig
from app.constants import APP_TITLE
from core.chatbot.chat_service import ChatService
from core.recommendation.recommender_service import RecommenderService
from data.db.connection import connect
from data.db.repositories.media_repository import MediaRepository
from ui.chatbot_panel import ChatbotPanel
from ui.recommendation_panel import RecommendationPanel
from ui.settings_dialog import SettingsDialog
from ui.styles import APP_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.chat_service = ChatService(config)

        tmdb_client = None
        if config.tmdb_api_key:
            from integrations.tmdb_client import TmdbClient
            tmdb_client = TmdbClient(config.tmdb_api_key)

        omdb_client = None
        if config.omdb_api_key:
            from integrations.omdb_client import OmdbClient
            omdb_client = OmdbClient(config.omdb_api_key)

        spotify_client = None
        if config.spotify_client_id and config.spotify_client_secret:
            from integrations.spotify_client import SpotifyClient
            spotify_client = SpotifyClient(config.spotify_client_id, config.spotify_client_secret)

        db_conn = connect()
        media_repo = MediaRepository(db_conn)

        self.recommender_service = RecommenderService(
            tmdb_client=tmdb_client,
            omdb_client=omdb_client,
            spotify_client=spotify_client,
            media_repository=media_repo,
        )

        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 720)
        self.setStyleSheet(APP_STYLESHEET)

        self.chatbot_panel = ChatbotPanel()
        self.recommendation_panel = RecommendationPanel()
        self.chatbot_panel.submitted.connect(self.handle_user_prompt)

        self.setMenuBar(self._build_menu())
        self.setCentralWidget(self._build_content())
        self.recommendation_panel.show_recommendations([])

    def _build_menu(self) -> QMenuBar:
        menu_bar = QMenuBar()
        app_menu = menu_bar.addMenu("App")

        settings_action = app_menu.addAction("Provider Settings")
        settings_action.triggered.connect(self.open_settings)

        about_action = app_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

        return menu_bar

    def _build_content(self) -> QWidget:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(18, 16, 18, 18)
        root_layout.setSpacing(14)

        title = QLabel(APP_TITLE)
        title.setObjectName("Title")
        if self.config.tmdb_api_key:
            media_status = "TMDB live"
        elif self.config.omdb_api_key:
            media_status = "OMDb live"
        else:
            media_status = "sample data (no API key)"
        subtitle = QLabel(
            f"Natural language chatbot + modular recommendation engine. "
            f"AI: offline provider | Media: {media_status}."
        )
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)

        splitter = QSplitter()
        splitter.addWidget(self._wrap_panel("Chatbot", self.chatbot_panel))
        splitter.addWidget(self._wrap_panel("Recommendations", self.recommendation_panel))
        splitter.setSizes([520, 660])

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(splitter, stretch=1)
        return root

    def _wrap_panel(self, title: str, widget: QWidget) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label = QLabel(title)
        label.setStyleSheet("font-weight: 700; font-size: 16px;")

        layout.addWidget(label)
        layout.addWidget(widget, stretch=1)
        return panel

    def handle_user_prompt(self, text: str, ai_mode: str, media_type: str) -> None:
        self.chatbot_panel.append_user_message(text)

        chat_result = self.chat_service.respond(
            user_message=text,
            mode=ai_mode,
            context={"media_type": media_type},
        )
        self.chatbot_panel.append_assistant_message(chat_result.text, chat_result.provider_name)

        recommendations = self.recommender_service.recommend(
            user_prompt=text,
            selected_media_type=media_type,
        )
        self.recommendation_panel.show_recommendations(recommendations)

    def open_settings(self) -> None:
        SettingsDialog(self.config).exec()

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            (
                "Desktop Multimedia Recommender\n\n"
                "First iteration: PyQt GUI, provider-based chatbot, "
                "and explainable recommendation engine scaffold."
            ),
        )
