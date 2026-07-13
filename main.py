from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BEIJING = ZoneInfo("Asia/Shanghai")
NOW_UTC = datetime.now(UTC)
CUTOFF = NOW_UTC - timedelta(hours=24)
REPORT_DATE = datetime.now(BEIJING).strftime("%Y-%m-%d")


# 使用多个查询，分别覆盖资本市场、融资、基础设施和监管。
SEARCH_QUERIES = [
    (
        '(AI OR "artificial intelligence") '
        '(earnings OR revenue OR stock OR shares OR valuation OR capex) '
        "when:1d"
    ),
    (
        '(AI OR "artificial intelligence") '
        '(funding OR IPO OR acquisition OR merger OR investment OR order) '
        "when:1d"
    ),
    (
        '("AI chip" OR GPU OR HBM OR semiconductor OR "data center") '
        '(demand OR supply OR capex OR revenue OR order) '
        "when:1d"
    ),
    (
        '(AI OR "artificial intelligence") '
        '(regulation OR "export controls" OR copyright '
        "OR antitrust OR procurement) "
        "when:1d"
    ),
    (
        "(OpenAI OR Anthropic OR Nvidia OR Microsoft "
        "OR Google OR Meta OR Amazon) "
        "(AI OR model OR cloud) "
        "when:1d"
    ),
]


# 数值越高，来源优先级越高。
SOURCE_WEIGHTS = {
    "reuters": 14,
    "bloomberg": 14,
    "financial times": 14,
    "the wall street journal": 14,
    "wall street journal": 14,
    "cnbc": 11,
    "associated press": 11,
    "ap news": 11,
    "nikkei asia": 11,
    "bbc": 9,
    "sec.gov": 14,
    "securities and exchange commission": 14,
    "european commission": 12,
    "department of commerce": 12,
    "nvidia": 9,
    "microsoft": 9,
    "google": 9,
    "meta": 9,
    "amazon": 9,
    "openai": 9,
    "anthropic": 9,
    "techcrunch": 7,
    "the verge": 6,
    "venturebeat": 5,
}


# 资本市场相关关键词评分。
KEYWORD_WEIGHTS = {
    "earnings": 6,
    "revenue": 5,
    "profit": 5,
    "margin": 5,
    "guidance": 6,
    "shares": 5,
    "stock": 5,
    "valuation": 6,
    "ipo": 8,
    "funding": 6,
    "acquisition": 8,
    "acquire": 7,
    "merger": 8,
    "investment": 5,
    "order": 5,
    "contract": 6,
    "capex": 7,
    "capital expenditure": 7,
    "gpu": 6,
    "hbm": 7,
    "semiconductor": 5,
    "chip": 5,
    "data center": 6,
    "datacenter": 6,
    "cloud": 4,
    "power": 4,
    "electricity": 5,
    "export control": 8,
    "regulation": 6,
    "regulator": 6,
    "copyright": 6,
    "lawsuit": 6,
    "antitrust": 7,
    "government": 3,
    "procurement": 6,
    "price": 4,
    "pricing": 4,
    "users": 3,
    "subscriber": 4,
}


# 降低营销稿和低价值内容的排名。
NEGATIVE_TERMS = {
    "sponsored": -10,
    "webinar": -8,
    "top 10": -7,
    "best ai tools": -8,
    "how to": -5,
    "opinion": -2,
    "award": -5,
}


CATEGORY_RULES = [
    (
        "监管与政策",
        {
            "regulation",
            "regulator",
            "export control",
            "copyright",
            "lawsuit",
            "antitrust",
            "government",
            "procurement",
        },
        (
            "监管、出口限制或诉讼可能改变市场准入、"
            "合规成本与风险溢价。"
        ),
    ),
    (
        "融资、IPO与并购",
        {
            "funding",
            "ipo",
            "acquisition",
            "acquire",
            "merger",
            "investment",
        },
        (
            "融资或交易定价可能成为同类公司的估值参照，"
            "并影响一级与二级市场风险偏好。"
        ),
    ),
    (
        "业绩与估值",
        {
            "earnings",
            "revenue",
            "profit",
            "margin",
            "guidance",
            "shares",
            "stock",
            "valuation",
        },
        (
            "市场可能据此重新评估收入增速、利润率、"
            "订单能见度与当前估值是否匹配。"
        ),
    ),
    (
        "芯片与AI基础设施",
        {
            "gpu",
            "hbm",
            "semiconductor",
            "chip",
            "data center",
            "datacenter",
            "cloud",
            "power",
            "electricity",
            "capex",
        },
        (
            "该信息可能影响算力、存储、云服务、数据中心、"
            "电力及半导体供应链的需求预期。"
        ),
    ),
    (
        "商业化与重大订单",
        {
            "order",
            "contract",
            "price",
            "pricing",
            "users",
            "subscriber",
        },
        (
            "需要跟踪订单兑现、定价、客户增长及其对收入"
            "和利润率的实际贡献。"
        ),
    ),
]


AI_TERMS = {
    " ai ",
    "artificial intelligence",
    "openai",
    "anthropic",
    "nvidia",
    "gpu",
    "large language model",
    "llm",
    "machine learning",
}


