from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.error
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

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
FINAL_ITEM_COUNT = int(os.getenv("FINAL_ITEM_COUNT", "18"))
MAX_CANDIDATES_FOR_AI = int(os.getenv("MAX_CANDIDATES_FOR_AI", "45"))

CATEGORY_ORDER = [
    "模型与技术",
    "商业动态",
    "政策法规",
    "产品发布",
    "行业应用",
    "安全与治理",
]

CATEGORY_EMOJI = {
    "模型与技术": "🧠",
    "商业动态": "💰",
    "政策法规": "📋",
    "产品发布": "🚀",
    "行业应用": "🏭",
    "安全与治理": "🛡️",
}

FEED_LOCALES = [
    {"hl": "en-US", "gl": "US", "ceid": "US:en"},
    {"hl": "zh-CN", "gl": "CN", "ceid": "CN:zh-Hans"},
]

SEARCH_QUERIES = [
    # 模型与技术
    (
        '(AI OR "artificial intelligence") '
        '(model OR benchmark OR training OR inference OR reasoning '
        'OR multimodal OR "open source" OR agent) when:1d'
    ),
    (
        '(OpenAI OR Anthropic OR DeepSeek OR Google DeepMind OR Meta '
        'OR Mistral OR xAI) '
        '(model OR release OR benchmark OR API OR open-source) when:1d'
    ),
    "人工智能 大模型 模型发布 推理 训练 多模态 智能体 开源 when:1d",

    # 商业动态与AI基础设施
    (
        '(AI OR "artificial intelligence") '
        '(funding OR IPO OR acquisition OR merger OR investment '
        'OR valuation OR earnings OR revenue OR order OR contract) when:1d'
    ),
    (
        '("AI chip" OR GPU OR HBM OR semiconductor OR "data center" '
        'OR cloud OR power OR storage OR networking) '
        '(capex OR demand OR supply OR order OR revenue OR investment) when:1d'
    ),
    "人工智能 融资 IPO 并购 投资 估值 财报 收入 订单 when:1d",
    "人工智能 芯片 算力 数据中心 电力 云服务 存储 网络 资本开支 when:1d",

    # 政策法规
    (
        '(AI OR "artificial intelligence") '
        '(regulation OR "export controls" OR copyright OR antitrust '
        'OR law OR legislation OR procurement OR regulator) when:1d'
    ),
    "人工智能 监管 法规 出口管制 版权 反垄断 政府采购 when:1d",

    # 产品发布
    (
        '(AI OR "artificial intelligence") '
        '(launch OR launches OR released OR product OR app OR API '
        'OR copilot OR assistant OR agent OR feature) when:1d'
    ),
    "人工智能 产品发布 应用 上线 功能 API 助手 智能体 when:1d",

    # 行业应用
    (
        '(AI OR "artificial intelligence") '
        '(healthcare OR finance OR manufacturing OR automotive '
        'OR education OR retail OR enterprise OR robotics) when:1d'
    ),
    "人工智能 医疗 金融 制造 汽车 教育 零售 企业服务 机器人 when:1d",

    # 安全与治理
    (
        '(AI OR "artificial intelligence") '
        '(safety OR security OR governance OR privacy OR deepfake '
        'OR evaluation OR red-team OR alignment OR audit) when:1d'
    ),
    "人工智能 安全 治理 隐私 深度伪造 评测 红队 对齐 审计 when:1d",
]

SOURCE_WEIGHTS = {
    "reuters": 18,
    "路透": 18,
    "bloomberg": 17,
    "彭博": 17,
    "financial times": 17,
    "wall street journal": 17,
    "华尔街日报": 17,
    "associated press": 14,
    "ap news": 14,
    "nikkei asia": 14,
    "日经": 14,
    "cnbc": 13,
    "bbc": 11,
    "sec.gov": 18,
    "securities and exchange commission": 18,
    "european commission": 17,
    "department of commerce": 17,
    "证券时报": 11,
    "中国证券报": 11,
    "上海证券报": 11,
    "第一财经": 11,
    "财联社": 10,
    "界面新闻": 9,
    "36氪": 8,
    "techcrunch": 8,
    "the verge": 7,
    "venturebeat": 6,
    "nvidia": 12,
    "microsoft": 12,
    "google": 12,
    "meta": 12,
    "amazon": 12,
    "openai": 12,
    "anthropic": 12,
    "apple": 12,
    "intel": 12,
    "amd": 12,
    "tsmc": 12,
}

