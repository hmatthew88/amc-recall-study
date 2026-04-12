import os
import asyncio
import json
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_id = os.getenv('TG_API_ID')
api_hash = os.getenv('TG_API_HASH')

# Support multiple groups via comma-separated TG_GROUP_LINKS (falls back to TG_GROUP_LINK for compatibility)
def get_group_links():
    links_str = os.getenv('TG_GROUP_LINKS') or os.getenv('TG_GROUP_LINK')
    if not links_str:
        links_str = input("Please enter one or more Group Links or IDs (comma-separated): ")
    return [link.strip() for link in links_str.split(',') if link.strip()]

async def scrape_group(client, group_identifier, download_dir, output_file):
    """Scrape a single Telegram group and merge results into the shared output file."""
    try:
        entity = await client.get_entity(group_identifier)
        group_title = entity.title
        print(f"\n=== Scraping group: {group_title} ({group_identifier}) ===")

        existing_messages = []
        last_id_for_group = 0

        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_messages = json.load(f)
                # Find the last message ID that belongs to THIS group
                group_messages = [m for m in existing_messages if m.get('source_group') == group_title]
                if group_messages:
                    last_id_for_group = max(m['id'] for m in group_messages)
                    print(f"  Found existing data for '{group_title}'. Last message ID: {last_id_for_group}")
            except Exception as e:
                print(f"  Could not load existing data: {e}")

        new_messages = []

        if last_id_for_group > 0:
            print(f"  Fetching new messages since ID {last_id_for_group}...")
            async for message in client.iter_messages(entity, min_id=last_id_for_group):
                data = await process_message(message, download_dir, group_title)
                if data:
                    new_messages.append(data)
        else:
            two_months_ago = datetime.now(timezone.utc) - timedelta(days=60)
            print(f"  Initial run. Fetching messages since: {two_months_ago.strftime('%Y-%m-%d %H:%M:%S')} UTC (last 2 months)")
            async for message in client.iter_messages(entity):
                if message.date < two_months_ago:
                    break
                data = await process_message(message, download_dir, group_title)
                if data:
                    new_messages.append(data)

        print(f"  Fetched {len(new_messages)} new message(s) from '{group_title}'.")

        # Merge with existing, deduplicate by (id, source_group)
        all_messages = new_messages + existing_messages
        seen = set()
        unique_messages = []
        for m in all_messages:
            key = (m['id'], m.get('source_group', ''))
            if key not in seen:
                unique_messages.append(m)
                seen.add(key)

        unique_messages.sort(key=lambda x: x['id'])

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_messages, f, ensure_ascii=False, indent=4)

        print(f"  Saved. Total messages in file: {len(unique_messages)}")
        return len(new_messages)

    except Exception as e:
        print(f"Error scraping group '{group_identifier}': {e}")
        return 0


async def process_message(message, download_dir, source_group):
    """Helper to process a single message and download its media."""
    image_path = None
    if message.photo:
        print(f"  Downloading image for message {message.id}...")
        image_path = await message.download_media(file=download_dir)
        if image_path:
            image_path = os.path.basename(image_path)

    return {
        'id': message.id,
        'date': message.date.isoformat(),
        'sender_id': message.sender_id,
        'text': message.text,
        'image_path': image_path,
        'source_group': source_group,
    }


async def main():
    group_links = get_group_links()
    print(f"Groups to scrape: {group_links}")

    # Create downloads directory
    download_dir = 'downloads'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"Created directory: {download_dir}")

    output_file = 'chat_history_last_month.json'
    total_new = 0

    async with TelegramClient('session_name', api_id, api_hash) as client:
        for group_identifier in group_links:
            count = await scrape_group(client, group_identifier, download_dir, output_file)
            total_new += count

    print(f"\n=== Scraping complete. {total_new} new message(s) fetched across all groups. ===")


if __name__ == '__main__':
    asyncio.run(main())
