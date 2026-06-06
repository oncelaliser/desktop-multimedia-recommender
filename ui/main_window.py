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

        self.intent_parser = self._build_intent_parser(config)
        self.recommender_service = RecommenderService(
            tmdb_client=tmdb_client,
            omdb_client=omdb_client,
            spotify_client=spotify_client,
            media_repository=media_repo,
            intent_parser=self.intent_parser,
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
        if self.config.openai_api_key:
            intent_status = f"LLM ({self.config.openai_model})"
        elif self.config.lmstudio_model:
            intent_status = f"LM Studio ({self.config.lmstudio_model})"
        else:
            intent_status = "keyword parser"
        subtitle = QLabel(
            f"Natural language chatbot + modular recommendation engine. "
            f"Intent: {intent_status} | Media: {media_status}."
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

        # Preferred path: a single LLM call returns BOTH the chatbot reply and the
        # structured intent. This guarantees the left panel's answer and the right
        # panel's recommendations describe the same titles, and halves API usage
        # (avoiding the rate-limit races that desynced the two panels before).
        shared_intent = None
        reply = None
        provider_name = None
        llm_mode = ai_mode == "OpenAI-Compatible API"
        analyze = getattr(self.intent_parser, "analyze", None)
        if llm_mode and callable(analyze):
            reply, shared_intent = analyze(text)
            provider_name = self.config.openai_model

        if shared_intent is None:
            shared_intent = self.intent_parser.parse(text)

        recommendations = self.recommender_service.recommend(
            user_prompt=text,
            selected_media_type=media_type,
            parsed_intent=shared_intent,
        )

        if reply is not None:
            # Unified LLM path succeeded — reply and recommendations share one intent.
            self.chatbot_panel.append_assistant_message(reply, provider_name or "LLM")
        elif llm_mode:
            # LLM mode but the unified call failed (e.g. rate limit). Do NOT make a
            # separate chat call — that's what desynced the panels before. Instead build
            # the reply FROM the actual recommendations so left always matches right.
            self.chatbot_panel.append_assistant_message(
                self._reply_from_recommendations(recommendations),
                "fallback (API limiti)",
            )
        else:
            # Non-LLM chat providers (Offline Basic, LM Studio) — use chat service.
            chat_result = self.chat_service.respond(
                user_message=text,
                mode=ai_mode,
                context={"media_type": media_type},
            )
            self.chatbot_panel.append_assistant_message(chat_result.text, chat_result.provider_name)

        self.recommendation_panel.show_recommendations(recommendations)

    @staticmethod
    def _reply_from_recommendations(recommendations: list) -> str:
        """Build a chatbot reply from the actual recommendation list, so the left panel
        stays consistent with the right even when the LLM call failed."""
        if not recommendations:
            return "Şu an uygun bir öneri bulamadım. Aramanı biraz farklı ifade eder misin?"
        titles = []
        for rec in recommendations[:5]:
            year = f" ({rec.media.release_year})" if rec.media.release_year else ""
            titles.append(f"{rec.media.title}{year}")
        listed = ", ".join(titles)
        return f"İşte sana uygun önerilerim: {listed}. Sağdaki listede detaylarını görebilirsin."

    def _build_intent_parser(self, config: AppConfig):
        from core.chatbot.intent_parser import IntentParser
        keyword_parser = IntentParser()
        if config.openai_api_key:
            try:
                from core.chatbot.llm_intent_parser import LLMIntentParser
                return LLMIntentParser(
                    base_url=config.openai_base_url,
                    api_key=config.openai_api_key,
                    model=config.openai_model,
                    fallback=keyword_parser,
                )
            except Exception:
                pass
        # Try LM Studio if running (no key needed, just check base URL is set)
        if config.lmstudio_base_url and config.lmstudio_model:
            try:
                import requests as _req
                _req.get(f"{config.lmstudio_base_url}/models", timeout=1)
                from core.chatbot.llm_intent_parser import LLMIntentParser
                return LLMIntentParser(
                    base_url=config.lmstudio_base_url,
                    api_key=None,
                    model=config.lmstudio_model,
                    fallback=keyword_parser,
                )
            except Exception:
                pass
        return keyword_parser

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
