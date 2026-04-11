from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from bson import ObjectId
from pymongo import DESCENDING, MongoClient, ReturnDocument

from app.config import Settings
from app.schemas import (
    DatasetAnalyticsResponse,
    DetectionMeta,
    HistoryDetailResponse,
    HistoryListResponse,
    HistoryRecordSummary,
    HistorySummaryResponse,
    KnowledgeListResponse,
    KnowledgeStatsResponse,
    ManualResponse,
    ReviewUpdateRequest,
)


DEFAULT_MANUAL_SECTIONS = [
    {
        "id": "quick-start",
        "title": "快速开始",
        "summary": "从输入新闻到查看报告，全流程只需要几步。",
        "bullets": [
            "在首页点击“开始检测”，填写新闻标题并上传新闻图片。",
            "系统会并行调度文本真实性、视觉真实性和跨模态一致性三个智能体。",
            "综合裁决智能体汇总证据后，会生成最终结论与 PDF 报告。",
        ],
        "highlights": [
            "建议上传清晰、完整的新闻配图，以提升视觉分析质量。",
            "标题尽量保留原始表述，避免人工改写导致的语义漂移。",
        ],
    },
    {
        "id": "knowledge-base",
        "title": "知识库使用说明",
        "summary": "知识库用于浏览典型图文对案例，辅助复查与经验沉淀。",
        "bullets": [
            "可按真假分类、失真类型和关键词筛选历史样本。",
            "点击卡片可查看样本的推理摘要，便于对照当前检测任务。",
            "知识库适合作为人工复查前的参考样例库，而不是最终裁决依据。",
        ],
        "highlights": [
            "优先关注与当前事件领域相近的样本，比如灾害、名人、体育赛事等。",
            "遇到图文不一致样例时，重点比对图片语义与标题实体是否同源。",
        ],
    },
    {
        "id": "history-review",
        "title": "历史记录与人工复查",
        "summary": "所有检测任务会自动进入历史记录，支持人工标注与纠偏。",
        "bullets": [
            "复查状态分为待复查、复查确认、人工改判和继续跟进。",
            "复查时可补充人工结论、备注和复查人，形成可追踪的审核链路。",
            "建议在改判时明确记录证据来源，以便后续追溯与复盘。",
        ],
        "highlights": [
            "若模型结论可信但证据不足，可标记为“继续跟进”。",
            "若人工结论与模型结论冲突，优先保留人工复查意见并说明理由。",
        ],
    },
    {
        "id": "operations",
        "title": "运行维护建议",
        "summary": "保证知识库、手册和历史记录统一由 MongoDB 管理，便于部署与扩展。",
        "bullets": [
            "确认 `MONGO_URI` 指向可写实例，并预先导入知识库样本集合。",
            "检测图片默认保存在后端 `storage/detections` 目录，并通过静态资源对外访问。",
            "如需替换知识库图片目录，可配置 `KNOWLEDGE_MEDIA_DIR`。",
        ],
        "highlights": [
            "建议定期备份 `detection_history` 与 `system_manual` 集合。",
            "生产环境部署时，应限制 MongoDB 网络访问范围并配置认证。",
        ],
    },
]