KEYWORD_WEIGHTS = {
    "earnings": 7,
    "财报": 7,
    "revenue": 6,
    "收入": 6,
    "profit": 6,
    "利润": 6,
    "margin": 6,
    "利润率": 6,
    "guidance": 7,
    "指引": 7,
    "stock": 6,
    "shares": 6,
    "股价": 6,
    "valuation": 8,
    "估值": 8,
    "ipo": 10,
    "上市": 8,
    "funding": 8,
    "融资": 8,
    "acquisition": 10,
    "acquire": 9,
    "merger": 10,
    "并购": 10,
    "收购": 10,
    "investment": 7,
    "投资": 7,
    "order": 7,
    "订单": 7,
    "contract": 8,
    "合同": 8,
    "capex": 9,
    "资本开支": 9,
    "gpu": 8,
    "hbm": 9,
    "semiconductor": 7,
    "chip": 7,
    "芯片": 7,
    "data center": 8,
    "datacenter": 8,
    "数据中心": 8,
    "cloud": 5,
    "云服务": 5,
    "power": 6,
    "electricity": 7,
    "电力": 7,
    "export control": 10,
    "出口管制": 10,
    "regulation": 8,
    "监管": 8,
    "copyright": 8,
    "版权": 8,
    "lawsuit": 8,
    "诉讼": 8,
    "antitrust": 9,
    "反垄断": 9,
    "procurement": 8,
    "政府采购": 8,
    "price": 5,
    "pricing": 5,
    "用户": 4,
    "users": 4,
    "model": 4,
    "benchmark": 5,
    "reasoning": 4,
    "multimodal": 4,
    "inference": 4,
    "open source": 4,
    "agent": 4,
    "大模型": 4,
    "模型发布": 5,
    "推理": 4,
    "多模态": 4,
    "开源": 4,
    "智能体": 4,
    "safety": 6,
    "security": 6,
    "governance": 6,
    "privacy": 6,
    "安全": 6,
    "治理": 6,
    "隐私": 6,
    "launch": 5,
    "released": 5,
    "product": 4,
    "app": 3,
    "healthcare": 4,
    "manufacturing": 4,
    "finance": 4,
    "robotics": 4,
    "产品发布": 5,
    "医疗": 4,
    "制造": 4,
    "金融": 4,
    "机器人": 4,
}

NEGATIVE_TERMS = {
    "sponsored": -15,
    "赞助": -15,
    "webinar": -12,
    "网络研讨会": -12,
    "top 10": -10,
    "best ai tools": -12,
    "how to": -8,
    "教程": -8,
    "opinion": -4,
    "评论": -4,
    "award": -8,
    "获奖": -6,
}

AI_TERMS = {
    " ai ",
    "artificial intelligence",
    "人工智能",
    "openai",
    "anthropic",
    "deepseek",
    "nvidia",
    "英伟达",
    "gpu",
    "llm",
    "大模型",
    "machine learning",
    "机器学习",
}


@dataclass
class Article:
    title: str
    link: str
    source: str
    published: datetime
    summary: str
    score: int = 0
    source_weight: int = 0


