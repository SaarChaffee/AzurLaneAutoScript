
from module.exception import ScriptError
from module.logger import logger
from module.os_shop.assets import PORT_SUPPLY_CHECK, SHOP_BUY_CONFIRM
from module.os_shop.akashi_shop import AkashiShop
from module.os_shop.port_shop import PortShop
from module.os_shop.ui import OS_SHOP_SCROLL
from module.shop.assets import AMOUNT_MAX, SHOP_BUY_CONFIRM_AMOUNT, SHOP_BUY_CONFIRM as OS_SHOP_BUY_CONFIRM
from module.shop.clerk import OCR_SHOP_AMOUNT

class OSShop(PortShop, AkashiShop):
    def os_shop_buy_execute(self, button, skip_first_screenshot=True) -> bool:
        """
        Args:
            button: Item to buy
            skip_first_screenshot:

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        success = False
        self.interval_clear(PORT_SUPPLY_CHECK)
        self.interval_clear(SHOP_BUY_CONFIRM)
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)
        self.interval_clear(OS_SHOP_BUY_CONFIRM)

        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_map_get_items(interval=1):
                self.interval_reset(PORT_SUPPLY_CHECK)
                success = True
                continue

            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=1):
                self.interval_reset(SHOP_BUY_CONFIRM)
                continue

            if self.appear_then_click(OS_SHOP_BUY_CONFIRM, offset=(20, 20), interval=1):
                self.interval_reset(OS_SHOP_BUY_CONFIRM)
                continue

            if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=1):
                self.shop_buy_amount_handler(button)
                self.device.click(SHOP_BUY_CONFIRM_AMOUNT)
                self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
                continue

            if not success and self.appear(PORT_SUPPLY_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue

            # End
            if success and self.appear(PORT_SUPPLY_CHECK, offset=(20, 20)):
                break

        return success

    def os_shop_buy(self, select_func) -> int:
        """
        Args:
            select_func:
        @@ -213,20 +341,131 @@ def os_shop_buy(self, select_func):
            in: PORT_SUPPLY_CHECK
        """
        count = 0
        for _ in range(12):
            button = select_func()
            if button is None:
                logger.info('Shop buy finished')
                return count
            else:
                self.os_shop_buy_execute(button)
                self.os_shop_get_coins()
                count += 1
                continue

        logger.warning('Too many items to buy, stopped')
        return count

    def shop_buy_amount_handler(self, item):
        """
        Handler item amount to buy.

        Args:
            currency (int): Coins currently had.
            price (int): Item price.
            skip_first_screenshot (bool, optional): Defaults to True.

        Raises:
            ScriptError: OCR_SHOP_AMOUNT

        Returns:
            bool: True if amount handler finished.
        """
        currency = self._shop_yellow_coins if item.cost == 'YellowCoins' else self._shop_purple_coins

        total = int(currency // item.price)

        if total == 1:
            return

        if self.appear(AMOUNT_MAX, offset=(50, 50)):
            limit = None
            for _ in range(3):
                self.appear_then_click(AMOUNT_MAX, offset=(50, 50))
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()
                limit = OCR_SHOP_AMOUNT.ocr(self.device.image)
                if limit and limit > 1:
                    break
            if not limit:
                logger.critical('OCR_SHOP_AMOUNT resulted in zero (0); '
                                'asset may be compromised')
                raise ScriptError

    def handle_port_supply_buy(self) -> bool:
        """
        Returns:
            bool: True if success to buy any or no items found.
                False if not enough coins to buy any.

        Pages:
            in: PORT_SUPPLY_CHECK
        """
        _count = 0
        temp_queue = self.device.click_record
        self.device.click_record.clear()

        for i in range(4):
            count = 0
            self.os_shop_side_navbar_ensure(upper=i + 1)
            pre_pos, cur_pos = self.init_slider()

            while True:
                pre_pos = self.pre_scroll(pre_pos, cur_pos)
                count += self.os_shop_buy(select_func=self.os_shop_get_item_to_buy_in_port)

                if count >= 10:
                    logger.info('This shop reach max buy count, go to next shop')
                    break
                elif OS_SHOP_SCROLL.at_bottom(main=self):
                    logger.info('OS shop reach bottom, stop')
                    break
                else:
                    OS_SHOP_SCROLL.next_page(main=self, page=0.5)
                    cur_pos = OS_SHOP_SCROLL.cal_position(main=self)
                    continue
            _count += count
            self.device.click_record.clear()

        self.device.click_record = temp_queue
        return _count > 0 or len(self.os_shop_items.items) == 0

    def handle_akashi_supply_buy(self, grid):
        """
        Args:
            grid: Grid where akashi stands.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        self.ui_click(grid, appear_button=self.is_in_map, check_button=PORT_SUPPLY_CHECK,
                      additional=self.handle_story_skip, skip_first_screenshot=True)
        self.os_shop_buy(select_func=self.os_shop_get_item_to_buy_in_akashi)
        self.ui_back(appear_button=PORT_SUPPLY_CHECK, check_button=self.is_in_map, skip_first_screenshot=True)
