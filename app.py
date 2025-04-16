import scrapper_bot
import poster_bot
import logging

sitemap_csv = "sitemap.csv"  # Define the path to your sitemap CSV file
log_file = "logs.txt"  # Define the path to your log file

# Configure logging to log to both console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),  # Log to logs.txt
        logging.StreamHandler()        # Log to console
    ]
)

def load_checkpoints():
    """Load URLs from the checkpoint file to avoid re-scraping."""
    try:
        with open(poster_bot.CHECKPOINT_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    except FileNotFoundError:
        return set()

if __name__ == "__main__":
    processed_urls = load_checkpoints()

    # Initialize the scraper bot
    with open(sitemap_csv) as f:
        sitemap_urls = [line.strip() for line in f.readlines()]
        for sitemap_url in sitemap_urls:
            urls = scrapper_bot.extract_post_links_from_sitemap(sitemap_url)
            for url in urls:
                if url in processed_urls:
                    log_message = f"⏩ Skipping already processed URL: {url}"
                    print(log_message)
                    logging.info(log_message)
                    continue

                log_message = f"📝 Scraping: {url}"
                print(log_message)
                logging.info(log_message)
                info = scrapper_bot.scrape_page_info(url)

                # Map scraped data to the new format
                slug = url.replace("https://downloadlynet.ir/", "").replace("/", "-").rstrip("-")
                formatted_data = {
                    "lang_id": 1,
                    "title": info["title"],
                    "slug": slug,
                    "keywords": info["tags"],
                    "summary": info["title"],
                    "content": info["content"],
                    "category_id": 1,
                    "post_type": 'article',
                    "video_embed_code": "",
                    "status": 1,
                    "image_url": info["image_url"],
                    "image_description": info["title"],
                    "tags": info["tags"]
                }

                posting = poster_bot.process_data(formatted_data)

                if posting:
                    log_message = f"✅ Successfully posted: {info['title']}"
                    print(log_message)
                    logging.info(log_message)
                    poster_bot.save_checkpoint(url)  # Save the URL to checkpoint file
                else:
                    log_message = f"❌ Failed to post: {info['title']}"
                    print(log_message)
                    logging.error(log_message)
                    poster_bot.save_failed_upload(url)  # Save failed post URL