def google_news_url(query: str, locale: dict[str, str]) -> str:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "hl": locale["hl"],
            "gl": locale["gl"],
            "ceid": locale["ceid"],
        }
    )
    return f"https://news.google.com/rss/search?{params}"


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; daily-market-brief/3.0; "
                "+https://github.com/catherinejiaoyt-a11y/daily-market-brief)"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def first_text(node: ET.Element, tags: list[str]) -> str:
    for tag in tags:
        found = node.find(tag)
        if found is not None and found.text:
            return found.text.strip()
    return ""


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def parse_feed(data: bytes) -> list[Article]:
    root = ET.fromstring(data)
    articles: list[Article] = []

    for item in root.findall(".//item"):
        title = clean_text(first_text(item, ["title"]))
        link = first_text(item, ["link"])
        published = parse_datetime(first_text(item, ["pubDate", "date"]))
        summary = clean_text(first_text(item, ["description", "summary"]))

        source_node = item.find("source")
        source = ""
        if source_node is not None and source_node.text:
            source = clean_text(source_node.text)

        if source and title.endswith(f" - {source}"):
            title = title[: -(len(source) + 3)]
        elif not source and " - " in title:
            title, source = title.rsplit(" - ", 1)

        if title and link and published:
            articles.append(
                Article(
                    title=title,
                    link=link,
                    source=source or "未知来源",
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
        if name.lower() in lowered
    ]
    return max(scores, default=0)


def score_article(article: Article) -> Article:
    text = f" {article.title} {article.summary} ".lower()
    article.source_weight = source_score(article.source)
    score = article.source_weight

    for keyword, weight in KEYWORD_WEIGHTS.items():
        if keyword.lower() in text:
            score += weight

    for keyword, weight in NEGATIVE_TERMS.items():
        if keyword.lower() in text:
            score += weight

    if any(term.lower() in text for term in AI_TERMS):
        score += 7
    else:
        score -= 25

    age_hours = (NOW_UTC - article.published).total_seconds() / 3600
    if age_hours <= 6:
        score += 5
    elif age_hours <= 12:
        score += 3

    article.score = score
    return article


def title_tokens(title: str) -> set[str]:
    words = set(re.findall(r"[\u4e00-\u9fff]|[a-z0-9]+", title.lower()))
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
        "将",
        "的",
        "了",
        "与",
        "和",
        "在",
        "对",
    }
    return words - stopwords


def is_duplicate(article: Article, selected: list[Article]) -> bool:
    current = title_tokens(article.title)
    if not current:
        return False

    for existing in selected:
        other = title_tokens(existing.title)
        union = current | other
        if union and len(current & other) / len(union) >= 0.50:
            return True

    return False


def collect_candidates() -> list[Article]:
    raw_articles: list[Article] = []

    for locale in FEED_LOCALES:
        for query in SEARCH_QUERIES:
            try:
                articles = parse_feed(fetch_bytes(google_news_url(query, locale)))
                raw_articles.extend(articles)
                print(
                    f"Fetched {len(articles)} items for locale={locale['hl']}."
                )
                time.sleep(0.15)
            except Exception as exc:
                print(f"Warning: RSS fetch failed: {exc}", file=sys.stderr)

    recent = [
        score_article(article)
        for article in raw_articles
        if CUTOFF <= article.published <= NOW_UTC + timedelta(minutes=10)
    ]

    recent.sort(
        key=lambda item: (item.score, item.published),
        reverse=True,
    )

    selected: list[Article] = []
    seen_links: set[str] = set()

    for article in recent:
        if article.score < 10 or article.link in seen_links:
            continue

        if is_duplicate(article, selected):
            continue

        selected.append(article)
        seen_links.add(article.link)

        if len(selected) == MAX_CANDIDATES_FOR_AI:
            break

    return selected


def candidate_payload(articles: list[Article]) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []

    for index, article in enumerate(articles, start=1):
        summary = article.summary[:800].strip()
        payload.append(
            {
                "source_index": index,
                "source": article.source,
                "published_beijing": article.published.astimezone(BEIJING).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "original_title": article.title,
                "rss_summary": summary,
                "url": article.link,
                "rule_score": article.score,
            }
        )

    return payload


