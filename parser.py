from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Locator

from storage import Storage
from logger import logger


class BankruptParser:
    def __init__(self, storage: Storage) -> None:
        self._url = "https://bankrot.fedresurs.ru/bankrupts"
        self._storage = storage
        self._user_data_dir = "./tmp"

    async def start(
        self, data: dict[str, str] | list[dict[str, str]], debug: bool = False
    ):
        logger.info("Browser initialization...")
        async with async_playwright() as p:
            browser_type = p.chromium
            browser = await browser_type.launch_persistent_context(
                self._user_data_dir,
                headless=not debug,
                viewport=None,
                channel="chromium",
                args=[
                    "--start-maximized",
                    "--enable-javascript",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--allow-insecure-localhost",
                    "--ignore-certificate-errors",
                    "--user-agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:72.0) Gecko/20100101 Firefox/72.0'",
                ],
            )

            await self.__run(data, browser)

            logger.info("Browser close")
            await browser.close()

    async def __run(
        self, data: dict[str, str] | list[dict[str, str]], context: BrowserContext
    ):
        logger.info("Start parsing")
        if isinstance(data, dict):
            result = await self._check_user(
                context, username=data["username"], birthday=data["birthday"]
            )
            self._storage.add(result)
        elif isinstance(data, list):
            for data_item in data:
                result = await self._check_user(
                    context,
                    username=data_item["username"],
                    birthday=data_item["birthday"],
                )
                self._storage.add(result)

    async def _check_user(self, context: BrowserContext, username: str, birthday: str):
        logger.info(f"Check user {username} {birthday}")
        page = await context.new_page()
        await page.goto(self._url)
        await page.wait_for_load_state("domcontentloaded")
        _input = page.locator("xpath=//input[@formcontrolname='searchString']")
        await _input.fill(username)
        await _input.press("Enter")
        await page.wait_for_timeout(2000)

        cards_block = page.locator("//app-bankrupt-result-persons")
        cards = cards_block.locator("xpath=.//app-bankrupt-result-card-person")
        cards_count = await cards.count()

        logger.info(f"{cards_count} user cards found")

        if cards_count > 1:
            all_cards = await cards.all()
        elif cards_count == 1:
            all_cards = [cards]
        else:
            return self._get_user_card(False, username=username, birthday=birthday)

        for card in all_cards:
            answer = await self._check_card(context, card, birthday, username)
            if answer["found"]:
                return answer
            else:
                return self._get_user_card(False, username=username, birthday=birthday)
        return self._get_user_card(False, username=username, birthday=birthday)

    async def _check_card(
        self, context: BrowserContext, card: Locator, birthday: str, username: str
    ):
        async with context.expect_page() as new_tab_event:
            await card.locator("xpath=.//a").click()
            new_tab = await new_tab_event.value
        await new_tab.wait_for_selector(".info-item", state="visible")

        info = new_tab.locator("xpath=//div[@class='info-item']")

        is_valid = await self._data_is_valid(
            await info.all(), "дата рождения", birthday
        )

        return self._get_user_card(
            is_valid, username=username, birthday=birthday, link=new_tab.url
        )

    async def _data_is_valid(
        self, items: list[Locator], target_field: str, control_data: str
    ):
        logger.info(f"Check control_data {control_data}")
        for item in items:
            title = await item.locator(".info-item-name").text_content()
            if title and title.strip().lower() == target_field:
                value = await item.locator(".info-item-value").text_content()
                if value == control_data:
                    logger.info("Target found")
                    return True
        return False

    def _get_user_card(
        self,
        found: bool,
        *,
        username: str,
        birthday: str,
        link: Optional[str] = None,
    ):
        return {
            "found": found,
            "username": username,
            "birthday": birthday,
            "link": link,
        }
