import requests
import bs4
import re
import pandas as pd
import poster_bot  # Import to use save_failed_upload

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
REQUEST_HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'en-US, en;q=0.5',
}

def get_page_html(url):
    try:
        res = requests.get(url=url, headers=REQUEST_HEADER, timeout=10)
        return res.content
    except requests.exceptions.ReadTimeout:
        print(f"Timeout occurred for URL: {url}")
        poster_bot.save_failed_upload(url)  # Add to failed uploads
        return None
    except Exception as e:
        print(f"Error fetching URL {url}: {e}")
        poster_bot.save_failed_upload(url)  # Add to failed uploads
        return None

def get_page_title(soup):
    try:
        main_page_title = soup.find('h2', class_="w-post-elm post_title us_custom_9de87d4e align_left entry-title color_link_inherit")
        return main_page_title.find('a').text.strip()
    except:
        return ''

# def get_download_links(soup):
#     download_links = {}
#     try:
#         download_sections = soup.find_all('h3', string=re.compile(r'download link', re.IGNORECASE))
#         for section in download_sections:
#             for link in section.find_next_siblings('p'):
#                 for child in link.findChildren('a'):
#                     download_links[child.text.strip()] = child['href']
#     except:
#         pass
#     return download_links

def get_image(soup):
    try:
        image_section = soup.find('div', class_='w-post-elm post_image us_custom_447bff20')
        return image_section.find('img')['src']
    except Exception as e:
        print(f"Error scraping Image: {e}")
        return ''

def get_category(soup):
    try:
        tag_sections = soup.find_all("div", class_="w-post-elm post_taxonomy style_simple color_link_inherit")
        if len(tag_sections) >= 1:
            category_links = tag_sections[0].find_all("a", href=True)
            return [a.text.strip() for a in category_links]
        return []
    except Exception as e:
        print(f"Error extracting categories: {e}")
        return []

def get_tags(soup):
    try:
        tag_sections = soup.find_all("div", class_="w-post-elm post_taxonomy style_simple color_link_inherit")
        if len(tag_sections) >= 2:
            tag_links = tag_sections[1].find_all("a", href=True)
            return [a.text.strip() for a in tag_links]
        return []
    except Exception as e:
        print(f"Error extracting tags: {e}")
        return []

def get_content(soup):
    try:
        content_block = soup.find("div", class_="w-post-elm post_content")
        if not content_block:
            return ''

        # Remove unwanted line: "File password" line
        for h5 in content_block.find_all("h5"):
            if "File password" in h5.text and "downloadly.ir" in h5.text:
                h5.decompose()

        # Remove unwanted heading: "Description" <h2>
        for h2 in content_block.find_all("h2"):
            if "Description" in h2.text:
                h2.decompose()

        # Collect blog-relevant elements only
        content_html = ''
        for child in content_block.contents:
            if child.name in ['h2', 'h3', 'h4', 'h5', 'p', 'ul', 'ol', 'li', 'img', 'div', 'hr']:
                content_html += str(child)

        return content_html.strip()

    except Exception as e:
        print(f"Error extracting post content: {e}")
        return ''

def scrape_page_info(url):
    html = get_page_html(url)
    if html is None:  # Check if the HTML content is None
        print(f"Failed to fetch HTML for URL: {url}")
        return None

    soup = bs4.BeautifulSoup(html, 'lxml')
    title = get_page_title(soup)
    category = get_category(soup)
    tags = get_tags(soup)
    # download_links = get_download_links(soup)
    content = get_content(soup)
    image_url = get_image(soup)
    return {
        'title': title,
        'image_url': image_url,
        'category': ", ".join(category),
        'tags': ", ".join(tags),
        'content': content,
        'scrap_url': url
    }

def extract_post_links_from_sitemap(sitemap_url):
    print(f"🔍 Reading sitemap: {sitemap_url}")
    html = get_page_html(sitemap_url)
    soup = bs4.BeautifulSoup(html, 'lxml-xml')
    return [loc.text.strip() for loc in soup.find_all("loc")]
