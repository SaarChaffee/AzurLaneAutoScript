from module.base.button import Button, ButtonGrid
from module.base.decorator import cached_property
from module.base.template import Template
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import DigitYuv
from module.os_handler.map_event import MapEventHandler
from module.os_handler.os_status import OSStatus
from module.os_shop.selector import Selector
from module.os_shop.ui import OSShopPrice, OSShopUI
from module.statistics.item import ItemGrid

TEMPLATE_YELLOW_COINS = Template('./assets/shop/os_cost/YellowCoins_1.png')
TEMPLATE_PURPLE_COINS = Template('./assets/shop/os_cost/PurpleCoins_1.png')
TEMPLATE_YELLOW_COINS_SOLD_OUT = Template('./assets/shop/os_cost_sold_out/YellowCoins.png')
TEMPLATE_PURPLE_COINS_SOLD_OUT = Template('./assets/shop/os_cost_sold_out/PurpleCoins.png')
TEMPLATES = [TEMPLATE_YELLOW_COINS, TEMPLATE_PURPLE_COINS, TEMPLATE_YELLOW_COINS_SOLD_OUT, TEMPLATE_PURPLE_COINS_SOLD_OUT]

class PortShop(OSStatus, OSShopUI, Selector, MapEventHandler):
    _shop_yellow_coins = 0
    _shop_purple_coins = 0

    def os_shop_get_coins(self):
        self._shop_yellow_coins = self.get_yellow_coins()
        self._shop_purple_coins = self.get_purple_coins()
        logger.info(f'Yellow coins: {self._shop_yellow_coins}, purple coins: {self._shop_purple_coins}')

    def _get_os_shop_cost(self) -> list:
        """
        Returns the coordinates of the upper left corner of each coin icon.

        Returns:
            list:
        """
        image = self.image_crop((360, 320, 410, 720))
        result = sum([template.match_multi(image) for template in TEMPLATES], [])
        logger.info(f'Costs: {result}')
        return Points([(0., m.area[1]) for m in result]).group(threshold=5)

    @cached_property
    def os_shop_items(self) -> ItemGrid:
        os_shop_items = ItemGrid(
            grids=None, templates={}, amount_area=(77, 77, 96, 96), price_area=(52, 132, 130, 165))
        os_shop_items.price_ocr = OSShopPrice([], letter=(255, 223, 57), threshold=32, name='Price_ocr')
        os_shop_items.load_template_folder('./assets/shop/os')
        os_shop_items.load_cost_template_folder('./assets/shop/os_cost')
        return os_shop_items

    def _get_os_shop_grid(self, cost) -> ButtonGrid:
        """
        Returns shop grid.

        Args:
            cost: The coordinates of the upper left corner of coin icon.

        Returns:
            ButtonGris:
        """
        y = 320 + cost[1] - 130

        return ButtonGrid(
            origin=(356, y), delta=(160, 0), button_shape=(98, 98), grid_shape=(5, 1), name='OS_SHOP_GRID')

    def os_shop_get_items(self, name=True) -> list:
        """
        Args:
            name (bool): If detect item name. True if detect akashi shop, false if detect port shop.

        Returns:
            list[Item]:
        """
        items = []
        costs = self._get_os_shop_cost()

        for cost in costs:
            self.os_shop_items.grids = self._get_os_shop_grid(cost)
            if self.config.SHOP_EXTRACT_TEMPLATE:
                self.os_shop_items.extract_template(self.device.image, './assets/shop/os')
            self.os_shop_items.predict(self.device.image, name=name, amount=name, cost=True, price=True)
            shop_items = self.os_shop_items.items

            if len(shop_items):
                row = [str(item) for item in shop_items]
                logger.info(f'Shop items found: {row}')
                items += shop_items
            else:
                logger.info('No shop items found')

        return items

    def os_shop_get_item_to_buy_in_port(self) -> Button:
        """
        Returns:
            list[Item]:
        """
        self.os_shop_get_coins()
        items = self.os_shop_get_items(name=True)
        logger.attr('CL1 enabled', self.is_cl1_enabled)

        for _ in range(2):
            if not len(items) or any('Empty' in item.name for item in items):
                logger.warning('Empty OS shop or empty items, confirming')
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()
                items = self.os_shop_get_items(name=True)
                continue
            else:
                items = self.items_filter_in_os_shop(items)
                if not len(items):
                    return None
                else:
                    return items.pop()

        return None
