from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from data.models.recommendation import Recommendation


class RecommendationCard(QFrame):
    def __init__(self, recommendation: Recommendation) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        media = recommendation.media
        year = f" • {media.release_year}" if media.release_year else ""
        genres = ", ".join(media.genres) if media.genres else "Uncategorized"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        title = QLabel(media.title)
        title.setStyleSheet("font-weight: 700; font-size: 16px;")
        title.setWordWrap(True)

        header = QHBoxLayout()
        score_label = QLabel(f"{recommendation.score:.1f}% match")
        score_label.setObjectName("Score")
        header.addWidget(score_label)
        header.addStretch()
        if media.rating is not None:
            rating_label = QLabel(f"★ {media.rating:.1f}")
            rating_label.setStyleSheet("color: #f0a500; font-weight: 600;")
            header.addWidget(rating_label)

        meta = QLabel(f"{media.media_type.title()}{year} • {genres} • {media.source}")
        meta.setObjectName("Muted")
        meta.setWordWrap(True)

        reason = QLabel(recommendation.reason)
        reason.setWordWrap(True)

        layout.addWidget(title)
        layout.addLayout(header)
        layout.addWidget(meta)
        layout.addWidget(reason)


class RecommendationPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        content = QWidget()
        content.setLayout(self.cards_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def show_recommendations(self, recommendations: list[Recommendation]) -> None:
        self.clear()
        if not recommendations:
            empty = QLabel("Henüz öneri yok. Sohbet kutusuna bir istek yaz.")
            empty.setObjectName("Muted")
            empty.setWordWrap(True)
            self.cards_layout.addWidget(empty)
            return

        for recommendation in recommendations:
            self.cards_layout.addWidget(RecommendationCard(recommendation))

    def clear(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
