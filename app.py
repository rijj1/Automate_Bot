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

def find_category_id(category_name):
    """Find the category ID based on the category name."""
    categories = {
        1: "Antivirus firewall",
        2: "Audio / Video editors",
        3: "Backup",
        4: "Common Software",
        5: "Compressor",
        6: "Converter",
        7: "Copy CD DVD Blue-Ray",
        8: "Data Recovery",
        9: "Dictionary",
        10: "Disk ISO archive editor",
        11: "Driver",
        12: "E-Learning",
        13: "Engineering specialized",
        14: "File Manager",
        15: "File Manager",
        16: "Graphic",
        17: "Hard Disk partition manager",
        18: "Internet",
        19: "Mobile",
        20: "Mobile Tools",
        21: "Network / Server",
        22: "Office PDF",
        23: "Operating System",
        24: "Optimizer",
        25: "Player",
        26: "Programming",
        27: "System",
        28: "Theme",
        29: "Utility",
        30: "Video Tutorial",
        31: "WordPress Theme"
    }
    category_name_first_part = category_name.split(",")[0].strip().lower()
    for category_id, name in categories.items():
        category_first_part = name.split(",")[0].strip().lower()
        if category_first_part == category_name_first_part:
            return category_id
    return None


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
                category_id = find_category_id(info["category"])
                if category_id is None:
                    log_message = f"❌ Category not found for URL: {url}"
                    print(log_message)
                    logging.error(log_message)
                    category_id = 32  # Default to "Other" category if not found
                    continue

                # Map scraped data to the new format
                slug = url.replace("https://downloadlynet.ir/", "").replace("/", "-").rstrip("-")
                formatted_data = {
                    "lang_id": 1,
                    "title": info["title"],
                    "slug": slug,
                    "keywords": info["tags"],
                    "summary": info["title"],
                    "content": info["content"],
                    "category_id": category_id,
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