@dataclass
class Article:
    title: str
    link: str
    source: str
    published: datetime
    summary: str
    score: int = 0
    category: str = "AI行业动态"
    observation: str = (
        "需要继续跟踪其对竞争格局、成本曲线和"
        "商业化路径的实际影响。"
    )
    source_weight: int = 0


def google_news_url(query: str) -> str:
    """生成公开新闻RSS搜索地址。"""
    params = urllib.parse.urlencode(
        {
            "q": query,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        }
    )
    return f"https://news.google.com/rss/search?{params}"


def fetch_bytes(url: str) -> bytes:
    """下载RSS内容。"""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "daily-market-brief/1.0 "
                "(https://github.com/"
                "catherinejiaoyt-a11y/daily-market-brief)"
            )
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        return response.read()


def first_text(
    node: ET.Element,
    tags: list[str],
) -> str:
    for tag in tags:
        found = node.find(tag)

        if found is not None and found.text:
            return found.text.strip()

    return ""


def clean_text(value: str) -> str:
    """清除HTML标签和多余空格。"""
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def parse_feed(data: bytes) -> list[Article]:
    """兼容常见RSS与Atom格式。"""
    root = ET.fromstring(data)
    articles: list[Article] = []

    rss_items = root.findall(".//item")

    if rss_items:
        for item in rss_items:
            title = clean_text(
                first_text(item, ["title"])
            )
            link = first_text(item, ["link"])
            published = parse_datetime(
                first_text(
                    item,
                    ["pubDate", "date"],
                )
            )
            summary = clean_text(
                first_text(
                    item,
                    ["description", "summary"],
                )
            )

            source_node = item.find("source")
            source = ""

            if (
                source_node is not None
                and source_node.text
            ):
                source = clean_text(source_node.text)

            if source and title.endswith(
                f" - {source}"
            ):
                title = title[
                    : -(len(source) + 3)
                ]
            elif not source and " - " in title:
                title, source = title.rsplit(
                    " - ",
                    1,
                )

            if title and link and published:
                articles.append(
                    Article(
                        title=title,
                        link=link,
                        source=source or "Unknown source",
                        published=published,
                        summary=summary,
                    )
                )

        return articles

    # Atom格式
    for entry in root.findall(".//{*}entry"):
        title = clean_text(
            first_text(
                entry,
                ["{*}title"],
            )
        )
        published = parse_datetime(
            first_text(
                entry,
                [
                    "{*}published",
                    "{*}updated",
                ],
            )
        )
        summary = clean_text(
            first_text(
                entry,
                [
                    "{*}summary",
                    "{*}content",
                ],
            )
        )

        link = ""

        for link_node in entry.findall(
            "{*}link"
        ):
            href = link_node.attrib.get(
                "href",
                "",
            )
            rel = link_node.attrib.get(
                "rel",
                "alternate",
            )

            if href and rel in (
                "alternate",
                "",
            ):
                link = href
                break

        source = first_text(
            entry,
            [
                "{*}source/{*}title",
                "{*}author/{*}name",
            ],
        )

        if title and link and published:
            articles.append(
                Article(
                    title=title,
                    link=link,
                    source=source or "Unknown source",
                    published=published,
                    summary=summary,
                )
            )

    return articles


def source_score(source: str) -> int:
    lowered = source.lower()

    scores = [
        weight
        for name, weight in SOURCE_WEIGHTS.items()
        if name in lowered
    ]

    return max(scores, default=0)


def classify(
    text: str,
) -> tuple[str, str]:
    lowered = text.lower()

    for (
        category,
        terms,
        observation,
    ) in CATEGORY_RULES:
        if any(
            term in lowered
            for term in terms
        ):
            return category, observation

    return (
        "重要模型与竞争格局",
        (
            "只有在该进展明显改变能力、成本或商业化"
            "路径时，才可能对相关公司的估值产生实质影响。"
        ),
    )


def score_article(
    article: Article,
) -> Article:
    searchable = (
        f" {article.title} "
        f"{article.summary} "
    ).lower()

    article.source_weight = source_score(
        article.source
    )
    score = article.source_weight

    for keyword, weight in (
        KEYWORD_WEIGHTS.items()
    ):
        if keyword in searchable:
            score += weight

    for keyword, weight in (
        NEGATIVE_TERMS.items()
    ):
        if keyword in searchable:
            score += weight

    if any(
        term in searchable
        for term in AI_TERMS
    ):
        score += 5
    else:
        score -= 20

    age_hours = (
        NOW_UTC - article.published
    ).total_seconds() / 3600

    if age_hours <= 6:
        score += 4
    elif age_hours <= 12:
        score += 2

    (
        article.category,
        article.observation,
    ) = classify(searchable)

    article.score = score
    return article


def title_tokens(title: str) -> set[str]:
    words = set(
        re.findall(
            r"[a-z0-9]+",
            title.lower(),
        )
    )

    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "for",
        "in",
        "on",
        "with",
        "as",
        "at",
        "from",
        "by",
        "is",
        "are",
        "its",
        "after",
    }

    return words - stopwords


