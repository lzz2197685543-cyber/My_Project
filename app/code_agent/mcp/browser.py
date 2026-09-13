from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from mcp.server.fastmcp import FastMCP

import time
import random

service = Service('D:/app/chromedriver-win64/chromedriver.exe')

mcp = FastMCP()
def create_driver():
    """创建带基本反检测配置的 Chrome 驱动"""
    options = Options()

    # 核心：关闭自动化特征 + 移除自动化提示
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=service,options=options)

    # 核心：隐藏 navigator.webdriver
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
    )

    return driver

def scroll_to_bottom(driver, max_scrolls=10, pause=0.5):
    """滚动到底部，触发懒加载，直到页面高度不再变化"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    stable_count = 0  # 连续多少次高度没变，才算真的加载完

    for _ in range(max_scrolls):
        # 滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # 随机延时，模拟人工
        time.sleep(pause + random.uniform(0.3, 0.8))

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            stable_count += 1
            # 连续 2 次高度没变，认为加载完成
            if stable_count >= 2:
                break
        else:
            stable_count = 0
            last_height = new_height

    # 滚动回顶部（可选，让后续操作从顶部开始）
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.3)


@mcp.tool(name='search query word in Baidu')
def search_in_baidu(query: str) -> str:
    driver = create_driver()

    try:
        driver.get("https://www.baidu.com")

        # 输入框：兼容 AI 版(chat-textarea) 和 普通版(kw)
        text_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='chat-textarea' or @id='kw']")
            )
        )
        text_box.send_keys(query)
        time.sleep(random.uniform(0.5, 1))

        # 搜索按钮：兼容 AI 版(chat-submit-button/ci-submit-button) 和 普通版(su)
        # 找不到就按回车
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

        # 等待结果
        WebDriverWait(driver, 20).until(EC.title_contains(query[:10]))

        # 翻页优化
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

            # 滚动加载全部内容
            scroll_to_bottom(driver, max_scrolls=10)

            # 滚动完重新获取 body，避免 stale
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


if __name__ == "__main__":
    mcp.run(transport='stdio')
    # result=search_in_baidu("江门的天气")
    # print(result)