SYSTEM_PROMPT = """
你是一名严谨的中文AI行业与资本市场情报编辑。
请从用户提供的候选新闻中筛选重要信息，按固定栏目分类，并输出严格合法的JSON。

固定栏目只能使用以下六个名称：
1. 模型与技术
2. 商业动态
3. 政策法规
4. 产品发布
5. 行业应用
6. 安全与治理

分类规则：
- 模型与技术：模型能力、架构、训练、推理、基准、开源、智能体核心技术。
- 商业动态：融资、IPO、并购、投资、订单、财报、收入、估值，以及芯片、
  算力、云、数据中心、电力、存储和网络等产业链商业变化。
- 政策法规：法律、监管、出口管制、版权、反垄断、政府采购和市场准入。
- 产品发布：面向用户或开发者的新产品、App、API、功能、工具和服务上线。
- 行业应用：AI在医疗、金融、制造、汽车、教育、零售、企业服务和机器人等场景落地。
- 安全与治理：AI安全、隐私、深度伪造、评测、红队、模型对齐、审计和治理机制。

必须遵守：
1. 只能使用候选新闻中明确提供的标题、RSS摘要、来源、时间和URL。
2. 不得虚构金额、公司行为、交易条款、股价表现、模型参数、性能结果、因果关系或引语。
3. RSS摘要不足时，在 uncertainty 中写“待确认：公开摘要信息有限”，
   并使用“据标题和摘要显示”“可能”“需跟踪”等谨慎表达。
4. 去除重复事件、低价值营销稿、单纯教程和无实质变化的纯技术细节。
5. 默认选出不超过用户指定数量的高价值信息。高质量信息不足时可以少选，禁止凑数。
6. 在有合格候选信息时，尽量覆盖六个栏目；没有可靠候选时允许某栏目为空。
7. 同一事件只能进入一个最匹配的栏目。
8. title_zh 必须是中文总结标题，不能只是逐字翻译，要说明事件核心变化。
9. news_summary 用2至4句说明什么公司在什么时间发布或被报道了什么。
10. changes 说明相较此前有什么新变化；无法确认时明确写“公开摘要未说明此前状态”。
11. world_ai_impact 说明对全球AI竞争、成本、产业落地或治理的潜在影响，
    必须区分事实与推断。
12. capital_market_observation 说明潜在受益方、承压方或需跟踪的变量，
    末尾必须包含“不构成投资建议”。
13. source_index 必须来自候选新闻，不得新增URL。
14. 所有输出使用中文。
15. 输出只能是JSON对象，不得使用Markdown代码块。

JSON格式：
{
  "opening_line": "一句话概括今日AI世界的主要变化",
  "key_events": ["重点事件1", "重点事件2", "重点事件3"],
  "items": [
    {
      "source_index": 1,
      "category": "模型与技术",
      "title_zh": "中文总结标题",
      "company_or_entity": "公司或机构",
      "published_at": "北京时间 YYYY-MM-DD HH:MM",
      "what_happened": "发生了什么",
      "changes": "主要变化",
      "news_summary": "2至4句新闻总结",
      "world_ai_impact": "对世界或AI发展的潜在影响",
      "capital_market_observation": "资本市场观察；不构成投资建议",
      "uncertainty": ""
    }
  ],
  "today_theme": "今日主线总结"
}
""".strip()


def call_deepseek(articles: list[Article]) -> dict[str, object]:
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "没有读取到 DEEPSEEK_API_KEY，请先添加 GitHub Actions Secret。"
        )

    candidates_json = json.dumps(
        candidate_payload(articles),
        ensure_ascii=False,
        separators=(",", ":"),
    )

    user_prompt = (
        f"当前北京时间日期为 {REPORT_DATE}。"
        f"候选新闻共 {len(articles)} 条。"
        f"请最多筛选 {FINAL_ITEM_COUNT} 条高价值新闻，尽量覆盖六个栏目。"
        "以下为候选新闻JSON：\n\n"
        f"{candidates_json}"
    )

    request_body = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "thinking": {"type": "disabled"},
        "max_tokens": 12000,
        "stream": False,
    }

    request = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    last_error: Exception | None = None

    for attempt in range(1, 3):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode("utf-8")
                result = json.loads(raw)

            content = (
                result.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

            if not content.strip():
                raise RuntimeError("DeepSeek 返回了空内容。")

            parsed = json.loads(content)
            print(
                "DeepSeek usage:",
                json.dumps(result.get("usage", {}), ensure_ascii=False),
            )
            return parsed

        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"DeepSeek HTTP {exc.code}: {body}"
            )
            if exc.code in {401, 402, 422}:
                break

        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc

        if attempt < 2:
            print(f"DeepSeek call failed, retrying: {last_error}", file=sys.stderr)
            time.sleep(3)

    raise RuntimeError(f"DeepSeek API 调用失败：{last_error}")