def is_duplicate(
    article: Article,
    selected: list[Article],
) -> bool:
    current = title_tokens(article.title)

    if not current:
        return False

    for existing in selected:
        other = title_tokens(
            existing.title
        )
        union = current | other

        if (
            union
            and len(current & other)
            / len(union)
            >= 0.55
        ):
            return True

    return False


def collect_articles() -> list[Article]:
    candidates: list[Article] = []

    for query in SEARCH_QUERIES:
        url = google_news_url(query)

        try:
            feed_articles = parse_feed(
                fetch_bytes(url)
            )
            candidates.extend(
                feed_articles
            )
            print(
                "Fetched",
                len(feed_articles),
                "items.",
            )
        except Exception as exc:
            print(
                (
                    "Warning: failed to "
                    f"fetch query: {exc}"
                ),
                file=sys.stderr,
            )

    recent = [
        score_article(article)
        for article in candidates
        if (
            CUTOFF
            <= article.published
            <= NOW_UTC
            + timedelta(minutes=10)
        )
    ]

    recent.sort(
        key=lambda item: (
            item.score,
            item.published,
        ),
        reverse=True,
    )

    selected: list[Article] = []

    # 第一轮：优先选择可信来源。
    for article in recent:
        if (
            article.source_weight < 5
            or article.score < 10
        ):
            continue

        if not is_duplicate(
            article,
            selected,
        ):
            selected.append(article)

        if len(selected) == 8:
            return selected

    # 第二轮：若不足8条，用高相关候选补足。
    for article in recent:
        if (
            article in selected
            or article.score < 10
        ):
            continue

        if not is_duplicate(
            article,
            selected,
        ):
            selected.append(article)

        if len(selected) == 8:
            break

    return selected


def build_report(
    articles: list[Article],
) -> str:
    lines = [
        f"AI资本日报｜{REPORT_DATE}",
        "",
        (
            "说明：无AI API试运行版。程序依据公开RSS"
            "进行规则筛选与去重；英文标题保留原文，"
            "请以来源页面为准。"
        ),
        "",
    ]

    if not articles:
        lines.extend(
            [
                (
                    "过去24小时内未抓取到满足规则的"
                    "候选信息。"
                ),
                (
                    "请在 GitHub Actions 日志中检查"
                    "网络或RSS来源状态。"
                ),
            ]
        )
        return "\n".join(lines)

    for index, article in enumerate(
        articles,
        start=1,
    ):
        local_time = (
            article.published
            .astimezone(BEIJING)
            .strftime("%m-%d %H:%M")
        )

        confirmation = (
            "；待确认"
            if article.source_weight < 5
            else ""
        )

        lines.extend(
            [
                (
                    f"{index}. 标题："
                    f"{article.title}"
                ),
                (
                    f"摘要：{article.source} "
                    f"于北京时间 {local_time} "
                    "发布或报道该消息。"
                    f"规则将其归入“{article.category}”"
                    f"{confirmation}。"
                ),
                (
                    "资本市场观察："
                    f"{article.observation}"
                    "不构成投资建议。"
                ),
                f"来源：{article.link}",
                "",
            ]
        )

    category_counts: dict[str, int] = {}

    for article in articles:
        category_counts[article.category] = (
            category_counts.get(
                article.category,
                0,
            )
            + 1
        )

    main_theme = max(
        category_counts,
        key=category_counts.get,
    )

    lines.extend(
        [
            "今日主线",
            (
                "今日入选信息主要集中在"
                f"“{main_theme}”。建议结合公司公告、"
                "监管文件与后续市场表现继续核验。"
            ),
        ]
    )

    return "\n".join(lines).strip()


def save_report(report: str) -> Path:
    output_dir = Path("reports")
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"{REPORT_DATE}.md"
    )

    output_path.write_text(
        report + "\n",
        encoding="utf-8",
    )

    return output_path


def send_to_feishu(report: str) -> None:
    webhook_url = os.environ.get(
        "FEISHU_WEBHOOK_URL",
        "",
    ).strip()

    if not webhook_url:
        raise RuntimeError(
            "没有读取到 FEISHU_WEBHOOK_URL。"
        )

    payload = {
        "msg_type": "text",
        "content": {
            "text": report,
        },
    }

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8"),
        headers={
            "Content-Type": (
                "application/json; "
                "charset=utf-8"
            )
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        body = response.read().decode(
            "utf-8",
            errors="replace",
        )
        print(
            "Feishu response:",
            body,
        )

        result = json.loads(body)

        code = result.get("code")
        status_code = result.get(
            "StatusCode"
        )

        if (
            code not in (None, 0)
            or status_code not in (None, 0)
        ):
            raise RuntimeError(
                f"飞书返回错误：{result}"
            )


def main() -> None:
    articles = collect_articles()
    report = build_report(articles)

    output_path = save_report(report)
    print(
        f"Saved report to {output_path}"
    )
    print(report)

    send_to_feishu(report)
    print(
        "Report sent to Feishu successfully."
    )


if __name__ == "__main__":
    main()