class MongoContentService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = MongoClient(settings.mongo_uri)
        self.db = self.client[settings.mongo_db]
        self.knowledge_zh = self.db[settings.knowledge_collection_zh]
        self.knowledge_en = self.db[settings.knowledge_collection_en]
        self.history = self.db[settings.history_collection]
        self.manual = self.db[settings.manual_collection]
        self._ensure_indexes()

    def close(self) -> None:
        self.client.close()

    def _ensure_indexes(self) -> None:
        self.history.create_index([("created_at", DESCENDING)])
        self.history.create_index("review_status")
        self.manual.create_index("key", unique=True)

    def ensure_manual_seed(self) -> None:
        now = datetime.now(timezone.utc)
        self.manual.update_one(
            {"key": "system_manual"},
            {
                "$setOnInsert": {
                    "key": "system_manual",
                    "updated_at": now,
                    "sections": DEFAULT_MANUAL_SECTIONS,
                }
            },
            upsert=True,
        )

    def list_knowledge(
        self,
        *,
        base_url: str,
        lang: str,
        page: int,
        page_size: int,
        fake_type: str | None = None,
        binary_fake_type: str | None = None,
        theme: str | None = None,
        search: str | None = None,
        random_sample: bool = False,
    ) -> KnowledgeListResponse:
        collection = self.knowledge_zh if lang == "zh" else self.knowledge_en
        query: dict[str, object] = {}

        if fake_type:
            fake_type_values = self._expand_fake_type_aliases(fake_type)
            query["Final_answers.fake_type"] = (
                fake_type_values[0] if len(fake_type_values) == 1 else {"$in": fake_type_values}
            )
        if binary_fake_type:
            binary_values = self._expand_binary_fake_type_aliases(binary_fake_type)
            query["Final_answers.binary_fake_type"] = (
                binary_values[0] if len(binary_values) == 1 else {"$in": binary_values}
            )
        if theme:
            theme_query = self._build_theme_query(theme)
            if theme_query:
                query["$or"] = theme_query
        if search:
            query["Basic_info.News_Caption"] = {"$regex": search, "$options": "i"}

        total = collection.count_documents(query)
        total_pages = (total + page_size - 1) // page_size if total else 0
        items = []
        if random_sample and total:
            pipeline = []
            if query:
                pipeline.append({"$match": query})
            pipeline.append({"$sample": {"size": min(page_size, total)}})
            docs = collection.aggregate(pipeline)
        else:
            docs = (
                collection.find(query)
                .sort("_id", DESCENDING)
                .skip((page - 1) * page_size)
                .limit(page_size)
            )

        for doc in docs:
            items.append(self._serialize_knowledge_item(doc=doc, base_url=base_url))

        return KnowledgeListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items,
        )

    def _serialize_knowledge_item(self, *, doc: dict, base_url: str) -> dict:
        basic = doc.get("Basic_info", {})
        final = doc.get("Final_answers", {})
        return {
            "id": str(doc["_id"]),
            "title": basic.get("News_Caption", ""),
            "image_url": self._build_knowledge_image_url(base_url, basic.get("image_path", "")),
            "fake_type": final.get("fake_type", ""),
            "binary_fake_type": final.get("binary_fake_type", ""),
            "theme": self._classify_knowledge_theme(
                basic.get("image_path", ""),
                basic.get("source", ""),
            ),
            "reasoning": final.get("reasoning", ""),
            "dataset": doc.get("dataset", "MMFakeBench"),
            "source": basic.get("source", ""),
        }

    def get_knowledge_stats(self, *, lang: str) -> KnowledgeStatsResponse:
        collection = self.knowledge_zh if lang == "zh" else self.knowledge_en
        total = collection.count_documents({})
        fake_type_stats = list(
            collection.aggregate(
                [
                    {"$group": {"_id": "$Final_answers.fake_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                ]
            )
        )
        binary_stats = list(
            collection.aggregate(
                [{"$group": {"_id": "$Final_answers.binary_fake_type", "count": {"$sum": 1}}}]
            )
        )
        return KnowledgeStatsResponse(
            total=total,
            fake_type_stats={item["_id"] or "unknown": item["count"] for item in fake_type_stats},
            binary_stats={item["_id"] or "unknown": item["count"] for item in binary_stats},
        )

    def get_dataset_analytics(self) -> DatasetAnalyticsResponse:
        dataset_root = self._resolve_dataset_root()
        if not dataset_root.exists():
            return DatasetAnalyticsResponse()

        folders = []
        split_stats = {"fake": 0, "real": 0}
        theme_stats: dict[str, int] = {}
        technique_stats: dict[str, int] = {}

        for split in ("fake", "real"):
            split_dir = dataset_root / split
            if not split_dir.exists():
                continue

            for folder in sorted(split_dir.iterdir(), key=lambda item: item.name.lower()):
                if not folder.is_dir():
                    continue

                count = sum(1 for child in folder.iterdir() if child.is_file())
                if not count:
                    continue

                theme = self._classify_dataset_theme(folder.name)
                technique = self._classify_dataset_technique(folder.name, split)

                split_stats[split] = split_stats.get(split, 0) + count
                theme_stats[theme] = theme_stats.get(theme, 0) + count
                technique_stats[technique] = technique_stats.get(technique, 0) + count
                folders.append(
                    {
                        "name": folder.name,
                        "split": split,
                        "count": count,
                        "theme": theme,
                        "technique": technique,
                    }
                )

        folders.sort(key=lambda item: (-item["count"], item["name"].lower()))
        total = split_stats.get("fake", 0) + split_stats.get("real", 0)

        return DatasetAnalyticsResponse(
            total=total,
            fake_total=split_stats.get("fake", 0),
            real_total=split_stats.get("real", 0),
            folder_total=len(folders),
            split_stats=split_stats,
            theme_stats=dict(sorted(theme_stats.items(), key=lambda item: (-item[1], item[0]))),
            technique_stats=dict(sorted(technique_stats.items(), key=lambda item: (-item[1], item[0]))),
            folders=folders,
        )

    def list_history(
        self,
        *,
        base_url: str,
        page: int,
        page_size: int,
        review_status: str | None = None,
        search: str | None = None,
    ) -> HistoryListResponse:
        query: dict[str, object] = {}
        if review_status:
            query["review_status"] = review_status
        if search:
            query["title"] = {"$regex": search, "$options": "i"}

        total = self.history.count_documents(query)
        total_pages = (total + page_size - 1) // page_size if total else 0
        cursor = (
            self.history.find(query)
            .sort("created_at", DESCENDING)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )

        return HistoryListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[self._serialize_history_summary(doc, base_url) for doc in cursor],
        )

    def get_history_summary(self) -> HistorySummaryResponse:
        total = self.history.count_documents({})
        counts = {
            item["_id"]: item["count"]
            for item in self.history.aggregate(
                [{"$group": {"_id": "$review_status", "count": {"$sum": 1}}}]
            )
        }
        return HistorySummaryResponse(
            total=total,
            pending_review=counts.get("pending", 0),
            approved_count=counts.get("approved", 0),
            corrected_count=counts.get("corrected", 0),
            flagged_count=counts.get("flagged", 0),
        )

    def get_history_detail(self, *, record_id: str, base_url: str) -> HistoryDetailResponse:
        doc = self.history.find_one({"_id": self._parse_object_id(record_id)})
        if not doc:
            raise ValueError("History record not found")

        return HistoryDetailResponse(
            item=self._serialize_history_summary(doc, base_url),
            agents=doc.get("agents", {}),
            judge=doc.get("judge", {}),
            meta=DetectionMeta(**doc.get("meta", {})),
        )

    def delete_history_record(self, *, record_id: str) -> str:
        doc = self.history.find_one_and_delete({"_id": self._parse_object_id(record_id)})
        if not doc:
            raise ValueError("History record not found")

        self._delete_stored_media(doc.get("image_path", ""))
        return str(doc["_id"])

    def update_history_review(
        self,
        *,
        record_id: str,
        payload: ReviewUpdateRequest,
        base_url: str,
    ) -> HistoryRecordSummary:
        now = datetime.now(timezone.utc)
        result = self.history.find_one_and_update(
            {"_id": self._parse_object_id(record_id)},
            {
                "$set": {
                    "review_status": payload.review_status or "pending",
                    "updated_at": now,
                    "review": {
                        "manual_verdict": payload.manual_verdict.strip(),
                        "notes": payload.notes.strip(),
                        "reviewer": payload.reviewer.strip(),
                        "reviewed_at": now,
                    },
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            raise ValueError("History record not found")
        return self._serialize_history_summary(result, base_url)

    def get_manual(self) -> ManualResponse:
        self.ensure_manual_seed()
        doc = self.manual.find_one({"key": "system_manual"}) or {}
        return ManualResponse(
            updated_at=self._serialize_datetime(doc.get("updated_at")),
            sections=doc.get("sections", []),
        )

    def create_history_record(self, document: dict) -> str:
        result = self.history.insert_one(document)
        return str(result.inserted_id)

    def _serialize_history_summary(self, doc: dict, base_url: str) -> HistoryRecordSummary:
        review = doc.get("review", {})
        verdict = doc.get("verdict", {})
        meta = doc.get("meta", {})
        return HistoryRecordSummary(
            id=str(doc["_id"]),
            title=doc.get("title", ""),
            image_url=self._build_media_url(base_url, doc.get("image_path", "")),
            created_at=self._serialize_datetime(doc.get("created_at")),
            updated_at=self._serialize_datetime(doc.get("updated_at")),
            response_language=meta.get("response_language", ""),
            auto_verdict=verdict.get("verdict", ""),
            auto_category=verdict.get("category", ""),
            auto_confidence=verdict.get("confidence", 0),
            auto_reasoning=verdict.get("reasoning", ""),
            review_status=doc.get("review_status", "pending"),
            manual_verdict=review.get("manual_verdict", ""),
            reviewer=review.get("reviewer", ""),
            reviewed_at=self._serialize_datetime(review.get("reviewed_at")),
            review_notes=review.get("notes", ""),
        )

    def _build_media_url(self, base_url: str, relative_path: str) -> str:
        if not relative_path:
            return ""
        if relative_path.startswith("http://") or relative_path.startswith("https://"):
            return relative_path
        return self._join_url(base_url, "media", relative_path)

    def _classify_knowledge_theme(self, image_path: str, source: str = "") -> str:
        folder_name = self._extract_folder_name_from_image_path(image_path) or source
        return self._classify_dataset_theme(folder_name)

    def _extract_folder_name_from_image_path(self, image_path: str) -> str:
        if not image_path:
            return ""

        raw_path = image_path.replace("\\", "/").strip()
        for prefix in ("./data/", "data/", "/data/"):
            if raw_path.startswith(prefix):
                raw_path = raw_path[len(prefix):]
                break

        parts = [part for part in Path(raw_path).parts if part not in ("", ".", "..")]
        return parts[-2] if len(parts) >= 2 else ""

    def _build_theme_query(self, theme: str) -> list[dict[str, object]]:
        theme_keywords = {
            "政治与公共议题": ["politicat", "fever", "bbc", "guardian", "usa_today", "wash"],
            "娱乐与名人": ["gossipcop", "gossip"],
            "科学与科普": ["science"],
            "新闻报道场景": ["newsclipings"],
            "社交媒体内容": ["fakeddit", "chatgpt"],
            "通用视觉场景": ["coco", "antifact", "dgm4"],
            "文本生成改写": ["llm_rewrite"],
        }

        patterns = theme_keywords.get(str(theme or "").strip(), [])
        conditions: list[dict[str, object]] = []
        for pattern in patterns:
            regex = {"$regex": pattern, "$options": "i"}
            conditions.append({"Basic_info.image_path": regex})
            conditions.append({"Basic_info.source": regex})
        return conditions

    def _resolve_dataset_root(self) -> Path:
        dataset_root = self.settings.knowledge_media_dir / "MMFakeBench_val"
        return dataset_root if dataset_root.exists() else self.settings.knowledge_media_dir

    def _classify_dataset_theme(self, folder_name: str) -> str:
        normalized = folder_name.lower()

        if normalized.startswith(("politicat", "fever", "bbc", "guardian", "usa_today", "wash")):
            return "政治与公共议题"
        if "gossipcop" in normalized or "gossip" in normalized:
            return "娱乐与名人"
        if "science" in normalized:
            return "科学与科普"
        if normalized.startswith("newsclipings"):
            return "新闻报道场景"
        if normalized.startswith(("fakeddit", "chatgpt")):
            return "社交媒体内容"
        if normalized.startswith(("coco", "antifact", "dgm4")):
            return "通用视觉场景"
        if normalized.startswith("llm_rewrite"):
            return "文本生成改写"
        return "综合开放域"

    def _classify_dataset_technique(self, folder_name: str, split: str) -> str:
        if split == "real":
            return "真实样本"

        normalized = folder_name.lower()
        if "image_edit" in normalized or "photo_edit" in normalized:
            return "图像编辑"
        if "text_edit" in normalized:
            return "文本编辑"
        if "rewrite" in normalized:
            return "文本改写"
        if "midjourney" in normalized or "generation" in normalized or "_ai_" in normalized:
            return "AIGC生成"
        if any(keyword in normalized for keyword in ("match", "semantic", "scene", "person")):
            return "图文错配"
        return "其他伪造"

    def _expand_fake_type_aliases(self, value: str) -> list[str]:
        normalized = str(value or "").strip()
        aliases = {
            "original": ["original", "Original", "原始新闻", "真实", "真实新闻"],
            "真实新闻": ["original", "Original", "原始新闻", "真实", "真实新闻"],
            "原始新闻": ["original", "Original", "原始新闻", "真实", "真实新闻"],
            "真实": ["original", "Original", "原始新闻", "真实", "真实新闻"],
            "textual_veracity_distortion": [
                "textual_veracity_distortion",
                "Textual Distortion",
                "文本事实失真",
                "文本虚假",
            ],
            "文本事实失真": [
                "textual_veracity_distortion",
                "Textual Distortion",
                "文本事实失真",
                "文本虚假",
            ],
            "文本虚假": [
                "textual_veracity_distortion",
                "Textual Distortion",
                "文本事实失真",
                "文本虚假",
            ],
            "visual_veracity_distortion": [
                "visual_veracity_distortion",
                "Visual Distortion",
                "视觉事实失真",
                "视觉虚假",
            ],
            "视觉事实失真": [
                "visual_veracity_distortion",
                "Visual Distortion",
                "视觉事实失真",
                "视觉虚假",
            ],
            "视觉虚假": [
                "visual_veracity_distortion",
                "Visual Distortion",
                "视觉事实失真",
                "视觉虚假",
            ],
            "mismatch": ["mismatch", "Mismatch", "图文不匹配", "图文不一致"],
            "图文不匹配": ["mismatch", "Mismatch", "图文不匹配", "图文不一致"],
            "图文不一致": ["mismatch", "Mismatch", "图文不匹配", "图文不一致"],
        }
        values = aliases.get(normalized, [normalized])
        return list(dict.fromkeys(item for item in values if item))

    def _expand_binary_fake_type_aliases(self, value: str) -> list[str]:
        normalized = str(value or "").strip()
        aliases = {
            "True": ["True", "真实", "true"],
            "真实": ["True", "真实", "true"],
            "Fake": ["Fake", "虚假", "fake"],
            "虚假": ["Fake", "虚假", "fake"],
            "Uncertain": ["Uncertain", "待定", "uncertain"],
            "待定": ["Uncertain", "待定", "uncertain"],
        }
        values = aliases.get(normalized, [normalized])
        return list(dict.fromkeys(item for item in values if item))

    def _build_knowledge_image_url(self, base_url: str, image_path: str) -> str:
        if not image_path:
            return ""
        if image_path.startswith("http://") or image_path.startswith("https://"):
            return image_path

        raw_path = image_path.replace("\\", "/").strip()
        for prefix in ("./data/", "data/", "/data/"):
            if raw_path.startswith(prefix):
                raw_path = raw_path[len(prefix):]
                break

        return self._join_url(base_url, "knowledge-media", raw_path)

    def _join_url(self, base_url: str, mount_name: str, relative_path: str) -> str:
        clean_base = base_url.rstrip("/")
        parts = [quote(part) for part in Path(relative_path).parts if part not in ("", ".", "..")]
        suffix = "/".join(parts)
        return f"{clean_base}/{mount_name}/{suffix}" if suffix else f"{clean_base}/{mount_name}"

    def _delete_stored_media(self, relative_path: str) -> None:
        if not relative_path:
            return

        storage_root = self.settings.storage_dir.resolve()
        target_path = (self.settings.storage_dir / relative_path).resolve()

        try:
            target_path.relative_to(storage_root)
        except ValueError:
            return

        if target_path.is_file():
            target_path.unlink()

    def _serialize_datetime(self, value: object) -> str:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return ""

    def _parse_object_id(self, value: str) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid record id")
        return ObjectId(value)

