import mysql.connector
from mysql.connector import Error
import json
import requests

# Load configuration from config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

api_url = config["api_url"]
mysql_config = config["mysql_config"]
cookies = config["cookies"]

CHECKPOINT_FILE = "checkpoint.txt"
FAILED_UPLOADS_FILE = "failed_uploads.txt"

def save_checkpoint(url):
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(url + "\n")

def save_failed_upload(url):
    with open(FAILED_UPLOADS_FILE, "a") as f:
        f.write(url + "\n")

def process_data(data):
    try:
        connection = mysql.connector.connect(**mysql_config)
        cursor = connection.cursor()

        # Ensure the parameter is passed as a tuple
        cursor.execute("SELECT id FROM posts WHERE slug = %s", (data['slug'],))  # Add a comma to make it a tuple
        existing_record = cursor.fetchone()

        if existing_record:
            update_post_query = """
            UPDATE `posts`
            SET `title` = %s, `keywords` = %s, `summary` = %s, `content` = %s, `category_id` = %s,
                `image_url` = %s, `image_description` = %s, `updated_at` = NOW()
            WHERE `slug` = %s
            """
            cursor.execute(update_post_query, (
                data['title'],
                data['keywords'],
                data['summary'],
                data['content'],
                data['category_id'],
                data['image_url'],
                data['image_description'],
                data['slug']  # Ensure this is part of the tuple
            ))
            connection.commit()
            post_id = existing_record[0]
            print(f"Post updated with ID: {post_id}")

        else:
            insert_post_query = """
            INSERT INTO `posts` (`lang_id`, `title`, `slug`, `title_hash`, `keywords`, `summary`, `content`, `category_id`, `image_id`, `optional_url`, `pageviews`, `comment_count`, `need_auth`, `slider_order`, `featured_order`, `is_scheduled`, `visibility`, `show_right_column`, `post_type`, `video_path`, `video_storage`, `image_url`, `video_url`, `video_embed_code`, `user_id`, `status`, `feed_id`, `post_url`, `show_post_url`, `image_description`, `show_item_numbers`, `is_poll_public`, `link_list_style`, `recipe_info`, `post_data`, `updated_at`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            post_data = (
                1,
                data['title'],
                data['slug'],
                None,
                data['keywords'],
                data['summary'],
                data['content'],
                data['category_id'],
                None, None, 0, 0, 0, 1, 1, 0, 1, 1, 'article', None, 'local',
                data['image_url'],
                None, None, 1, 1, None, None, 0,
                data['image_description'],
                0, 1, 'a:3:{i:1;a:2:{s:5:\"style\";s:4:\"none\";s:6:\"status\";i:0;}i:2;a:2:{s:5:\"style\";s:4:\"none\";s:6:\"status\";i:0;}i:3;a:2:{s:5:\"style\";s:4:\"none\";s:6:\"status\";i:0;}}',
                None, None, None,
            )
            
            cursor.execute(insert_post_query, post_data)
            post_id = cursor.lastrowid
            connection.commit()
            print(f"Post inserted with ID: {post_id}")

    except Error as e:
        print(f"Error: {e}")
        return False

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    # Convert tags to JSON format
    tags = data['tags']
    tags_list = [{"value": tag.strip()} for tag in tags.split(",")]
    tags_json = json.dumps(tags_list)  # Serialize to a JSON string

    api_payload = {
        "postId": post_id,
        "tags": tags_json
    }
    
    try:
        response = requests.post(api_url, json=api_payload, headers={'Content-Type': 'application/json'}, cookies=cookies)
        if response.status_code == 200:
            print("API Response:", response.json())
            return True
        else:
            print("API Error:", response.status_code, response.text)
            return False
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")