import os
import requests
from datetime import datetime, timedelta

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def get_gaming_news():
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    queries = ['gaming scandal streamer', 'game release announcement', 'esports drama', 'gaming news']
    all_articles = []
    for query in queries:
        params = {
            'q': query,
            'from': yesterday,
            'sortBy': 'popularity',
            'language': 'en',
            'pageSize': 5,
            'apiKey': NEWSAPI_KEY
        }
        try:
            r = requests.get("https://newsapi.org/v2/everything", params=params, timeout=10)
            data = r.json()
            if data.get('articles'):
                all_articles.extend(data['articles'][:3])
        except Exception as e:
            print(f"NewsAPI error: {e}")
    seen = set()
    unique = []
    for a in all_articles:
        t = a.get('title', '')
        if t and t not in seen and '[Removed]' not in t:
            seen.add(t)
            unique.append(a)
    return unique[:10]

def generate_post(articles):
    if not articles:
        news_text = "Придумай актуальную тему из мира гейминга или киберспорта"
        image_url = None
    else:
        news_text = "\n\n".join([
            f"- {a.get('title', '')}: {a.get('description', '')}"
            for a in articles
        ])
        image_url = None
        for a in articles:
            if a.get('urlToImage'):
                image_url = a['urlToImage']
                break

    prompt = f"""Ты пишешь посты от имени Вероники - автора Telegram-канала о гейминге для русскоязычной аудитории.

Вот примеры её постов (изучи стиль):

Пример 1:
Мои хорошие, всем доброе утро и классного дня 🐱

Какой же жирненький месяц выходит, игра за игрой, хотя слышала весь год таким будет!

Помню у меня тут кто-то из вас говорил про Бонда. Глядите, какую новость нашла!

🦋**007 FIRST LIGHT** выходит 27 мая

Молодой Бонд до того, как стал Бондом. Делают создатели Hitman (не играла пока) - те самые, у которых можно убить злодея люстрой.

Стелс, гаджеты, погони. Или можно забить на стелс и просто стрелять, как в Резике 😸

Слухи ходят о том что это следующая «игра года». Посмотрим 😊

👎 Вы вообще в шпионские игры играете или тоже сразу на штурм?
Кто-то точно да. Я лично еще не пробовала.

Ждете игру? 🤩

Пример 2:
GTA 6: ДАТА, КОТОРУЮ БОЯТСЯ СГЛАЗИТЬ

**19 ноября 2026 - теперь официально.** Но фанаты уже не верят на слово: эту игру переносили дважды 😎

В этот раз есть железный аргумент - деньги. Take-Two заложила GTA 6 в прогноз на 💵 8 миллиардов выручки. Гендиректор прямо назвал релиз главным драйвером года. Подвинут дату - рухнет вся финансовая отчётность.

Я в GTA даже не вкатилась толком, но азарт вокруг чувствую за версту 😎

👎 **Ваши ставки: ноябрь или опять «ещё чуть-чуть»?**

---

Вот свежие новости:
{news_text}

Выбери ОДНУ самую интересную новость и напиши пост в стиле Вероники.

Правила:
- Пиши от первого лица как Вероника
- Короткие абзацы, каждый на отдельной строке
- Тире только через дефис `-`, никогда не используй длинное тире `—`
- Название игры/события выдели **жирным**
- Можно честно признать что не играла в игру
- 2-4 эмодзи в тексте, в конце абзацев
- Заканчивай вопросом к аудитории
- Без хэштегов
- Только текст поста, никаких пояснений"""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
        data = r.json()
        if 'content' in data:
            return data['content'][0]['text'].strip(), image_url
        else:
            print(f"Claude error: {data}")
            return None, None
    except Exception as e:
        print(f"Claude request error: {e}")
        return None, None

def send_preview(text, image_url=None):
    caption = f"📋 Предпросмотр поста на сегодня:\n\n{text}\n\n⬇️ Одобрить и опубликовать или пропустить?"

    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Одобрить", "callback_data": "approve"},
            {"text": "❌ Пропустить", "callback_data": "skip"}
        ]]
    }

    if image_url:
        try:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": image_url,
                "caption": caption,
                "reply_markup": keyboard
            }
            r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", json=payload, timeout=15)
            data = r.json()
            if data.get('ok'):
                print("✅ Превью с картинкой отправлено в Telegram!")
                return True
            else:
                print(f"Photo send failed: {data}, trying text only...")
        except Exception as e:
            print(f"Photo error: {e}, trying text only...")

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    try:
        r = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json=payload, timeout=10)
        data = r.json()
        if data.get('ok'):
            print("✅ Превью отправлено в Telegram!")
            return True
        else:
            print(f"Telegram error: {data}")
            return False
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def main():
    print(f"🎮 Запуск бота - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("📰 Собираю новости...")
    articles = get_gaming_news()
    print(f"   Найдено статей: {len(articles)}")
    print("🤖 Генерирую пост через Claude...")
    post, image_url = generate_post(articles)
    if not post:
        print("❌ Не удалось сгенерировать пост")
        return
    print(f"📝 Пост готов:\n{post}\n")
    if image_url:
        print(f"🖼 Картинка: {image_url}")
    print("📤 Отправляю превью в Telegram...")
    send_preview(post, image_url)

if __name__ == "__main__":
    main()