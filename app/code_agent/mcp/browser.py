import re

from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from mcp.server.fastmcp import FastMCP

import time
import random

# === Linux: 用匹配 Chrome 154 的 chromedriver ===
service = Service('/usr/local/bin/chromedriver')

# Windows 下可以这样指定（按需取消注释）
# service = Service('D:/app/chromedriver-win64/chromedriver.exe')

mcp = FastMCP()


def create_driver_window():
    """创建带基本反检测配置的 Chrome 驱动（有界面场景）"""
    options = Options()
    options.binary_location = "/usr/bin/google-chrome"   # 关键：用 Google Chrome

    # options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    # options.add_argument("--disable-blink-features=AutomationControlled")
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
    )
    return driver


def create_driver_linux():
    options = Options()

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=0")
    options.add_argument("--headless=new")
    options.binary_location = "/usr/bin/google-chrome"

    # === 反检测加强 ===
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36"
    )
    options.add_argument("--lang=zh-CN")

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)

    # === 更完整的 CDP 注入 ===
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','zh']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = { runtime: {} };
        """
    })
    return driver


def open_chrome():
    driver = create_driver_linux()
    try:
        driver.get("https://www.baidu.com")
        driver.execute_script('window.open("http://www.sogou.com","_blank");')

        all_handles = driver.window_handles
        print(all_handles)

        driver.switch_to.window(all_handles[0])
    finally:
        driver.quit()


def scroll_to_bottom(driver, max_scrolls=10, pause=0.5):
    """滚动到底部，触发懒加载，直到页面高度不再变化"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    stable_count = 0

    for _ in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause + random.uniform(0.3, 0.8))

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            stable_count += 1
            if stable_count >= 2:
                break
        else:
            stable_count = 0
            last_height = new_height

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.3)


# @mcp.tool(name='search query word in Baidu')
def search_in_baidu(query: str) -> str:
    driver = create_driver_linux()
    try:
        driver.get("https://www.baidu.com")

        text_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='chat-textarea' or @id='kw']")
            )
        )
        text_box.send_keys(query)
        time.sleep(random.uniform(0.5, 1))

        try:
            submit_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//*[@id='chat-submit-button' or @id='ci-submit-button' or @id='su']")
                )
            )
            submit_button.click()
        except Exception:
            from selenium.webdriver.common.keys import Keys
            text_box.send_keys(Keys.ENTER)

        WebDriverWait(driver, 20).until(EC.title_contains(query[:10]))

        page_text_list = []
        for i in range(3):
            if i > 0:
                print("当前页数：", i + 1)
                old_url = driver.current_url

                next_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".page-inner_2jZi2 > a.next_d-g2R")
                    )
                )
                driver.execute_script("arguments[0].click();", next_btn)

                WebDriverWait(driver, 10).until(lambda d: d.current_url != old_url)
                time.sleep(random.uniform(1, 2))

            scroll_to_bottom(driver, max_scrolls=10)

            page_content = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            page_text_list.append(f"第{i + 1}页\n" + page_content.text + "\n --- \n")
        return page_text_list

    except Exception as e:
        print(f"出错: {e}")
        return ""
    finally:
        driver.quit()


def pretty_html(html: str) -> str:
    print('没有优化：', len(html))
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(['script', 'style', 'link', 'meta', 'symbol', 'path', 'canvas', 'svg']):
        tag.extract()

    display_none_re = re.compile(r"display\s*:\s*none", re.IGNORECASE)
    for tag in soup.find_all(True):
        style = tag.get('style', '')
        if display_none_re.search(style):
            tag.extract()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.find_all(True):
        if tag.name == 'a':
            if 'href' in tag.attrs:
                if 'javascript:' in tag.attrs['href'] or '/' == tag.attrs['href']:
                    tag.extract()
                else:
                    tag.attrs = {'href': tag.attrs['href']}
        else:
            tag.attrs = {}

    result = soup.prettify()
    print("优化后：", len(result))
    return result


@mcp.tool(name='search query word in Baidu')
def search_in_baidu_with_html(query: str) -> str:
    driver = create_driver_linux()
    try:
        driver.get("https://www.baidu.com")

        text_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='chat-textarea' or @id='kw']")
            )
        )
        text_box.send_keys(query)
        time.sleep(random.uniform(0.5, 1))

        try:
            submit_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH,
                     "//*[@id='chat-submit-button' or @id='ci-submit-button' or @id='su']")
                )
            )
            submit_button.click()
        except Exception:
            from selenium.webdriver.common.keys import Keys
            text_box.send_keys(Keys.ENTER)

        WebDriverWait(driver, 20).until(EC.title_contains(query[:10]))

        page_text_list = []
        for i in range(1):
            if i > 0:
                print("当前页数：", i + 1)
                old_url = driver.current_url

                next_btn = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".page-inner_2jZi2 > a.next_d-g2R")
                    )
                )
                driver.execute_script("arguments[0].click();", next_btn)

                WebDriverWait(driver, 10).until(lambda d: d.current_url != old_url)
                time.sleep(random.uniform(1, 2))

            scroll_to_bottom(driver, max_scrolls=10)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            page_content = driver.find_element(By.TAG_NAME, "body")
            page_text = page_content.get_attribute("innerHTML")
            page_text_list.append(page_text)

        html = '\n'.join(page_text_list)
        return pretty_html(html)

    except Exception as e:
        print(f"出错: {e}")
        return ""
    finally:
        driver.quit()


if __name__ == "__main__":
    # mcp.run(transport='stdio')
    result = search_in_baidu_with_html("江门的天气")
    print(result[:2000] if result else "（无结果）")


r"""
控制我们已经登录过某些网站的浏览器，就是保持登录态
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList '--remote-debugging-port=9222','--user-data-dir="D:\selenium_profile"'
"""