def normalize_ai_result(
    ai_result: dict[str, object],
    articles: list[Article],
) -> list[tuple[dict[str, str], Article]]:
    raw_items = ai_result.get("items", [])
    if not isinstance(raw_items, list):
        raise RuntimeError("DeepSeek JSON 中 items 不是列表。")

    normalized: list[tuple[dict[str, str], Article]] = []
    used_indexes: set[int] = set()

    fields = [
        "category",
        "title_zh",
        "company_or_entity",
        "published_at",
        "what_happened",
        "changes",
        "news_summary",
        "world_ai_impact",
        "capital_market_observation",
        "uncertainty",
    ]

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        try:
            source_index = int(raw_item.get("source_index", 0))
        except (TypeError, ValueError):
            continue

        if (
            source_index < 1
            or source_index > len(articles)
            or source_index in used_indexes
        ):
            continue

        article = articles[source_index - 1]
        item = {
            field: clean_text(str(raw_item.get(field, "")))
            for field in fields
        }

        if item["category"] not in CATEGORY_ORDER:
            continue
        if not item["title_zh"] or not item["news_summary"]:
            continue

        if "不构成投资建议" not in item["capital_market_observation"]:
            item["capital_market_observation"] = (
                item["capital_market_observation"].rstrip("。； ")
                + "；不构成投资建议。"
            )

        normalized.append((item, article))
        used_indexes.add(source_index)

        if len(normalized) == FINAL_ITEM_COUNT:
            break

    if not normalized:
        raise RuntimeError("DeepSeek 没有返回可用的新闻条目。")

    return normalized


def build_ai_report(
    ai_result: dict[str, object],
    articles: list[Article],
) -> str:
    items = normalize_ai_result(ai_result, articles)
    opening_line = clean_text(str(ai_result.get("opening_line", "")))
    today_theme = clean_text(str(ai_result.get("today_theme", "")))

    raw_key_events = ai_result.get("key_events", [])
    key_events = (
        [clean_text(str(item)) for item in raw_key_events if clean_text(str(item))]
        if isinstance(raw_key_events, list)
        else []
    )

    grouped: dict[str, list[tuple[dict[str, str], Article]]] = {
        category: [] for category in CATEGORY_ORDER
    }
    for item, article in items:
        grouped[item["category"]].append((item, article))

    covered_categories = [
        category for category in CATEGORY_ORDER if grouped[category]
    ]

    lines = [
        f"AI资本日报｜{REPORT_DATE}",
        "",
        "🤖 AI行业日报",
        opening_line
        or "今日AI行业继续围绕技术迭代、商业落地与监管治理展开。",
        "",
        "📊 今日概览",
        f"收录资讯：{len(items)}条",
        f"候选来源：最近24小时公开RSS候选 {len(articles)} 条",
        f"覆盖分类：{'、'.join(covered_categories)}",
    ]

    if key_events:
        lines.append("重点事件：" + "；".join(key_events[:5]))

    global_index = 1

    for category in CATEGORY_ORDER:
        section_items = grouped[category]
        if not section_items:
            continue

        lines.extend(
            [
                "",
                "————————————",
                f"{CATEGORY_EMOJI[category]} {category}",
                "",
            ]
        )

        for item, article in section_items:
            published_at = (
                item["published_at"]
                or article.published.astimezone(BEIJING).strftime(
                    "北京时间 %Y-%m-%d %H:%M"
                )
            )

            lines.extend(
                [
                    f"{global_index}. {item['title_zh']}",
                    f"公司/机构：{item['company_or_entity'] or '待确认'}",
                    f"发布时间：{published_at}",
                    f"发生了什么：{item['what_happened']}",
                    f"主要变化：{item['changes']}",
                    f"新闻总结：{item['news_summary']}",
                    f"对世界/AI发展的影响：{item['world_ai_impact']}",
                    f"资本市场观察：{item['capital_market_observation']}",
                ]
            )

            if item["uncertainty"]:
                lines.append(f"不确定性：{item['uncertainty']}")

            lines.extend(
                [
                    f"原始标题：{article.title}",
                    f"来源：{article.link}",
                    "",
                ]
            )
            global_index += 1

    lines.extend(
        [
            "————————————",
            "🔎 今日主线",
            today_theme
            or "继续跟踪模型能力、商业化收入、算力投入与监管变化之间的相互影响。",
        ]
    )

    return "\n".join(lines).strip()


def build_fallback_report(articles: list[Article], reason: str) -> str:
    lines = [
        f"AI资本日报｜{REPORT_DATE}",
        "",
        "🤖 AI行业日报",
        f"DeepSeek API 未能完成分析，已切换为基础候选列表。原因：{reason}",
        "",
    ]

    for index, article in enumerate(articles[:FINAL_ITEM_COUNT], start=1):
        local_time = article.published.astimezone(BEIJING).strftime(
            "%Y-%m-%d %H:%M"
        )
        lines.extend(
            [
                f"{index}. 标题：{article.title}",
                f"公司/机构：待确认",
                f"发布时间：北京时间 {local_time}",
                f"新闻内容总结：{article.summary or 'RSS未提供摘要，请打开来源核验。'}",
                "对世界/AI发展的影响：待人工判断。",
                "资本市场观察：需结合原始来源继续核验；不构成投资建议。",
                f"来源：{article.link}",
                "",
            ]
        )

    lines.extend(
        [
            "今日主线",
            "DeepSeek API 调用失败，本期未生成智能主线分析。",
        ]
    )
    return "\n".join(lines).strip()


def save_report(report: str) -> Path:
    output_dir = Path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{REPORT_DATE}.md"
    output_path.write_text(report + "\n", encoding="utf-8")
    return output_path


def split_report(report: str, max_chars: int = 3500) -> list[str]:
    paragraphs = report.split("\n\n")
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)

        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for start in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[start : start + max_chars])
            current = ""

    if current:
        chunks.append(current)

    if len(chunks) <= 1:
        return chunks

    total = len(chunks)
    return [
        (
            f"AI资本日报｜{REPORT_DATE}｜第{index}/{total}部分\n\n"
            + chunk.removeprefix(f"AI资本日报｜{REPORT_DATE}\n\n")
        )
        for index, chunk in enumerate(chunks, start=1)
    ]


def send_feishu_message(webhook_url: str, text: str) -> None:
    payload = {
        "msg_type": "text",
        "content": {"text": text},
    }

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
        result = json.loads(body)
        print("Feishu response:", body)

    code = result.get("code")
    status_code = result.get("StatusCode")
    if code not in (None, 0) or status_code not in (None, 0):
        raise RuntimeError(f"飞书返回错误：{result}")


def send_to_feishu(report: str) -> None:
    webhook_url = os.getenv("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook_url:
        raise RuntimeError("没有读取到 FEISHU_WEBHOOK_URL。")

    chunks = split_report(report)
    for index, chunk in enumerate(chunks, start=1):
        send_feishu_message(webhook_url, chunk)
        print(f"Sent Feishu message {index}/{len(chunks)}.")
        time.sleep(1)


def main() -> None:
    articles = collect_candidates()
    print(f"Selected {len(articles)} candidates for DeepSeek.")

    if not articles:
        report = build_fallback_report([], "最近24小时没有收集到候选新闻。")
    else:
        try:
            ai_result = call_deepseek(articles)
            report = build_ai_report(ai_result, articles)
        except Exception as exc:
            print(f"DeepSeek processing failed: {exc}", file=sys.stderr)
            report = build_fallback_report(articles, str(exc))

    output_path = save_report(report)
    print(f"Saved report to {output_path}")
    print(report)

    send_to_feishu(report)
    print("Report sent to Feishu successfully.")


if __name__ == "__main__":
    main()
